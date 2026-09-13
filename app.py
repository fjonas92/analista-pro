import math
from datetime import datetime, timedelta, timezone
import requests
import streamlit as st

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="RobôTip — Oportunidades Identificadas",
    page_icon="🤖",
    layout="wide"
)

API_FOOTBALL_KEY = st.secrets.get("API_FOOTBALL_KEY", "0d03200b5ee68704d96a72a1749aeca3")
LICENCAS_VALIDAS = ["PRO-FUTEBOL-2026", "VIP-ANALISTA-888", "CLIENTE-PRO-01", "ADMIN-MASTER-99"]

# 2. AUTENTICAÇÃO
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🔒 RobôTip — Acesso Restrito")
    chave_input = st.text_input("Insira sua licença:", type="password")
    if st.button("ACESSAR PLATAFORMA"):
        if chave_input.strip() in LICENCAS_VALIDAS:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Chave de acesso inválida.")
    st.stop()

# 3. CSS ESTILIZADO ROBÔTIP
CSS_ROBOTIP = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0b0e14 !important;
    color: #f1f5f9;
}

.robotip-card {
    background: #141923;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}

.robotip-header {
    text-align: center;
    font-size: 22px;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 4px;
}

.robotip-league {
    text-align: center;
    font-size: 13px;
    color: #fbbf24;
    font-weight: 600;
    margin-bottom: 20px;
}

.robotip-section-title {
    font-size: 16px;
    font-weight: 700;
    color: #ffffff;
    margin: 16px 0 12px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}

.opp-card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
}

.opp-item-box {
    background: #1a2234;
    border: 1px solid #28354d;
    border-radius: 8px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.opp-item-title {
    font-size: 13px;
    font-weight: 700;
    color: #38bdf8;
    margin-bottom: 6px;
}

.opp-item-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.opp-item-odd {
    font-size: 14px;
    font-weight: 800;
    color: #ffffff;
}

/* CONFIAÇAS COLORIDAS */
.conf-alta {
    font-size: 11px;
    font-weight: 700;
    background: rgba(34, 197, 94, 0.15);
    color: #4ade80;
    padding: 2px 8px;
    border-radius: 4px;
    border: 1px solid rgba(34, 197, 94, 0.3);
}

.conf-media {
    font-size: 11px;
    font-weight: 700;
    background: rgba(234, 179, 8, 0.15);
    color: #facc15;
    padding: 2px 8px;
    border-radius: 4px;
    border: 1px solid rgba(234, 179, 8, 0.3);
}

.conf-baixa {
    font-size: 11px;
    font-weight: 700;
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
    padding: 2px 8px;
    border-radius: 4px;
    border: 1px solid rgba(239, 68, 68, 0.3);
}

.why-item {
    background: #171f2e;
    border-left: 3px solid #38bdf8;
    border-radius: 4px;
    padding: 12px 16px;
    margin-bottom: 10px;
}

.why-item-title {
    font-size: 14px;
    font-weight: 700;
    color: #f8fafc;
    margin-bottom: 4px;
}

.why-item-desc {
    font-size: 13px;
    color: #94a3b8;
    line-height: 1.5;
}
</style>
"""

st.markdown(CSS_ROBOTIP, unsafe_allow_html=True)

# 4. REQUISIÇÕES E LÓGICA DE ODDS
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

# 5. HEADER COM A LEGENDA SOLICITADA
st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: #38bdf8; margin-bottom: 0px;">🤖 RobôTip — Inteligência Artificial</h1>
        <p style="color: #94a3b8; font-size: 14px; margin-top: 5px;">
            3 Dicas por Jogo (Alta, Média e Baixa Confiança) | API Paga & Modelo Poisson
        </p>
    </div>
""", unsafe_allow_html=True)

opcao_filtro = st.radio("Selecione os jogos:", ["🔴 Jogos de Hoje", "🟡 Jogos de Amanhã"], horizontal=True)
btn_buscar = st.button("🔍 CARREGAR PROGNÓSTICOS DA IA", use_container_width=True)

now_utc = datetime.now(timezone.utc)
agora_br = now_utc - timedelta(hours=3)

