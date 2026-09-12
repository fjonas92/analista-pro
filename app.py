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

THE_ODDS_API_KEY = "e484810f517d8e428f3cbf3e89e2973b"

# Estilização CSS Personalizada
st.markdown(
    """
    <style>
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

# Cabeçalho Principal
st.markdown(
    "<div class='main-header'><h1>⚽ ANALISTA PRO</h1></div>",
    unsafe_allow_html=True,
)

# Mapeamento de Datas
dt_hoje = datetime.now()
dt_amanha = dt_hoje + timedelta(days=1)
dt_depois = dt_hoje + timedelta(days=2)

datas_map = {
    "Hoje": dt_hoje.strftime("%Y-%m-%d"),
    "Amanhã": dt_amanha.strftime("%Y-%m-%d"),
    "Depois de Amanhã": dt_depois.strftime("%Y-%m-%d"),
}

col_sel, col_btn = st.columns([1, 2])

with col_sel:
    opcao_dia = st.selectbox("Selecione o Dia:", list(datas_map.keys()))

with col_btn:
    st.write("")
    st.write("")
    btn_buscar = st.button("🔍 GERAR ANÁLISES E MONTAR BILHETES", use_container_width=True)


def carregar_jogos(data_alvo_str):
    url_main = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={THE_ODDS_API_KEY}&regions=eu&markets=h2h,totals"
    try:
        res = requests.get(url_main, timeout=12)
        if res.status_code != 200:
            return None, f"Erro na API: status {res.status_code}"
        return res.json(), None
    except Exception as e:
        return None, str(e)


if btn_buscar:
    data_alvo = datas_map[opcao_dia]

    with st.spinner("Conectando e buscando lista completa de jogos..."):
        jogos_raw, erro = carregar_jogos(data_alvo)

    if erro:
        st.error(f"⚠️ Erro de conexão: {erro}")
    elif not jogos_raw:
        st.warning(f"Nenhum jogo encontrado para {opcao_dia}.")
    else:
        agora_utc = datetime.now(timezone.utc)
        jogos_processados = []

        for item in jogos_raw:
            time_casa = item.get("home_team", "Mandante")
            time_fora = item.get("away_team", "Visitante")
            liga = item.get("sport_title", "Futebol")

            data_raw = item.get("commence_time", "")
            data_formatada = "Data N/A"
            data_jogo_local_str = ""

            try:
                dt_utc = datetime.strptime(
                    data_raw, "%Y-%m-%dT%H:%M:%SZ"
                ).replace(tzinfo=timezone.utc)
                if dt_utc <= agora_utc:
                    continue
                dt_local = dt_utc - timedelta(hours=3)
                data_formatada = dt_local.strftime("%d/%m - %H:%M")
                data_jogo_local_str = dt_local.strftime("%Y-%m-%d")
            except Exception:
                pass

            if (
                data_alvo
                and data_jogo_local_str
                and (data_jogo_local_str != data_alvo)
            ):
                continue

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
                            elif out["name"].lower() == "draw":
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
                dica_alta = (
                    f"Dupla Chance {equipe_dc} ou Empate (Odd @{odd_dc})"
                )
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
                "est_faltas": "22 a 27 Faltas Totais",
                "dica_alta": dica_alta,
                "dica_media": dica_media,
                "dica_baixa": dica_baixa,
                "odd_alta_val": odd_alta_val,
            }

            info = {
                "liga": liga,
                "casa": time_casa,
                "fora": time_fora,
                "data_hora": data_formatada,
            }
            jogos_processados.append((info, analise))

        if not jogos_processados:
            st.warning(
                f"Nenhum jogo pré-partida disponível para {opcao_dia}. As odds ainda não foram abertas."
            )
        else:
            st.success(
                f"✅ {len(jogos_processados)} jogos carregados com sucesso para {opcao_dia}!"
            )

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
                        st.write(
                            f"🚩 **Escanteios (Estimativa):** {analise['est_cantos']}"
                        )
                        st.write(
                            f"🎯 **Finalizações no Gol:** {analise['est_chutes']}"
                        )
                        st.write(
                            f"🟨 **Cartões (Estimativa):** {analise['est_cartoes']}"
                        )
                        st.write(
                            f"⚠️ **Faltas Cometidas:** {analise['est_faltas']}"
                        )

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

            # Seção de Bilhetes Prontos
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
                        f"• {j1_info['casa']} vs {j1_info['fora']} ➔ {j1_an['dica_alta']}\n\n"
                        f"• {j2_info['casa']} vs {j2_info['fora']} ➔ {j2_an['dica_alta']}"
                    )

                jogos_mult = sorted(
                    jogos_processados,
                    key=lambda x: x[1]["odd_alta_val"],
                    reverse=True,
                )
                mult_jogos = []
                odd_mult = 1.0

                for j_info, j_an in jogos_mult:
                    mult_jogos.append((j_info, j_an))
                    odd_mult *= j_an["odd_alta_val"]
                    if odd_mult >= 4.00 and len(mult_jogos) >= 3:
                        break

                if odd_mult >= 4.00 and len(mult_jogos) >= 3:
                    texto_mult = "\n\n".join(
                        [
                            f"• {ji['casa']} vs {ji['fora']} ➔ {ja['dica_alta']}"
                            for ji, ja in mult_jogos
                        ]
                    )
                    st.warning(
                        f"**🔥 MÚLTIPLA DO DIA — ODD TOTAL: @{round(odd_mult, 2)}**\n\n{texto_mult}"
                    )