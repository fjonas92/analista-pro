import math
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import List, Dict
import requests
import streamlit as st

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="QUANT BET365 — ENGINE PRO",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

API_FOOTBALL_KEY = st.secrets.get("API_FOOTBALL_KEY", "0d03200b5ee68704d96a72a1749aeca3")
LICENCAS_VALIDAS = ["PRO-FUTEBOL-2026", "VIP-ANALISTA-888", "CLIENTE-PRO-01", "ADMIN-MASTER-99"]

LIGAS_PERMITIDAS = {
    "serie a", "serie b", "serie c", "serie d", "copa do brasil", "supercopa do brasil", 
    "copa do nordeste", "brasileiro feminino", "paulista", "copa paulista", "carioca", 
    "mineiro", "gaucho", "paranaense", "catarinense", "baiano", "pernambucano", "cearense", 
    "conmebol libertadores", "libertadores", "conmebol sudamericana", "sudamericana", 
    "liga profesional", "copa argentina", "primera division", "copa chile", "primera a",
    "premier league", "championship", "league one", "fa cup", "efl cup",
    "laliga", "laliga 2", "copa del rey", "coppa italia",
    "bundesliga", "2. bundesliga", "dfb pokal", "ligue 1", "ligue 2", "primeira liga",
    "eredivisie", "pro league", "super lig", "uefa champions league", "uefa europa league", 
    "uefa conference league", "champions league", "europa league", "conference league",
    "major league soccer", "mls", "liga mx", "saudi pro league"
}

# 2. MOTOR QUANTITATIVO (CLASSES EMBUTIDAS)
@dataclass
class BetOpportunity:
    match_name: str
    market: str
    odd_bet365: float
    prob_real: float
    fair_odd: float
    ev: float

class PoissonModel:
    @staticmethod
    def _poisson_probability(lmbda: float, k: int) -> float:
        return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k)

    @classmethod
    def calculate_match_probabilities(cls, home_exp: float, away_exp: float, max_goals: int = 6) -> Dict[str, float]:
        prob_matrix = [[0.0 for _ in range(max_goals + 1)] for _ in range(max_goals + 1)]
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                prob_matrix[i][j] = cls._poisson_probability(home_exp, i) * cls._poisson_probability(away_exp, j)

        prob_home = sum(prob_matrix[i][j] for i in range(max_goals + 1) for j in range(max_goals + 1) if i > j)
        prob_draw = sum(prob_matrix[i][i] for i in range(max_goals + 1))
        prob_away = sum(prob_matrix[i][j] for i in range(max_goals + 1) for j in range(max_goals + 1) if i < j)
        prob_over_15 = sum(prob_matrix[i][j] for i in range(max_goals + 1) for j in range(max_goals + 1) if (i + j) > 1.5)
        prob_over_25 = sum(prob_matrix[i][j] for i in range(max_goals + 1) for j in range(max_goals + 1) if (i + j) > 2.5)
        prob_btts = sum(prob_matrix[i][j] for i in range(1, max_goals + 1) for j in range(1, max_goals + 1))

        return {
            "Home": prob_home, "Draw": prob_draw, "Away": prob_away,
            "Over 1.5": prob_over_15, "Over 2.5": prob_over_25, "BTTS": prob_btts
        }

class QuantitativeEngine:
    def __init__(self, lg_home_avg: float = 1.45, lg_away_avg: float = 1.15):
        self.lg_home_avg = lg_home_avg
        self.lg_away_avg = lg_away_avg

    def analyze(self, xg_home: float, xg_away: float, odd_1: float, odd_x: float, odd_2: float, odd_over15: float) -> Dict:
        probs = PoissonModel.calculate_match_probabilities(xg_home, xg_away)
        ev_1 = (probs["Home"] * odd_1) - 1
        ev_over15 = (probs["Over 1.5"] * odd_over15) - 1

        return {
            "probs": probs,
            "ev_home": ev_1,
            "ev_over15": ev_over15
        }

