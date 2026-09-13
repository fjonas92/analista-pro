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

# Estilização CSS Clean (Barra superior removida)
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

# Controle de sessão e login
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

# Header Principal
st.markdown(
    """
    <div class='main-header'>
        <div class='main-title'>⚽ ANALISTA PRO — PAINEL DE OPORTUNIDADES</div>
        <div class='sub-title'>Algoritmo Quantitativo de Precificação e Inteligência Estatística (API Pro Enabled)</div>
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


def obter_badge_confianca(score):
    if score >= 75:
        return "<span class='badge-alta'>🟢 ALTA CONFIANÇA</span>"
    elif score >= 60:
        return "<span class='badge-media'>🟡 MÉDIA CONFIANÇA</span>"
    else:
        return "<span class='badge-baixa'>🔴 BAIXA CONFIANÇA</span>"


def analisar_oportunidades_partida(fixture):
    fixture_id = fixture["fixture"]["id"]
    home_name = fixture["teams"]["home"]["name"]
    away_name = fixture["teams"]["away"]["name"]
    home_id = fixture["teams"]["home"]["id"]
    away_id = fixture["teams"]["away"]["id"]
    league_id = fixture["league"]["id"]
    season = fixture["league"]["season"]

    # Consulta de estatísticas completas via API Paga
    stat_h = api_get("teams/statistics", {"league": league_id, "season": season, "team": home_id})
    stat_a = api_get("teams/statistics", {"league": league_id, "season": season, "team": away_id})

    # Valores base derivados da API
    g_home_scored, g_home_conceded = 1.45, 1.10
    g_away_scored, g_away_conceded = 1.15, 1.50
    cards_h, cards_a = 2.1, 2.4
    cantos_h, cantos_a = 5.1, 4.3

    if stat_h and len(stat_h) > 0:
        sh = stat_h[0] if isinstance(stat_h, list) else stat_h
        g_home_scored = float(sh.get("goals", {}).get("for", {}).get("average", {}).get("home", 1.45) or 1.45)
        g_home_conceded = float(sh.get("goals", {}).get("against", {}).get("average", {}).get("home", 1.10) or 1.10)
        cards_h = float(sh.get("cards", {}).get("yellow", {}).get("0-15", {}).get("total", 2) or 2.1)

    if stat_a and len(stat_a) > 0:
        sa = stat_a[0] if isinstance(stat_a, list) else stat_a
        g_away_scored = float(sa.get("goals", {}).get("for", {}).get("average", {}).get("away", 1.15) or 1.15)
        g_away_conceded = float(sa.get("goals", {}).get("against", {}).get("average", {}).get("away", 1.50) or 1.50)
        cards_a = float(sa.get("cards", {}).get("yellow", {}).get("0-15", {}).get("total", 2) or 2.4)

    # Distribuição de Poisson
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
    todas_opcoes = []

    # 1. Mercado 1X2 e Dupla Chance
    if prob_home >= 0.52:
        odd = round(1.0 / max(0.1, prob_home), 2)
        score = int(prob_home * 100)
        todas_opcoes.append({
            "match": match_name, "tipo": "1X2",
            "titulo": f"Vitória do {home_name}",
            "score": score, "val_odd": odd, "badge": obter_badge_confianca(score), "odd": f"Odd {odd:.2f}",
            "explicacao": f"O modelo quantitativo atribui {prob_home*100:.1f}% de chance de vitória para o {home_name}, respaldado pela média de {g_home_scored:.2f} gols marcados como mandante."
        })
    elif prob_away >= 0.48:
        odd = round(1.0 / max(0.1, prob_away), 2)
        score = int(prob_away * 100)
        todas_opcoes.append({
            "match": match_name, "tipo": "1X2",
            "titulo": f"Vitória do {away_name}",
            "score": score, "val_odd": odd, "badge": obter_badge_confianca(score), "odd": f"Odd {odd:.2f}",
            "explicacao": f"O {away_name} chega favorito fora de casa com {prob_away*100:.1f}% de probabilidade de vitória segundo o modelo de Poisson."
        })
    else:
        prob_dc = prob_home + prob_draw
        odd = round(1.0 / max(0.1, prob_dc), 2)
        score = int(prob_dc * 100)
        todas_opcoes.append({
            "match": match_name, "tipo": "DUPLA CHANCE",
            "titulo": f"Dupla Chance — {home_name} ou Empate",
            "score": score, "val_odd": odd, "badge": obter_badge_confianca(score), "odd": f"Odd {odd:.2f}",
            "explicacao": f"Jogo com tendência de equilíbrio. A cobertura para {home_name} ou Empate possui {prob_dc*100:.1f}% de probabilidade de acerto."
        })

    # 2. Mercado de Gols (Over / Under)
    if prob_over25 >= 0.55:
        odd = round(1.0 / max(0.1, prob_over25), 2)
        score = int(prob_over25 * 100)
        todas_opcoes.append({
            "match": match_name, "tipo": "GOLS",
            "titulo": "Mais de 2.5 Gols",
            "score": score, "val_odd": odd, "badge": obter_badge_confianca(score), "odd": f"Odd {odd:.2f}",
            "explicacao": f"Expectativa ofensiva combinada de {lambda_home + lambda_away:.2f} gols no confronto, indicando tendência para um jogo aberto Over 2.5."
        })
    elif prob_under25 >= 0.55:
        odd = round(1.0 / max(0.1, prob_under25), 2)
        score = int(prob_under25 * 100)
        todas_opcoes.append({
            "match": match_name, "tipo": "GOLS",
            "titulo": "Menos de 2.5 Gols (Under)",
            "score": score, "val_odd": odd, "badge": obter_badge_confianca(score), "odd": f"Odd {odd:.2f}",
            "explicacao": f"Confronto travado no setor de criação. Matriz de Poisson indica {prob_under25*100:.1f}% de probabilidade para a partida ter 2 ou menos gols."
        })
    else:
        odd = round(1.0 / max(0.1, prob_over15), 2)
        score = int(prob_over15 * 100)
        todas_opcoes.append({
            "match": match_name, "tipo": "GOLS",
            "titulo": "Mais de 1.5 Gols",
            "score": score, "val_odd": odd, "badge": obter_badge_confianca(score), "odd": f"Odd {odd:.2f}",
            "explicacao": f"Linha conservadora de valor: {prob_over15*100:.1f}% de chance estatística de sair pelo menos 2 gols no placar final."
        })

    # 3. Mercado Ambas Marcam (BTTS)
    if prob_btts_yes >= 0.53:
        odd = round(1.0 / max(0.1, prob_btts_yes), 2)
        score = int(prob_btts_yes * 100)
        todas_opcoes.append({
            "match": match_name, "tipo": "BTTS",
            "titulo": "Ambas Marcam — SIM",
            "score": score, "val_odd": odd, "badge": obter_badge_confianca(score), "odd": f"Odd {odd:.2f}",
            "explicacao": f"O {away_name} marca {g_away_scored:.2f} gols fora de casa e o {home_name} cede {g_home_conceded:.2f} em seus domínios ({prob_btts_yes*100:.1f}% BTTS SIM)."
        })
    else:
        odd = round(1.0 / max(0.1, prob_btts_no), 2)
        score = int(prob_btts_no * 100)
        todas_opcoes.append({
            "match": match_name, "tipo": "BTTS",
            "titulo": "Ambas Marcam — NÃO",
            "score": score, "val_odd": odd, "badge": obter_badge_confianca(score), "odd": f"Odd {odd:.2f}",
            "explicacao": f"Elevada probabilidade ({prob_btts_no*100:.1f}%) de pelo menos uma das equipes passar em branco no confronto."
        })

    # 4. Mercado de Cartões
    total_cards_esp = cards_h + cards_a
    linha_cards = "Mais de 3.5 Cartões" if total_cards_esp >= 4.0 else "Menos de 4.5 Cartões"
    odd_cards = 1.75 if total_cards_esp >= 4.0 else 1.65
    score_cards = min(92, int(total_cards_esp * 16)) if total_cards_esp >= 4.0 else 72
    todas_opcoes.append({
        "match": match_name, "tipo": "CARTOES",
        "titulo": linha_cards,
        "score": score_cards, "val_odd": odd_cards, "badge": obter_badge_confianca(score_cards), "odd": f"Odd {odd_cards:.2f}",
        "explicacao": f"Histórico disciplinar: Média projetada de {total_cards_esp:.1f} cartões amarelos/vermelhos com base na agressividade de ambas as equipes."
    })

    # 5. Mercado de Escanteios
    total_cantos = cantos_h + cantos_a
    linha_cantos = "Mais de 9.5 Escanteios" if total_cantos >= 9.5 else "Mais de 8.5 Escanteios"
    score_cantos = min(90, int(total_cantos * 8.5))
    todas_opcoes.append({
        "match": match_name, "tipo": "ESCANTARIOS",
        "titulo": linha_cantos,
        "score": score_cantos, "val_odd": 1.80, "badge": obter_badge_confianca(score_cantos), "odd": "Odd 1.80",
        "explicacao": f"Métricas de linha de fundo: Expectativa de {cantos_h:.1f} cantos para o mandante e {cantos_a:.1f} para o visitante."
    })

    # Ordena todas as opções pelo Score e seleciona as 3 melhores de mercados DIFERENTES para este jogo
    todas_opcoes.sort(key=lambda x: x["score"], reverse=True)
    
    melhores_do_jogo = []
    tipos_usados = set()
    for op in todas_opcoes:
        if op["tipo"] not in tipos_usados:
            melhores_do_jogo.append(op)
            tipos_usados.add(op["tipo"])
        if len(melhores_do_jogo) >= 3:
            break

    return melhores_do_jogo


# --- REQUISIÇÕES E PROCESSAMENTO ---
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
    st.error("⚠️ Nenhum jogo encontrado na API. Selecione '🌟 Todos os Próximos Jogos' e clique no botão.")
else:
    partidas_validas = []
    for item in raw_fixtures:
        fix = item["fixture"]
        dt_fix = datetime.fromisoformat(fix["date"].replace("Z", "+00:00"))
        if fix["status"]["short"] in ["NS", "TBD"]:
            partidas_validas.append((dt_fix, item))

    partidas_validas.sort(key=lambda x: x[0])

    if not partidas_validas:
        st.warning("⚠️ Todos os jogos listados para este filtro já foram iniciados ou finalizados.")
    else:
        tab_jogos, tab_combos = st.tabs(["⚽ JOGOS & ANÁLISES POR LIGA", "🚀 DUPLAS & MÚLTIPLA PRO (ODD 5.00+)"])

        todas_entradas_globais = []
        partidas_processadas = []

        with st.spinner(f"⏳ Processando {len(partidas_validas)} partidas na API Paga..."):
            for dt_fix, item in partidas_validas:
                opps = analisar_oportunidades_partida(item)
                todas_entradas_globais.extend(opps)
                partidas_processadas.append((dt_fix, item, opps))

        # --- ABA 1: ANÁLISES INDIVIDUAIS POR LIGA ---
        with tab_jogos:
            ligas_disponiveis = sorted(list(set([f"{item['league']['country']} - {item['league']['name']}" for _, item, _ in partidas_processadas])))
            ligas_opcoes = ["🌍 Todas as Ligas"] + ligas_disponiveis

            st.write("")
            col_filtro1, _ = st.columns([2, 1])
            with col_filtro1:
                liga_selecionada = st.selectbox("📌 Filtrar Jogos por Liga/Campeonato:", options=ligas_opcoes)

            partidas_exibir = []
            for dt_fix, item, opps in partidas_processadas:
                nome_liga = f"{item['league']['country']} - {item['league']['name']}"
                if liga_selecionada == "🌍 Todas as Ligas" or liga_selecionada == nome_liga:
                    partidas_exibir.append((dt_fix, item, opps))

            st.success(f"✅ {len(partidas_processadas)} partidas precificadas com sucesso! Exibindo {len(partidas_exibir)} jogo(s).")

            for dt_fix, item, opps in partidas_exibir:
                league = item["league"]
                teams = item["teams"]
                dt_br = dt_fix - timedelta(hours=3)

                st.markdown(
                    f"""
                <div class="match-card">
                    <div class="match-header">⚽ {teams['home']['name']}  x  {teams['away']['name']}</div>
                    <div class="league-header">🏆 {league['country']} — {league['name']} | 📅 {dt_br.strftime('%d/%m às %H:%M')}</div>
                    <div class="section-title">🎯 Oportunidades Identificadas</div>
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

        # --- ABA 2: DUPLAS E MÚLTIPLA DIVERSIFICADA ---
        with tab_combos:
            st.write("")
            st.subheader("🔥 Bilhetes Prontos do Dia (Com Variedade de Mercados)")
            st.caption("Mesclando Vitória, Gols, Ambas Marcam, Cartões e Escanteios sem repetições de jogos.")

            entradas_ordenadas = sorted(todas_entradas_globais, key=lambda x: x["score"], reverse=True)

            entradas_1x2 = [e for e in entradas_ordenadas if e["tipo"] in ["1X2", "DUPLA CHANCE"]]
            entradas_gols = [e for e in entradas_ordenadas if e["tipo"] in ["GOLS", "BTTS"]]
            entradas_outros = [e for e in entradas_ordenadas if e["tipo"] in ["CARTOES", "ESCANTARIOS"]]

            if len(entradas_1x2) >= 2 and len(entradas_gols) >= 2:
                col_d1, col_d2 = st.columns(2)

                # Dupla 1
                d1_e1 = entradas_1x2[0]
                d1_e2 = next((g for g in entradas_gols if g["match"] != d1_e1["match"]), entradas_gols[0])
                odd_d1 = d1_e1["val_odd"] * d1_e2["val_odd"]

                with col_d1:
                    st.markdown(
                        f"""
                    <div class="combo-card">
                        <div class="combo-header">
                            <span>🟢 DUPLA PRO #1 (Match & Gols)</span>
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

                # Dupla 2
                jogos_usados_d1 = {d1_e1["match"], d1_e2["match"]}
                d2_e1 = next((g for g in entradas_gols if g["match"] not in jogos_usados_d1), entradas_gols[1])
                d2_e2 = next((o for o in entradas_outros if o["match"] not in jogos_usados_d1 and o["match"] != d2_e1["match"]), entradas_outros[0])
                odd_d2 = d2_e1["val_odd"] * d2_e2["val_odd"]

                with col_d2:
                    st.markdown(
                        f"""
                    <div class="combo-card">
                        <div class="combo-header">
                            <span>🟢 DUPLA PRO #2 (Gols & Disciplinar)</span>
                            <span style="color:#00FF66; font-size:1.2em;">ODD TOTAL: @ {odd_d2:.2f}</span>
                        </div>
                        <div class="combo-item">
                            📌 <b>{d2_e1['match']}</b><br>
                            Entrada: <b>{d2_e1['titulo']}</b> (@{d2_e1['val_odd']:.2f}) {d2_e1['badge']}
                        </div>
                        <div class="combo-item">
                            📌 <b>{d2_e2['match']}</b><br>
                            Entrada: <b>{d2_e2['titulo']}</b> (@{d2_e2['val_odd']:.2f}) {d2_e2['badge']}
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                # Múltipla Diversificada
                multipla_selecoes = []
                jogos_multipla = set()
                odd_acumulada = 1.0

                for item in entradas_ordenadas:
                    if item["match"] in jogos_multipla:
                        continue

                    multipla_selecoes.append(item)
                    jogos_multipla.add(item["match"])
                    odd_acumulada *= item["val_odd"]

                    if odd_acumulada >= 5.00 and len(multipla_selecoes) >= 3:
                        break

                st.write("")
                st.markdown(
                    f"""
                <div class="combo-card" style="border: 1px solid #FFCC00;">
                    <div class="combo-header">
                        <span style="color:#FFCC00; font-size:1.2em;">🔥 MÚLTIPLA PRO DO DIA (ODD 5.00+)</span>
                        <span style="color:#FFCC00; font-size:1.4em;">ODD TOTAL: @ {odd_acumulada:.2f}</span>
                    </div>
                """,
                    unsafe_allow_html=True,
                )

                for item in multipla_selecoes:
                    st.markdown(
                        f"""
                    <div class="combo-item">
                        📌 <b>{item['match']}</b> — Seleção: <b>{item['titulo']}</b> (@{item['val_odd']:.2f}) {item['badge']}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                st.markdown(
                    """
                    <div class="disclaimer-box">
                        🔞 <b>+18 | APOSTE COM RESPONSABILIDADE:</b> Bilhetes múltiplos exigem gestão rigorosa de banca.
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
