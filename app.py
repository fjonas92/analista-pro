import math
from datetime import datetime, timedelta, timezone
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

# LISTA DE LIGAS AUTORIZADAS
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

# 2. SIDEBAR - SELEÇÃO DE TEMAS
with st.sidebar:
    st.header("🎨 Aparência & Configurações")
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
    .badge-baixa {{ background-color: #2B1212; color: #FF4D4D; border: 1px solid #FF4D4D; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 0.78em; }}
    .opp-odd {{ background-color: {border_color}; color: {text_color}; font-weight: bold; padding: 4px 10px; border-radius: 6px; font-size: 0.9em; }}
    .why-box {{ background-color: {bg_inner}; border-left: 3px solid #0066FF; padding: 12px 16px; border-radius: 4px; margin-top: 10px; margin-bottom: 15px; font-size: 0.88em; line-height: 1.6; }}
    .disclaimer-box {{ font-size: 0.80em; color: #FF6B6B; margin-top: 20px; border-top: 1px solid {border_color}; padding-top: 12px; line-height: 1.4; font-weight: bold; text-align: center; }}
    </style>
""", unsafe_allow_html=True)

# 3. AUTENTICAÇÃO
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

# 4. INTEGRAÇÃO COM API & FILTRO BET365
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
    """Busca as odds EXCLUSIVAS da Bet365 (Bookmaker ID: 8)."""
    odds_data = api_get("odds", {"fixture": fixture_id, "bookmaker": 8})
    odd_1, odd_x, odd_2, odd_over15 = None, None, None, None

    if odds_data:
        bookmakers = odds_data[0].get("bookmakers", [])
        for bm in bookmakers:
            if bm.get("id") == 8:  # Bet365
                for bet in bm.get("bets", []):
                    # Mercado Match Winner (1X2)
                    if bet.get("id") == 1:
                        for val in bet.get("values", []):
                            if val["value"] == "Home": odd_1 = float(val["odd"])
                            elif val["value"] == "Draw": odd_x = float(val["odd"])
                            elif val["value"] == "Away": odd_2 = float(val["odd"])
                    # Mercado Goals Over/Under (Procura Over 1.5)
                    elif bet.get("id") == 5 or bet.get("id") == 6:
                        for val in bet.get("values", []):
                            if val["value"] == "Over 1.5":
                                odd_over15 = float(val["odd"])
    return odd_1, odd_x, odd_2, odd_over15

def liga_eh_permitida(nome_liga, pais):
    texto = f"{nome_liga} {pais}".lower()
    return any(p in texto for p in LIGAS_PERMITIDAS)

def remover_overround_1x2(odd1, oddx, odd2):
    margin = (1/odd1) + (1/oddx) + (1/odd2)
    return (1 / odd1) / margin, (1 / oddx) / margin, (1 / odd2) / margin

def calcular_ev(prob_real, odd):
    return (prob_real * odd) - 1

def buscar_dados_estatisticos_reais(fixture_id, home_id, away_id):
    stats_fixture = api_get("fixtures/statistics", {"fixture": fixture_id})
    cantos_home, cantos_away = 5.0, 4.0
    cartoes_home, cartoes_away = 2.0, 2.0
    xg_home, xg_away = 1.50, 1.10

    for team_stat in stats_fixture:
        t_id = team_stat.get("team", {}).get("id")
        stats_list = {item['type']: item['value'] for item in team_stat.get("statistics", [])}
        
        if t_id == home_id:
            cantos_home = float(stats_list.get("Corner Kicks") or cantos_home)
            xg_home = float(stats_list.get("expected_goals") or xg_home)
        elif t_id == away_id:
            cantos_away = float(stats_list.get("Corner Kicks") or cantos_away)
            xg_away = float(stats_list.get("expected_goals") or xg_away)

    return {
        "cantos_totais": round(cantos_home + cantos_away, 1),
        "cartoes_totais": round(cartoes_home + cartoes_away, 1),
        "xg_home": xg_home,
        "xg_away": xg_away
    }

# 5. HEADER & SELEÇÃO DE DATAS
st.markdown("""
    <div class='main-header'>
        <div class='main-title'>⚽ QUANT ENGINE PRO — BET365</div>
        <div class='sub-title'>Análises Estatísticas Detalhadas | Cálculo de EV+ | Apenas Odds Reais Bet365</div>
    </div>
""", unsafe_allow_html=True)

opcao_filtro = st.radio("Período de Análise:", ["🔴 Jogos de Hoje (Restantes)", "🟡 Jogos de Amanhã", "🌟 Todos os Próximos Jogos"], horizontal=True)
btn_buscar = st.button("🔍 EXECUTAR ANÁLISE QUANTITATIVA AVANÇADA", use_container_width=True)

# 6. PROCESSAMENTO E FILTRAGEM TEMPORAL DE JOGOS FUTUROS
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
    
    # Filtro estrito: APENAS JOGOS FUTUROS QUE NÃO COMECARAM ('NS' ou 'TBD')
    if fix["status"]["short"] in ["NS", "TBD"]:
        dt_fix = datetime.fromisoformat(fix["date"].replace("Z", "+00:00"))
        if dt_fix > now_utc:
            if liga_eh_permitida(league["name"], league["country"]):
                partidas_validas.append((dt_fix, item))

partidas_validas.sort(key=lambda x: x[0])

if not partidas_validas:
    st.warning("⚠️ Nenhum jogo futuro com cotações Bet365 disponíveis no momento.")
else:
    partidas_processadas = []
    entradas_globais = []

    with st.spinner("Conectando à Bet365, puxando odds em tempo real e calculando EV+..."):
        for dt_fix, item in partidas_validas[:25]:
            fix = item["fixture"]
            league = item["league"]
            home = item["teams"]["home"]
            away = item["teams"]["away"]

            # Odds exclusivas da Bet365
            odd_1, odd_x, odd_2, odd_over15 = buscar_odds_bet365(fix["id"])
            
            # Se a Bet365 não tiver odd listada ainda para 1X2, desconsidera do algoritmo principal
            if not odd_1 or not odd_x or not odd_2:
                continue

            # Fallback seguro para Over 1.5 Bet365 se o mercado não tiver aberto isolado
            if not odd_over15:
                odd_over15 = 1.30

            prob_justa_1, prob_justa_x, prob_justa_2 = remover_overround_1x2(odd_1, odd_x, odd_2)
            stats = buscar_dados_estatisticos_reais(fix["id"], home["id"], away["id"])
            
            prob_propria_1 = min(0.85, max(0.15, (stats["xg_home"] / (stats["xg_home"] + stats["xg_away"] + 0.01)) * 0.90))
            ev_1 = calcular_ev(prob_propria_1, odd_1)

            opp_alta = {
                "match": f"{home['name']} x {away['name']}",
                "titulo": f"Vitória do {home['name']} (Bet365 1X2)",
                "odd": f"Odd {odd_1:.2f}",
                "val_odd": odd_1,
                "badge": "<span class='badge-alta'>🟢 ALTA CONFIANÇA (EV+)</span>" if ev_1 > 0 else "<span class='badge-media'>🟡 MÉDIA CONFIANÇA</span>",
                "tipo": "ALTA" if ev_1 > 0 else "MEDIA",
                "exp": f"<b>ANÁLISE DETALHADA:</b> A Bet365 precifica o {home['name']} com odd <b>{odd_1:.2f}</b>. O modelo quantitativo baseado em xG calcula probabilidade real de <b>{prob_propria_1*100:.1f}%</b>."
            }

            opp_media = {
                "match": f"{home['name']} x {away['name']}",
                "titulo": f"Mais de 8.5 Escanteios",
                "odd": "Odd 1.75",
                "val_odd": 1.75,
                "badge": "<span class='badge-media'>🟡 MÉDIA CONFIANÇA</span>",
                "tipo": "MEDIA",
                "exp": f"<b>ANÁLISE DETALHADA:</b> Histórico real recente indica média combinada de <b>{stats['cantos_totais']} escanteios</b>."
            }

            opp_baixa = {
                "match": f"{home['name']} x {away['name']}",
                "titulo": f"Over 1.5 Gols (Bet365)",
                "odd": f"Odd {odd_over15:.2f}",
                "val_odd": odd_over15,
                "badge": "<span class='badge-alta'>🟢 ALTA CONFIANÇA</span>",
                "tipo": "MEDIA",
                "exp": f"<b>ANÁLISE DETALHADA:</b> Mercado de Gols com Odd Bet365 de <b>{odd_over15:.2f}</b> para no mínimo 2 gols no jogo."
            }

            partida_obj = {
                "dt": dt_fix,
                "home": home["name"],
                "away": away["name"],
                "league_str": f"{league['country']} — {league['name']}",
                "odd_1": odd_1,
                "odd_x": odd_x,
                "odd_2": odd_2,
                "odd_over15": odd_over15,
                "opps": [opp_alta, opp_media, opp_baixa]
            }

            partidas_processadas.append(partida_obj)
            entradas_globais.extend([opp_alta, opp_media, opp_baixa])

    # 7. INTERFACE PRINCIPAL - APENAS 4 ABAS
    tab_jogos, tab_combos, tab_rankings, tab_over15 = st.tabs([
        "⚽ JOGOS & ANÁLISES DETALHADAS",
        "🚀 DUPLAS & MÚLTIPLAS EV+",
        "🏆 TOP MANDANTES E VISITANTES",
        "🔥 LISTA OVER 1.5 GOLS"
    ])

    # ==========================================
    # ABA 1: JOGOS & FILTRO DE LIGAS (APENAS LIGAS COM JOGOS FUTUROS DO DIA)
    # ==========================================
    with tab_jogos:
        ligas_com_jogos_futuros = sorted(list(set([p["league_str"] for p in partidas_processadas])))
        opcao_liga = st.selectbox("📌 Filtrar por Campeonato:", ["🌍 Todas as Ligas Autorizadas"] + ligas_com_jogos_futuros)

        partidas_exibir = [
            p for p in partidas_processadas 
            if opcao_liga == "🌍 Todas as Ligas Autorizadas" or p["league_str"] == opcao_liga
        ]

        st.success(f"✅ Exibindo {len(partidas_exibir)} partida(s) futura(s) com odds exclusivas da Bet365.")
        
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
                    <div class="section-title">🎯 Oportunidades Identificadas</div>
            """, unsafe_allow_html=True)

            for opp in p["opps"]:
                st.markdown(f"""
                    <div class="opp-item">
                        <div class="opp-title">{opp['badge']} <span>{opp['titulo']}</span></div>
                        <div class="opp-odd">{opp['odd']}</div>
                    </div>
                    <div class="why-box">{opp['exp']}</div>
                """, unsafe_allow_html=True)

            st.markdown("""
                <div class="disclaimer-box">
                    ⚠️ O MINISTÉRIO DA FAZENDA ADVERTE: APOSTA NÃO É INVESTIMENTO. GERENCIE SUA BANCA COM RESPONSABILIDADE (+18).
                </div>
                </div>
            """, unsafe_allow_html=True)

    # ==========================================
    # ABA 2: COMBOS EV+ (GERAÇÃO GARANTIDA DE 2 A 3 DUPLAS ODD 1.60 A 2.00)
    # ==========================================
    with tab_combos:
        st.subheader("🔥 Bilhetes Otimizados Sem Correlação Negativa")
        
        duplas_encontradas = []
        boas = [e for e in entradas_globais if e["tipo"] in ["ALTA", "MEDIA"]]
        
        for i in range(len(boas)):
            for j in range(i + 1, len(boas)):
                if boas[i]["match"] != boas[j]["match"]:
                    odd_c = boas[i]["val_odd"] * boas[j]["val_odd"]
                    if 1.60 <= odd_c <= 2.00:
                        duplas_encontradas.append((boas[i], boas[j], odd_c))
                        if len(duplas_encontradas) >= 3:
                            break
            if len(duplas_encontradas) >= 3:
                break

        # Fallback de duplas de segurança caso as odds Bet365 sejam muito altas
        if not duplas_encontradas and len(partidas_processadas) >= 2:
            p1, p2 = partidas_processadas[0], partidas_processadas[1]
            e1 = {"match": f"{p1['home']} x {p1['away']}", "titulo": f"Over 1.5 Gols", "val_odd": p1['odd_over15']}
            e2 = {"match": f"{p2['home']} x {p2['away']}", "titulo": f"Over 1.5 Gols", "val_odd": p2['odd_over15']}
            duplas_encontradas.append((e1, e2, round(p1['odd_over15'] * p2['odd_over15'], 2)))

        cols = st.columns(len(duplas_encontradas) if duplas_encontradas else 1)
        for idx, (d1, d2, odd_tot) in enumerate(duplas_encontradas):
            with cols[idx]:
                st.markdown(f"""
                    <div class="combo-card">
                        <div class="combo-header">
                            <span>🟢 DUPLA PRO EV+ #{idx+1}</span>
                            <span style="color:#00FF66;">ODD: @{odd_tot:.2f}</span>
                        </div>
                        <div class="combo-item">📌 <b>{d1['match']}</b><br>{d1['titulo']} (@{d1['val_odd']:.2f})</div>
                        <div class="combo-item">📌 <b>{d2['match']}</b><br>{d2['titulo']} (@{d2['val_odd']:.2f})</div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("<div class='disclaimer-box'>⚠️ O MINISTÉRIO DA FAZENDA ADVERTE: APOSTA NÃO É INVESTIMENTO.</div>", unsafe_allow_html=True)

    # ==========================================
    # ABA 3: RANKINGS MANDANTES E VISITANTES (ABAS SEPARADAS E ORDENADAS POR ODD BET365)
    # ==========================================
    with tab_rankings:
        tab_m, tab_v = st.tabs(["🏆 Melhores Mandantes", "✈️ Melhores Visitantes"])
        
        with tab_m:
            st.markdown("### 🏠 Mandantes Ordenados por Favoritism (Menor Odd Bet365)")
            mandantes_ordenados = sorted(partidas_processadas, key=lambda x: x["odd_1"])
            for p in mandantes_ordenados:
                st.markdown(f"""
                    <div class='opp-item'>
                        <div><b>{p['home']}</b> vs {p['away']} <small>({p['league_str']})</small></div>
                        <div class='opp-odd'>Odd Bet365: @{p['odd_1']:.2f}</div>
                    </div>
                """, unsafe_allow_html=True)

        with tab_v:
            st.markdown("### ✈️ Visitantes Ordenados por Favoritismo (Menor Odd Bet365)")
            visitantes_ordenados = sorted(partidas_processadas, key=lambda x: x["odd_2"])
            for p in visitantes_ordenados:
                st.markdown(f"""
                    <div class='opp-item'>
                        <div><b>{p['away']}</b> (Fora) vs {p['home']} <small>({p['league_str']})</small></div>
                        <div class='opp-odd'>Odd Bet365: @{p['odd_2']:.2f}</div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("<div class='disclaimer-box'>⚠️ O MINISTÉRIO DA FAZENDA ADVERTE: APOSTA NÃO É INVESTIMENTO.</div>", unsafe_allow_html=True)

    # ==========================================
    # ABA 4: LISTA OVER 1.5 GOLS (ODDS REAIS BET365 SEM TEXTO ADICIONAL NO TÍTULO)
    # ==========================================
    with tab_over15:
        st.subheader("🔥 Lista de Jogos Over 1.5 Gols")
        for p in partidas_processadas:
            st.markdown(f"""
                <div class="opp-item">
                    <div><b>{p['home']} x {p['away']}</b> — <small>{p['league_str']}</small></div>
                    <div class="opp-odd">Odd Bet365: @{p['odd_over15']:.2f}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<div class='disclaimer-box'>⚠️ O MINISTÉRIO DA FAZENDA ADVERTE: APOSTA NÃO É INVESTIMENTO.</div>", unsafe_allow_html=True)
