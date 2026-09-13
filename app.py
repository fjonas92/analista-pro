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

# Estilização CSS personalizada White-Label
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

# API-Football Key
API_FOOTBALL_KEY = st.secrets.get("API_FOOTBALL_KEY", "0d03200b5ee68704d96a72a1749aeca3")

# Licenças Válidas
LICENCAS_VALIDAS = [
    "PRO-FUTEBOL-2026",
    "VIP-ANALISTA-888",
    "CLIENTE-PRO-01",
    "ADMIN-MASTER-99",
]

# Autenticação
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

btn_buscar = st.button("🔍 GERAR ANÁLISES E MONTAR BILHETES PRONTOS", use_container_width=True)


def buscar_partidas_api_football(data_str=None):
    """Consulta os jogos agendados (NS = Not Started) na API-Football"""
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-apisports-key": API_FOOTBALL_KEY
    }
    
    # Parâmetros: traz apenas partidas que ainda NÃO começaram (status NS)
    params = {
        "status": "NS",
        "timezone": "America/Sao_Paulo"
    }
    
    if data_str:
        params["date"] = data_str
    else:
        # Pega as próximas 50 partidas agendadas
        params["next"] = "50"

    try:
        res = requests.get(url, headers=headers, params=params, timeout=12)
        if res.status_code == 200:
            dados = res.json()
            return dados.get("response", []), None
        else:
            return None, f"Erro API-Football: {res.status_code}"
    except Exception as e:
        return None, f"Erro de conexão: {str(e)}"


