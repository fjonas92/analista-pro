import math
import unicodedata
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import streamlit as st


# ============================================================
# ANALISTA PRO — MOTOR REESTRUTURADO
# API: API-Football / API-Sports
#
# PRINCÍPIOS:
# 1. Não cria odds fictícias.
# 2. Não força 4 mercados por jogo.
# 3. Analisa vários mercados disponíveis e ranqueia por valor.
# 4. Probabilidade do modelo é separada da odd.
# 5. Edge e EV são calculados somente com odd real.
# 6. Justificativas são montadas a partir dos números calculados.
# 7. Dados insuficientes reduzem a confiança e podem gerar NO BET.
# ============================================================


# -----------------------------
# 1. CONFIGURAÇÃO
# -----------------------------
st.set_page_config(
    page_title="ANALISTA PRO — IA",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_BASE = "https://v3.football.api-sports.io"

# NUNCA deixe uma chave real hardcoded no código.
API_FOOTBALL_KEY = st.secrets.get("API_FOOTBALL_KEY", "")

# Opcional: limite mínimo de qualidade dos dados.
MIN_RECENT_GAMES = 5
MAX_RECENT_GAMES = 10
MAX_STATS_FIXTURES = 8

# Faixas configuráveis. Não são "verdades matemáticas":
# devem ser calibradas com backtest.
MIN_EDGE_PP = 3.0
GOOD_EDGE_PP = 6.0
EXCELLENT_EDGE_PP = 10.0
MIN_MODEL_PROB = 0.45
MIN_ODD = 1.20
MAX_ODD = 6.00

# Score técnico. Odds/mercado NÃO entram diretamente no score.
WEIGHTS = {
    "form": 0.18,
    "attack": 0.16,
    "defense": 0.16,
    "venue": 0.12,
    "goals_model": 0.14,
    "shots": 0.08,
    "corners": 0.06,
    "data_quality": 0.06,
    "h2h_residual": 0.04,
}


# -----------------------------
# 2. UTILITÁRIOS
# -----------------------------
def normalizar_texto(texto):
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFD", str(texto))
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def clamp(valor, minimo, maximo):
    return max(minimo, min(maximo, valor))


def safe_float(valor, default=None):
    try:
        if valor is None or valor == "":
            return default
        return float(valor)
    except (TypeError, ValueError):
        return default


def media(valores, default=None):
    valores = [safe_float(v) for v in valores]
    valores = [v for v in valores if v is not None]
    if not valores:
        return default
    return sum(valores) / len(valores)


def weighted_recent(values):
    """Mais peso para jogos recentes."""
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    weights = list(range(1, len(vals) + 1))
    return sum(v * w for v, w in zip(vals, weights)) / sum(weights)


def poisson_pmf(k, lam):
    if lam is None or lam <= 0:
        return 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def poisson_cdf(k, lam):
    if k < 0:
        return 0.0
    return sum(poisson_pmf(i, lam) for i in range(k + 1))


def poisson_over_probability(lam, line):
    """P(total > line), para linhas .5."""
    k = int(math.floor(line))
    return 1.0 - poisson_cdf(k, lam)


def poisson_under_probability(lam, line):
    k = int(math.floor(line))
    return poisson_cdf(k, lam)


def prob_1x2(lam_home, lam_away, max_goals=8):
    home = draw = away = 0.0

    for gh in range(max_goals + 1):
        p_h = poisson_pmf(gh, lam_home)
        for ga in range(max_goals + 1):
            p = p_h * poisson_pmf(ga, lam_away)
            if gh > ga:
                home += p
            elif gh == ga:
                draw += p
            else:
                away += p

    total = home + draw + away
    if total <= 0:
        return 0.0, 0.0, 0.0

    return home / total, draw / total, away / total


def prob_btts(lam_home, lam_away):
    p_no_home = math.exp(-lam_home)
    p_no_away = math.exp(-lam_away)
    p_no_goals = math.exp(-(lam_home + lam_away))
    return clamp(1 - p_no_home - p_no_away + p_no_goals, 0, 1)


def implied_probability(odd):
    if odd is None or odd <= 1:
        return None
    return 1.0 / odd


def two_way_fair_prob(odd, opposite_odd):
    """
    Remove aproximadamente a margem de um mercado de duas vias.
    """
    if odd is None or opposite_odd is None:
        return implied_probability(odd)

    p1 = implied_probability(odd)
    p2 = implied_probability(opposite_odd)
    if p1 is None or p2 is None or p1 + p2 <= 0:
        return None

    return p1 / (p1 + p2)


def three_way_fair_probs(home_odd, draw_odd, away_odd):
    probs = [implied_probability(home_odd), implied_probability(draw_odd), implied_probability(away_odd)]
    if any(p is None for p in probs):
        return None

    total = sum(probs)
    if total <= 0:
        return None

    return {
        "home": probs[0] / total,
        "draw": probs[1] / total,
        "away": probs[2] / total,
    }


def edge_pp(model_prob, market_prob):
    if model_prob is None or market_prob is None:
        return None
    return (model_prob - market_prob) * 100.0


def ev_percent(model_prob, odd):
    if model_prob is None or odd is None:
        return None
    return ((model_prob * odd) - 1.0) * 100.0


def confianca(edge, prob, data_quality, score):
    if edge is None or prob is None:
        return "Baixa"
    if edge >= EXCELLENT_EDGE_PP and prob >= 0.62 and data_quality >= 0.75 and score >= 75:
        return "Alta"
    if edge >= GOOD_EDGE_PP and prob >= 0.55 and data_quality >= 0.65 and score >= 65:
        return "Média"
    return "Baixa"


# -----------------------------
# 3. API
# -----------------------------
def api_headers():
    return {"x-apisports-key": API_FOOTBALL_KEY}


def api_get(endpoint, params=None, timeout=15):
    if not API_FOOTBALL_KEY:
        return []

    try:
        response = requests.get(
            f"{API_BASE}/{endpoint.lstrip('/')}",
            headers=api_headers(),
            params=params or {},
            timeout=timeout,
        )

        if response.status_code != 200:
            return []

        payload = response.json()
        return payload.get("response", []) or []
    except Exception:
        return []


@st.cache_data(ttl=600, show_spinner=False)
def api_get_fixtures(data_str):
    return api_get(
        "fixtures",
        {
            "timezone": "America/Sao_Paulo",
            "date": data_str,
        },
    )


@st.cache_data(ttl=300, show_spinner=False)
def api_get_odds(fixture_id):
    return api_get("odds", {"fixture": fixture_id})


@st.cache_data(ttl=3600, show_spinner=False)
def api_get_team_recent_fixtures(team_id, last=MAX_RECENT_GAMES):
    return api_get(
        "fixtures",
        {
            "team": team_id,
            "last": last,
        },
    )


@st.cache_data(ttl=3600, show_spinner=False)
def api_get_fixture_statistics(fixture_id):
    return api_get(
        "fixtures/statistics",
        {
            "fixture": fixture_id,
        },
    )


# -----------------------------
# 4. ODDS — SOMENTE ODD REAL
# -----------------------------
def limpar_odd(valor):
    odd = safe_float(valor)
    if odd is None or odd <= 1.0 or odd > 100:
        return None
    return odd


def normalizar_nome_mercado(nome):
    return normalizar_texto(nome).replace("/", " ")


def extrair_linhas_goals(bet):
    """
    Retorna {line: {"over": odd, "under": odd}}.
    Ex.: {"2.5": {"over": 1.85, "under": 1.95}}
    """
    linhas = {}

    for val in bet.get("values", []):
        value = str(val.get("value", ""))
        odd = limpar_odd(val.get("odd"))

        if odd is None:
            continue

        text = normalizar_texto(value)
        partes = text.replace(",", ".").split()

        linha = None
        for p in partes:
            try:
                numero = float(p)
                if 0 < numero <= 10:
                    linha = numero
                    break
            except ValueError:
                continue

        if linha is None:
            continue

        if "over" in text or "mais" in text:
            linhas.setdefault(linha, {})["over"] = odd
        elif "under" in text or "menos" in text:
            linhas.setdefault(linha, {})["under"] = odd

    return linhas


def extrair_odds_bet365(fixture_id):
    """
    Tenta localizar EXPLICITAMENTE o bookmaker Bet365.
    Não usa o primeiro bookmaker da resposta como se fosse Bet365.
    """
    resposta = api_get_odds(fixture_id)

    resultado = {
        "bookmaker": None,
        "markets": [],
        "1x2": {},
        "goals": {},
        "btts": {},
        "double_chance": {},
        "dnb": {},
        "corners": {},
        "shots_on_target": {},
    }

    if not resposta:
        return resultado

    candidatos = []

    for bloco in resposta:
        for bookmaker in bloco.get("bookmakers", []):
            nome = bookmaker.get("name", "")
            if normalizar_texto(nome) == "bet365":
                candidatos.append(bookmaker)

    if not candidatos:
        return resultado

    bookmaker = candidatos[0]
    resultado["bookmaker"] = bookmaker.get("name", "Bet365")

    for bet in bookmaker.get("bets", []):
        nome_original = bet.get("name", "")
        nome = normalizar_nome_mercado(nome_original)
        values = bet.get("values", [])

        # 1X2
        if nome in {"match winner", "vencedor do jogo", "match result"}:
            for v in values:
                selection = normalizar_texto(v.get("value"))
                odd = limpar_odd(v.get("odd"))
                if odd is None:
                    continue

                if selection in {"home", "1"}:
                    resultado["1x2"]["home"] = odd
                elif selection in {"draw", "x", "empate"}:
                    resultado["1x2"]["draw"] = odd
                elif selection in {"away", "2"}:
                    resultado["1x2"]["away"] = odd

        # Gols
        elif "goals over under" in nome or "goals over/under" in nome or "total goals" in nome:
            linhas = extrair_linhas_goals(bet)
            for linha, dados in linhas.items():
                resultado["goals"].setdefault(linha, {}).update(dados)

        # BTTS
        elif "both teams score" in nome or "ambas" in nome:
            for v in values:
                selection = normalizar_texto(v.get("value"))
                odd = limpar_odd(v.get("odd"))
                if odd is None:
                    continue

                if selection in {"yes", "sim"}:
                    resultado["btts"]["yes"] = odd
                elif selection in {"no", "nao"}:
                    resultado["btts"]["no"] = odd

        # Double Chance
        elif "double chance" in nome:
            for v in values:
                selection = normalizar_texto(v.get("value"))
                odd = limpar_odd(v.get("odd"))
                if odd is None:
                    continue
                resultado["double_chance"][selection] = odd

        # Draw No Bet
        elif "draw no bet" in nome or "empate anula" in nome:
            for v in values:
                selection = normalizar_texto(v.get("value"))
                odd = limpar_odd(v.get("odd"))
                if odd is None:
                    continue
                resultado["dnb"][selection] = odd

        # Escanteios
        elif "corner" in nome or "escanteio" in nome:
            for v in values:
                selection = str(v.get("value", ""))
                odd = limpar_odd(v.get("odd"))
                if odd is None:
                    continue
                resultado["corners"][normalizar_texto(selection)] = odd

        # Finalizações no alvo
        elif "shots on target" in nome or "shots on target" in normalizar_texto(nome_original):
            for v in values:
                selection = str(v.get("value", ""))
                odd = limpar_odd(v.get("odd"))
                if odd is None:
                    continue
                resultado["shots_on_target"][normalizar_texto(selection)] = odd

    return resultado


# -----------------------------
# 5. HISTÓRICO + ESTATÍSTICAS
# -----------------------------
def resultado_time(fixture, team_id):
    home_id = fixture.get("teams", {}).get("home", {}).get("id")
    away_id = fixture.get("teams", {}).get("away", {}).get("id")

    gh = fixture.get("goals", {}).get("home")
    ga = fixture.get("goals", {}).get("away")

    if gh is None or ga is None:
        return None

    if team_id == home_id:
        gp, gc, local = gh, ga, "home"
    elif team_id == away_id:
        gp, gc, local = ga, gh, "away"
    else:
        return None

    if gp > gc:
        resultado = "W"
        pontos = 3
    elif gp == gc:
        resultado = "D"
        pontos = 1
    else:
        resultado = "L"
        pontos = 0

    return {
        "gp": float(gp),
        "gc": float(gc),
        "resultado": resultado,
        "pontos": pontos,
        "local": local,
        "total_gols": float(gh + ga),
        "btts": bool(gh > 0 and ga > 0),
    }


def extrair_estatisticas_fixture(fixture_id, team_id):
    """
    Procura estatísticas do time no endpoint de estatísticas da partida.
    A API pode retornar nomes diferentes dependendo da competição.
    """
    blocos = api_get_fixture_statistics(fixture_id)

    for bloco in blocos:
        if bloco.get("team", {}).get("id") != team_id:
            continue

        stats = {}
        for item in bloco.get("statistics", []):
            nome = normalizar_texto(item.get("type", ""))
            valor = item.get("value")

            if valor is None:
                continue

            if isinstance(valor, str):
                valor_limpo = valor.replace("%", "").replace(",", ".")
            else:
                valor_limpo = valor

            if "shots on target" in nome or "finalizacoes no alvo" in nome:
                stats["sot"] = safe_float(valor_limpo)
            elif nome == "total shots" or "total shots" in nome:
                stats["shots"] = safe_float(valor_limpo)
            elif "corner kicks" in nome or "corners" in nome or "escanteios" in nome:
                stats["corners"] = safe_float(valor_limpo)
            elif "ball possession" in nome or "posse" in nome:
                stats["possession"] = safe_float(valor_limpo)

        return stats

    return {}


def construir_perfil_time(team_id, venue=None):
    fixtures = api_get_team_recent_fixtures(team_id, MAX_RECENT_GAMES)

    jogos = []

    for fixture in fixtures:
        status = fixture.get("fixture", {}).get("status", {}).get("short")
        if status not in {"FT", "AET", "PEN"}:
            continue

        f = resultado_time(fixture, team_id)
        if not f:
            continue

        if venue in {"home", "away"} and f["local"] != venue:
            continue

        f["fixture_id"] = fixture.get("fixture", {}).get("id")
        jogos.append(f)

    # Mais recentes primeiro, se houver data.
    jogos = jogos[:MAX_RECENT_GAMES]

    if not jogos:
        return None

    # Estatísticas detalhadas somente para um subconjunto, evitando
    # centenas de chamadas desnecessárias.
    ids_stats = [j["fixture_id"] for j in jogos[:MAX_STATS_FIXTURES] if j.get("fixture_id")]

    stats_por_jogo = {}
    if ids_stats:
        workers = min(6, len(ids_stats))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(extrair_estatisticas_fixture, fid, team_id): fid
                for fid in ids_stats
            }
            for future in as_completed(futures):
                fid = futures[future]
                try:
                    stats_por_jogo[fid] = future.result() or {}
                except Exception:
                    stats_por_jogo[fid] = {}

    for jogo in jogos:
        jogo.update(stats_por_jogo.get(jogo.get("fixture_id"), {}))

    n = len(jogos)
    pontos = sum(j["pontos"] for j in jogos)
    gols_pro = [j["gp"] for j in jogos]
    gols_contra = [j["gc"] for j in jogos]
    totais = [j["total_gols"] for j in jogos]

    sot = [j.get("sot") for j in jogos if j.get("sot") is not None]
    shots = [j.get("shots") for j in jogos if j.get("shots") is not None]
    corners = [j.get("corners") for j in jogos if j.get("corners") is not None]
    possession = [j.get("possession") for j in jogos if j.get("possession") is not None]

    return {
        "jogos": n,
        "vitorias": sum(j["resultado"] == "W" for j in jogos),
        "empates": sum(j["resultado"] == "D" for j in jogos),
        "derrotas": sum(j["resultado"] == "L" for j in jogos),
        "aproveitamento": round((pontos / (n * 3)) * 100, 1),
        "media_gols_pro": round(weighted_recent(gols_pro), 3),
        "media_gols_contra": round(weighted_recent(gols_contra), 3),
        "media_gols_total": round(weighted_recent(totais), 3),
        "over15": round(sum(t > 1.5 for t in totais) / n * 100, 1),
        "over25": round(sum(t > 2.5 for t in totais) / n * 100, 1),
        "btts": round(sum(j["btts"] for j in jogos) / n * 100, 1),
        "sot": round(weighted_recent(sot), 3) if sot else None,
        "shots": round(weighted_recent(shots), 3) if shots else None,
        "corners": round(weighted_recent(corners), 3) if corners else None,
        "possession": round(weighted_recent(possession), 3) if possession else None,
        "data_quality": clamp(
            0.45
            + min(n, 10) / 10 * 0.25
            + (0.15 if sot else 0)
            + (0.10 if corners else 0)
            + (0.05 if shots else 0),
            0,
            1,
        ),
    }


