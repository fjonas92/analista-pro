"""
ANALISTA PRO — ponto de entrada do Streamlit.

Este arquivo só orquestra: cada responsabilidade real mora em core/.
    core/config.py    → chave da API, licenças, registro de erros
    core/auth.py      → tela de login por licença
    core/theme.py     → CSS dos temas escuro/claro
    core/api_client.py→ todas as chamadas HTTP pra API-Football
    core/analysis.py  → motor de decisão (as 4 dicas por jogo)
    core/ui.py        → renderização dos cards de partida
"""
from datetime import datetime, timedelta, timezone
import streamlit as st

from core.config import carregar_api_key, inicializar_estado, registrar_erro_api
from core.auth import exigir_login
from core.theme import aplicar_tema, seletor_tema
from core.api_client import api_get_fixtures
from core.ui import renderizar_card_jogo

MAX_JOGOS_EXIBIDOS = 15

st.set_page_config(
    page_title="Analisador Pro — IA",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inicializar_estado()
API_FOOTBALL_KEY = carregar_api_key()
exigir_login()
aplicar_tema()

# --- Cabeçalho -------------------------------------------------------
col_h1, col_h2, col_h3 = st.columns([1, 2, 1])
seletor_tema(col_h3)

with col_h2:
    try:
        st.image("logo.png", use_container_width=True)
    except Exception:
        cor_titulo = "#38bdf8" if st.session_state["tema"] == "Escuro 🌙" else "#0284c7"
        st.markdown(f"<h1 style='text-align: center; color: {cor_titulo}; margin-bottom: 20px;'>⚽ ANALISTA PRO</h1>", unsafe_allow_html=True)

# --- Filtros de data e liga -------------------------------------------
now_utc = datetime.now(timezone.utc)
agora_br = now_utc - timedelta(hours=3)

col_f1, col_f2 = st.columns([1, 2])
with col_f1:
    opcao_filtro = st.radio("Selecione a data:", ["🔴 Jogos de Hoje", "🟡 Jogos de Amanhã"], horizontal=True)

data_alvo_str = (
    agora_br.strftime("%Y-%m-%d")
    if "Hoje" in opcao_filtro
    else (agora_br + timedelta(days=1)).strftime("%Y-%m-%d")
)

partidas_brutas, erro_fixtures = api_get_fixtures(API_FOOTBALL_KEY, data_alvo_str)
if erro_fixtures:
    registrar_erro_api("fixtures", {"errors": erro_fixtures}, 200)

partidas_validas_dia = [
    item for item in partidas_brutas
    if item.get("fixture", {}).get("status", {}).get("short") != "CANC"
]

# Painel de diagnóstico: mostra erros reais da API em vez de escondê-los
if st.session_state["api_erros"]:
    with st.expander("⚠️ Avisos da API (clique para ver detalhes)", expanded=False):
        for msg in st.session_state["api_erros"]:
            st.write(f"- {msg}")

ligas_do_dia = sorted({
    f"{item['league'].get('country', '')}: {item['league'].get('name', '')}".strip(": ")
    for item in partidas_validas_dia
})

with col_f2:
    ligas_selecionadas = st.multiselect(
        "Filtrar Ligas Disponíveis no Dia:",
        options=ligas_do_dia,
        placeholder="Todas as ligas com jogos hoje/amanhã",
    )

st.button("🔍 CARREGAR PROGNÓSTICOS DA IA", use_container_width=True)

if ligas_selecionadas:
    partidas_filtradas = [
        item for item in partidas_validas_dia
        if f"{item['league'].get('country', '')}: {item['league'].get('name', '')}".strip(": ") in ligas_selecionadas
    ]
else:
    partidas_filtradas = partidas_validas_dia

# --- Exibição das partidas --------------------------------------------
if not partidas_filtradas:
    st.warning("⚠️ Nenhum jogo encontrado para a data selecionada.")
else:
    for item in partidas_filtradas[:MAX_JOGOS_EXIBIDOS]:
        renderizar_card_jogo(API_FOOTBALL_KEY, item)
