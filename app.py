import unicodedata
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
import requests
import streamlit as st

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Analisador Pro — IA",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# A chave NUNCA deve ficar escrita no código. Configure em .streamlit/secrets.toml:
# API_FOOTBALL_KEY = "sua_chave_aqui"
API_FOOTBALL_KEY = st.secrets.get("API_FOOTBALL_KEY")
if not API_FOOTBALL_KEY:
    st.error("⚠️ API_FOOTBALL_KEY não configurada em st.secrets. Adicione em .streamlit/secrets.toml e reinicie o app.")
    st.stop()

LICENCAS_VALIDAS = ["PRO-FUTEBOL-2026", "VIP-ANALISTA-888", "CLIENTE-PRO-01", "ADMIN-MASTER-99"]

if "api_erros" not in st.session_state:
    st.session_state["api_erros"] = []

def registrar_erro_api(origem, resp_json, status_code):
    """Guarda qualquer erro/aviso real vindo da API para exibir ao usuário,
    em vez de deixar a exceção sumir silenciosamente."""
    erros = resp_json.get("errors") if isinstance(resp_json, dict) else None
    if erros:
        msg = f"[{origem}] {erros}"
        if msg not in st.session_state["api_erros"]:
            st.session_state["api_erros"].append(msg)
    if status_code != 200:
        msg = f"[{origem}] HTTP {status_code}"
        if msg not in st.session_state["api_erros"]:
            st.session_state["api_erros"].append(msg)