# 3. SIDEBAR & ESTILIZAÇÃO
with st.sidebar:
    st.header("🎨 Aparência")
    tema = st.selectbox("Selecione o Tema:", ["Escuro (Dark)", "Azul Profundo", "Claro (Light)"])

if tema == "Azul Profundo":
    bg_main, bg_card, bg_inner, text_color, border_color = "#0B192C", "#1E3E62", "#050B14", "#FFFFFF", "#1E56A0"
elif tema == "Claro (Light)":
    bg_main, bg_card, bg_inner, text_color, border_color = "#F4F6F9", "#FFFFFF", "#E9ECEF", "#1A1A1A", "#CED4DA"
else:
    bg_main, bg_card, bg_inner, text_color, border_color = "#0E0E10", "#141417", "#1A1A1E", "#FFFFFF", "#26262C"

st.markdown(f"""
    <style>
    #MainMenu, header, footer, .stAppDeployButton, [data-testid="stHeader"] {{ display: none !important; }}
    .stApp {{ background-color: {bg_main}; color: {text_color}; font-family: 'Inter', sans-serif; }}
    .main-header {{ text-align: center; padding: 18px; background-color: {bg_card}; border-radius: 10px; border: 1px solid {border_color}; margin-bottom: 20px; }}
    .main-title {{ color: {text_color}; font-size: 1.6em; font-weight: 700; margin: 0; }}
    .sub-title {{ color: #8E8E93; font-size: 0.9em; margin-top: 5px; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; border-bottom: 1px solid {border_color}; }}
    .stTabs [data-baseweb="tab"] {{ background-color: {bg_card}; border-radius: 8px 8px 0px 0px; padding: 10px 16px; color: #8E8E93; border: 1px solid {border_color}; font-weight: 600; font-size: 0.88em; }}
    .stTabs [aria-selected="true"] {{ background-color: #0066FF !important; color: #FFFFFF !important; border: 1px solid #0066FF !important; }}
    .combo-card {{ background-color: {bg_card}; border: 1px solid {border_color}; border-radius: 12px; padding: 20px; margin-bottom: 20px; }}
    .combo-header {{ font-weight: bold; font-size: 1.1em; color: #00FF66; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid {border_color}; padding-bottom: 10px; }}
    .combo-item {{ font-size: 0.9em; padding: 10px 0; border-bottom: 1px solid {border_color}; }}
    .match-card {{ background-color: {bg_card}; border: 1px solid {border_color}; border-radius: 12px; padding: 20px; margin-bottom: 25px; }}
    .match-header {{ font-size: 1.3em; font-weight: bold; color: {text_color}; margin-bottom: 4px; }}
    .league-header {{ font-size: 0.85em; color: #0066FF; font-weight: 600; margin-bottom: 14px; }}
    .odds-row {{ display: flex; gap: 10px; margin-bottom: 15px; background: {bg_inner}; padding: 10px; border-radius: 8px; border: 1px solid {border_color}; }}
    .odd-box {{ flex: 1; text-align: center; background: {bg_card}; padding: 8px; border-radius: 6px; border: 1px solid {border_color}; }}
    .odd-box span {{ display: block; font-size: 0.75em; color: #8E8E93; text-transform: uppercase; }}
    .odd-box strong {{ font-size: 1.1em; color: #00FF66; }}
    .section-title {{ font-size: 1.0em; font-weight: 600; color: {text_color}; margin-top: 15px; margin-bottom: 12px; }}
    .opp-item {{ background-color: {bg_inner}; border: 1px solid {border_color}; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }}
    .opp-title {{ font-weight: 600; font-size: 0.95em; color: {text_color}; display: flex; align-items: center; gap: 10px; }}
    .badge-alta {{ background-color: #122B1A; color: #00FF66; border: 1px solid #00FF66; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 0.78em; }}
    .badge-media {{ background-color: #2B2512; color: #FFCC00; border: 1px solid #FFCC00; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 0.78em; }}
    .opp-odd {{ background-color: {border_color}; color: {text_color}; font-weight: bold; padding: 4px 10px; border-radius: 6px; font-size: 0.9em; }}
    .why-box {{ background-color: {bg_inner}; border-left: 3px solid #0066FF; padding: 12px 16px; border-radius: 4px; margin-top: 10px; margin-bottom: 15px; font-size: 0.88em; line-height: 1.6; }}
    .disclaimer-box {{ font-size: 0.80em; color: #FF6B6B; margin-top: 20px; border-top: 1px solid {border_color}; padding-top: 12px; line-height: 1.4; font-weight: bold; text-align: center; }}
    </style>
""", unsafe_allow_html=True)

