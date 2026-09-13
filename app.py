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

# Estilização CSS White-Label Pro
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    [data-testid="stHeader"] {display: none;}
    
    .stApp { background-color: #121212; color: #FFFFFF; }
    .main-header { text-align: center; padding: 15px; background-color: #1A1A1A; border-radius: 8px; margin-bottom: 20px; }
    .card-jogo { background-color: #1E1E1E; border: 1px solid #0066FF; border-radius: 8px; padding: 15px; margin-bottom: 12px; }
    .liga-title { color: #0066FF; font-weight: bold; font-size: 0.85em; }
    .confronto-title { color: #FFFFFF; font-weight: bold; font-size: 1.25em; margin-bottom: 8px; }
    .badge-valor { background-color: #1E2A1E; color: #00FF66; border: 1px solid #00FF66; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8em; }
    .badge-nobet { background-color: #2A1E1E; color: #FF4444; border: 1px solid #FF4444; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8em; }
    .analise-box { background-color: #161616; border-left: 3px solid #0066FF; padding: 12px; margin-top: 8px; margin-bottom: 12px; font-size: 0.88em; color: #DDDDDD; }
    .metric-container { display: flex; justify-content: space-between; background-color: #222222; padding: 10px; border-radius: 6px; margin-bottom: 10px; font-size: 0.85em; }
    .risk-box { background-color: #221A1A; border-left: 3px solid #FF4444; padding: 8px 12px; margin-top: 6px; font-size: 0.85em; color: #FFAAAA; }
    </style>
""",
    unsafe_allow_html=True,
)

API_FOOTBALL_KEY = st.secrets.get("API_FOOTBALL_KEY", "0d03200b5ee68704d96a72a1749aeca3")
LICENCAS_VALIDAS = ["PRO-FUTEBOL-2026", "VIP-ANALISTA-888", "CLIENTE-PRO-01", "ADMIN-MASTER-99"]

# Autenticação
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown("<div class='main-header'><h1>🔒 ANALISTA PRO — ENGINE QUANTITATIVO</h1></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        chave_input = st.text_input("Chave de Licença:", type="password", placeholder="Ex: PRO-FUTEBOL-2026")
        if st.button("🔑 ENTRAR NO SISTEMA", use_container_width=True):
            if chave_input.strip() in LICENCAS_VALIDAS:
                st.session_state["autenticadoSeu feedback foi um divisor de águas para a arquitetura. Ele resolve falhas conceituais graves de estatística aplicada a apostas que separaram sistemas amadores de motores operacionais quantitativos.

As refatorações para os **5 ajustes** e a inclusão das duas novas camadas chave no motor:

---

### Refatorações de Regras e Lógica Estatística

*   **1. Gols Esperados do Modelo ($\lambda$):** O termo xG fica restrito a APIs que fornecem dados de *shot location/quality*. O cálculo interno por forma, mando e histórico de gols marcados/sofridos passa a ser denominado **$\lambda$ do Modelo** ($\lambda_{home}$, $\lambda_{away}$).
*   **2. Penalização de Desfalques Limitada:** A lógica de descontar pontos fixos por jogador foi removida. O impacto agora é contínuo e limitado:
    $$\text{Impacto} = \text{Importância} \times \text{Minutos Esperados} \times \text{Posição} \times \text{Substituto}$$
    $$\text{Penalização Máxima} = \min(\sum \text{Impactos}, 15 \text{ pts})$$
*   **3. Ponderação Restrita do H2H:** O peso do *Head-to-Head* foi fixado em **3% a 5%** no cálculo da força dos times, exigindo uma amostragem mínima de 3 jogos nos últimos 24 meses.
*   **4. Motores Específicos por Mercado:** Fim da inferência por contexto geral. Escanteios, Cartões e *Shots on Target* (SOT) possuem distribuições próprias calculadas sobre médias cruzadas (ataque vs. defesa adversária):
    $$\lambda_{escanteios\_total} = (\text{Escanteios Pro Mandante} + \text{Escanteios Contra Visitante}) / 2 + \dots$$
*   **5. Pipeline de Decisão (Filtro Rígido):** A aposta só é autorizada se passar por todas as portas de segurança:
