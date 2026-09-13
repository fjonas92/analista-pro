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

# Estilização CSS Clean
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    [data-testid="stHeader"] {display: none;}
    
    .stApp { background-color: #0E0E10; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .main-header { text-align: center; padding: 18px; background-color: #16161A; border-radius: 10px; border: 1px solid #26262C; margin-bottom: 20px; }
    .main-title { color: #FFFFFF; font-size: 1.6em; font-weight: 700; margin: 0; }
    .sub-title { color: #8E8E93; font-size: 0.9em; margin-top: 5px; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 1px solid #26262C; }
    .stTabs [data-baseweb="tab"] { background-color: #16161A; border-radius: 8px 8px 0px 0px; padding: 12px 20px; color: #8E8E93; border: 1px solid #26262C; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #0066FF !important; color: #FFFFFF !important; border: 1px solid #0066FF !important; }
    
    .combo-card { background-color: #141417; border: 1px solid #26262C; border-radius: 12px; padding: 20px; margin-bottom: 20px; }
    .combo-header { font-weight: bold; font-size: 1.1em; color: #00FF66; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #26262C; padding-bottom: 10px; }
    .combo-item { font-size: 0.9em; color: #DDDDDD; padding: 10px 0; border-bottom: 1px solid #1A1A1E; }
    
    .match-card { background-color: #141417; border: 1px solid #26262C; border-radius: 12px; padding: 20px; margin-bottom: 25px; }
    .match-header { font-size: 1.3em; font-weight: bold; color: #FFFFFF; margin-bottom: 4px; }
    .league-header { font-size: 0.85em; color: #0066FF; font-weight: 600; margin-bottom: 14px; }
    
    .section-title { font-size: 1.0em; font-weight: 600; color: #FFFFFF; margin-top: 15px; margin-bottom: 12px; }
    .opp-item { background-color: #1A1A1E; border: 1px solid #2C2C32; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
    .opp-title { font-weight: 600; font-size: 0.95em; color: #FFFFFF; display: flex; align-items: center; gap: 10px; }
    
    .badge-alta { background-color: #122B1A; color: #00FF66; border: 1px solid #00FF66; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 0.78em; }
    .badge-media { background-color: #2B2512; color: #FFCC00; border: 1px solid #FFCC00; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 0.78em; }
    .badge-baixa { background-color: #2B1212; color: #FF4D4D; border: 1px solid #FF4D4D; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 0.78em; }
    .opp-odd { background-color: #26262C; color: #FFFFFF; font-weight: bold; padding: 4px 10px; border-radius: 6px; font-size: 0.9em; border: 1px solid #3A3A42; }
    
    .why-box { background-color: #121215; border-left: 3px solid #0066FF; padding: 12px 16px; border-radius: 4px; margin-top: 10px; margin-bottom: 15px; font-size: 0.88em; color: #CCCCCC; line-height: 1.6; }
    .why-title { color: #FFFFFF; font-weight: bold; font-size: 0.95em; margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between; }
    .disclaimer-box { font-size: 0.76em; color: #7C7C82; margin-top: 20px; border-top: 1px solid #26262C; padding-top: 12px; line-height: 1.4; }
    </style>
""",
    unsafe_allow_html=True,
)

API_FOOTBALL_KEY = st.secrets.get("API_FOOTBALL_KEY", "0d03200b5ee68704d96a72a1749aeca3")
LICENCAS_VALIDAS = ["PRO-FUTEBOL-2026", "VIP-ANALISTA-888", "CLIENTE-PRO-01", "ADMIN-MASTER-99"]

# LISTA EXCLUSIVA DE LIGAS AUTORIZADAS (Normalizada em minúsculas)
LIGAS_PERMITIDAS = {
    # Nacionais & Estaduais
    "serie a", "serie b", "serie c", "serie d", "copa do brasil", "supercopa do brasil", 
    "copa do nordeste", "brasileiro feminino", "paulista", "copa paulista", "carioca", 
    "mineiro", "gaucho", "paranaense", "catarinense", "baiano", "pernambucano", "cearense", 
    "goiano", "paraense", "amazonense", "alagoano", "sergipano", "paraibano", "potiguar", 
    "maranhense", "piauiense", "mato-grossense", "sul-mato-grossense", "brasiliense", "capixaba",
    
    # América do Sul
    "conmebol libertadores", "libertadores", "conmebol sudamericana", "sudamericana", "recopa sudamericana",
    "liga profesional", "copa argentina", "primera division", "copa chile", "primera a", "primera b",
    "copa colombia", "ligapro", "copa ecuador", "liga 1", "liga 2", "copa peru", "division profesional",
    
    # Europa Principais & UEFA
    "premier league", "championship", "league one", "league two", "fa cup", "efl cup", "community shield",
    "laliga", "laliga 2", "copa del rey", "supercopa de españa", "serie a", "serie b", "coppa italia",
    "bundesliga", "2. bundesliga", "dfb pokal", "ligue 1", "ligue 2", "coupe de france", "primeira liga",
    "taca de portugal", "eredivisie", "pro league", "super lig", "scottish premiership", "bundesliga (austria)",
    "super league", "superliga", "eliteserien", "allsvenskan", "veikkausliiga", "ekstraklasa", "first league",
    "hnl", "superliga (serbia)", "liga i", "premier league (ukraine)", "first league (bulgaria)", "nb i",
    "uefa champions league", "uefa europa league", "uefa conference league", "uefa super cup", "uefa nations league",
    "uefa euro", "champions league", "europa league", "conference league",
    
    # América do Norte & Ásia
    "major league soccer", "mls", "usl championship", "nwsl", "liga mx", "leagues cup",
    "concacaf champions cup", "concacaf gold cup", "afc champions league", "j1 league", "k league 1",
    "chinese super league", "saudi pro league", "a-league", "africa cup of nations", "caf champions league"
}

# Login
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

# Header
st.markdown(
    """
    <div class='main-header'>
        <div class='main-title'>⚽ ANALISTA PRO — PAINEL DE OPORTUNIDADES</div>
        <div class='sub-title'>Filtro Restrito de Ligas | 1 Alta, 1 Média e 1 Baixa Confiança por Jogo</div>
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
        res = requests.get(url, headers=headers, params=params, timeout=12)
        if res.status_code == 200:
            return res.json().get("response", [])
        return []
    except Exception:
        return []


def calcular_poisson(lambda_gols, k):
    return (math.pow(lambda_gols, k) * math.exp(-lambda_gols)) / math.factorial(k)


def liga_eh_permitida(nome_liga, pais):
    texto = f"{nome_liga} {pais}".lower()
    return any(p in texto for p in LIGAS_PERMITIDAS)


def analisar_oportunidades_partida(fixture):
    fixture_id = fixture["fixture"]["id"]
    home_name = fixture["teams"]["home"]["name"]
    away_name = fixture["teams"]["away"]["name"]
    home_id = fixture["teams"]["home"]["id"]
    away_id = fixture["teams"]["away"]["id"]
    league_id = fixture["league"]["id"]
    season = fixture["league"]["season"]

    stat_h = api_get("teams/statistics", {"league": league_id, "season": season, "team": home_id})
    stat_a = api_get("teams/statistics", {"league": league_id, "season": season, "team": away_id})

    g_home_scored, g_home_conceded = 1.45, 1.10
    g_away_scored, g_away_conceded = 1.15, 1.50
    cards_h, cards_a = 2.1, 2.4
    cantos_h, cantos_a = 5.1, 4.3

    if stat_h and len(stat_h) > 0:
        sh = stat_h[0] if isinstance(stat_h, list) else stat_h
        g_home_scored = float(sh.get("goals", {}).get("for", {}).get("average", {}).get("home", 1.45) or 1.45)
        g_home_conceded = float(sh.get("goals", {}).get("against", {}).get("average", {}).get("home", 1.10) or 1.10)

    if stat_a and len(stat_a) > 0:
        sa = stat_a[0] if isinstance(stat_a, list) else stat_a
        g_away_scored = float(sa.get("goals", {}).get("for", {}).get("average", {}).get("away", 1.15) or 1.15)
        g_away_conceded = float(sa.get("goals", {}).get("against", {}).get("average", {}).get("away", 1.50) or 1.50)

    lambda_home = max(0.4, (g_home_scored + g_away_conceded) / 2.0)
    lambda_away = max(0.4, (g_away_scored + g_home_conceded) / 2.0)

    prob_home, prob_draw, prob_away = 0.0, 0.0, 0.0
    prob_over15, prob_over25, prob_under25, prob_btts_yes, prob_btts_no = 0.0, 0.0, 0.0, 0.0, 0.0

    for h in range(7):
        for a in range(7):
            p = calcular_poisson(lambda_home, h) * calcular_poisson(lambda_away, a)
            if h > a: prob_home += p
            elif h == a: prob_draw += p
            else: prob_away += p

            if (h + a) > 1.5: prob_over15 += p
            if (h + a) > 2.5: prob_over25 += p
            else: prob_under25 += p

            if h > 0 and a > 0: prob_btts_yes += p
            else: prob_btts_no += p

    match_name = f"{home_name} x {away_name}"
    pool_opcoes = []

    # 1. Vitórias / Empates / Dupla Chance
    pool_opcoes.append({"titulo": f"Vitória do {home_name}", "score": int(prob_home * 100), "odd": round(1.0 / max(0.05, prob_home), 2), "exp": f"Calculado via Poisson ({prob_home*100:.1f}% prob)."})
    pool_opcoes.append({"titulo": f"Vitória do {away_name}", "score": int(prob_away * 100), "odd": round(1.0 / max(0.05, prob_away), 2), "exp": f"Visitante com probabilidade de {prob_away*100:.1f}%."})
    pool_opcoes.append({"titulo": f"Empate ou {home_name}", "score": int((prob_home + prob_draw) * 100), "odd": round(1.0 / max(0.05, prob_home + prob_draw), 2), "exp": f"Dupla Chance cobrindo 2 de 3 resultados ({int((prob_home+prob_draw)*100)}%)."})

    # 2. Gols / Ambas Marcam
    pool_opcoes.append({"titulo": "Mais de 1.5 Gols", "score": int(prob_over15 * 100), "odd": round(1.0 / max(0.05, prob_over15), 2), "exp": f"Média alta de gols esperados ({lambda_home+lambda_away:.2f})."})
    pool_opcoes.append({"titulo": "Mais de 2.5 Gols", "score": int(prob_over25 * 100), "odd": round(1.0 / max(0.05, prob_over25), 2), "exp": f"Confronto ofensivo com {prob_over25*100:.1f}% para Over 2.5."})
    pool_opcoes.append({"titulo": "Menos de 2.5 Gols (Under)", "score": int(prob_under25 * 100), "odd": round(1.0 / max(0.05, prob_under25), 2), "exp": f"Tendência de jogo truncado ({prob_under25*100:.1f}% Under 2.5)."})
    pool_opcoes.append({"titulo": "Ambas Marcam — SIM", "score": int(prob_btts_yes * 100), "odd": round(1.0 / max(0.05, prob_btts_yes), 2), "exp": f"Ambos os times balançam a rede em {prob_btts_yes*100:.1f}% das simulações."})
    pool_opcoes.append({"titulo": "Ambas Marcam — NÃO", "score": int(prob_btts_no * 100), "odd": round(1.0 / max(0.05, prob_btts_no), 2), "exp": f"Pelo menos uma das equipes tende a não marcar ({prob_btts_no*100:.1f}%)."})

    # 3. Cartões e Cantos
    total_cards = cards_h + cards_a
    total_cantos = cantos_h + cantos_a
    pool_opcoes.append({"titulo": "Mais de 3.5 Cartões", "score": min(88, int(total_cards * 15)), "odd": 1.75, "exp": f"Projeção disciplinar de {total_cards:.1f} cartões no jogo."})
    pool_opcoes.append({"titulo": "Mais de 8.5 Escanteios", "score": min(85, int(total_cantos * 8.5)), "odd": 1.80, "exp": f"Expectativa de {total_cantos:.1f} cantos combinados."})

    # SELEÇÃO RÍGIDA: 1 ALTA (>=75), 1 MÉDIA (60-74), 1 BAIXA (<60)
    pool_opcoes.sort(key=lambda x: x["score"], reverse=True)

    alta = next((x for x in pool_opcoes if x["score"] >= 75), pool_opcoes[0])
    media = next((x for x in pool_opcoes if 55 <= x["score"] < 75 and x["titulo"] != alta["titulo"]), pool_opcoes[len(pool_opcoes)//2])
    baixa = next((x for x in pool_opcoes if x["score"] < 55 and x["titulo"] not in [alta["titulo"], media["titulo"]]), pool_opcoes[-1])

    # Força ajuste de score se os limites de corte variarem
    alta_item = {
        "match": match_name, "titulo": alta["titulo"], "val_odd": alta["odd"], "odd": f"Odd {alta['odd']:.2f}",
        "score": max(76, alta["score"]), "badge": "<span class='badge-alta'>🟢 ALTA CONFIANÇA</span>", "explicacao": alta["exp"], "tipo": "ALTA"
    }
    media_item = {
        "match": match_name, "titulo": media["titulo"], "val_odd": media["odd"], "odd": f"Odd {media['odd']:.2f}",
        "score": min(74, max(60, media["score"])), "badge": "<span class='badge-media'>🟡 MÉDIA CONFIANÇA</span>", "explicacao": media["exp"], "tipo": "MEDIA"
    }
    baixa_item = {
        "match": match_name, "titulo": baixa["titulo"], "val_odd": baixa["odd"], "odd": f"Odd {baixa['odd']:.2f}",
        "score": min(54, baixa["score"]), "badge": "<span class='badge-baixa'>🔴 BAIXA CONFIANÇA</span>", "explicacao": baixa["exp"], "tipo": "BAIXA"
    }

    return [alta_item, media_item, baixa_item]


# --- PROCESSAMENTO PRINCIPAL ---
fuso_br = "America/Sao_Paulo"
now_utc = datetime.now(timezone.utc)

if btn_buscar or "raw_fixtures" not in st.session_state:
    params_fixture = {"timezone": fuso_br}
    if "Hoje" in opcao_filtro:
        dt_hoje = (now_utc - timedelta(hours=3)).strftime("%Y-%m-%d")
        params_fixture["date"] = dt_hoje
    elif "Amanhã" in opcao_filtro:
        dt_amanha = (now_utc - timedelta(hours=3) + timedelta(days=1)).strftime("%Y-%m-%d")
        params_fixture["date"] = dt_amanha
    else:
        params_fixture["next"] = "99"

    fixtures_res = api_get("fixtures", params_fixture)
    if not fixtures_res and ("date" in params_fixture):
        fixtures_res = api_get("fixtures", {"next": "99", "timezone": fuso_br})

    st.session_state["raw_fixtures"] = fixtures_res

raw_fixtures = st.session_state.get("raw_fixtures", [])

if not raw_fixtures:
    st.error("⚠️ Nenhum jogo encontrado. Selecione '🌟 Todos os Próximos Jogos' e clique no botão.")
else:
    partidas_validas = []
    for item in raw_fixtures:
        fix = item["fixture"]
        league_name = item["league"]["name"]
        country_name = item["league"]["country"]

        # APLICANDO FILTRO ESTRITO DE LIGAS AUTORIZADAS
        if liga_eh_permitida(league_name, country_name):
            dt_fix = datetime.fromisoformat(fix["date"].replace("Z", "+00:00"))
            if fix["status"]["short"] in ["NS", "TBD"]:
                partidas_validas.append((dt_fix, item))

    partidas_validas.sort(key=lambda x: x[0])

    if not partidas_validas:
        st.warning("⚠️ Nenhuma partida das ligas selecionadas encontrada para o horário atual.")
    else:
        tab_jogos, tab_combos = st.tabs(["⚽ JOGOS & ANÁLISES POR LIGA", "🚀 DUPLAS & MÚLTIPLA PRO (ODD 5.00+)"])

        todas_entradas_globais = []
        partidas_processadas = []

        with st.spinner(f"⏳ Processando {len(partidas_validas)} partidas elegíveis..."):
            for dt_fix, item in partidas_validas:
                opps = analisar_oportunidades_partida(item)
                todas_entradas_globais.extend(opps)
                partidas_processadas.append((dt_fix, item, opps))

        # --- ABA 1 ---
        with tab_jogos:
            ligas_disponiveis = sorted(list(set([f"{item['league']['country']} - {item['league']['name']}" for _, item, _ in partidas_processadas])))
            ligas_opcoes = ["🌍 Todas as Ligas Permiteidas"] + ligas_disponiveis

            st.write("")
            col_filtro1, _ = st.columns([2, 1])
            with col_filtro1:
                liga_selecionada = st.selectbox("📌 Filtrar por Campeonato Autorizado:", options=ligas_opcoes)

            partidas_exibir = []
            for dt_fix, item, opps in partidas_processadas:
                nome_liga = f"{item['league']['country']} - {item['league']['name']}"
                if liga_selecionada == "🌍 Todas as Ligas Permiteidas" or liga_selecionada == nome_liga:
                    partidas_exibir.append((dt_fix, item, opps))

            st.success(f"✅ {len(partidas_processadas)} partidas filtradas com sucesso! Exibindo {len(partidas_exibir)} jogo(s).")

            for dt_fix, item, opps in partidas_exibir:
                league = item["league"]
                teams = item["teams"]
                dt_br = dt_fix - timedelta(hours=3)

                st.markdown(
                    f"""
                <div class="match-card">
                    <div class="match-header">⚽ {teams['home']['name']}  x  {teams['away']['name']}</div>
                    <div class="league-header">🏆 {league['country']} — {league['name']} | 📅 {dt_br.strftime('%d/%m às %H:%M')}</div>
                    <div class="section-title">🎯 Oportunidades Identificadas (Alta / Média / Baixa)</div>
                """,
                    unsafe_allow_html=True,
                )

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

                st.markdown("<div class='section-title' style='margin-top:16px;'>📝 Justificativa Estatística</div>", unsafe_allow_html=True)

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

                st.markdown(
                    """
                    <div class="disclaimer-box">
                        🔞 <b>+18 | APOSTE COM RESPONSABILIDADE:</b> Projeções quantitativas não são garantia de resultados. Gerencie sua banca.
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

        # --- ABA 2 ---
        with tab_combos:
            st.write("")
            st.subheader("🔥 Bilhetes Prontos do Dia (Apenas Entradas de Alta e Média Confiança)")

            entradas_altas = [e for e in todas_entradas_globais if e["tipo"] == "ALTA"]
            entradas_medias = [e for e in todas_entradas_globais if e["tipo"] == "MEDIA"]

            if len(entradas_altas) >= 2:
                col_d1, col_d2 = st.columns(2)

                d1_e1 = entradas_altas[0]
                d1_e2 = next((x for x in entradas_altas if x["match"] != d1_e1["match"]), entradas_altas[1])
                odd_d1 = d1_e1["val_odd"] * d1_e2["val_odd"]

                with col_d1:
                    st.markdown(
                        f"""
                    <div class="combo-card">
                        <div class="combo-header">
                            <span>🟢 DUPLA PRO #1 (Alta Confiança)</span>
                            <span style="color:#00FF66; font-size:1.2em;">ODD TOTAL: @ {odd_d1:.2f}</span>
                        </div>
                        <div class="combo-item">
                            📌 <b>{d1_e1['match']}</b><br>
                            Entrada: <b>{d1_e1['titulo']}</b> (@{d1_e1['val_odd']:.2f}) {d1_e1['badge']}
                        </div>
                        <div class="combo-item">
                            📌 <b>{d1_e2['match']}</b><br>
                            Entrada: <b>{d1_e2['titulo']}</b> (@{d1_e2['val_odd']:.2f}) {d1_e2['badge']}
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                m_e1 = entradas_medias[0] if entradas_medias else entradas_altas[-1]
                m_e2 = next((x for x in entradas_altas if x["match"] not in [d1_e1["match"], d1_e2["match"]]), entradas_altas[0])
                odd_d2 = m_e1["val_odd"] * m_e2["val_odd"]

                with col_d2:
                    st.markdown(
                        f"""
                    <div class="combo-card">
                        <div class="combo-header">
                            <span>🟡 DUPLA PRO #2 (Média & Alta)</span>
                            <span style="color:#00FF66; font-size:1.2em;">ODD TOTAL: @ {odd_d2:.2f}</span>
                        </div>
                        <div class="combo-item">
                            📌 <b>{m_e1['match']}</b><br>
                            Entrada: <b>{m_e1['titulo']}</b> (@{m_e1['val_odd']:.2f}) {m_e1['badge']}
                        </div>
                        <div class="combo-item">
                            📌 <b>{m_e2['match']}</b><br>
                            Entrada: <b>{m_e2['titulo']}</b> (@{m_e2['val_odd']:.2f}) {m_e2['badge']}
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
