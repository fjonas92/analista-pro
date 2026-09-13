"""
Configuração central do app: chave da API, licenças válidas e o
registro de erros que a API devolve (pra nunca mais mascarar falha
com dado inventado).
"""
import streamlit as st

LICENCAS_VALIDAS = ["PRO-FUTEBOL-2026", "VIP-ANALISTA-888", "CLIENTE-PRO-01", "ADMIN-MASTER-99"]


def carregar_api_key():
    """Lê a chave da API-Football de st.secrets. Nunca deixar a chave
    escrita no código-fonte — configure em .streamlit/secrets.toml:
        API_FOOTBALL_KEY = "sua_chave_aqui"
    """
    api_key = st.secrets.get("API_FOOTBALL_KEY")
    if not api_key:
        st.error("⚠️ API_FOOTBALL_KEY não configurada em st.secrets. Adicione em .streamlit/secrets.toml e reinicie o app.")
        st.stop()
    return api_key


def inicializar_estado():
    """Garante que as chaves de session_state usadas pelo app existam
    antes de qualquer tela ser desenhada."""
    if "api_erros" not in st.session_state:
        st.session_state["api_erros"] = []
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    if "tema" not in st.session_state:
        st.session_state["tema"] = "Escuro 🌙"


def registrar_erro_api(origem, resp_json, status_code):
    """Guarda qualquer erro/aviso real vindo da API para exibir ao
    usuário, em vez de deixar a exceção sumir silenciosamente.

    IMPORTANTE: só pode ser chamada a partir da thread principal do
    Streamlit. Funções que rodam dentro de um ThreadPoolExecutor devem
    retornar a mensagem de erro e deixar quem chamou (na thread
    principal) registrar aqui.
    """
    erros = resp_json.get("errors") if isinstance(resp_json, dict) else None
    if erros:
        msg = f"[{origem}] {erros}"
        if msg not in st.session_state["api_erros"]:
            st.session_state["api_erros"].append(msg)
    if status_code != 200:
        msg = f"[{origem}] HTTP {status_code}"
        if msg not in st.session_state["api_erros"]:
            st.session_state["api_erros"].append(msg)