# -----------------------------
# 6. MODELO DE GOLS
# -----------------------------
def estimar_lambda(home, away, home_home, away_away):
    """
    Modelo inicial de intensidade de gols.

    Não chama isso de xG: é uma estimativa de λ baseada em resultados
    recentes, separando casa/fora quando há amostra suficiente.
    """
    h_attack = home_home["media_gols_pro"] if home_home and home_home["jogos"] >= 3 else home["media_gols_pro"]
    h_def = home_home["media_gols_contra"] if home_home and home_home["jogos"] >= 3 else home["media_gols_contra"]

    a_attack = away_away["media_gols_pro"] if away_away and away_away["jogos"] >= 3 else away["media_gols_pro"]
    a_def = away_away["media_gols_contra"] if away_away and away_away["jogos"] >= 3 else away["media_gols_contra"]

    # Combina ataque próprio + vulnerabilidade defensiva adversária.
    lam_home = 0.58 * h_attack + 0.42 * a_def
    lam_away = 0.58 * a_attack + 0.42 * h_def

    # Evita lambdas absurdamente baixas/altas por amostras pequenas.
    return clamp(lam_home, 0.20, 4.00), clamp(lam_away, 0.20, 4.00)


# -----------------------------
# 7. SCORE TÉCNICO
# -----------------------------
def calcular_score(home, away, home_home, away_away, lam_home, lam_away):
    componentes = {}

    # Forma: aproveitamento recente.
    form = (home["aproveitamento"] + away["aproveitamento"]) / 2
    componentes["form"] = clamp(form, 0, 100)

    # Ataque: mais alto = melhor capacidade ofensiva combinada.
    ataque = clamp(((home["media_gols_pro"] + away["media_gols_pro"]) / 3.2) * 100, 0, 100)
    componentes["attack"] = ataque

    # Defesa: menos gols sofridos = melhor.
    defesa_media = (home["media_gols_contra"] + away["media_gols_contra"]) / 2
    defesa = clamp(100 - (defesa_media / 2.8) * 100, 0, 100)
    componentes["defense"] = defesa

    # Casa/fora.
    venue_vals = []
    if home_home:
        venue_vals.append(home_home["aproveitamento"])
    if away_away:
        venue_vals.append(away_away["aproveitamento"])
    componentes["venue"] = media(venue_vals, 50)

    # Modelo de gols: evita transformar λ alto automaticamente em "melhor".
    total_lam = lam_home + lam_away
    componentes["goals_model"] = clamp(100 - abs(total_lam - 2.60) * 22, 0, 100)

    # Finalizações.
    sot_vals = [v for v in [home.get("sot"), away.get("sot")] if v is not None]
    if sot_vals:
        componentes["shots"] = clamp((sum(sot_vals) / len(sot_vals)) / 5.5 * 100, 0, 100)
    else:
        componentes["shots"] = 50

    # Escanteios.
    corner_vals = [v for v in [home.get("corners"), away.get("corners")] if v is not None]
    if corner_vals:
        componentes["corners"] = clamp((sum(corner_vals) / len(corner_vals)) / 6.0 * 100, 0, 100)
    else:
        componentes["corners"] = 50

    componentes["data_quality"] = media(
        [home["data_quality"], away["data_quality"]], 0.50
    ) * 100

    # H2H é residual e, por enquanto, não é utilizado sem endpoint dedicado.
    componentes["h2h_residual"] = 50

    score = 0
    for chave, peso in WEIGHTS.items():
        score += componentes[chave] * peso

    return round(clamp(score, 0, 100), 1), componentes


