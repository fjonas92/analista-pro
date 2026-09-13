"""
Toda a comunicação com a API-Football vive aqui.

Regra de ouro do módulo: nenhuma função aqui inventa dado. Se a API não
responder algo, a função retorna None (ou uma lista/erro vazio) e quem
chama decide como lidar com a ausência — nunca preenchemos com valor
fixo fingindo que é real, porque isso é o que fazia todo jogo mostrar
a mesma dica.
"""
from concurrent.futures import ThreadPoolExecutor
import requests
import streamlit as st

BASE_URL = "https://v3.football.api-sports.io"


def _headers(api_key):
    return {"x-apisports-key": api_key}


@st.cache_data(ttl=600)
def api_get_fixtures(api_key, data_str):
    """Busca as partidas de uma data (YYYY-MM-DD), fuso America/Sao_Paulo.
    Retorna (lista_de_partidas, mensagem_de_erro_ou_None)."""
    url = f"{BASE_URL}/fixtures"
    params = {"timezone": "America/Sao_Paulo", "date": data_str}
    try:
        res = requests.get(url, headers=_headers(api_key), params=params, timeout=10)
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
def api_get_odds(api_key, fixture_id):
    """Busca odds pré-jogo de uma partida específica.
    Retorna (lista_de_bookmakers, mensagem_de_erro_ou_None)."""
    url = f"{BASE_URL}/odds"
    params = {"fixture": fixture_id}
    try:
        res = requests.get(url, headers=_headers(api_key), params=params, timeout=10)
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
        # Comum quando a liga/partida ainda não tem odds publicadas por
        # nenhuma casa parceira, ou o jogo está distante demais no tempo.
        return [], "Endpoint /odds voltou vazio para esta partida (sem cobertura de odds nesta consulta)."
    return resposta, None


@st.cache_data(ttl=3600)
def obter_estatisticas_reais_time(api_key, team_id, tipo_mando="geral"):
    """Últimos jogos de um time (opcionalmente filtrados por mando de
    campo: 'home', 'away' ou 'geral') e as métricas derivadas deles.
    Retorna None se não houver jogos suficientes — nunca um valor
    fabricado."""
    if not team_id:
        return None

    url = f"{BASE_URL}/fixtures"
    params = {"team": team_id, "last": 8}

    try:
        res = requests.get(url, headers=_headers(api_key), params=params, timeout=10)
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

    # Se o filtro por mando não deixou nenhum jogo, os dados são
    # insuficientes de verdade — melhor avisar do que fabricar um número.
    if jogos_processados == 0:
        return None

    n = jogos_processados
    aproveitamento = (vitorias * 3 + empates) / (n * 3)

    return {
        "jogos": n, "vitorias": vitorias, "empates": empates, "derrotas": derrotas,
        "media_gols_pro": round(gols_pro / n, 2),
        "media_gols_contra": round(gols_contra / n, 2),
        "aproveitamento": round(aproveitamento * 100, 1),
    }


def extrair_odds_partida(api_key, fixture_id):
    """Lê as odds de 1X2, Over/Under e BTTS de uma partida.

    IMPORTANTE — thread safety: esta função é chamada de dentro de um
    ThreadPoolExecutor (veja core/analysis.py). Ela NUNCA deve tocar em
    st.session_state diretamente; por isso retorna a mensagem de erro
    como valor de retorno, e quem chamou (já de volta na thread
    principal) é quem registra o erro.

    Retorna (dict_de_odds, tem_1x2_real: bool, mensagem_de_erro_ou_None).
    """
    raw_odds, erro = api_get_odds(api_key, fixture_id)

    odds = {
        "home": None, "draw": None, "away": None,
        "over15": None, "over25": None, "under25": None,
        "btts_yes": None,
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
    return odds, tem_1x2_real, erro


def buscar_dados_partida_paralelo(api_key, home_id, away_id, fixture_id):
    """Dispara em paralelo as 3 chamadas caras (stats casa, stats fora,
    odds) e devolve os resultados brutos. A montagem das dicas fica em
    core/analysis.py — este módulo só busca dado, não decide nada."""
    with ThreadPoolExecutor(max_workers=3) as executor:
        f_home = executor.submit(obter_estatisticas_reais_time, api_key, home_id, "home")
        f_away = executor.submit(obter_estatisticas_reais_time, api_key, away_id, "away")
        f_odds = executor.submit(extrair_odds_partida, api_key, fixture_id)

        h = f_home.result()
        a = f_away.result()
        o, tem_odds_1x2, erro_odds = f_odds.result()

    # Segundo nível: se não teve jogos suficientes filtrando por mando de
    # campo, tenta de novo sem esse filtro antes de desistir.
    if h is None:
        h = obter_estatisticas_reais_time(api_key, home_id, "geral")
    if a is None:
        a = obter_estatisticas_reais_time(api_key, away_id, "geral")

    return h, a, o, tem_odds_1x2, erro_odds
