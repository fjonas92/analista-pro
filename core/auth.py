"""Tela de acesso restrito por chave de licença."""
import streamlit as st
from core.config import LICENCAS_VALIDAS


def exigir_login():
    """Bloqueia a tela até o usuário digitar uma licença válida.
    Interrompe a execução do script (st.stop()) enquanto não autenticado."""
    if st.session_state["autenticado"]:
        return

    st.title("🔒 Analisador Pro — Acesso Restrito")
    chave_input = st.text_input("Insira sua licença:", type="password")
    if st.button("ACESSAR PLATAFORMA"):
        if chave_input.strip() in LICENCAS_VALIDAS:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Chave de acesso inválida.")
    st.stop()