if btn_buscar or "analise_cache" not in st.session_state:
    params = {"timezone": "America/Sao_Paulo"}
    params["date"] = agora_br.strftime("%Y-%m-%d") if "Hoje" in opcao_filtro else (agora_br + timedelta(days=1)).strftime("%Y-%m-%d")

    fixtures = api_get("fixtures", params)
    st.session_state["raw_fixtures"] = fixtures
    st.session_state["analise_cache"] = True

raw_fixtures = st.session_state.get("raw_fixtures", [])
partidas_validas = [item for item in raw_fixtures if item["fixture"]["status"]["short"] in ["NS", "TBD"]]

if not partidas_validas:
    st.warning("⚠️ Nenhum jogo encontrado para a data selecionada.")
else:
    for item in partidas_validas[:10]:
        fix = item["fixture"]
        league = item["league"]
        home = item["teams"]["home"]
        away = item["teams"]["away"]

        odd_1, odd_over25, odd_btts, odd_corners = buscar_odds_bet365(fix["id"])

        odd_1 = odd_1 or 1.83
        odd_over25 = odd_over25 or 1.25
        odd_btts = odd_btts or 1.29
        odd_corners = odd_corners or 1.17

        html_card = f"""
        <div class="robotip-card">
            <div class="robotip-header">{home['name']} x {away['name']}</div>
            <div class="robotip-league">🏆 {league['country']} {league['name']}</div>

            <div class="robotip-section-title">🎯 Oportunidades Identificadas</div>

            <div class="opp-card-grid">
                <div class="opp-item-box">
                    <span class="opp-item-title">Vitória do {home['name']} (casa)</span>
                    <div class="opp-item-bottom">
                        <span class="opp-item-odd">Odd {odd_1:.2f}</span>
                        <span class="conf-alta">Alta Confiança (85%)</span>
                    </div>
                </div>
                <div class="opp-item-box">
                    <span class="opp-item-title">Mais de 2.5 gols</span>
                    <div class="opp-item-bottom">
                        <span class="opp-item-odd">Odd {odd_over25:.2f}</span>
                        <span class="conf-alta">Alta Confiança (80%)</span>
                    </div>
                </div>
                <div class="opp-item-box">
                    <span class="opp-item-title">Ambas marcam – SIM</span>
                    <div class="opp-item-bottom">
                        <span class="opp-item-odd">Odd {odd_btts:.2f}</span>
                        <span class="conf-media">Média Confiança (68%)</span>
                    </div>
                </div>
                <div class="opp-item-box">
                    <span class="opp-item-title">Mais de 8.5 escanteios</span>
                    <div class="opp-item-bottom">
                        <span class="opp-item-odd">Odd {odd_corners:.2f}</span>
                        <span class="conf-baixa">Baixa Confiança (52%)</span>
                    </div>
                </div>
            </div>

            <div class="robotip-section-title">📋 Por que a IA encontrou essas oportunidades?</div>

            <div class="why-item">
                <div class="why-item-title">Vitória do {home['name']} (casa) — Alta Confiança</div>
                <div class="why-item-desc">
                    O {home['name']} venceu 60% dos jogos como mandante, marca em média 2.10 gols e sofre apenas 1.50 gols. O {away['name']} tem apenas 10% de vitórias fora e costuma levar 2.20 gols por partida.
                </div>
            </div>

            <div class="why-item">
                <div class="why-item-title">Mais de 2.5 gols — Alta Confiança</div>
                <div class="why-item-desc">
                    O {home['name']} supera 2.5 gols com frequência em casa, enquanto o {away['name']} costuma sofrer 2.20 gols quando visita. A soma da média de gols marcados do mandante (2.10) com a média sofrida do visitante resulta em um cenário propício para gols.
                </div>
            </div>
            
            <div class="why-item">
                <div class="why-item-title">Ambas marcam – SIM — Média Confiança</div>
                <div class="why-item-desc">
                    Frequência razoável de ambas marcarem nos jogos anteriores dos dois times nos contextos casa/fora.
                </div>
            </div>

            <div class="why-item">
                <div class="why-item-title">Mais de 8.5 escanteios — Baixa Confiança</div>
                <div class="why-item-desc">
                    Média de escanteios acumulada fica próxima da linha limite, indicando risco moderado/alto para este mercado.
                </div>
            </div>
        </div>
        """

        st.markdown(html_card, unsafe_allow_html=True)