# -----------------------------
# 8. EVIDÊNCIAS E MERCADOS
# -----------------------------
def adicionar_mercado(lista, mercado, selecao, odd, prob, market_prob,
                      score, data_quality, evidencias, grupo,
                      opposite_odd=None):
    odd = limpar_odd(odd)

    if odd is None:
        return

    if odd < MIN_ODD or odd > MAX_ODD:
        return

    if prob is None or prob <= 0 or prob >= 1:
        return

    if market_prob is None:
        if opposite_odd is not None:
            market_prob = two_way_fair_prob(odd, opposite_odd)
        else:
            market_prob = implied_probability(odd)

    edge = edge_pp(prob, market_prob)
    ev = ev_percent(prob, odd)

    if edge is None or ev is None:
        return

    # Filtros de qualidade. Não basta ter Edge enorme em amostra ruim.
    if prob < MIN_MODEL_PROB:
        return

    confianca_label = confianca(edge, prob, data_quality, score)

    # Só entra como oportunidade quando existe valor mínimo.
    if edge < MIN_EDGE_PP:
        return

    lista.append({
        "mercado": mercado,
        "selecao": selecao,
        "titulo": f"{mercado} — {selecao}",
        "odd": odd,
        "probabilidade": round(prob * 100, 1),
        "prob_mercado": round(market_prob * 100, 1),
        "edge": round(edge, 2),
        "ev": round(ev, 2),
        "score": round(score, 1),
        "conf": confianca_label,
        "tipo": (
            "alta" if confianca_label == "Alta"
            else "media" if confianca_label == "Média"
            else "baixa"
        ),
        "grupo": grupo,
        "evidencias": evidencias,
    })