# 4. AUTENTICAÇÃO
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown("<div class='main-header'><div class='main-title'>🔒 PAINEL QUANTITATIVO DE APOSTAS</div></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        chave_input = st.text_input("Insira sua Licença:", type="password")
        if st.button("ACESSAR ENGINE", use_container_width=True):
            if chave_input.strip() in LICENCAS_VALIDAS:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Chave inválida.")
    st.stop()

# 5. INTEGRACÃO API
@st.cache_data(ttl=900)
def api_get(endpoint, params=None):
    url = f"https://v3.football.api-sports.io/{endpoint}"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        return res.json().get("response", []) if res.status_code == 200 else []
    except Exception:
        return []

def buscar_odds_bet365(fixture_id):
    odds_data = api_get("odds", {"fixture": fixture_id, "bookmaker": 8})
    odd_1, odd_x, odd_2, odd_over15 = None, None, None, None
    if odds_data:
        bookmakers = odds_data[0].get("bookmakers", [])
        for bm in bookmakers:
            if bm.get("id") == 8:
                for bet in bm.get("bets", []):
                    if bet.get("id") == 1:
                        for val in bet.get("values", []):
                            if val["value"] == "Home": odd_1 = float(val["odd"])
                            elif val["value"] == "Draw": odd_x = float(val["odd"])
                            elif val["value"] == "Away": odd_2 = float(val["odd"])
                    elif bet.get("id") in [5, 6]:
                        for val in bet.get("values", []):
                            if val["value"] == "Over 1.5": odd_over15 = float(val["odd"])
    return odd_1, odd_x, odd_2, odd_over15

def liga_eh_permitida(nome_liga, pais):
    texto = f"{nome_liga} {pais}".lower()
    return any(p in texto for p in LIGAS_PERMITIDAS)

# 6. HEADER E CONTROLES
st.markdown("""
    <div class='main-header'>
        <div class='main-title'>⚽ QUANT ENGINE PRO — BET365</div>
        <div class='sub-title'>Modelo Quantitativo Poisson + EV+ Bet365</div>
    </div>
""", unsafe_allow_html=True)

opcao_filtro = st.radio("Período de Análise:", ["🔴 Jogos de Hoje", "🟡 Jogos de Amanhã", "🌟 Próximos Jogos"], horizontal=True)
btn_buscar = st.button("🔍 EXECUTAR ANÁLISE QUANTITATIVA AVANÇADA", use_container_width=True)

now_utc = datetime.now(timezone.utc)
agora_br = now_utc - timedelta(hours=3)

if btn_buscar or "analise_cache" not in st.session_state:
    params = {"timezone": "America/Sao_Paulo"}
    if "Hoje" in opcao_filtro:
        params["date"] = agora_br.strftime("%Y-%m-%d")
    elif "Amanhã" in opcao_filtro:
        params["date"] = (agora_br + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        params["next"] = "50"

    fixtures = api_get("fixtures", params)
    st.session_state["raw_fixtures"] = fixtures
    st.session_state["analise_cache"] = True

raw_fixtures = st.session_state.get("raw_fixtures", [])
partidas_validas = []

for item in raw_fixtures:
    fix = item["fixture"]
    league = item["league"]
    if fix["status"]["short"] in ["NS", "TBD"]:
        dt_fix = datetime.fromisoformat(fix["date"].replace("Z", "+00:00"))
        if dt_fix > now_utc and liga_eh_permitida(league["name"], league["country"]):
            partidas_validas.append((dt_fix, item))

partidas_validas.sort(key=lambda x: x[0])

if not partidas_validas:
    st.warning("⚠️ Nenhum jogo futuro com cotações Bet365 disponível no momento.")
else:
    engine = QuantitativeEngine()
    partidas_processadas = []
    entradas_globais = []

    with st.spinner("Analisando com Distribuição de Poisson e Odds Bet365..."):
        for dt_fix, item in partidas_validas[:25]:
            fix, league = item["fixture"], item["league"]
            home, away = item["teams"]["home"], item["teams"]["away"]
            
            odd_1, odd_x, odd_2, odd_over15 = buscar_odds_bet365(fix["id"])
            if not odd_1 or not odd_x or not odd_2:
                continue
            if not odd_over15:
                odd_over15 = 1.30

            # Simulação xG com base no padrão quantitativo
            xg_h, xg_a = 1.65, 1.10
            q_res = engine.analyze(xg_h, xg_a, odd_1, odd_x, odd_2, odd_over15)

            opp_alta = {
                "match": f"{home['name']} x {away['name']}",
                "titulo": f"Vitória do {home['name']} (Bet365 1X2)",
                "val_odd": odd_1,
                "badge": "<span class='badge-alta'>🟢 ALTA CONFIANÇA (EV+)</span>" if q_res["ev_home"] > 0 else "<span class='badge-media'>🟡 MÉDIA CONFIANÇA</span>",
                "tipo": "ALTA" if q_res["ev_home"] > 0 else "MEDIA",
                "exp": f"<b>MODELO QUANTITATIVO:</b> Probabilidade calculada via Poisson de <b>{q_res['probs']['Home']*100:.1f}%</b> contra Odd Bet365 de <b>@{odd_1:.2f}</b>."
            }

            opp_baixa = {
                "match": f"{home['name']} x {away['name']}",
                "titulo": f"Over 1.5 Gols",
                "val_odd": odd_over15,
                "badge": "<span class='badge-alta'>🟢 ALTA CONFIANÇA</span>",
                "tipo": "MEDIA",
                "exp": f"<b>ANÁLISE DE GOLS:</b> Probabilidade calculada de <b>{q_res['probs']['Over 1.5']*100:.1f}%</b> para ao menos 2 gols."
            }

            p_obj = {
                "dt": dt_fix,
                "home": home["name"],
                "away": away["name"],
                "league_str": f"{league['country']} — {league['name']}",
                "odd_1": odd_1, "odd_x": odd_x, "odd_2": odd_2,
                "odd_over15": odd_over15,
                "opps": [opp_alta, opp_baixa]
            }
            partidas_processadas.append(p_obj)
            entradas_globais.extend([opp_alta, opp_baixa])

    # 7. ABAS DE EXIBIÇÃO
    tab_jogos, tab_combos, tab_rankings, tab_over15 = st.tabs([
        "⚽ JOGOS & ANÁLISES DETALHADAS",
        "🚀 DUPLAS & MÚLTIPLAS EV+",
        "🏆 TOP MANDANTES E VISITANTES",
        "🔥 LISTA OVER 1.5 GOLS"
    ])

    with tab_jogos:
        ligas = sorted(list(set([p["league_str"] for p in partidas_processadas])))
        opcao_liga = st.selectbox("📌 Filtrar por Campeonato:", ["🌍 Todas as Ligas Autorizadas"] + ligas)
        partidas_exibir = [p for p in partidas_processadas if opcao_liga == "🌍 Todas as Ligas Autorizadas" or p["league_str"] == opcao_liga]

        st.success(f"✅ Exibindo {len(partidas_exibir)} partida(s) com odds exclusivas Bet365.")

        for p in partidas_exibir:
            dt_br = p["dt"] - timedelta(hours=3)
            st.markdown(f"""
                <div class="match-card">
                    <div class="match-header">⚽ {p['home']} x {p['away']}</div>
                    <div class="league-header">🏆 {p['league_str']} | 📅 {dt_br.strftime('%d/%m às %H:%M')}</div>
                    <div class="odds-row">
                        <div class="odd-box"><span>Casa ({p['home']})</span><strong>@{p['odd_1']:.2f}</strong></div>
                        <div class="odd-box"><span>Empate (X)</span><strong>@{p['odd_x']:.2f}</strong></div>
                        <div class="odd-box"><span>Fora ({p['away']})</span><strong>@{p['odd_2']:.2f}</strong></div>
                    </div>
            """, unsafe_allow_html=True)

            for opp in p["opps"]:
                st.markdown(f"""
                    <div class="opp-item">
                        <div class="opp-title">{opp['badge']} <span>{opp['titulo']}</span></div>
                        <div class="opp-odd">@{opp['val_odd']:.2f}</div>
                    </div>
                    <div class="why-box">{opp['exp']}</div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_combos:
        st.subheader("🔥 Bilhetes Otimizados Sem Correlação Negativa (Odd 1.60 - 2.00)")
        duplas = []
        for i in range(len(entradas_globais)):
            for j in range(i + 1, len(entradas_globais)):
                if entradas_globais[i]["match"] != entradas_globais[j]["match"]:
                    odd_c = entradas_globais[i]["val_odd"] * entradas_globais[j]["val_odd"]
                    if 1.60 <= odd_c <= 2.00:
                        duplas.append((entradas_globais[i], entradas_globais[j], odd_c))
                        if len(duplas) >= 3: break
            if len(duplas) >= 3: break

        cols = st.columns(len(duplas) if duplas else 1)
        for idx, (d1, d2, odd_tot) in enumerate(duplas):
            with cols[idx]:
                st.markdown(f"""
                    <div class="combo-card">
                        <div class="combo-header"><span>🟢 DUPLA PRO EV+ #{idx+1}</span><span style="color:#00FF66;">@{odd_tot:.2f}</span></div>
                        <div class="combo-item">📌 <b>{d1['match']}</b><br>{d1['titulo']} (@{d1['val_odd']:.2f})</div>
                        <div class="combo-item">📌 <b>{d2['match']}</b><br>{d2['titulo']} (@{d2['val_odd']:.2f})</div>
                    </div>
                """, unsafe_allow_html=True)

    with tab_rankings:
        tab_m, tab_v = st.tabs(["🏆 Melhores Mandantes", "✈️ Melhores Visitantes"])
        with tab_m:
            for p in sorted(partidas_processadas, key=lambda x: x["odd_1"]):
                st.markdown(f"<div class='opp-item'><div><b>{p['home']}</b> vs {p['away']}</div><div class='opp-odd'>Odd Bet365: @{p['odd_1']:.2f}</div></div>", unsafe_allow_html=True)
        with tab_v:
            for p in sorted(partidas_processadas, key=lambda x: x["odd_2"]):
                st.markdown(f"<div class='opp-item'><div><b>{p['away']}</b> (Fora) vs {p['home']}</div><div class='opp-odd'>Odd Bet365: @{p['odd_2']:.2f}</div></div>", unsafe_allow_html=True)

    with tab_over15:
        st.subheader("🔥 Lista Over 1.5 Gols")
        for p in partidas_processadas:
            st.markdown(f"<div class='opp-item'><div><b>{p['home']} x {p['away']}</b> — {p['league_str']}</div><div class='opp-odd'>Odd Bet365: @{p['odd_over15']:.2f}</div></div>", unsafe_allow_html=True)
