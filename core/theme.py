"""CSS dos dois temas visuais do app (Escuro / Claro)."""
import streamlit as st

_CSS_BASE = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    #MainMenu, header, footer, [data-testid="stToolbar"], [data-testid="stHeader"] {{ visibility: hidden !important; display: none !important; }}

    .stApp {{ background-color: {bg}; color: {fg}; }}
    .opp-box {{
        background-color: {box_bg};
        border: 1px solid {box_border};
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        {box_shadow}
    }}
    .opp-title {{ font-size: 13px; font-weight: 700; color: {accent}; margin-bottom: 8px; }}
    .opp-odd {{ font-size: 14px; font-weight: 800; color: {fg}; }}
    .badge-alta {{ font-size: 11px; font-weight: 700; background: {alta_bg}; color: {alta_fg}; padding: 2px 8px; border-radius: 4px; border: 1px solid {alta_border}; }}
    .badge-media {{ font-size: 11px; font-weight: 700; background: {media_bg}; color: {media_fg}; padding: 2px 8px; border-radius: 4px; border: 1px solid {media_border}; }}
    .badge-baixa {{ font-size: 11px; font-weight: 700; background: {baixa_bg}; color: {baixa_fg}; padding: 2px 8px; border-radius: 4px; border: 1px solid {baixa_border}; }}
    .badge-indisponivel {{ font-size: 11px; font-weight: 700; background: {indisp_bg}; color: {indisp_fg}; padding: 2px 8px; border-radius: 4px; border: 1px solid {indisp_border}; }}

    .analysis-card {{ border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; border-left: 4px solid; }}
    .analysis-alta {{ background-color: {an_alta_bg}; border-color: {accent}; }}
    .analysis-media {{ background-color: {an_media_bg}; border-color: {media_fg}; }}
    .analysis-baixa {{ background-color: {an_baixa_bg}; border-color: {baixa_fg}; }}
    .analysis-header {{ font-size: 14px; font-weight: 700; color: {fg}; margin-bottom: 8px; }}
    .analysis-list {{ margin: 0; padding-left: 18px; font-size: 13px; color: {list_fg}; line-height: 1.6; }}
"""

_TEMA_ESCURO = dict(
    bg="#0e1726", fg="#f8fafc", box_bg="#1a2234", box_border="#28354d", box_shadow="",
    accent="#38bdf8",
    alta_bg="rgba(34, 197, 94, 0.15)", alta_fg="#4ade80", alta_border="rgba(34, 197, 94, 0.3)",
    media_bg="rgba(234, 179, 8, 0.15)", media_fg="#facc15", media_border="rgba(234, 179, 8, 0.3)",
    baixa_bg="rgba(239, 68, 68, 0.15)", baixa_fg="#f87171", baixa_border="rgba(239, 68, 68, 0.3)",
    indisp_bg="rgba(148, 163, 184, 0.15)", indisp_fg="#94a3b8", indisp_border="rgba(148, 163, 184, 0.3)",
    an_alta_bg="rgba(14, 116, 144, 0.15)", an_media_bg="rgba(161, 98, 7, 0.15)", an_baixa_bg="rgba(153, 27, 27, 0.15)",
    list_fg="#cbd5e1",
)

_TEMA_CLARO = dict(
    bg="#f8fafc", fg="#0f172a", box_bg="#ffffff", box_border="#cbd5e1",
    box_shadow="box-shadow: 0 1px 3px rgba(0,0,0,0.05);",
    accent="#0284c7",
    alta_bg="#dcfce7", alta_fg="#15803d", alta_border="#86efac",
    media_bg="#fef9c3", media_fg="#a16207", media_border="#fde047",
    baixa_bg="#fee2e2", baixa_fg="#b91c1c", baixa_border="#fca5a5",
    indisp_bg="#e2e8f0", indisp_fg="#475569", indisp_border="#cbd5e1",
    an_alta_bg="#f0f9ff", an_media_bg="#fefce8", an_baixa_bg="#fef2f2",
    list_fg="#334155",
)


def aplicar_tema():
    """Injeta o CSS do tema atualmente selecionado em st.session_state['tema']."""
    valores = _TEMA_ESCURO if st.session_state["tema"] == "Escuro 🌙" else _TEMA_CLARO
    css = "<style>" + _CSS_BASE.format(**valores) + "</style>"
    st.markdown(css, unsafe_allow_html=True)


def seletor_tema(container):
    """Desenha o rádio de troca de tema dentro do container (coluna) passado."""
    with container:
        novo_tema = st.radio(
            "Aparência:",
            ["Escuro 🌙", "Claro ☀️"],
            index=0 if st.session_state["tema"] == "Escuro 🌙" else 1,
            horizontal=True
        )
        if novo_tema != st.session_state["tema"]:
            st.session_state["tema"] = novo_tema
            st.rerun()