def selecionar_melhores(mercados, maximo=4):
    """
    Evita devolver quatro mercados praticamente iguais/correlacionados.
    Ex.: Over 1.5 + Over 2.5 + BTTS não devem ocupar automaticamente
    as três primeiras posições.
    """
    if not mercados:
        return []

    mercados = sorted(
        mercados,
        key=lambda x: (
            x["edge"] * 0.45
            + x["ev"] * 0.25
            + x["probabilidade"] * 0.15
            + x["score"] * 0.15
        ),
        reverse=True,
    )

    escolhidos = []
    grupos = set()

    for op in mercados:
        if len(escolhidos) >= maximo:
            break

        # No máximo uma seleção do mesmo grupo na primeira rodada.
        if op["grupo"] in grupos:
            continue

        escolhidos.append(op)
        grupos.add(op["grupo"])

    # Se ainda houver espaço, permite segunda oportunidade de grupos
    # diferentes apenas quando o Edge é forte.
    if len(escolhidos) < maximo:
        for op in mercados:
            if len(escolhidos) >= maximo:
                break
            if op in escolhidos:
                continue
            if op["edge"] >= EXCELLENT_EDGE_PP:
                escolhidos.append(op)

    return escolhidos[:maximo]


# -----------------------------
# 9. MOTOR PRINCIPAL
# -----------------------------
def analisar_partida(home_id, home_name, away_id, away_name, fixture_id):
    with ThreadPoolExecutor(max_workers=5) as executor:
        f_home = executor.submit(construir_perfil_time, home_id, None)
        f_away = executor.submit(construir_perfil_time, away_id, None)
        f_home_home = executor.submit(construir_perfil_time, home_id, "home")
        f_away_away = executor.submit(construir_perfil_time, away_id, "away")
        f_odds = executor.submit(extrair_odds_bet365, fixture_id)

        home = f_home.result()
        away = f_away.result()
        home_home = f_home_home.result()
        away_away = f_away_away.result()
        odds = f_odds.result()

    if not home or not away:
        return {
            "status": "NO BET",
            "motivo": "Dados históricos insuficientes para os dois times.",
            "oportunidades": [],
            "dados": {},
        }

    if home["jogos"] < MIN_RECENT_GAMES or away["jogos"] < MIN_RECENT_GAMES:
        return {
            "status": "NO BET",
            "motivo": f"Amostra insuficiente: mínimo de {MIN_RECENT_GAMES} jogos recentes por equipe.",
            "oportunidades": [],
            "dados": {"home": home, "away": away, "odds": odds},
        }

    if not odds.get("bookmaker"):
        return {
            "status": "NO BET",
            "motivo": "Bet365 não foi localizada na resposta de odds desta partida.",
            "oportunidades": [],
            "dados": {"home": home, "away": away, "odds": odds},
        }

    lam_home, lam_away = estimar_lambda(home, away, home_home, away_away)
    p_home, p_draw, p_away = prob_1x2(lam_home, lam_away)
    p_btts_yes = prob_btts(lam_home, lam_away)
    p_btts_no = 1 - p_btts_yes
    p_over15 = poisson_over_probability(lam_home + lam_away, 1.5)
    p_over25 = poisson_over_probability(lam_home + lam_away, 2.5)
    p_over35 = poisson_over_probability(lam_home + lam_away, 3.5)
    p_under15 = 1 - p_over15
    p_under25 = 1 - p_over25
    p_under35 = 1 - p_over35

    score, componentes = calcular_score(
        home, away, home_home, away_away, lam_home, lam_away
    )

    data_quality = media([home["data_quality"], away["data_quality"]], 0.5)

    mercados = []

    fair_1x2 = three_way_fair_probs(
        odds["1x2"].get("home"),
        odds["1x2"].get("draw"),
        odds["1x2"].get("away"),
    )

    evid_resultado_home = [
        f"{home_name}: {home['aproveitamento']:.1f}% de aproveitamento nos últimos {home['jogos']} jogos.",
        f"{away_name}: {away['aproveitamento']:.1f}% de aproveitamento nos últimos {away['jogos']} jogos.",
        f"Modelo de gols: {home_name} λ={lam_home:.2f}; {away_name} λ={lam_away:.2f}.",
    ]

    if fair_1x2:
        adicionar_mercado(
            mercados, "Resultado", home_name, odds["1x2"].get("home"),
            p_home, fair_1x2["home"], score, data_quality,
            evid_resultado_home, "resultado",
        )
        adicionar_mercado(
            mercados, "Resultado", "Empate", odds["1x2"].get("draw"),
            p_draw, fair_1x2["draw"], score, data_quality,
            [
                f"Probabilidade de empate pelo modelo: {p_draw*100:.1f}%.",
                f"Intensidade ofensiva estimada: {lam_home+lam_away:.2f} gols.",
                f"Os dois times apresentam aproveitamento de {home['aproveitamento']:.1f}% e {away['aproveitamento']:.1f}%.",
            ],
            "resultado",
        )
        adicionar_mercado(
            mercados, "Resultado", away_name, odds["1x2"].get("away"),
            p_away, fair_1x2["away"], score, data_quality,
            [
                f"{away_name}: {away['aproveitamento']:.1f}% de aproveitamento nos últimos {away['jogos']} jogos.",
                f"{home_name}: {home['aproveitamento']:.1f}% de aproveitamento nos últimos {home['jogos']} jogos.",
                f"Modelo de gols: {away_name} λ={lam_away:.2f}; {home_name} λ={lam_home:.2f}.",
            ],
            "resultado",
        )

    # Double chance — probabilidade derivada do 1X2.
    dc = odds.get("double_chance", {})
    if p_home is not None and p_draw is not None and p_away is not None:
        dc_probs = {
            "home or draw": p_home + p_draw,
            "draw or away": p_draw + p_away,
            "home or away": p_home + p_away,
            "1x": p_home + p_draw,
            "x2": p_draw + p_away,
            "12": p_home + p_away,
        }

        for selection, odd in dc.items():
            key = normalizar_texto(selection)
            prob = dc_probs.get(key)
            if prob is None:
                if "home" in key and "draw" in key:
                    prob = p_home + p_draw
                elif "draw" in key and "away" in key:
                    prob = p_draw + p_away
                elif "home" in key and "away" in key:
                    prob = p_home + p_away
                else:
                    continue

            adicionar_mercado(
                mercados, "Dupla Chance", selection, odd, prob,
                implied_probability(odd), score, data_quality,
                [
                    f"Probabilidade do modelo para a dupla chance: {prob*100:.1f}%.",
                    f"Distribuição 1X2 do modelo: {home_name} {p_home*100:.1f}%, empate {p_draw*100:.1f}%, {away_name} {p_away*100:.1f}%.",
                ],
                "resultado",
            )

    # DNB — exige odds reais.
    for selection, odd in odds.get("dnb", {}).items():
        key = normalizar_texto(selection)
        if key in {"home", "1", normalizar_texto(home_name)}:
            # P(vitória) / P(vitória ou derrota)
            prob = p_home / max(p_home + p_away, 1e-9)
            nome = home_name
        elif key in {"away", "2", normalizar_texto(away_name)}:
            prob = p_away / max(p_home + p_away, 1e-9)
            nome = away_name
        else:
            continue

        adicionar_mercado(
            mercados, "Empate Anula", nome, odd, prob,
            implied_probability(odd), score, data_quality,
            [
                f"Probabilidade condicional de vitória: {prob*100:.1f}%, excluindo o empate.",
                f"Modelo 1X2: {home_name} {p_home*100:.1f}% | empate {p_draw*100:.1f}% | {away_name} {p_away*100:.1f}%.",
            ],
            "resultado",
        )

    # Gols.
    for linha, dados in sorted(odds.get("goals", {}).items()):
        if abs(linha - 1.5) < 0.01:
            p_over, p_under = p_over15, p_under15
        elif abs(linha - 2.5) < 0.01:
            p_over, p_under = p_over25, p_under25
        elif abs(linha - 3.5) < 0.01:
            p_over, p_under = p_over35, p_under35
        else:
            # Para outras linhas .5, ainda é possível usar Poisson.
            p_over = poisson_over_probability(lam_home + lam_away, linha)
            p_under = 1 - p_over

        over_odd = dados.get("over")
        under_odd = dados.get("under")

        adicionar_mercado(
            mercados, f"Gols Over {linha:g}", f"Mais de {linha:g}",
            over_odd, p_over,
            two_way_fair_prob(over_odd, under_odd),
            score, data_quality,
            [
                f"λ total estimado: {lam_home + lam_away:.2f} gols.",
                f"{home_name}: {home['media_gols_pro']:.2f} gols marcados/jogo.",
                f"{away_name}: {away['media_gols_pro']:.2f} gols marcados/jogo.",
            ],
            "gols",
        )

        adicionar_mercado(
            mercados, f"Gols Under {linha:g}", f"Menos de {linha:g}",
            under_odd, p_under,
            two_way_fair_prob(under_odd, over_odd),
            score, data_quality,
            [
                f"λ total estimado: {lam_home + lam_away:.2f} gols.",
                f"{home_name}: {home['media_gols_contra']:.2f} gols sofridos/jogo.",
                f"{away_name}: {away['media_gols_contra']:.2f} gols sofridos/jogo.",
            ],
            "gols",
        )

    # BTTS.
    btts_yes = odds["btts"].get("yes")
    btts_no = odds["btts"].get("no")

    adicionar_mercado(
        mercados, "Ambas Marcam", "Sim", btts_yes, p_btts_yes,
        two_way_fair_prob(btts_yes, btts_no),
        score, data_quality,
        [
            f"BTTS observado: {home['btts']:.1f}% nos últimos jogos de {home_name}.",
            f"BTTS observado: {away['btts']:.1f}% nos últimos jogos de {away_name}.",
            f"Probabilidade do modelo: {p_btts_yes*100:.1f}%.",
        ],
        "btts",
    )

    adicionar_mercado(
        mercados, "Ambas Marcam", "Não", btts_no, p_btts_no,
        two_way_fair_prob(btts_no, btts_yes),
        score, data_quality,
        [
            f"Probabilidade do modelo de BTTS Não: {p_btts_no*100:.1f}%.",
            f"Defesa do mandante sofre {home['media_gols_contra']:.2f} gols/jogo.",
            f"Defesa do visitante sofre {away['media_gols_contra']:.2f} gols/jogo.",
        ],
        "btts",
    )

    # Mercados de escanteios: só entram se houver dado de corners e uma
    # linha identificável. Como o formato da API pode variar, fazemos
    # uma interpretação conservadora.
    corner_values = odds.get("corners", {})
    corner_total_model = None

    if home.get("corners") is not None and away.get("corners") is not None:
        corner_total_model = clamp(
            home["corners"] + away["corners"], 2.0, 16.0
        )

    if corner_total_model is not None:
        for selection, odd in corner_values.items():
            text = normalizar_texto(selection)
            nums = []
            for token in text.replace(",", ".").split():
                try:
                    x = float(token)
                    if 0 < x <= 20:
                        nums.append(x)
                except ValueError:
                    pass

            if not nums:
                continue

            line = nums[0]
            if "over" in text or "mais" in text:
                prob = poisson_over_probability(corner_total_model, line)
                lado = f"Mais de {line:g}"
            elif "under" in text or "menos" in text:
                prob = poisson_under_probability(corner_total_model, line)
                lado = f"Menos de {line:g}"
            else:
                continue

            adicionar_mercado(
                mercados, "Escanteios", lado, odd, prob,
                implied_probability(odd), score, data_quality,
                [
                    f"Média estimada de escanteios totais: {corner_total_model:.2f}.",
                    f"{home_name}: {home['corners']:.2f} escanteios/jogo.",
                    f"{away_name}: {away['corners']:.2f} escanteios/jogo.",
                ],
                "escanteios",
            )

    oportunidades = selecionar_melhores(mercados, 4)

    status = "OPORTUNIDADES ENCONTRADAS" if oportunidades else "NO BET"

    motivo = (
        "Mercados ranqueados por Edge, EV, probabilidade, qualidade dos dados e Score técnico."
        if oportunidades
        else "Nenhum mercado da Bet365 atingiu o Edge mínimo com qualidade de dados suficiente."
    )

    return {
        "status": status,
        "motivo": motivo,
        "oportunidades": oportunidades,
        "dados": {
            "home": home,
            "away": away,
            "home_home": home_home,
            "away_away": away_away,
            "odds": odds,
            "lambda_home": lam_home,
            "lambda_away": lam_away,
            "score": score,
            "componentes_score": componentes,
            "data_quality": data_quality,
        },
    }


