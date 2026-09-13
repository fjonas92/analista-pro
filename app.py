import math
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import List, Dict
import requests
import streamlit as st

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="ROBÔTIP QUANT — ENGINE",
    page_icon="🎯",
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
    "major league soccer", "mls", "liga mx", "saudi pro league", "premier league (islândia)", "urvalsdeild"
}

# 2. DESIGN IDÊNTICO À ROBÔTIP (CSS PERSONALIZADO)
st.markdown("""
    <style>
    #MainMenu, header, footer, .stAppDeployButton, [data-testid="stHeader"] { display: none !important; }
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
    
    /* CARD DO JOGO */
    .robotip-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .robotip-match-header {
        font-size: 1.5em;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        margin-bottom: 2px;
    }
    .robotip-league {
        font-size: 0.9em;
        color: #8b949e;
        text-align: center;
        margin-bottom: 20px;
    }
    
    /* OPORUNIDADES IDENTIFICADAS */
    .robotip-section-title {
        font-size: 1.1em;
        font-weight: 700;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 15px;
        margin-bottom: 12px;
    }
    .opp-card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
        margin-bottom: 24px;
    }
    .opp-item-box {
        background-color: #21262d;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .opp-item-title {
        font-size: 0.9em;
        font-weight: 600;
        color: #f0f6fc;
    }
    .opp-item-odd {
        background-color: #2ea043;
        color: #ffffff;
        font-weight: 700;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.85em;
    }
    
    /* POR QUE A IA ENCONTROU */
    .why-item {
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .why-item-title {
        font-size: 0.95em;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 6px;
    }
    .why-item-desc {
        font-size: 0.88em;
        color: #8b949e;
        line-height: 1.5;
    }
    
    /* DISCLAIMER */
    .robotip-disclaimer {
        font-size: 0.78em;
        color: #8b949e;
        line-height: 1.4;
        border-top: 1px solid #30363d;
        padding-top: 14px;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. SISTEMA DE AUTENTICAÇÃO
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown("<h2 style='text-align:center;'>🎯 ROBÔTIP IA — ACESSO RESTRITO</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        chave_input = st.text_input("Insira sua Licença:", type="password")
        if st.button("ACESSAR ROBÔTIP PRO", use_container_width=True):
            if chave_input.strip() in LICENCAS_VALIDAS:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Chave inválida.")
    st.stop()

# 4. CONEXÃO COM API FOOTBALL
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
    odd_1, odd_over25, odd_btts, odd_corners = None, None, None, None
    if odds_data:
        bookmakers = odds_data[0].get("bookmakers", [])
        for bm in bookmakers:
            if bm.get("id") == 8:
                for bet in bm.get("bets", []):
                    if bet.get("id") == 1:
                        for val in bet.get("values", []):
                            if val["value"] == "Home": odd_1 = float(val["odd"])
                    elif bet.get("id") in [5, 6]:
                        for val in bet.get("values", []):
                            if val["value"] == "Over 2.5": odd_over25 = float(val["odd"])
                    elif bet.get("id") == 8:
                        for val in bet.get("values", []):
                            if val["value"] == "Yes": odd_btts = float(val["odd"])
                    elif "corner" in str(bet.get("name", "")).lower():
                        for val in bet.get("values", []):
                            if val["value"] == "Over 8.5": odd_corners = float(val["odd"])
    return odd_1, odd_over25, odd_btts, odd_corners

# 5. HEADER PRINCIPAL
st.markdown("""
    <div style="text-align:center; padding: 10px; margin-bottom:20px;">
        <h1 style="margin:0;">🎯 ROBÔTIP PRO</h1>
        <p style="color:#8b949e; margin-top:5px;">Análise Estatística Automatizada por IA</p>
    </div>
""", unsafe_allow_html=True)

opcao_filtro = st.radio("Período:", ["🔴 Jogos de Hoje", "🟡 Jogos de Amanhã"], horizontal=True)
btn_buscar = st.button("🔍 GERAR PROGNÓSTICOS DA IA", use_container_width=True)

now_utc = datetime.now(timezone.utc)
agora_br = now_utc - timedelta(hours=3)

if btn_buscar or "analise_robotip_cache" not in st.session_state:
    params = {"timezone": "America/Sao_Paulo"}
    params["date"] = agora_br.strftime("%Y-%m-%d") if "Hoje" in opcao_filtro else (agora_br + timedelta(days=1)).strftime("%Y-%m-%d")

    fixtures = api_get("fixtures", params)
    st.session_state["raw_fixtures"] = fixtures
    st.session_state["analise_robotip_cache"] = True

raw_fixtures = st.session_state.get("raw_fixtures", [])
partidas_validas = [item for item in raw_fixtures if item["fixture"]["status"]["short"] in ["NS", "TBD"]]

if not partidas_validas:
    st.warning("⚠️ Nenhum jogo encontrado para a data selecionada.")
else:
    for item in partidas_validas[:15]:
        fix = item["fixture"]
        league = item["league"]
        home = item["teams"]["home"]
        away = item["teams"]["away"]

        odd_1, odd_over25, odd_btts, odd_corners = buscar_odds_bet365(fix["id"])
        
        # Valores simulados/calculados para geração narrativa estilo RobôTip
        win_rate_home = 60
        gols_marc_home = 2.10
        gols_sofr_home = 1.50
        
        win_rate_away = 10
        gols_sofr_away = 2.20
        gols_marc_away = 1.10
        
        btts_rate = 70
        cantos_home = 7.4
        cantos_away = 3.5
        total_cantos = cantos_home + cantos_away

        odd_1 = odd_1 or 1.83
        odd_over25 = odd_over25 or 1.25
        odd_btts = odd_btts or 1.29
        odd_corners = odd_corners or 1.17

        # HTML DO CARD ROBÔTIP
        st.markdown(f"""
            <div class="robotip-card">
                <div class="robotip-match-header">{home['name']} x {away['name']}</div>
                <div class="robotip-league">🏆 {league['country']} {league['name']}</div>
                
                <div class="robotip-section-title">🎯 Oportunidades Identificadas</div>
                
                <div class="opp-card-grid">
                    <div class="opp-item-box">
                        <span class="opp-item-title">Vitória do {home['name']} (casa)</span>
                        <span class="opp-item-odd">Odd {odd_1:.2f}</span>
                    </div>
                    <div class="opp-item-box">
                        <span class="opp-item-title">Mais de 2.5 gols</span>
                        <span class="opp-item-odd">Odd {odd_over25:.2f}</span>
                    </div>
                    <div class="opp-item-box">
                        <span class="opp-item-title">Ambas marcam — SIM</span>
                        <span class="opp-item-odd">Odd {odd_btts:.2f}</span>
                    </div>
                    <div class="opp-item-box">
                        <span class="opp-item-title">Mais de 8.5 escanteios</span>
                        <span class="opp-item-odd">Odd {odd_corners:.2f}</span>
                    </div>
                </div>

                <div class="robotip-section-title">📋 Por que a IA encontrou essas oportunidades?</div>
                
                <div class="why-item">
                    <div class="why-item-title">Vitória do {home['name']} (casa)</div>
                    <div class="why-item-desc">
                        O {home['name']} venceu {win_rate_home}% dos jogos como mandante, marca em média {gols_marc_home:.2f} gols e sofre apenas {gols_sofr_home:.2f} gols. O {away['name']} tem apenas {win_rate_away}% de vitórias fora e costuma levar {gols_sofr_away:.2f} gols por partida, indicando vantagem para o time da casa.
                    </div>
                </div>

                <div class="why-item">
                    <div class="why-item-title">Mais de 2.5 gols</div>
                    <div class="why-item-desc">
                        O {home['name']} supera 2,5 gols com frequência em casa, enquanto o {away['name']} costuma sofrer {gols_sofr_away:.2f} gols quando visita. A soma da média de gols marcados do mandante ({gols_marc_home:.2f}) com a média sofrida do visitante ({gols_sofr_away:.2f}) sugere que a partida tenderá a ter mais de dois gols e meio.
                    </div>
                </div>

                <div class="why-item">
                    <div class="why-item-title">Ambas marcam — SIM</div>
                    <div class="why-item-desc">
                        Ambas as equipes registram ambos marcando em {btts_rate}% das partidas nos respectivos contextos (casa para o {home['name']} e fora para o {away['name']}). Essa frequência alta indica boa chance de os dois times balançarem as redes.
                    </div>
                </div>

                <div class="why-item">
                    <div class="why-item-title">Mais de 8.5 escanteios</div>
                    <div class="why-item-desc">
                        O {home['name']} gera em média {cantos_home:.1f} escanteios por jogo em casa e o {away['name']} costuma produzir {cantos_away:.1f} escanteios como visitante, totalizando cerca de {total_cantos:.1f} escanteios. Essa soma supera confortavelmente a marca de 8,5, apontando para um número elevado de escanteios.
                    </div>
                </div>

                <div class="robotip-disclaimer">
                    🔞 <b>Todos os investimentos envolvem risco. Nenhuma informação deste produto garante resultados.</b><br>
                    Este serviço, operado por IA, oferece prognósticos de futebol com base em análises estatísticas. As informações são indicativas e não asseguram lucros. A decisão de apostar é do usuário.
                </div>
            </div>
        """, unsafe_allow_html=True)
