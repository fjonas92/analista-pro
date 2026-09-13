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

    # Coleta estatística de cada equipe com fallback de segurança
    stat_home = api_get("teams/statistics", {"league": league_id, "season": season, "team": home_id})
    stat_away = api_get("teams/statistics", {"league": league_id, "season": season, "team": away_id})

    # Valores padrão robustos caso a liga ainda não tenha estatísticas consolidadas
    g_home_scored = 1.3
    g_home_conceded = 1.1
    g_away_scored = 1.0
    g_away_conceded = 1.4

    if stat_home and isinstance(stat_home, list) and len(stat_home) > 0:
        sh = stat_home[0] if isinstance(stat_home, list) else stat_home
        if isinstance(sh, dict):
            g_home_scored = float(sh.get("goals", {}).get("for", {}).get("average", {}).get("home", 1.3) or 1.3)
            g_home_conceded = float(sh.get("goals", {}).get("against", {}).get("average", {}).get("home", 1.1) or 1.1)

    if stat_away and isinstance(stat_away, list) and len(stat_away) > 0:
        sa = stat_away[0] if isinstance(stat_away, list) else stat_away
        if isinstance(sa, dict):
            g_away_scored = float(sa.get("goals", {}).get("for", {}).get("average", {}).get("away", 1.0) or 1.0)
            g_away_conceded = float(sa.get("goals", {}).get("against", {}).get("average", {}).get("away", 1.4) or 1.4)

    # Cálculo dos Lambdas de Gols Esperados do Modelo
    lambda_home = (g_home_scored + g_away_conceded) / 2.0
    lambda_away = (g_away_scored + g_home_conceded) / 2.0

    # Distribuição Poisson Bivariada para Probabilidades
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

    # Odds padrão pré-definidas para simulação caso a API de Odds não retorne a tempo
    odd_h, odd_d, odd_a = 2.05, 3.30, 3.40
    odd_o15, odd_o25, odd_btts = 1.32, 1.95, 1.83

    # Coleta de Odds reais da Bet365 (Bookmaker 8)
    odds_raw = api_get("odds", {"fixture": fixture_id, "bookmaker": "8"})
    if odds_raw and len(odds_raw) > 0 and "bookmakers" in odds_raw[0]:
        for bet in odds_raw[0]["bookmakers"][0].get("bets", []):
            if bet["id"] == 1:  # 1X2
                for v in bet["values"]:
                    if v["value"] == "Home": odd_h = float(v["odd"])
                    elif v["value"] == "Draw": odd_d = float(v["odd"])
                    elif v["value"] == "Away": odd_a = float(v["odd"])
            elif bet["id"] == 5:  # Over/Under
                for v in bet["values"]:
                    if v["value"] == "Over 2.5": odd_o25 = float(v["odd"])
            elif bet["id"] == 8:  # BTTS
                for v in bet["values"]:
                    if v["value"] == "Yes": odd_btts = float(v["odd"])

    # Cálculo do Edge e Analista Score (0-100)
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

    if edge_h >= 5.0 and score_h >= 65:
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
            f"Probabilidade do modelo ({prob_modelo:.1f}%) gera Edge positivo de +{edge_final:.1f} p.p. sobre a odd @{odd_h}."
        ]
        justificativa_risco = [
            "Oscilações de desempenho em partidas fora de casa do visitante.",
            "Possíveis rotações no segundo tempo."
        ]

    elif edge_o15 >= 4.0 and score_o15 >= 65:
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
            f"Edge de +{edge_final:.1f} p.p. detectado em relação à precificação da Bet365."
        ]
        justificativa_risco = [
            "Possível desaceleração do ritmo caso o primeiro gol aconteça muito cedo."
        ]

    elif edge_btts >= 4.5 and score_btts >= 65:
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
            "Eficiência em bolas paradas defensivas de ambas as equipes."
        ]

    else:
        justificativa_pos = ["Modelagem Poisson calculada."]
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
    with st.spinner("Filtrando partidas futuras e executando modelo Quantitativo..."):
        now_utc = datetime.now(timezone.utc)

        data_str = None
        if "Hoje" in opcao_filtro:
            data_str = now_utc.strftime("%Y-%m-%d")
        elif "Amanhã" in opcao_filtro:
            data_str = (now_utc + timedelta(days=1)).strftime("%Y-%m-%d")

        # Busca partidas na API
        params_fixture = {"date": data_str} if data_str else {"next": "40"}
        raw_fixtures = api_get("fixtures", params_fixture)

    if not raw_fixtures:
        st.warning("Nenhum jogo encontrado para o período selecionado.")
    else:
        # 1. Filtro Temporal Rígido: Apenas partidas FUTURAS (commence_time > now_utc)
        partidas_validas = []
        for item in raw_fixtures:
            fix = item["fixture"]
            dt_fix = datetime.fromisoformat(fix["date"].replace("Z", "+00:00"))
            
            # Filtra apenas quem ainda NÃO começou e tem status de "não iniciado"
            if dt_fix > now_utc and fix["status"]["short"] in ["NS", "TBD"]:
                partidas_validas.append((dt_fix, item))

        # Ordena cronologicamente do mais próximo ao mais distante
        partidas_validas.sort(key=lambda x: x[0])

        if not partidas_validas:
            st.info("⚠️ Não há partidas pendentes (não iniciadas) para o filtro selecionado.")
        else:
            st.success(f"✅ {len(partidas_validas)} partidas futuras encontradas! Processando melhores oportunidades...")

            jogos_processados = 0
            for dt_fix, item in partidas_validas:
                if jogos_processados >= 15:  # Limite confortável para evitar estouro de cota da API
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
                        <span>📊 <b>λ Mandante (Gols Esp.):</b> {res_quant['lambda_home']}</span>
                        <span>📊 <b>λ Visitante (Gols Esp.):</b> {res_quant['lambda_away']}</span>
                        <span>🎯 <b>Analista Score:</b> {res_quant['score']}/100</span>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    if res_quant["score"] > 0 and res_quant["edge"] > 0:
                        st.markdown(
                            f"<span class='{res_quant['status_class']}'>ENTRADA CONFIRMADA</span> **{res_quant['indicacao']} (Odd @{res_quant['odd']})**",
                            unsafe_allow_html=True,
                        )
                        pos_str = "<br>• ".join(res_quant["just_pos"])
                        st.markdown(
                            f"""
                        <div class='analise-box'>
                            <b>📋 MÉTRICAS DE PRECIFICAÇÃO & VALOR (EV+):</b><br>
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