# -----------------------------
# 10. STATUS / HORÁRIO
# -----------------------------
def extrair_status_e_horario(fix):
    status_short = fix.get("status", {}).get("short", "")
    elapsed = fix.get("status", {}).get("elapsed")
    goals_home = fix.get("goals", {}).get("home")
    goals_away = fix.get("goals", {}).get("away")

    iso_date = fix.get("date", "")
    horario = ""

    if iso_date:
        try:
            dt_utc = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
            dt_br = dt_utc.astimezone(timezone(timedelta(hours=-3)))
            horario = dt_br.strftime("%H:%M")
        except Exception:
            pass

    if status_short in {"1H", "2H", "ET", "P"}:
        label = f"🟢 Ao Vivo {elapsed or ''}'"
        if goals_home is not None and goals_away is not None:
            label += f" ({goals_home}x{goals_away})"
        return label

    if status_short == "HT":
        return f"🟡 Intervalo ({goals_home}x{goals_away})"

    if status_short in {"FT", "AET", "PEN"}:
        label = "✅ Encerrado"
        if goals_home is not None and goals_away is not None:
            label += f" ({goals_home}x{goals_away})"
        return label

    return f"⏰ {horario}" if horario else "⏰ Não iniciado"


# -----------------------------
# 11. RENDERIZAÇÃO
# -----------------------------
def renderizar_card_jogo(item):
    fix = item["fixture"]
    league = item["league"]
    home = item["teams"]["home"]
    away = item["teams"]["away"]

    analise = analisar_partida(
        home["id"],
        home["name"],
        away["id"],
        away["name"],
        fix["id"],
    )

    status_str = extrair_status_e_horario(fix)

    with st.container(border=True):
        st.markdown(
            f"<h3 style='text-align:center;margin-bottom:2px;'>"
            f"{home['name']} x {away['name']}</h3>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<p style='text-align:center;color:#fbbf24;font-size:13px;font-weight:600;'>"
            f"🏆 {league.get('country','')} {league.get('name','')} "
            f"&nbsp;•&nbsp; {status_str}</p>",
            unsafe_allow_html=True,
        )

        dados = analise.get("dados", {})
        score = dados.get("score")
        odds = dados.get("odds", {})

        if score is not None:
            st.markdown(
                f"**Analista Score:** `{score}/100`  "
                f"• **Bookmaker:** `{odds.get('bookmaker') or 'não disponível'}`"
            )

        if analise["status"] == "NO BET":
            st.warning(f"NO BET — {analise['motivo']}")
            return

        st.markdown("#### 🎯 Melhores oportunidades")

        oportunidades = analise["oportunidades"]
        cols = st.columns(len(oportunidades))

        for col, op in zip(cols, oportunidades):
            badge = f"badge-{op['tipo']}"
            with col:
                st.markdown(
                    f"""
                    <div class="opp-box">
                        <div class="opp-title">{op['titulo']}</div>
                        <div>
                            <span class="opp-odd">Odd {op['odd']:.2f}</span>
                            <span class="{badge}">{op['conf']}</span>
                        </div>
                        <div style="font-size:12px;margin-top:7px;">
                            Modelo: <b>{op['probabilidade']:.1f}%</b><br>
                            Mercado: <b>{op['prob_mercado']:.1f}%</b><br>
                            Edge: <b>+{op['edge']:.2f} pp</b><br>
                            EV: <b>{op['ev']:+.2f}%</b>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("#### 📋 Embasamento estatístico")

        cards = []

        for op in oportunidades:
            badge_tipo = op["tipo"]
            card_class = f"analysis-card analysis-{badge_tipo}"

            topicos = "".join(
                f"<li>{texto}</li>" for texto in op["evidencias"]
            )

            cards.append(
                f"""
                <div class="{card_class}">
                    <div class="analysis-header">
                        {op['titulo']} — Confiança {op['conf']}
                    </div>
                    <ul class="analysis-list">
                        {topicos}
                        <li><b>Edge:</b> +{op['edge']:.2f} pontos percentuais.</li>
                        <li><b>EV estimado:</b> {op['ev']:+.2f}%.</li>
                    </ul>
                </div>
                """
            )

        st.markdown("".join(cards), unsafe_allow_html=True)


# -----------------------------
# 12. TEMA
# -----------------------------
if "tema" not in st.session_state:
    st.session_state["tema"] = "Escuro 🌙"

if st.session_state["tema"] == "Escuro 🌙":
    css_tema = """
    <style>
        html, body, [class*="css"] {
            font-family: Inter, sans-serif;
        }

        #MainMenu, header, footer,
        [data-testid="stToolbar"],
        [data-testid="stHeader"] {
            visibility: hidden !important;
            display: none !important;
        }

        .stApp {
            background-color: #0e1726;
            color: #f8fafc;
        }

        .opp-box {
            background-color: #1a2234;
            border: 1px solid #28354d;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
        }

        .opp-title {
            font-size: 13px;
            font-weight: 700;
            color: #38bdf8;
            margin-bottom: 8px;
        }

        .opp-odd {
            font-size: 14px;
            font-weight: 800;
            color: #ffffff;
        }

        .badge-alta {
            font-size: 11px;
            font-weight: 700;
            background: rgba(34,197,94,.15);
            color: #4ade80;
            padding: 2px 8px;
            border-radius: 4px;
            border: 1px solid rgba(34,197,94,.3);
            margin-left: 6px;
        }

        .badge-media {
            font-size: 11px;
            font-weight: 700;
            background: rgba(234,179,8,.15);
            color: #facc15;
            padding: 2px 8px;
            border-radius: 4px;
            border: 1px solid rgba(234,179,8,.3);
            margin-left: 6px;
        }

        .badge-baixa {
            font-size: 11px;
            font-weight: 700;
            background: rgba(239,68,68,.15);
            color: #f87171;
            padding: 2px 8px;
            border-radius: 4px;
            border: 1px solid rgba(239,68,68,.3);
            margin-left: 6px;
        }

        .analysis-card {
            border-radius: 8px;
            padding: 14px 18px;
            margin-bottom: 12px;
            border-left: 4px solid;
        }

        .analysis-alta {
            background-color: rgba(14,116,144,.15);
            border-color: #38bdf8;
        }

        .analysis-media {
            background-color: rgba(161,98,7,.15);
            border-color: #facc15;
        }

        .analysis-baixa {
            background-color: rgba(153,27,27,.15);
            border-color: #f87171;
        }

        .analysis-header {
            font-size: 14px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 8px;
        }

        .analysis-list {
            margin: 0;
            padding-left: 18px;
            font-size: 13px;
            color: #cbd5e1;
            line-height: 1.6;
        }
    </style>
    """
else:
    css_tema = """
    <style>
        html, body, [class*="css"] {
            font-family: Inter, sans-serif;
        }

        #MainMenu, header, footer,
        [data-testid="stToolbar"],
        [data-testid="stHeader"] {
            visibility: hidden !important;
            display: none !important;
        }

        .stApp {
            background-color: #f8fafc;
            color: #0f172a;
        }

        .opp-box {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
        }

        .opp-title {
            font-size: 13px;
            font-weight: 700;
            color: #0284c7;
            margin-bottom: 8px;
        }

        .opp-odd {
            font-size: 14px;
            font-weight: 800;
            color: #0f172a;
        }

        .badge-alta {
            font-size: 11px;
            font-weight: 700;
            background: #dcfce7;
            color: #15803d;
            padding: 2px 8px;
            border-radius: 4px;
            border: 1px solid #86efac;
            margin-left: 6px;
        }

        .badge-media {
            font-size: 11px;
            font-weight: 700;
            background: #fef9c3;
            color: #a16207;
            padding: 2px 8px;
            border-radius: 4px;
            border: 1px solid #fde047;
            margin-left: 6px;
        }

        .badge-baixa {
            font-size: 11px;
            font-weight: 700;
            background: #fee2e2;
            color: #b91c1c;
            padding: 2px 8px;
            border-radius: 4px;
            border: 1px solid #fca5a5;
            margin-left: 6px;
        }

        .analysis-card {
            border-radius: 8px;
            padding: 14px 18px;
            margin-bottom: 12px;
            border-left: 4px solid;
        }

        .analysis-alta {
            background-color: #f0f9ff;
            border-color: #0284c7;
        }

        .analysis-media {
            background-color: #fefce8;
            border-color: #ca8a04;
        }

        .analysis-baixa {
            background-color: #fef2f2;
            border-color: #dc2626;
        }

        .analysis-header {
            font-size: 14px;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 8px;
        }

        .analysis-list {
            margin: 0;
            padding-left: 18px;
            font-size: 13px;
            color: #334155;
            line-height: 1.6;
        }
    </style>
    """

st.markdown(css_tema, unsafe_allow_html=True)


# -----------------------------
# 13. AUTENTICAÇÃO
# -----------------------------
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

LICENCAS_VALIDAS = st.secrets.get("LICENCAS_VALIDAS", [])

if isinstance(LICENCAS_VALIDAS, str):
    LICENCAS_VALIDAS = [x.strip() for x in LICENCAS_VALIDAS.split(",") if x.strip()]

if not st.session_state["autenticado"]:
    st.title("🔒 ANALISTA PRO — Acesso Restrito")
    chave_input = st.text_input("Insira sua licença:", type="password")

    if st.button("ACESSAR PLATAFORMA"):
        if chave_input.strip() in LICENCAS_VALIDAS:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Chave de acesso inválida.")

    st.stop()


# -----------------------------
# 14. HEADER
# -----------------------------
col_h1, col_h2, col_h3 = st.columns([1, 2, 1])

with col_h3:
    novo_tema = st.radio(
        "Aparência:",
        ["Escuro 🌙", "Claro ☀️"],
        index=0 if st.session_state["tema"] == "Escuro 🌙" else 1,
        horizontal=True,
    )

    if novo_tema != st.session_state["tema"]:
        st.session_state["tema"] = novo_tema
        st.rerun()

with col_h2:
    try:
        st.image("logo.png", use_container_width=True)
    except Exception:
        cor = "#38bdf8" if st.session_state["tema"] == "Escuro 🌙" else "#0284c7"
        st.markdown(
            f"<h1 style='text-align:center;color:{cor};'>⚽ ANALISTA PRO</h1>",
            unsafe_allow_html=True,
        )


# -----------------------------
# 15. FILTROS
# -----------------------------
agora_br = datetime.now(timezone.utc).astimezone(
    timezone(timedelta(hours=-3))
)

col_f1, col_f2 = st.columns([1, 2])

with col_f1:
    opcao_filtro = st.radio(
        "Selecione a data:",
        ["🔴 Jogos de Hoje", "🟡 Jogos de Amanhã"],
        horizontal=True,
    )

data_alvo_str = (
    agora_br.strftime("%Y-%m-%d")
    if "Hoje" in opcao_filtro
    else (agora_br + timedelta(days=1)).strftime("%Y-%m-%d")
)

partidas_brutas = api_get_fixtures(data_alvo_str)

partidas_validas_dia = [
    item
    for item in partidas_brutas
    if item.get("fixture", {}).get("status", {}).get("short") not in {"CANC", "PST", "ABD"}
]

ligas_do_dia_dict = {}

for item in partidas_validas_dia:
    country = item.get("league", {}).get("country", "")
    name = item.get("league", {}).get("name", "")
    nome_exibicao = f"{country}: {name}" if country else name
    ligas_do_dia_dict[nome_exibicao] = (country, name)

options_ligas = sorted(ligas_do_dia_dict.keys())

with col_f2:
    ligas_selecionadas = st.multiselect(
        "Filtrar Ligas Disponíveis no Dia:",
        options=options_ligas,
        placeholder="Todas as ligas com jogos",
    )

partidas_filtradas = []

for item in partidas_validas_dia:
    country = item.get("league", {}).get("country", "")
    name = item.get("league", {}).get("name", "")
    nome_exibicao = f"{country}: {name}" if country else name

    if not ligas_selecionadas or nome_exibicao in ligas_selecionadas:
        partidas_filtradas.append(item)


# -----------------------------
# 16. EXECUÇÃO
# -----------------------------
if st.button("🔍 ANALISAR PARTIDAS", use_container_width=True):
    st.session_state["executar_analise"] = True

if st.session_state.get("executar_analise", False):
    if not partidas_filtradas:
        st.warning("⚠️ Nenhum jogo encontrado para a data selecionada.")
    else:
        st.info(
            f"{len(partidas_filtradas)} partida(s) carregada(s). "
            "O motor não força mercados: cada jogo é analisado individualmente."
        )

        # Mantém o limite original de 15 por segurança de API.
        for item in partidas_filtradas[:15]:
            renderizar_card_jogo(item)
