from datetime import datetime, timedelta, timezone
import requests
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="ANALISTA PRO",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilização CSS personalizada
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    [data-testid="stHeader"] {display: none;}
    
    .stApp {
        background-color: #121212;
        color: #FFFFFF;
    }
    .main-header {
        text-align: center;
        padding: 15px;
        background-color: #1A1A1A;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    .card-jogo {
        background-color: #1E1E1E;
        border: 1px solid #0066FF;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }
    .liga-title {
        color: #0066FF;
        font-weight: bold;
        font-size: 0.85em;
    }
    .confronto-title {
        color: #FFFFFF;
        font-weight: bold;
        font-size: 1.2em;
        margin-bottom: 10px;
    }
    .badge-alta {
        background-color: #1E2A1E;
        color: #00FF66;
        border: 1px solid #00FF66;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85em;
    }
    .badge-media {
        background-color: #2A281E;
        color: #FFCC00;
        border: 1px solid #FFCC00;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85em;
    }
    .badge-baixa {
        background-color: #2A1E1E;
        color: #FF4444;
        border: 1px solid #FF4444;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85em;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# API Key
THE_ODDS_API_KEY = st.secrets.get(
    "THE_ODDS_API_KEY", "e484810f517d8e428f3cbf3e89e2973b"
)

# Licenças Válidas
LICENCAS_VALIDAS = [
    "PRO-FUTEBOL-2026",
    "VIP-ANALISTA-888",
    "CLIENTE-PRO-01",
    "ADMIN-MASTER-99",
]

# Ligas Monitoradas
LIGAS_FUTEBOL = [
    "soccer_brazil_campeonato",
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "soccer_germany_bundesliga",
    "soccer_france_ligue_one",
    "soccer_uefa_champs_league",
    "soccer_uefa_europa_league",
    "soccer_argentina_primera_division",
    "soccer_usa_mls",
]

# Login
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown(
        "<div class='main-header'><h1>🔒 ANALISTA PRO — ÁREA EXCLUSIVA</h1></div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Digite sua Chave de Acesso")
        chave_input = st.text_input(
            "Chave de Licença:", type="password", placeholder="Ex: PRO-FUTEBOL-2026"
        )
        btn_entrar = st.button("🔑 ENTRAR NO SISTEMA", use_container_width=True)

        if btn_entrar:
            if chave_input.strip() in LICENCAS_VALIDAS:
                st.session_state["autenticado"] = True
                st.success("Acesso liberado!")
                st.rerun()
            else:
                st.error("❌ Chave de licença inválida ou expirada.")

        st.markdown("---")
        st.info("💡 Adquira sua chave VIP para acesso ilimitado.")
    st.stop()

# --- PAINEL PRINCIPAL ---
st.markdown(
    "<div class='main-header'><h1>⚽ ANALISTA PRO</h1></div>",
    unsafe_allow_html=True,
)

# Filtro por Data
st.subheader("📅 SELECIONE O FILTRO DE DATA DE JOGOS:")
opcao_filtro = st.radio(
    "Filtrar partidas por período:",
    options=[
        "🌟 Todos os Próximos Jogos",
        "🔴 Jogos de Hoje (Restantes)",
        "🟡 Jogos de Amanhã",
        "🔵 Jogos de Depois de Amanhã em Diante",
    ],
    horizontal=True,
)

btn_buscar = st.button("🔍 GERAR ANÁLISES COM O FILTRO SELECIONADO", use_container_width=True)


def buscar_jogos_futuros():
    jogos_brutos = []
    ids_processados = set()

    for liga_key in LIGAS_FUTEBOL:
        url = f"https://api.the-odds-api.com/v4/sports/{liga_key}/odds/?apiKey={THE_ODDS_API_KEY}&regions=eu,us&markets=h2h,totals"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                dados = res.json()
                if isinstance(dados, list):
                    for jogo in dados:
                        jogo_id = jogo.get("id")
                        if jogo_id not in ids_processados:
                            ids_processados.add(jogo_id)
                            jogos_brutos.append(jogo)
        except Exception:
            continue

    if not jogos_brutos:
        url_fallback = f"https://api.the-odds-api.com/v4/sports/upcoming/odds/?apiKey={THE_ODDS_API_KEY}&regions=eu,us&markets=h2h,totals"
        try:
            res = requests.get(url_fallback, timeout=8)
            if res.status_code == 200:
                dados = res.json()
                if isinstance(dados, list):
                    for jogo in dados:
                        if "soccer" in jogo.get("sport_key", ""):
                            jogos_brutos.append(jogo)
        except Exception:
            pass

    return jogos_brutos


if btn_buscar:
    with st.spinner("Buscando partidas de acordo com o filtro selecionado..."):
        jogos_raw = buscar_jogos_futuros()

    if not jogos_raw:
        st.warning("Nenhum evento futuro encontrado nas ligas monitoradas.")
    else:
        jogos_processados = []
        agora_utc = datetime.now(timezone.utc)
        hoje_local = (agora_utc - timedelta(hours=3)).date()
        amanha_local = hoje_local + timedelta(days=1)

        for item in jogos_raw:
            data_raw = item.get("commence_time", "")
            if not data_raw:
                continue

            try:
                dt_utc = datetime.strptime(data_raw, "%Y-%m-%dT%H:%M:%SZ").replace(
                    tzinfo=timezone.utc
                )
                
                # GARANTIA: Ignora partidas que já iniciaram
                if dt_utc <= agora_utc:
                    continue

                dt_local = dt_utc - timedelta(hours=3)  # Fuso de Brasília
                data_jogo = dt_local.date()

                # --- APLICAÇÃO DO FILTRO SOLICITADO ---
                if "Hoje" in opcao_filtro and data_jogo != hoje_local:
                    continue
                elif "Amanhã" in opcao_filtro and "Depois" not in opcao_filtro and data_jogo != amanha_local:
                    continue
                elif "Depois de Amanhã" in opcao_filtro and data_jogo <= amanha_local:
                    continue

                # Rótulo Visual de Data
                if data_jogo == hoje_local:
                    rotulo_data = f"HOJE às {dt_local.strftime('%H:%M')}"
                elif data_jogo == amanha_local:
                    rotulo_data = f"AMANHÃ às {dt_local.strftime('%H:%M')}"
                else:
                    rotulo_data = dt_local.strftime("%d/%m às %H:%M")

            except Exception:
                continue

            time_casa = item.get("home_team", "Mandante")
            time_fora = item.get("away_team", "Visitante")
            liga = item.get("sport_title", "Futebol Global")

            odd_casa, odd_empate, odd_fora = "N/A", "N/A", "N/A"
            odd_over25, odd_under25 = "N/A", "N/A"

            if item.get("bookmakers"):
                bookmaker = item["bookmakers"][0]
                for market in bookmaker.get("markets", []):
                    if market["key"] == "h2h":
                        for out in market.get("outcomes", []):
                            if out["name"] == time_casa:
                                odd_casa = out["price"]
                            elif out["name"] == time_fora:
                                odd_fora = out["price"]
                            elif out["name"].lower() in ["draw", "empate"]:
                                odd_empate = out["price"]
                    elif market["key"] == "totals":
                        for out in market.get("outcomes", []):
                            if out.get("point") == 2.5:
                                if out["name"].lower() == "over":
                                    odd_over25 = out["price"]
                                elif out["name"].lower() == "under":
                                    odd_under25 = out["price"]

            if odd_casa == "N/A" or odd_fora == "N/A":
                continue

            c, f = float(odd_casa), float(odd_fora)

            if c <= 1.65:
                dica_alta = f"Vitória do {time_casa} (Odd @{odd_casa})"
                odd_alta_val = c
                dica_media = "Over 1.5 Gols (Odd @1.32)"
                dica_baixa = f"Vitória do {time_casa} + Over 2.5 Gols (Odd @{round(c * 1.5, 2)})"
            elif f <= 1.65:
                dica_alta = f"Vitória do {time_fora} (Odd @{odd_fora})"
                odd_alta_val = f
                dica_media = "Over 1.5 Gols (Odd @1.32)"
                dica_baixa = f"Vitória do {time_fora} + Over 2.5 Gols (Odd @{round(f * 1.5, 2)})"
            else:
                odd_dc = round(c * 0.72, 2) if c < f else round(f * 0.72, 2)
                equipe_dc = time_casa if c < f else time_fora
                dica_alta = f"Dupla Chance {equipe_dc} ou Empate (Odd @{odd_dc})"
                odd_alta_val = odd_dc
                dica_media = (
                    f"Over 2.5 Gols (Odd @{odd_over25})"
                    if odd_over25 != "N/A"
                    else "Over 1.5 Gols (Odd @1.35)"
                )
                dica_baixa = f"Empate Anula: {time_casa} (Odd @{round(c * 0.85, 2)})"

            analise = {
                "odd_casa": odd_casa,
                "odd_empate": odd_empate,
                "odd_fora": odd_fora,
                "odd_over25": odd_over25,
                "odd_under25": odd_under25,
                "est_cantos": (
                    "Over 9.5 Escanteios"
                    if (c < 2.1 or f < 2.1)
                    else "Over 8.5 Escanteios"
                ),
                "est_chutes": (
                    "Over 8.5 Chutes no Gol"
                    if (c < 1.75 or f < 1.75)
                    else "Over 7.5 Chutes no Gol"
                ),
                "est_cartoes": (
                    "Over 4.5 Cartões Amarelos"
                    if (c < 2.2 and f < 2.2)
                    else "Under 4.5 Cartões Amarelos"
                ),
                "dica_alta": dica_alta,
                "dica_media": dica_media,
                "dica_baixa": dica_baixa,
                "odd_alta_val": odd_alta_val,
            }

            info = {
                "liga": liga,
                "casa": time_casa,
                "fora": time_fora,
                "data_hora": rotulo_data,
                "dt_utc": dt_utc,
            }
            jogos_processados.append((info, analise))

        # Ordena cronologicamente
        jogos_processados.sort(key=lambda x: x[0]["dt_utc"])

        if not jogos_processados:
            st.warning(f"Nenhum jogo pré-partida encontrado para o filtro: '{opcao_filtro}'.")
        else:
            st.success(f"✅ {len(jogos_processados)} partidas encontradas para '{opcao_filtro}'!")

            for info, analise in jogos_processados:
                with st.container():
                    st.markdown(
                        f"""
                    <div class="card-jogo">
                        <div class="liga-title">🏆 {info['liga'].upper()} | 📅 {info['data_hora']}</div>
                        <div class="confronto-title">{info['casa']} VS {info['fora']}</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    with st.expander("VER ANÁLISE COMPLETA ▼"):
                        st.write(
                            f"💰 **Odds 1X2:** Casa: @{analise['odd_casa']} | Empate: @{analise['odd_empate']} | Fora: @{analise['odd_fora']}"
                        )
                        st.write(
                            f"📈 **Gols (Over/Under 2.5):** Over 2.5: @{analise['odd_over25']} | Under 2.5: @{analise['odd_under25']}"
                        )
                        st.write(f"🚩 **Escanteios:** {analise['est_cantos']}")
                        st.write(f"🎯 **Finalizações no Gol:** {analise['est_chutes']}")
                        st.write(f"🟨 **Cartões:** {analise['est_cartoes']}")

                        st.markdown("---")
                        st.markdown("**🎯 INDICAÇÕES DE APOSTA:**")

                        st.markdown(
                            f"<span class='badge-alta'>🟢 CONFIANÇA ALTA</span> {analise['dica_alta']}",
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f"<span class='badge-media'>🟡 CONFIANÇA MÉDIA</span> {analise['dica_media']}",
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f"<span class='badge-baixa'>🔴 CONFIANÇA BAIXA</span> {analise['dica_baixa']}",
                            unsafe_allow_html=True,
                        )
                        st.write("")

            # BILHETES PRONTOS
            if len(jogos_processados) >= 2:
                st.markdown("---")
                st.subheader("🔥 BILHETES PRONTOS RECOMENDADOS 🔥")

                duplas = []
                jogos_usados = set()

                for i in range(len(jogos_processados)):
                    if i in jogos_usados:
                        continue
                    for j in range(i + 1, len(jogos_processados)):
                        if j in jogos_usados:
                            continue

                        j1_info, j1_an = jogos_processados[i]
                        j2_info, j2_an = jogos_processados[j]
                        odd_comb = round(
                            j1_an["odd_alta_val"] * j2_an["odd_alta_val"], 2
                        )

                        if 1.70 <= odd_comb <= 2.50:
                            duplas.append(
                                (j1_info, j1_an, j2_info, j2_an, odd_comb)
                            )
                            jogos_usados.add(i)
                            jogos_usados.add(j)
                            break
                    if len(duplas) == 3:
                        break

                for idx, (
                    j1_info,
                    j1_an,
                    j2_info,
                    j2_an,
                    odd_total,
                ) in enumerate(duplas, start=1):
                    st.info(
                        f"**🔹 DUPLA {idx} — ODD TOTAL: @{odd_total}**\n\n"
                        f"• [{j1_info['data_hora']}] {j1_info['casa']} vs {j1_info['fora']} ➔ {j1_an['dica_alta']}\n\n"
                        f"• [{j2_info['data_hora']}] {j2_info['casa']} vs {j2_info['fora']} ➔ {j2_an['dica_alta']}"
                    )
