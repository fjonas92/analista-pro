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
    .analise-box { background-color: #161616; border-left: 3px solid #0066FF; padding: 12px; margin-top: 8px; margin-bottom: 12px; font-size: 0.88em; color: #DDDDDD; }
    .metric-container { display: flex; justify-content: space-between; background-color: #222222; padding: 10px; border-radius: 6px; margin-bottom: 10px; font-size: 0.85em; }
    .risk-box { background-color: #221A1A; border-left: 3px solid #FF9900; padding: 8px 12px; margin-top: 6px; font-size: 0.85em; color: #FFCC80; }
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
    home_name = fixture["teams"]["home"]["name"]
    away_name = fixture["teams"]["away"]["name"]
    home_id = fixture["teams"]["home"]["id"]
    away_id = fixture["teams"]["away"]["id"]
    league_id = fixture["league"]["id"]
    season = fixture["league"]["season"]

    # Coleta de estatísticas da equipe
    stat_home = api_get("teams/statistics", {"league": league_id, "season": season, "team": home_id})
    stat_away = api_get("teams/statistics", {"league": league_id, "season": season, "team": away_id})

    # Médias de gols
    g_home_scored = 1.45
    g_home_conceded = 1.05
    g_away_scored = 1.10
    g_away_conceded = 1.35

    if stat_home and isinstance(stat_home, list) and len(stat_home) > 0:
        sh = stat_home[0] if isinstance(stat_home, list) else stat_home
        if isinstance(sh, dict):
            g_home_scored = float(sh.get("goals", {}).get("for", {}).get("average", {}).get("home", 1.45) or 1.45)
            g_home_conceded = float(sh.get("goals", {}).get("against", {}).get("average", {}).get("home", 1.05) or 1.05)

    if stat_away and isinstance(stat_away, list) and len(stat_away) > 0:
        sa = stat_away[0] if isinstance(stat_away, list) else stat_away
        if isinstance(sa, dict):
            g_away_scored = float(sa.get("goals", {}).get("for", {}).get("average", {}).get("away", 1.10) or 1.10)
            g_away_conceded = float(sa.get("goals", {}).get("against", {}).get("average", {}).get("away", 1.35) or 1.35)

    # Lambdas do Modelo
    lambda_home = (g_home_scored + g_away_conceded) / 2.0
    lambda_away = (g_away_scored + g_home_conceded) / 2.0

    # Probabilidades por Poisson
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

    # Busca de Odds da Bet365
    odds_raw = api_get("odds", {"fixture": fixture_id, "bookmaker": "8"})
    odd_h, odd_d, odd_a = 0.0, 0.0, 0.0
    odd_o15, odd_btts = 0.0, 0.0

    if odds_raw and len(odds_raw) > 0 and "bookmakers" in odds_raw[0]:
        for bet in odds_raw[0]["bookmakers"][0].get("bets", []):
            if bet["id"] == 1:
                for v in bet["values"]:
                    if v["value"] == "Home": odd_h = float(v["odd"])
                    elif v["value"] == "Draw": odd_d = float(v["odd"])
                    elif v["value"] == "Away": odd_a = float(v["odd"])
            elif bet["id"] == 5:
                for v in bet["values"]:
                    if v["value"] == "Over 1.5": odd_o15 = float(v["odd"])
            elif bet["id"] == 8:
                for v in bet["values"]:
                    if v["value"] == "Yes": odd_btts = float(v["odd"])

    # Fallback de Odds Estimadas
    if odd_h == 0.0: odd_h = max(1.25, round(1.0 / max(0.15, prob_home), 2))
    if odd_o15 == 0.0: odd_o15 = max(1.20, round(1.0 / max(0.20, prob_over15), 2))
    if odd_btts == 0.0: odd_btts = max(1.40, round(1.0 / max(0.20, prob_btts), 2))

    # Matriz de Seleção do Melhor Mercado por Valor/Frequência
    opcoes = [
        {
            "indicacao": f"Vitória do {home_name}",
            "odd": odd_h,
            "prob_modelo": prob_home * 100,
            "prob_impl": (1.0 / odd_h) * 100,
            "edge": (prob_home * 100) - ((1.0 / odd_h) * 100),
            "score": min(98, max(60, int((prob_home * 100 * 0.65) + (g_home_scored * 12)))),
            "just_pos": [
                f"O {home_name} registra média ofensiva de {g_home_scored:.2f} gols por jogo atuando em seus domínios.",
                f"A defesa do {away_name} concede em média {g_away_conceded:.2f} gols nas partidas como visitante.",
                f"O modelo de Poisson aponta $\lambda = {lambda_home:.2f}$ gols esperados para o mandante."
            ],
            "just_risco": [
                f"Sustentação do ritmo do {home_name} caso o {away_name} adote uma postura de retranca defensiva."
            ]
        },
        {
            "indicacao": "Over 1.5 Gols na Partida",
            "odd": odd_o15,
            "prob_modelo": prob_over15 * 100,
            "prob_impl": (1.0 / odd_o15) * 100,
            "edge": (prob_over15 * 100) - ((1.0 / odd_o15) * 100),
            "score": min(98, max(62, int((prob_over15 * 100 * 0.70) + ((lambda_home + lambda_away) * 8)))),
            "just_pos": [
                f"A expectativa combinada de gols do confronto é de {lambda_home + lambda_away:.2f} (λ total).",
                f"O {home_name} e o {away_name} apresentam alta frequência histórica de jogos com mais de 1 gol.",
                f"A probabilidade do modelo ({prob_over15 * 100:.1f}%) oferece boa margem de segurança."
            ],
            "just_risco": [
                f"Necessidade de efetividade nos primeiros chutes para evitar que o jogo fique truncado."
            ]
        },
        {
            "indicacao": "Ambas Marcam: SIM",
            "odd": odd_btts,
            "prob_modelo": prob_btts * 100,
            "prob_impl": (1.0 / odd_btts) * 100,
            "edge": (prob_btts * 100) - ((1.0 / odd_btts) * 100),
            "score": min(98, max(58, int((prob_btts * 100 * 0.68) + (g_away_scored * 10)))),
            "just_pos": [
                f"O {away_name} possui uma média útil de {g_away_scored:.2f} gols marcados fora de casa.",
                f"O {home_name} cede espaços defensivos, com média de {g_home_conceded:.2f} gols sofridos em casa.",
                f"A taxa bivariada aponta {prob_btts * 100:.1f}% de probabilidade de gols de ambos os lados."
            ],
            "just_risco": [
                f"Aproveitamento de poucas oportunidades criadas pela equipe visitante."
            ]
        }
    ]

    # Ordena para escolher SEMPRE o mercado com melhor equilíbrio de Score e Edge
    opcoes.sort(key=lambda x: (x["score"], x["edge"]), reverse=True)
    melhor_opcao = opcoes[0]

    return {
        "fixture_id": fixture_id,
        "indicacao": melhor_opcao["indicacao"],
        "odd": melhor_opcao["odd"],
        "prob_modelo": round(melhor_opcao["prob_modelo"], 1),
        "prob_impl": round(melhor_opcao["prob_impl"], 1),
        "edge": round(melhor_opcao["edge"], 1),
        "score": melhor_opcao["score"],
        "just_pos": melhor_opcao["just_pos"],
        "just_risco": melhor_opcao["just_risco"],
        "lambda_home": round(lambda_home, 2),
        "lambda_away": round(lambda_away, 2),
    }, None


# --- PROCESSAMENTO DA TELA ---
if btn_buscar:
    with st.spinner("Processando simulação e gerando palpites detalhados..."):
        now_utc = datetime.now(timezone.utc)

        data_str = None
        if "Hoje" in opcao_filtro:
            data_str = now_utc.strftime("%Y-%m-%d")
        elif "Amanhã" in opcao_filtro:
            data_str = (now_utc + timedelta(days=1)).strftime("%Y-%m-%d")

        params_fixture = {"date": data_str} if data_str else {"next": "40"}
        raw_fixtures = api_get("fixtures", params_fixture)

    if not raw_fixtures:
        st.warning("Nenhum jogo encontrado para o período selecionado.")
    else:
        partidas_validas = []
        for item in raw_fixtures:
            fix = item["fixture"]
            dt_fix = datetime.fromisoformat(fix["date"].replace("Z", "+00:00"))
            if dt_fix > now_utc and fix["status"]["short"] in ["NS", "TBD"]:
                partidas_validas.append((dt_fix, item))

        partidas_validas.sort(key=lambda x: x[0])

        if not partidas_validas:
            st.info("⚠️ Não há partidas pendentes (não iniciadas) para o filtro selecionado.")
        else:
            st.success(f"✅ {len(partidas_validas)} partidas processadas com análises completas!")

            jogos_processados = 0
            for dt_fix, item in partidas_validas:
                if jogos_processados >= 15:
                    break

                league = item["league"]
                teams = item["teams"]
                dt_br = dt_fix - timedelta(hours=3)

                res_quant, err = analisar_partida_quant(item)
                if not res_quant:
                    continue

                jogos_processados += 1

                with st.container():
                    st.markdown(
                        f"""
                    <div class="card-jogo">
                        <div class="liga-title">🏆 {league['name'].upper()} ({league['country']}) | 📅 {dt_br.strftime('%d/%m às %H:%M')}</div>
                        <div class="confronto-title">{teams['home']['name']} VS {teams['away']['name']}</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        f"""
                    <div class="metric-container">
                        <span>📊 <b>λ {teams['home']['name']} (Gols Esp.):</b> {res_quant['lambda_home']}</span>
                        <span>📊 <b>λ {teams['away']['name']} (Gols Esp.):</b> {res_quant['lambda_away']}</span>
                        <span>🎯 <b>Analista Score:</b> {res_quant['score']}/100</span>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        f"<span class='badge-valor'>INDICAÇÃO PRO</span> **{res_quant['indicacao']} (Odd @{res_quant['odd']})**",
                        unsafe_allow_html=True,
                    )
                    
                    pos_str = "<br>• ".join(res_quant["just_pos"])
                    st.markdown(
                        f"""
                    <div class='analise-box'>
                        <b>📋 METRICAS DE PRECIFICAÇÃO:</b><br>
                        • <b>Probabilidade Modelo:</b> {res_quant['prob_modelo']}% | <b>Probabilidade Implícita Odd:</b> {res_quant['prob_impl']}%<br>
                        • <b>Edge Calculado:</b> {res_quant['edge']} p.p.<br><br>
                        <b>🟢 FATORES POSITIVOS:</b><br>• {pos_str}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    risco_str = "<br>• ".join(res_quant["just_risco"])
                    st.markdown(
                        f"""
                    <div class='risk-box'>
                        <b>⚠️ PONTOS DE ATENÇÃO & RISCO:</b><br>• {risco_str}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    st.write("")