def normalizar_texto(texto):
    if not texto:
        return ""
    nfkd = unicodedata.normalize('NFD', texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower().strip()

# 2. AUTENTICAÇÃO
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🔒 Analisador Pro — Acesso Restrito")
    chave_input = st.text_input("Insira sua licença:", type="password")
    if st.button("ACESSAR PLATAFORMA"):
        if chave_input.strip() in LICENCAS_VALIDAS:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Chave de acesso inválida.")
    st.stop()

# 3. CONTROLE DE TEMA (ESCURO / CLARO)
if "tema" not in st.session_state:
    st.session_state["tema"] = "Escuro 🌙"

if st.session_state["tema"] == "Escuro 🌙":
    css_tema = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        #MainMenu, header, footer, [data-testid="stToolbar"], [data-testid="stHeader"] { visibility: hidden !important; display: none !important; }

        .stApp { background-color: #0e1726; color: #f8fafc; }
        .opp-box {
            background-color: #1a2234;
            border: 1px solid #28354d;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
        }
        .opp-title { font-size: 13px; font-weight: 700; color: #38bdf8; margin-bottom: 8px; }
        .opp-odd { font-size: 14px; font-weight: 800; color: #ffffff; }
        .badge-alta { font-size: 11px; font-weight: 700; background: rgba(34, 197, 94, 0.15); color: #4ade80; padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(34, 197, 94, 0.3); }
        .badge-media { font-size: 11px; font-weight: 700; background: rgba(234, 179, 8, 0.15); color: #facc15; padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(234, 179, 8, 0.3); }
        .badge-baixa { font-size: 11px; font-weight: 700; background: rgba(239, 68, 68, 0.15); color: #f87171; padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(239, 68, 68, 0.3); }
        .badge-indisponivel { font-size: 11px; font-weight: 700; background: rgba(148, 163, 184, 0.15); color: #94a3b8; padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(148, 163, 184, 0.3); }

        .analysis-card { border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; border-left: 4px solid; }
        .analysis-alta { background-color: rgba(14, 116, 144, 0.15); border-color: #38bdf8; }
        .analysis-media { background-color: rgba(161, 98, 7, 0.15); border-color: #facc15; }
        .analysis-baixa { background-color: rgba(153, 27, 27, 0.15); border-color: #f87171; }
        .analysis-header { font-size: 14px; font-weight: 700; color: #ffffff; margin-bottom: 8px; }
        .analysis-list { margin: 0; padding-left: 18px; font-size: 13px; color: #cbd5e1; line-height: 1.6; }
    </style>
    """
else:
    css_tema = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        #MainMenu, header, footer, [data-testid="stToolbar"], [data-testid="stHeader"] { visibility: hidden !important; display: none !important; }

        .stApp { background-color: #f8fafc; color: #0f172a; }
        .opp-box {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .opp-title { font-size: 13px; font-weight: 700; color: #0284c7; margin-bottom: 8px; }
        .opp-odd { font-size: 14px; font-weight: 800; color: #0f172a; }
        .badge-alta { font-size: 11px; font-weight: 700; background: #dcfce7; color: #15803d; padding: 2px 8px; border-radius: 4px; border: 1px solid #86efac; }
        .badge-media { font-size: 11px; font-weight: 700; background: #fef9c3; color: #a16207; padding: 2px 8px; border-radius: 4px; border: 1px solid #fde047; }
        .badge-baixa { font-size: 11px; font-weight: 700; background: #fee2e2; color: #b91c1c; padding: 2px 8px; border-radius: 4px; border: 1px solid #fca5a5; }
        .badge-indisponivel { font-size: 11px; font-weight: 700; background: #e2e8f0; color: #475569; padding: 2px 8px; border-radius: 4px; border: 1px solid #cbd5e1; }

        .analysis-card { border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; border-left: 4px solid; }
        .analysis-alta { background-color: #f0f9ff; border-color: #0284c7; }
        .analysis-media { background-color: #fefce8; border-color: #ca8a04; }
        .analysis-baixa { background-color: #fef2f2; border-color: #dc2626; }
        .analysis-header { font-size: 14px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }
        .analysis-list { margin: 0; padding-left: 18px; font-size: 13px; color: #334155; line-height: 1.6; }
    </style>
    """

st.markdown(css_tema, unsafe_allow_html=True)

# 4. REQUISIÇÕES DE API (agora com erro real exposto, sem silenciar exceções)
@st.cache_data(ttl=600)
def api_get_fixtures(data_str):
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    params = {"timezone": "America/Sao_Paulo", "date": data_str}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        body = res.json()
    except Exception as e:
        return [], f"Falha de conexão: {e}"
    erro = body.get("errors") if isinstance(body, dict) else None
    if erro:
        return [], f"API retornou erro: {erro}"
    if res.status_code != 200:
        return [], f"HTTP {res.status_code}"
    return body.get("response", []), None

@st.cache_data(ttl=300)
def api_get_odds(fixture_id):
    url = "https://v3.football.api-sports.io/odds"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    params = {"fixture": fixture_id}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        body = res.json()
    except Exception as e:
        return [], f"Falha de conexão: {e}"
    erro = body.get("errors") if isinstance(body, dict) else None
    if erro:
        return [], f"API retornou erro em /odds: {erro}"
    if res.status_code != 200:
        return [], f"HTTP {res.status_code} em /odds"
    resposta = body.get("response", [])
    if not resposta:
        # Muito comum em planos Free/Basic: o endpoint responde 200 mas sem dado nenhum.
        return [], "Endpoint /odds voltou vazio — confira se seu plano da API-Football inclui odds pré-jogo."
    return resposta, None

@st.cache_data(ttl=3600)
def obter_estatisticas_reais_time(team_id, tipo_mando="geral"):
    if not team_id:
        return None

    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    params = {"team": team_id, "last": 8}

    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        body = res.json()
    except Exception:
        return None

    erro = body.get("errors") if isinstance(body, dict) else None
    if erro or res.status_code != 200:
        return None

    fixtures = body.get("response", [])
    if not fixtures:
        return None

    vitorias, empates, derrotas = 0, 0, 0
    gols_pro, gols_contra = 0, 0
    jogos_processados = 0

    for fix in fixtures:
        if fix["fixture"]["status"]["short"] not in ["FT", "AET", "PEN"]:
            continue

        is_home = (fix["teams"]["home"]["id"] == team_id)

        if tipo_mando == "home" and not is_home:
            continue
        if tipo_mando == "away" and is_home:
            continue

        gh = fix["goals"]["home"] if fix["goals"]["home"] is not None else 0
        ga = fix["goals"]["away"] if fix["goals"]["away"] is not None else 0

        gp = gh if is_home else ga
        gc = ga if is_home else gh

        gols_pro += gp
        gols_contra += gc

        if gp > gc: vitorias += 1
        elif gp == gc: empates += 1
        else: derrotas += 1

        jogos_processados += 1

    # Se o filtro por mando (home/away) não deixou nenhum jogo, os dados são
    # insuficientes de verdade — melhor avisar do que fabricar um número.
    if jogos_processados == 0:
        return None

    n = jogos_processados
    aproveitamento = (vitorias * 3 + empates) / (n * 3)

    return {
        "jogos": n, "vitorias": vitorias, "empates": empates, "derrotas": derrotas,
        "media_gols_pro": round(gols_pro / n, 2),
        "media_gols_contra": round(gols_contra / n, 2),
        "aproveitamento": round(aproveitamento * 100, 1)
    }

def extrair_odds_partida(fixture_id):
    """Retorna odds reais quando disponíveis. NUNCA inventa valor —
    se a casa/mercado não veio da API, o campo fica None e quem chama
    decide o que fazer (ex.: mostrar 'N/D' ou usar critério alternativo)."""
    raw_odds, erro = api_get_odds(fixture_id)
    if erro:
        registrar_erro_api("odds", {"errors": erro}, 200)

    odds = {
        "home": None, "draw": None, "away": None,
        "over15": None, "over25": None, "under25": None,
        "btts_yes": None
    }

    if raw_odds:
        for bookmaker in raw_odds[0].get("bookmakers", []):
            for bet in bookmaker.get("bets", []):
                bet_name = bet.get("name", "")
                if bet_name == "Match Winner":
                    for val in bet.get("values", []):
                        if val["value"] == "Home" and not odds["home"]: odds["home"] = float(val["odd"])
                        elif val["value"] == "Draw" and not odds["draw"]: odds["draw"] = float(val["odd"])
                        elif val["value"] == "Away" and not odds["away"]: odds["away"] = float(val["odd"])
                elif bet_name == "Goals Over/Under":
                    for val in bet.get("values", []):
                        if val["value"] == "Over 1.5" and not odds["over15"]: odds["over15"] = float(val["odd"])
                        elif val["value"] == "Over 2.5" and not odds["over25"]: odds["over25"] = float(val["odd"])
                        elif val["value"] == "Under 2.5" and not odds["under25"]: odds["under25"] = float(val["odd"])
                elif bet_name == "Both Teams Score":
                    for val in bet.get("values", []):
                        if val["value"] == "Yes" and not odds["btts_yes"]: odds["btts_yes"] = float(val["odd"])

    tem_1x2_real = odds["home"] is not None and odds["away"] is not None
    return odds, tem_1x2_real

# 5. MOTOR DE ANÁLISE — agora sensível a dados reais x dados ausentes
def fmt_odd(v):
    return f"{v:.2f}" if v is not None else "N/D"

def processar_dados_partida_paralelo(home_id, home_name, away_id, away_name, fixture_id):
    with ThreadPoolExecutor(max_workers=3) as executor:
        f_home = executor.submit(obter_estatisticas_reais_time, home_id, "home")
        f_away = executor.submit(obter_estatisticas_reais_time, away_id, "away")
        f_odds = executor.submit(extrair_odds_partida, fixture_id)

        h = f_home.result()
        a = f_away.result()
        o, tem_odds_1x2 = f_odds.result()

    # Sem stats reais de mando (casa/fora) suficientes: tenta stats gerais como
    # segundo nível antes de desistir, em vez de inventar 1.2/45%.
    if h is None:
        h = obter_estatisticas_reais_time(home_id, "geral")
    if a is None:
        a = obter_estatisticas_reais_time(away_id, "geral")

    if h is None or a is None:
        return None  # sinaliza pro card renderizar "dados insuficientes"

    exp_gols_total = (h["media_gols_pro"] + a["media_gols_contra"] + a["media_gols_pro"] + h["media_gols_contra"]) / 2.0

    dicas = []

    if tem_odds_1x2:
        home_is_fav = o["home"] < o["away"]
        away_is_fav = o["away"] < o["home"]
    else:
        # Sem odds reais: usa aproveitamento recente como critério de favoritismo,
        # e nunca finge que existe uma odd de mercado.
        home_is_fav = h["aproveitamento"] > a["aproveitamento"] + 5
        away_is_fav = a["aproveitamento"] > h["aproveitamento"] + 5

    # 1. RESULTADO PRINCIPAL
    if home_is_fav:
        conf = "Alta" if (tem_odds_1x2 and o["home"] <= 1.60) or (not tem_odds_1x2 and h["aproveitamento"] >= 65) else "Média"
        dicas.append({
            "titulo": f"Vitória — {home_name}",
            "odd": o["home"] if tem_odds_1x2 else None,
            "conf": conf, "tipo": "alta" if conf == "Alta" else "media",
            "topicos": [
                (f"<b>Favoritismo pelas casas:</b> Odd {fmt_odd(o['home'])} para o mandante." if tem_odds_1x2
                 else "<b>Odds indisponíveis</b> nesta consulta — favoritismo calculado por desempenho recente."),
                f"<b>Retrospecto Local:</b> {home_name} tem {h['aproveitamento']}% de aproveitamento em ({h['jogos']} jogos analisados)."
            ]
        })
    elif away_is_fav:
        conf = "Alta" if (tem_odds_1x2 and o["away"] <= 1.60) or (not tem_odds_1x2 and a["aproveitamento"] >= 65) else "Média"
        dicas.append({
            "titulo": f"Vitória — {away_name}",
            "odd": o["away"] if tem_odds_1x2 else None,
            "conf": conf, "tipo": "alta" if conf == "Alta" else "media",
            "topicos": [
                (f"<b>Favoritismo pelas casas:</b> Odd {fmt_odd(o['away'])} para o visitante." if tem_odds_1x2
                 else "<b>Odds indisponíveis</b> nesta consulta — favoritismo calculado por desempenho recente."),
                f"<b>Desempenho Recente:</b> {away_name} tem {a['aproveitamento']}% de aproveitamento em ({a['jogos']} jogos analisados)."
            ]
        })
    else:
        fav_name = home_name if h["aproveitamento"] >= a["aproveitamento"] else away_name
        dicas.append({
            "titulo": f"{fav_name} — Empate Anula (DNB)",
            "odd": None, "conf": "Média", "tipo": "media",
            "topicos": [
                "<b>Equilíbrio Técnico:</b> nenhum lado com favoritismo claro nos dados disponíveis.",
                "Proteção de aposta com devolução integral em caso de empate."
            ]
        })

    # 2. LINHA / HANDICAP OU SEGURANÇA, só com odd real quando existir
    if tem_odds_1x2 and away_is_fav and o["away"] <= 1.65:
        dicas.append({
            "titulo": f"Handicap Asiático {away_name} (-1.0)",
            "odd": round(o["away"] * 1.45, 2), "conf": "Alta", "tipo": "alta",
            "topicos": [
                f"Projeção de vitória confortável do favorito visitante ({away_name}).",
                "Reembolso de aposta caso vença por apenas 1 gol de diferença."
            ]
        })
    elif tem_odds_1x2 and home_is_fav and o["home"] <= 1.65:
        dicas.append({
            "titulo": f"Handicap Asiático {home_name} (-1.0)",
            "odd": round(o["home"] * 1.45, 2), "conf": "Alta", "tipo": "alta",
            "topicos": [
                f"Projeção de domínio do mandante ({home_name}) em seus domínios.",
                "Devolução de aposta em caso de vitória por margem mínima."
            ]
        })
    else:
        dicas.append({
            "titulo": "Mais de 1.5 Gols no Jogo",
            "odd": o.get("over15") if tem_odds_1x2 else None, "conf": "Alta", "tipo": "alta",
            "topicos": [
                "Linha de alta frequência estatística para partidas com forças emparelhadas.",
                f"Médias combinadas de gols recentes: {home_name} {h['media_gols_pro']} g/j, {away_name} {a['media_gols_pro']} g/j."
            ]
        })

    # 3. TOTAL DE GOLS
    if exp_gols_total >= 2.6:
        dicas.append({
            "titulo": "Mais de 2.5 Gols",
            "odd": o.get("over25") if tem_odds_1x2 else None, "conf": "Média", "tipo": "media",
            "topicos": [
                f"<b>Expectativa de Gols:</b> média combinada projetada em {exp_gols_total:.2f} gols.",
                f"Ataque do mandante ({h['media_gols_pro']} g/j) e visitante ({a['media_gols_pro']} g/j) ativos."
            ]
        })
    else:
        dicas.append({
            "titulo": "Menos de 2.5 Gols (Under)",
            "odd": o.get("under25") if tem_odds_1x2 else None, "conf": "Média", "tipo": "media",
            "topicos": [
                f"<b>Projeção Truncada:</b> média combinada estimada em apenas {exp_gols_total:.2f} gols.",
                "Defesas bem postadas nos jogos recentes analisados."
            ]
        })

    # 4. AMBAS MARCAM OU ESCANTEIOS
    if h["media_gols_pro"] >= 1.1 and a["media_gols_pro"] >= 1.1:
        dicas.append({
            "titulo": "Ambas as Equipes Marcam (SIM)",
            "odd": o.get("btts_yes") if tem_odds_1x2 else None, "conf": "Média", "tipo": "media",
            "topicos": [
                "Ambos os times balançaram as redes na maioria dos seus últimos jogos.",
                f"Mandante marca {h['media_gols_pro']} g/j e Visitante marca {a['media_gols_pro']} g/j."
            ]
        })
    else:
        dicas.append({
            "titulo": "Mais de 8.5 Escanteios",
            "odd": None, "conf": "Baixa", "tipo": "baixa",
            "topicos": [
                "Estimativa por volume de jogo — sem dado direto de escanteios na fonte atual.",
                "Trate como mercado especulativo, confiança mais baixa que os demais."
            ]
        })

    return dicas[:4]

def extrair_status_e_horario(fix):
    status_short = fix.get("status", {}).get("short", "")
    elapsed = fix.get("status", {}).get("elapsed", 0)
    goals_home = fix.get("goals", {}).get("home")
    goals_away = fix.get("goals", {}).get("away")

    iso_date = fix.get("date", "")
    horario_str = ""
    if iso_date:
        try:
            dt_utc = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
            dt_br = dt_utc.astimezone(timezone(timedelta(hours=-3)))
            horario_str = dt_br.strftime("%H:%M")
        except Exception:
            horario_str = ""

    if status_short in ["1H", "2H", "ET", "P"]:
        status_label = f"🟢 Ao Vivo {elapsed}'"
        if goals_home is not None and goals_away is not None:
            status_label += f" ({goals_home}x{goals_away})"
    elif status_short in ["HT"]:
        status_label = f"🟡 Intervalo ({goals_home}x{goals_away})"
    elif status_short in ["FT", "AET", "PEN"]:
        status_label = f"✅ Encerrado"
        if goals_home is not None and goals_away is not None:
            status_label += f" ({goals_home}x{goals_away})"
    else:
        status_label = f"⏰ {horario_str}" if horario_str else "⏰ Não Iniciado"

    return status_label

# 6. RENDERIZAÇÃO
def renderizar_card_jogo_otimizado(item):
    fix = item["fixture"]
    league = item["league"]
    home = item["teams"]["home"]
    away = item["teams"]["away"]

    status_str = extrair_status_e_horario(fix)

    oportunidades = processar_dados_partida_paralelo(
        home["id"], home["name"], away["id"], away["name"], fix["id"]
    )

    with st.container(border=True):
        st.markdown(f"<h3 style='text-align: center; margin-bottom: 2px;'>{home['name']} x {away['name']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #fbbf24; font-size: 13px; font-weight: 600;'>🏆 {league['country']} {league['name']} &nbsp;•&nbsp; {status_str}</p>", unsafe_allow_html=True)

        if oportunidades is None:
            st.warning("⚠️ Dados históricos insuficientes para os dois times nesta consulta — pulando análise para não gerar dica genérica.")
            return

        st.markdown("#### 🎯 Dicas de Alto Valor")

        cols = st.columns(len(oportunidades))

        for idx, col in enumerate(cols):
            op = oportunidades[idx]
            badge_class = f"badge-{op['tipo']}"
            odd_texto = fmt_odd(op['odd'])

            with col:
                st.markdown(f"""
                <div class="opp-box">
                    <div class="opp-title">{op['titulo']}</div>
                    <div>
                        <span class="opp-odd">Odd {odd_texto}</span>
                        <span class="{badge_class}">{op['conf']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("#### 📋 Embasamento Estatístico")

        html_analises_lote = []
        for op in oportunidades:
            badge_tipo = op['tipo']
            card_class = f"analysis-card analysis-{badge_tipo}"
            topicos_html = "".join([f"<li>{t}</li>" for t in op['topicos']])

            html_analises_lote.append(f"""
            <div class="{card_class}">
                <div class="analysis-header">{op['titulo']} — Confiança {op['conf']}</div>
                <ul class="analysis-list">
                    {topicos_html}
                </ul>
            </div>
            """)

        st.markdown("".join(html_analises_lote), unsafe_allow_html=True)

# 7. HEADER PRINCIPAL
col_h1, col_h2, col_h3 = st.columns([1, 2, 1])

with col_h3:
    novo_tema = st.radio(
        "Aparência:",
        ["Escuro 🌙", "Claro ☀️"],
        index=0 if st.session_state["tema"] == "Escuro 🌙" else 1,
        horizontal=True
    )
    if novo_tema != st.session_state["tema"]:
        st.session_state["tema"] = novo_tema
        st.rerun()

with col_h2:
    try:
        st.image("logo.png", use_container_width=True)
    except Exception:
        cor_titulo = "#38bdf8" if st.session_state["tema"] == "Escuro 🌙" else "#0284c7"
        st.markdown(f"<h1 style='text-align: center; color: {cor_titulo}; margin-bottom: 20px;'>⚽ ANALISTA PRO</h1>", unsafe_allow_html=True)

# 8. FILTROS E EXECUÇÃO
now_utc = datetime.now(timezone.utc)
agora_br = now_utc - timedelta(hours=3)

col_f1, col_f2 = st.columns([1, 2])

with col_f1:
    opcao_filtro = st.radio("Selecione a data:", ["🔴 Jogos de Hoje", "🟡 Jogos de Amanhã"], horizontal=True)

data_alvo_str = agora_br.strftime("%Y-%m-%d") if "Hoje" in opcao_filtro else (agora_br + timedelta(days=1)).strftime("%Y-%m-%d")

partidas_brutas, erro_fixtures = api_get_fixtures(data_alvo_str)
if erro_fixtures:
    registrar_erro_api("fixtures", {"errors": erro_fixtures}, 200)

partidas_validas_dia = [item for item in partidas_brutas if item.get("fixture", {}).get("status", {}).get("short") != "CANC"]

# Painel de diagnóstico: mostra erros reais da API em vez de escondê-los
if st.session_state["api_erros"]:
    with st.expander("⚠️ Avisos da API (clique para ver detalhes)", expanded=False):
        for msg in st.session_state["api_erros"]:
            st.write(f"- {msg}")

ligas_do_dia_dict = {}
for item in partidas_validas_dia:
    country = item["league"].get("country", "")
    name = item["league"].get("name", "")
    nome_exibicao = f"{country}: {name}" if country else name

    if nome_exibicao not in ligas_do_dia_dict:
        ligas_do_dia_dict[nome_exibicao] = (country, name)

options_ligas_dia = sorted(list(ligas_do_dia_dict.keys()))

with col_f2:
    ligas_selecionadas_user = st.multiselect(
        "Filtrar Ligas Disponíveis no Dia:",
        options=options_ligas_dia,
        placeholder="Todas as ligas com jogos hoje/amanhã"
    )

btn_buscar = st.button("🔍 CARREGAR PROGNÓSTICOS DA IA", use_container_width=True)

partidas_filtradas = []
if ligas_selecionadas_user:
    for item in partidas_validas_dia:
        country = item["league"].get("country", "")
        name = item["league"].get("name", "")
        nome_exibicao = f"{country}: {name}" if country else name
        if nome_exibicao in ligas_selecionadas_user:
            partidas_filtradas.append(item)
else:
    partidas_filtradas = partidas_validas_dia

# 9. EXIBIÇÃO DAS PARTIDAS
if not partidas_filtradas:
    st.warning("⚠️ Nenhum jogo encontrado para a data selecionada.")
else:
    for item in partidas_filtradas[:15]:
        renderizar_card_jogo_otimizado(item)