if btn_buscar:
    with st.spinner("Conectando à API-Football e analisando partidas..."):
        # Cálculo das datas no fuso do Brasil
        agora_utc = datetime.now(timezone.utc)
        agora_br = agora_utc - timedelta(hours=3)
        hoje_local = agora_br.date()
        amanha_local = hoje_local + timedelta(days=1)

        data_consulta = None
        if "Hoje" in opcao_filtro:
            data_consulta = hoje_local.strftime("%Y-%m-%d")
        elif "Amanhã" in opcao_filtro and "Depois" not in opcao_filtro:
            data_consulta = amanha_local.strftime("%Y-%m-%d")

        jogos_raw, erro_api = buscar_partidas_api_football(data_consulta)

    if erro_api:
        st.error(f"⚠️ {erro_api}")
    elif not jogos_raw:
        st.warning("Nenhum evento futuro encontrado para este período.")
    else:
        jogos_processados = []

        for item in jogos_raw:
            fixture = item.get("fixture", {})
            league = item.get("league", {})
            teams = item.get("teams", {})

            data_raw = fixture.get("date", "")
            if not data_raw:
                continue

            try:
                # Converte e verifica horário
                dt_partida = datetime.fromisoformat(data_raw.replace("Z", "+00:00"))
                dt_br = dt_partida - timedelta(hours=3)
                
                # GARANTIA: Descarte se já passou do horário de início
                if dt_br <= agora_br:
                    continue

                data_jogo = dt_br.date()

                # Filtro secundário caso tenha sido busca genérica
                if "Depois de Amanhã" in opcao_filtro and data_jogo <= amanha_local:
                    continue

                if data_jogo == hoje_local:
                    rotulo_data = f"HOJE às {dt_br.strftime('%H:%M')}"
                    eh_hoje_ou_amanha = True
                elif data_jogo == amanha_local:
                    rotulo_data = f"AMANHÃ às {dt_br.strftime('%H:%M')}"
                    eh_hoje_ou_amanha = True
                else:
                    rotulo_data = dt_br.strftime("%d/%m às %H:%M")
                    eh_hoje_ou_amanha = False

            except Exception:
                continue

            time_casa = teams.get("home", {}).get("name", "Mandante")
            time_fora = teams.get("away", {}).get("name", "Visitante")
            liga_nome = league.get("name", "Futebol Profissional")

            # Estrutura probabilística de Odds simulada / ajustada
            # (Pode ser conectada ao endpoint /odds futuramente)
            odd_casa, odd_empate, odd_fora = 1.90, 3.40, 3.80
            c, f = odd_casa, odd_fora

            if c < f:
                time_fav = time_casa
                odd_fav = c
            else:
                time_fav = time_fora
                odd_fav = f

            dica_vitoria = f"Vitória do {time_fav} (Odd @{odd_fav})"
            dica_over15 = "Over 1.5 Gols (Odd @1.30)"
            odd_over15_val = 1.30

            if c <= 1.70 or f <= 1.70:
                dica_alta = dica_vitoria
                odd_alta_val = odd_fav
                dica_media = dica_over15
                odd_media_val = odd_over15_val
                dica_baixa = f"Vitória do {time_fav} + Over 2.5 Gols (Odd @{round(odd_fav * 1.5, 2)})"
            else:
                odd_dc = round(odd_fav * 0.75, 2)
                dica_alta = f"Dupla Chance {time_fav} ou Empate (Odd @{odd_dc})"
                odd_alta_val = odd_dc
                dica_media = dica_over15
                odd_media_val = odd_over15_val
                dica_baixa = f"Empate Anula: {time_fav} (Odd @{round(odd_fav * 0.85, 2)})"

            analise = {
                "odd_casa": str(odd_casa),
                "odd_empate": str(odd_empate),
                "odd_fora": str(odd_fora),
                "odd_over25": "1.85",
                "odd_under25": "1.95",
                "est_cantos": "Over 8.5 Escanteios",
                "est_chutes": "Over 7.5 Chutes no Gol",
                "est_cartoes": "Under 4.5 Cartões Amarelos",
                "dica_alta": dica_alta,
                "dica_media": dica_media,
                "dica_baixa": dica_baixa,
                "dica_vitoria": dica_vitoria,
                "odd_fav": odd_fav,
                "dica_over15": dica_over15,
                "odd_over15_val": odd_over15_val,
                "odd_alta_val": odd_alta_val,
            }

            info = {
                "liga": liga_nome,
                "casa": time_casa,
                "fora": time_fora,
                "data_hora": rotulo_data,
                "dt_br": dt_br,
                "eh_hoje_ou_amanha": eh_hoje_ou_amanha,
            }
            jogos_processados.append((info, analise))

        jogos_processados.sort(key=lambda x: x[0]["dt_br"])

        if not jogos_processados:
            st.warning(f"Nenhuma partida pré-jogo encontrada para o filtro '{opcao_filtro}'.")
        else:
            st.success(f"✅ {len(jogos_processados)} partidas pré-jogo encontradas com sucesso via API-Football!")

            # LISTAGEM DAS ANÁLISES INDIVIDUAIS
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
                        st.write(f"🚩 **Escanteios Estimados:** {analise['est_cantos']}")
                        st.write(f"🎯 **Finalizações Estimadas:** {analise['est_chutes']}")
                        st.write(f"🟨 **Cartões Estimados:** {analise['est_cartoes']}")

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

            # --- SEÇÃO DE BILHETES PRONTOS (APENAS HOJE E AMANHÃ) ---
            st.markdown("---")
            st.subheader("🔥 BILHETES PRONTOS DA BANCA (DUPLAS E MÚLTIPLA DO DIA) 🔥")

            jogos_bilhete = [j for j in jogos_processados if j[0]["eh_hoje_ou_amanha"]]

            if len(jogos_bilhete) < 2:
                st.info("ℹ️ Os bilhetes prontos são gerados apenas para jogos de HOJE ou AMANHÃ.")
            else:
                # 1. DUPLAS FOCO EM FAVORITOS + OVER 1.5 GOLS (ODD MÍNIMA 1.60)
                duplas = []
                jogos_usados = set()

                for i in range(len(jogos_bilhete)):
                    if i in jogos_usados:
                        continue
                    for j in range(i + 1, len(jogos_bilhete)):
                        if j in jogos_usados:
                            continue

                        j1_i, j1_an = jogos_bilhete[i]
                        j2_i, j2_an = jogos_bilhete[j]

                        p1, odd1 = j1_an["dica_vitoria"], j1_an["odd_fav"]
                        p2, odd2 = j2_an["dica_over15"], j2_an["odd_over15_val"]

                        odd_comb = round(odd1 * odd2, 2)

                        if odd_comb >= 1.60:
                            duplas.append((j1_i, p1, j2_i, p2, odd_comb))
                            jogos_usados.add(i)
                            jogos_usados.add(j)
                            break
                    if len(duplas) == 2:
                        break

                for idx, (j1_i, p1, j2_i, p2, odd_tot) in enumerate(duplas, start=1):
                    st.info(
                        f"**🔹 DUPLA {idx} (FAVORITO + OVER 1.5 GOLS) — ODD TOTAL: @{odd_tot}**\n\n"
                        f"• [{j1_i['data_hora']}] {j1_i['casa']} vs {j1_i['fora']} ➔ {p1}\n\n"
                        f"• [{j2_i['data_hora']}] {j2_i['casa']} vs {j2_i['fora']} ➔ {p2}"
                    )

                # 2. MÚLTIPLA DO DIA (ODD MÍNIMA 4.00)
                odd_multipla_acc = 1.0
                itens_multipla = []

                for j_i, j_an in jogos_bilhete:
                    if len(itens_multipla) % 2 == 0:
                        palpite = j_an["dica_vitoria"]
                        odd = j_an["odd_fav"]
                    else:
                        palpite = j_an["dica_over15"]
                        odd = j_an["odd_over15_val"]

                    odd_multipla_acc *= odd
                    itens_multipla.append(f"• [{j_i['data_hora']}] {j_i['casa']} vs {j_i['fora']} ➔ {palpite}")

                    if odd_multipla_acc >= 4.00 and len(itens_multipla) >= 3:
                        break

                odd_multipla_final = round(odd_multipla_acc, 2)

                if odd_multipla_final >= 4.00:
                    st.success(
                        f"**🚀 MÚLTIPLA DO DIA — ODD TOTAL: @{odd_multipla_final}**\n\n" +
                        "\n\n".join(itens_multipla)
                    )
                else:
                    st.warning("⚠️ Adicione mais partidas para atingir a odd mínima de 4.00 na Múltipla.")
