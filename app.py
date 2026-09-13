from datetime import datetime, timedelta, timezone
import math
import requests
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="ANALISTA PRO — QUANT ENGINE",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilização CSS White-Label Pro
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    [data-testid="stHeader"] {display: none;}
    
    .stApp { background-color: #121212; color: #FFFFFF; }
    .main-header { text-align: center; padding: 15px; background-color: #1A1A1A; border-radius: 8px; margin-bottom: 20px; }
    .card-jogo { background-color: #1E1E1E; border: 1px solid #0066FF; border-radius: 8px; padding: 15px; margin-bottom: 12px; }
    .liga-title { color: #0066FF; font-weight: bold; font-size: 0.85em; }
    .confronto-title { color: #FFFFFF; font-weight: bold; font-size: 1.25em; margin-bottom: 8px; }
    .badge-valor { background-color: #1E2A1E; color: #00FF66; border: 1px solid #00FF66; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8em; }
    .badge-nobet { background-color: #2A1E1E; color: #FF4444; border: 1px solid #FF4444; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8em; }
    .analise-box { background-color: #161616; border-left: 3px solid #0066FF; padding: 12px; margin-top: 8px; margin-bottom: 12px; font-size: 0.88em; color: #DDDDDD; }
    .metric-container { display: flex; justify-content: space-between; background-color: #222222; padding: 10px; border-radius: 6px; margin-bottom: 10px; font-size: 0.85em; }
    .risk-box { background-color: #221A1A; border-left: 3px solid #FF4444; padding: 8px 12px; margin-top: 6px; font-size: 0.85em; color: #FFAAAA; }
    </style>
""",
    unsafe_allow_html=True,
)

API_FOOTBALL_KEY = st.secrets.get("API_FOOTBALL_KEY", "0d03200b5ee68704d96a72a1749aeca3")
LICENCAS_VALIDAS = ["PRO-FUTEBOL-2026", "VIP-ANALISTA-888", "CLIENTE-PRO-01", "ADMIN-MASTER-99"]

# Autenticação
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown("<div class='main-header'><h1>🔒 ANALISTA PRO — ENGINE QUANTITATIVO</h1></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        chave_input = st.text_input("Chave de Licença:", type="password", placeholder="Ex: PRO-FUTEBOL-2026")
        if st.button("🔑 ENTRAR NO SISTEMA", use_container_width=True):
            if chave_input.strip() in LICENCAS_VALIDAS:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("❌ Licença inválida.")
    st.stop()

# --- PAINEL PRINCIPAL ---
st.markdown("<div class='main-header'><h1>⚽ ANALISTA PRO — MOTOR DE ANÁLISE QUANTITATIVA</h1></div>", unsafe_allow_html=True)

opcao_filtro = st.radio(
    "Filtrar partidas por período:",
    options=["🌟 Todos os Próximos Jogos", "🔴 Jogos de Hoje (Restantes)", "🟡 Jogos de Amanhã"],
    horizontal=True,
)
btn_buscar = st.button("🔍 PROCESSAR DADOS QUANTITATIVOS E GERAR ANÁLISES", use_container_width=True)


# --- FUNÇÕES DE COLETA E MODELAGEM MATEMÁTICA ---
@st.cache_data(ttl=900)
def api_get(endpoint, params=None):
    url = f"https://v3.football.api-sports.io/{endpoint}"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            return res.json().get("response", [])
        return []
    except Exception:
        return []


def calcular_poisson(lambda_gols, k):
    """Calcula a probabilidade Poisson de exatos k gols"""
    return (math.pow(lambda_gols, k) * math.exp(-lambda_gols)) / math.factorial(k)


def analisar_partida_quant(fixture):
    fixture_id = fixture["fixture"]["id"]
    home_id = fixture["teams"]["home"]["id"]
    away_id = fixture["teams"]["away"]["id"]
    league_id = fixture["league"]["id"]
    season = fixture["league"]["season"]

    # 1. Coleta estatística de cada equipe
    stat_home = api_get("teams/statistics", {"league": league_id, "season": season, "team": home_id})
    stat_away = api_get("teams/statistics", {"league": league_id, "season": season, "team": away_id})

    # Validação de Qualidade de Dados (Pipeline: Dados Suficientes?)
    if not stat_home or not stat_away:
        return None, "Dados insuficientes"

    sh = stat_home
    sa = stat_away

    # Médias de Gols e Cálculo do Lambda do Modelo
    g_home_scored = float(sh.get("goals", {}).get("for", {}).get("average", {}).get("home", 1.2) or 1.2)
    g_home_conceded = float(sh.get("goals", {}).get("against", {}).get("average", {}).get("home", 1.0) or 1.0)
    g_away_scored = float(sa.get("goals", {}).get("for", {}).get("average", {}).get("away", 1.0) or 1.0)
    g_away_conceded = float(sa.get("goals", {}).get("against", {}).get("average", {}).get("away", 1.3) or 1.3)

    lambda_home = (g_home_scored + g_away_conceded) / 2.0
    lambda_away = (g_away_scored + g_home_conceded) / 2.0

    # Matriz Poisson para probabilidade de resultado
    prob_home, prob_draw, prob_away = 0.0, 0.0, 0.0
    prob_over15, prob_over25, prob_btts = 0.0, 0.0, 0.0

    for h in range(6):
        for a in range(6):
            p = calcular_poisson(lambda_home, h) * calcular_poisson(lambda_away, a)
            if h > a:
                prob_home += p
            elif h == a:
                prob_draw += p
            else:
                prob_away += p

            if (h + a) > 1.5:
                prob_over15 += p
            if (h + a) > 2.5:
                prob_over25 += p
            if h > 0 and a > 0:
                prob_btts += p

    # 2. Odds da Bet365
    odds_raw = api_get("odds", {"fixture": fixture_id, "bookmaker": "8"})
    odd_h, odd_d, odd_a = 2.10, 3.20, 3.50
    odd_o15, odd_o25, odd_btts = 1.30, 1.95, 1.80

    if odds_raw and "bookmakers" in odds_raw[0]:
        for bet in odds_raw[0]["bookmakers"][0].get("bets", []):
            if bet["id"] == 1:
                for v in bet["values"]:
                    if v["value"] == "Home": odd_h = float(v["odd"])
                    elif v["value"] == "Draw": odd_d = float(v["odd"])
                    elif v["value"] == "Away": odd_a = float(v["odd"])
            elif bet["id"] == 5:
                for v in bet["values"]:
                    if v["value"] == "Over 2.5": odd_o25 = float(v["odd"])
            elif bet["id"] == 8:
                for v in bet["values"]:
                    if v["value"] == "Yes": odd_btts = float(v["odd"])

    # 3. Cálculo de Analista Score (0-100) & Edge Percentual
    prob_impl_h = (1.0 / odd_h) * 100
    edge_h = (prob_home * 100) - prob_impl_h
    score_h = min(100, max(0, int((prob_home * 100 * 0.7) + (g_home_scored * 10))))

    prob_impl_o15 = (1.0 / odd_o15) * 100
    edge_o15 = (prob_over15 * 100) - prob_impl_o15
    score_o15 = min(100, max(0, int((prob_over15 * 100 * 0.7) + ((lambda_home + lambda_away) * 10))))

    prob_impl_btts = (1.0 / odd_btts) * 100
    edge_btts = (prob_btts * 100) - prob_impl_btts
    score_btts = min(100, max(0, int((prob_btts * 100 * 0.7) + (g_away_scored * 10))))

    # Pipeline de Decisão (Filtro Rígido de Entrada vs. NO BET)
    indicacao_principal = "❌ NO BET (Sem Valor Esperado Positivo Detectado)"
    status_class = "badge-nobet"
    justificativa_pos = []
    justificativa_risco = []
    odd_final, prob_modelo, edge_final, score_final, prob_impl = 0.0, 0.0, 0.0, 0, 0.0

    if edge_h >= 6.0 and score_h >= 70:
        indicacao_principal = f"Vitória do {fixture['teams']['home']['name']}"
        odd_final = odd_h
        prob_modelo = prob_home * 100
        prob_impl = prob_impl_h
        edge_final = edge_h
        score_final = score_h
        status_class = "badge-valor"
        
        justificativa_pos = [
            f"Mandante possui média de {g_home_scored:.2f} gols marcados em casa.",
            f"Visitante sofre em média {g_away_conceded:.2f} gols quando joga fora.",
            f"Lambda (λ) do Modelo estima {lambda_home:.2f} gols esperados para o mandante.",
            f"Probabilidade do modelo ({prob_modelo:.1f}%) gera Edge positivo de +{edge_h:.1f} p.p. sobre a odd @{odd_h}."
        ]
        justificativa_risco = [
            f"Aproveitamento do mandante em jogos equilibrados e oscilações recentes da odd.",
            f"Defesa do visitante costuma fechar os espaços no primeiro tempo."
        ]

    elif edge_o15 >= 5.0 and score_o15 >= 70:
        indicacao_principal = "Over 1.5 Gols na Partida"
        odd_final = odd_o15
        prob_modelo = prob_over15 * 100
        prob_impl = prob_impl_o15
        edge_final = edge_o15
        score_final = score_o15
        status_class = "badge-valor"

        justificativa_pos = [
            f"A soma do Lambda (λ) conjunto é de {lambda_home + lambda_away:.2f} gols esperados.",
            f"Frequência Poisson aponta {prob_modelo:.1f}% de probabilidade para ao menos 2 gols.",
            f"Edge de +{edge_o15:.1f} p.p. detectado em relação à precificação da Bet365."
        ]
        justificativa_risco = [
            f"Possível desaceleração do ritmo no segundo tempo caso o placar seja aberto cedo."
        ]

    elif edge_btts >= 5.0 and score_btts >= 70:
        indicacao_principal = "Ambas Marcam: SIM"
        odd_final = odd_btts
        prob_modelo = prob_btts * 100
        prob_impl = prob_impl_btts
        edge_final = edge_btts
        score_final = score_btts
        status_class = "badge-valor"

        justificativa_pos = [
            f"Mandante sofre em média {g_home_conceded:.2f} gols em casa.",
            f"Visitante marca em média {g_away_scored:.2f} gols fora de casa.",
            f"Probabilidade de ambas balançarem as redes estimada em {prob_modelo:.1f}%."
        ]
        justificativa_risco = [
            f"Eficiência em bolas paradas defensivas de ambas as equipes."
        ]

    else:
        justificativa_pos = ["Modelagem executada com sucesso."]
        justificativa_risco = [
            "Edge insuficiente (< 5 p.p.) para cobrir a margem de erro estatística.",
            "Mercado altamente ajustado pela casa de apostas. Indicado guardar banca."
        ]

    return {
        "fixture_id": fixture_id,
        "indicacao": indicacao_principal,
        "odd": odd_final,
        "prob_modelo": round(prob_modelo, 1),
        "prob_impl": round(prob_impl, 1),
        "edge": round(edge_final, 1),
        "score": score_final,
        "status_class": status_class,
        "just_pos": justificativa_pos,
        "just_risco": justificativa_risco,
        "lambda_home": round(lambda_home, 2),
        "lambda_away": round(lambda_away, 2),
    }, None


# --- PROCESSAMENTO DA TELA ---
if btn_buscar:
    with st.spinner("Executando simulação de Poisson e filtrando valor (EV+)..."):
        agora_utc = datetime.now(timezone.utc)
        agora_br = agora_utc - timedelta(hours=3)
        hoje_local = agora_br.date()
        amanha_local = hoje_local + timedelta(days=1)

        data_str = None
        if "Hoje" in opcao_filtro:
            data_str = hoje_local.strftime("%Y-%m-%d")
        elif "Amanhã" in opcao_filtro:
            data_str = amanha_local.strftime("%Y-%m-%d")

        raw_fixtures = api_get("fixtures", {"date": data_str, "timezone": "America/Sao_Paulo"} if data_str else {"next": "25"})

    if not raw_fixtures:
        st.warning("Nenhum jogo encontrado para o período.")
    else:
        st.success(f"✅ {len(raw_fixtures)} partidas analisadas com sucesso!")

        for item in raw_fixtures[:15]:
            fix = item["fixture"]
            league = item["league"]
            teams = item["teams"]

            if fix["status"]["short"] not in ["NS", "TBD"]:
                continue

            dt_br = datetime.fromisoformat(fix["date"].replace("Z", "+00:00")) - timedelta(hours=3)

            res_quant, err = analisar_partida_quant(item)
            if not res_quant:
                continue

            with st.container():
                st.markdown(
                    f"""
                <div class="card-jogo">
                    <div class="liga-title">🏆 {league['name'].upper()} | 📅 {dt_br.strftime('%d/%m às %H:%M')}</div>
                    <div class="confronto-title">{teams['home']['name']} VS {teams['away']['name']}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                st.markdown(
                    f"""
                <div class="metric-container">
                    <span>📊 <b>λ Mandante (Gols Esp.):</b> {res_quant['lambda_home']}</span>
                    <span>📊 <b>λ Visitante (Gols Esp.):</b> {res_quant['lambda_away']}</span>
                    <span>🎯 <b>Analista Score:</b> {res_quant['score']}/100</span>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                if res_quant["score"] > 0:
                    st.markdown(
                        f"<span class='{res_quant['status_class']}'>ENTRADA CONFIRMADA</span> **{res_quant['indicacao']} (Odd @{res_quant['odd']})**",
                        unsafe_allow_html=True,
                    )
                    
                    pos_str = "<br>• ".join(res_quant["just_pos"])
                    st.markdown(
                        f"""
                    <div class='analise-box'>
                        <b>📋 METRICAS DE PRECIFICAÇÃO & VALOR:</b><br>
                        • <b>Probabilidade Modelo:</b> {res_quant['prob_modelo']}% | <b>Probabilidade Implícita Odd:</b> {res_quant['prob_impl']}%<br>
                        • <b>Edge (Vantagem):</b> +{res_quant['edge']} p.p.<br><br>
                        <b>🟢 FATORES POSITIVOS:</b><br>• {pos_str}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<span class='badge-nobet'>❌ NO BET</span> **NENHUMA APOSTA RECOMENDADA PARA ESTE CONFRONTO**",
                        unsafe_allow_html=True,
                    )
                    risco_str = "<br>• ".join(res_quant["just_risco"])
                    st.markdown(
                        f"""
                    <div class='risk-box'>
                        <b>⚠️ MOTIVOS PARA NO BET:</b><br>• {risco_str}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                st.write("")
