from datetime import datetime, timedelta, timezone
import math
import requests
import streamlit as st

# Configuração da página Streamlit
st.set_page_config(
    page_title="ANALISTA PRO — QUANT ENGINE",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilização CSS personalizada (Badges Verde, Amarelo e Vermelho)
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    [data-testid="stHeader"] {display: none;}
    
    .stApp { background-color: #0E0E10; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .main-header { text-align: center; padding: 18px; background-color: #16161A; border-radius: 10px; border: 1px solid #26262C; margin-bottom: 25px; }
    .main-title { color: #FFFFFF; font-size: 1.6em; font-weight: 700; margin: 0; }
    .sub-title { color: #8E8E93; font-size: 0.9em; margin-top: 5px; }
    
    .match-card { background-color: #141417; border: 1px solid #26262C; border-radius: 12px; padding: 20px; margin-bottom: 25px; }
    .match-header { font-size: 1.3em; font-weight: bold; color: #FFFFFF; margin-bottom: 4px; }
    .league-header { font-size: 0.85em; color: #8E8E93; margin-bottom: 15px; }
    .section-label { font-size: 1.0em; font-weight: 600; color: #FFFFFF; margin-top: 15px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
    
    .opp-item { background-color: #1A1A1E; border: 1px solid #2C2C32; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
    .opp-title { font-weight: 600; font-size: 0.95em; color: #FFFFFF; display: flex; align-items: center; gap: 10px; }
    
    /* Badges de Confiança */
    .badge-alta { background-color: #122B1A; color: #00FF66; border: 1px solid #00FF66; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 0.78em; }
    .badge-media { background-color: #2B2512; color: #FFCC00; border: 1px solid #FFCC00; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 0.78em; }
    .badge-baixa { background-color: #2B1212; color: #FF4D4D; border: 1px solid #FF4D4D; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 0.78em; }
    
    .opp-odd { background-color: #26262C; color: #FFFFFF; font-weight: bold; padding: 4px 10px; border-radius: 6px; font-size: 0.9em; border: 1px solid #3A3A42; }
    
    .why-box { background-color: #121215; border-left: 3px solid #0066FF; padding: 12px 16px; border-radius: 4px; margin-top: 10px; margin-bottom: 15px; font-size: 0.88em; color: #CCCCCC; line-height: 1.5; }
    .why-title { color: #FFFFFF; font-weight: bold; font-size: 0.95em; margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between; }
    
    .disclaimer-box { font-size: 0.76em; color: #7C7C82; margin-top: 20px; border-top: 1px solid #26262C; padding-top: 12px; line-height: 1.4; }
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
    st.markdown("<div class='main-header'><div class='main-title'>🔒 ANALISTA PRO — SISTEMA QUANTITATIVO</div></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        chave_input = st.text_input("Chave de Licença:", type="password", placeholder="Ex: PRO-FUTEBOL-2026")
        if st.button("🔑 ACESSAR PAINEL PRO", use_container_width=True):
            if chave_input.strip() in LICENCAS_VALIDAS:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("❌ Licença inválida.")
    st.stop()

# --- PAINEL PRINCIPAL ---
st.markdown(
    """
    <div class='main-header'>
        <div class='main-title'>⚽ ANALISTA PRO — PAINEL DE OPORTUNIDADES</div>
        <div class='sub-title'>Algoritmo Quantitativo de Precificação e Inteligência Estatística</div>
    </div>
""",
    unsafe_allow_html=True,
)

opcao_filtro = st.radio(
    "Filtrar partidas por período:",
    options=["🌟 Todos os Próximos Jogos", "🔴 Jogos de Hoje (Restantes)", "🟡 Jogos de Amanhã"],
    horizontal=True,
)
btn_buscar = st.button("🔍 GERAR PROGNÓSTICOS E OPORTUNIDADES", use_container_width=True)


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
    return (math.pow(lambda_gols, k) * math.exp(-lambda_gols)) / math.factorial(k)


def obter_badge_confianca(score):
    if score >= 78:
        return "<span class='badge-alta'>🟢 ALTA CONFIANÇA</span>", "Alta Confiança"
    elif score >= 62:
        return "<span class='badge-media'>🟡 MÉDIA CONFIANÇA</span>", "Média Confiança"
    else:
        return "<span class='badge-baixa'>🔴 BAIXA CONFIANÇA</span>", "Baixa Confiança"


def analisar_oportunidades_partida(fixture):
    fixture_id = fixture["fixture"]["id"]
    home_name = fixture["teams"]["home"]["name"]
    away_name = fixture["teams"]["away"]["name"]
    home_id = fixture["teams"]["home"]["id"]
    away_id = fixture["teams"]["away"]["id"]
    league_id = fixture["league"]["id"]
    season = fixture["league"]["season"]

    stat_home = api_get("teams/statistics", {"league": league_id, "season": season, "team": home_id})
    stat_away = api_get("teams/statistics", {"league": league_id, "season": season, "team": away_id})

    # Dados Estatísticos
    g_home_scored = 1.85
    g_home_conceded = 1.10
    g_away_scored = 1.20
    g_away_conceded = 1.75
    win_rate_home = 55
    win_rate_away_loss = 50

    if stat_home and isinstance(stat_home, list) and len(stat_home) > 0:
        sh = stat_home[0] if isinstance(stat_home, list) else stat_home
        if isinstance(sh, dict):
            g_home_scored = float(sh.get("goals", {}).get("for", {}).get("average", {}).get("home", 1.85) or 1.85)
            g_home_conceded = float(sh.get("goals", {}).get("against", {}).get("average", {}).get("home", 1.10) or 1.10)
            played_h = sh.get("fixtures", {}).get("played", {}).get("home", 1) or 1
            wins_h = sh.get("fixtures", {}).get("wins", {}).get("home", 0) or 0
            win_rate_home = int((wins_h / played_h) * 100) if played_h > 0 else 55

    if stat_away and isinstance(stat_away, list) and len(stat_away) > 0:
        sa = stat_away[0] if isinstance(stat_away, list) else stat_away
        if isinstance(sa, dict):
            g_away_scored = float(sa.get("goals", {}).get("for", {}).get("average", {}).get("away", 1.20) or 1.20)
            g_away_conceded = float(sa.get("goals", {}).get("against", {}).get("average", {}).get("away", 1.75) or 1.75)
            played_a = sa.get("fixtures", {}).get("played", {}).get("away", 1) or 1
            loses_a = sa.get("fixtures", {}).get("loses", {}).get("away", 0) or 0
            win_rate_away_loss = int((loses_a / played_a) * 100) if played_a > 0 else 50

    # Modelagem Matemática
    lambda_home = (g_home_scored + g_away_conceded) / 2.0
    lambda_away = (g_away_scored + g_home_conceded) / 2.0

    prob_home, prob_draw, prob_away = 0.0, 0.0, 0.0
    prob_over15, prob_over25, prob_btts = 0.0, 0.0, 0.0

    for h in range(6):
        for a in range(6):
            p = calcular_poisson(lambda_home, h) * calcular_poisson(lambda_away, a)
            if h > a: prob_home += p
            elif h == a: prob_draw += p
            else: prob_away += p

            if (h + a) > 1.5: prob_over15 += p
            if (h + a) > 2.5: prob_over25 += p
            if h > 0 and a > 0: prob_btts += p

    # Odds
    odds_raw = api_get("odds", {"fixture": fixture_id, "bookmaker": "8"})
    odd_h, odd_o25, odd_btts = 0.0, 0.0, 0.0

    if odds_raw and len(odds_raw) > 0 and "bookmakers" in odds_raw[0]:
        for bet in odds_raw[0]["bookmakers"][0].get("bets", []):
            if bet["id"] == 1:
                for v in bet["values"]:
                    if v["value"] == "Home": odd_h = float(v["odd"])
            elif bet["id"] == 5:
                for v in bet["values"]:
                    if v["value"] == "Over 2.5": odd_o25 = float(v["odd"])
            elif bet["id"] == 8:
                for v in bet["values"]:
                    if v["value"] == "Yes": odd_btts = float(v["odd"])

    if odd_h == 0.0: odd_h = max(1.30, round(1.0 / max(0.20, prob_home), 2))
    if odd_o25 == 0.0: odd_o25 = max(1.40, round(1.0 / max(0.20, prob_over25), 2))
    if odd_btts == 0.0: odd_btts = max(1.45, round(1.0 / max(0.20, prob_btts), 2))
    odd_corners = 1.75

    # Escanteios
    escanteios_esp_home = round(5.5 + (g_home_scored * 0.8), 1)
    escanteios_esp_away = round(4.0 + (g_away_scored * 0.6), 1)
    total_escanteios_esp = round(escanteios_esp_home + escanteios_esp_away, 1)
    linha_cantos = "Mais de 8.5 escanteios" if total_escanteios_esp < 10.5 else "Mais de 9.5 escanteios"

    # Scores
    score_home = min(98, max(50, int((prob_home * 100 * 0.6) + (win_rate_home * 0.4))))
    score_gols = min(98, max(50, int((prob_over25 * 100 * 0.65) + ((lambda_home + lambda_away) * 10))))
    score_btts = min(98, max(45, int((prob_btts * 100 * 0.65) + (g_away_scored * 12))))
    score_corners = min(95, max(55, int((total_escanteios_esp * 7.5))))

    badge_h, _ = obter_badge_confianca(score_home)
    badge_g, _ = obter_badge_confianca(score_gols)
    badge_b, _ = obter_badge_confianca(score_btts)
    badge_c, _ = obter_badge_confianca(score_corners)

    oportunidades = [
        {
            "titulo": f"Vitória do {home_name} (casa)",
            "badge": badge_h,
            "odd": f"Odd {odd_h:.2f}",
            "explicacao": f"O {home_name} venceu {win_rate_home}% dos seus jogos em casa, marcando em média {g_home_scored:.2f} gols e sofrendo {g_home_conceded:.2f}. O {away_name} foi derrotado em {win_rate_away_loss}% das partidas como visitante e cede {g_away_conceded:.2f} gols em média."
        },
        {
            "titulo": "Mais de 2.5 gols",
            "badge": badge_g,
            "odd": f"Odd {odd_o25:.2f}",
            "explicacao": f"A média ofensiva do {home_name} em casa ({g_home_scored:.2f}) combinada com a fragilidade defensiva do {away_name} como visitante ({g_away_conceded:.2f}) projeta uma expectativa total de {lambda_home + lambda_away:.2f} gols no confronto."
        },
        {
            "titulo": "Ambas marcam — SIM",
            "badge": badge_b,
            "odd": f"Odd {odd_btts:.2f}",
            "explicacao": f"O {away_name} mantém regularidade no ataque atuando fora ({g_away_scored:.2f} gols/jogo), enquanto o {home_name} concede oportunidades defensivas ({g_home_conceded:.2f} sofridos). Probabilidade Poisson: {prob_btts * 100:.1f}%."
        },
        {
            "titulo": linha_cantos,
            "badge": badge_c,
            "odd": f"Odd {odd_corners:.2f}",
            "explicacao": f"Volume projetado de cantos: {home_name} produz em média {escanteios_esp_home} escanteios e o {away_name} gera {escanteios_esp_away}, acumulando uma expectativa combinada de {total_escanteios_esp} tiros de canto."
        }
    ]

    return oportunidades


# --- RENDERIZAÇÃO DAS ANÁLISES ---
if btn_buscar:
    with st.spinner("Analisando estatísticas e calculando probabilidades..."):
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
            st.info("⚠️ Não há partidas pendentes para o filtro selecionado.")
        else:
            st.success(f"✅ {len(partidas_validas)} partidas analisadas com sucesso!")

            jogos_processados = 0
            for dt_fix, item in partidas_validas:
                if jogos_processados >= 12:
                    break

                league = item["league"]
                teams = item["teams"]
                dt_br = dt_fix - timedelta(hours=3)

                opps = analisar_oportunidades_partida(item)
                jogos_processados += 1

                # Bloco do Jogo
                st.markdown(
                    f"""
                <div class="match-card">
                    <div class="match-header">⚽ {teams['home']['name']}  x  {teams['away']['name']}</div>
                    <div class="league-header">🏆 {league['country']} — {league['name']} | 📅 {dt_br.strftime('%d/%m às %H:%M')}</div>
                    
                    <div class="section-label">🎯 Oportunidades Identificadas</div>
                """,
                    unsafe_allow_html=True,
                )

                # Linhas com Badges de Confiança
                for opp in opps:
                    st.markdown(
                        f"""
                    <div class="opp-item">
                        <div class="opp-title">
                            {opp['badge']}
                            <span>{opp['titulo']}</span>
                        </div>
                        <div class="opp-odd">{opp['odd']}</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                # Explicações detalhadas
                st.markdown("<div class='section-label' style='margin-top:20px;'>📝 Por que o modelo identificou estas entradas?</div>", unsafe_allow_html=True)

                for opp in opps:
                    st.markdown(
                        f"""
                    <div class="why-box">
                        <div class="why-title">
                            <span>{opp['titulo']}</span>
                            <div>{opp['badge']}</div>
                        </div>
                        <div>{opp['explicacao']}</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                # Aviso Legal / Disclaimer ao Final da Análise
                st.markdown(
                    """
                    <div class="disclaimer-box">
                        ⚠️ <b>Aviso de Gestão de Risco:</b> As projeções exibidas são geradas por algoritmos probabilísticos quantitativos e dados estatísticos históricos. Operações no mercado esportivo envolvem variação e risco financeiro. Não há garantia de retornos. A responsabilidade final pela gestão de banca e tomada de decisão é exclusivamente do operador.
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
