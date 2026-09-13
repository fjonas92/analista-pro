"""Renderização visual: status/horário da partida e o card completo de cada jogo."""
from datetime import datetime, timedelta, timezone
import streamlit as st
from core.analysis import processar_dados_partida, fmt_odd


def extrair_status_e_horario(fix):
    status_short = fix.get("status", {}).get("short", "")
    elapsed = fix.get("status", {}).get("elapsed", 0)
    goals_home = fix.get("goals", {}).get("home")
    goals_away = fix.get("goals", {}).get("away")

    iso_date = fix.get("date", "")
    horario_str = ""
    if iso_date:
        try:
            dt_utc = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
            dt_br = dt_utc.astimezone(timezone(timedelta(hours=-3)))
            horario_str = dt_br.strftime("%H:%M")
        except Exception:
            horario_str = ""

    if status_short in ["1H", "2H", "ET", "P"]:
        status_label = f"🟢 Ao Vivo {elapsed}'"
        if goals_home is not None and goals_away is not None:
            status_label += f" ({goals_home}x{goals_away})"
    elif status_short == "HT":
        status_label = f"🟡 Intervalo ({goals_home}x{goals_away})"
    elif status_short in ["FT", "AET", "PEN"]:
        status_label = "✅ Encerrado"
        if goals_home is not None and goals_away is not None:
            status_label += f" ({goals_home}x{goals_away})"
    else:
        status_label = f"⏰ {horario_str}" if horario_str else "⏰ Não Iniciado"

    return status_label


def renderizar_card_jogo(api_key, item):
    """Desenha o card completo de uma partida: cabeçalho, grade de
    dicas e o embasamento estatístico de cada uma."""
    fix = item["fixture"]
    league = item["league"]
    home = item["teams"]["home"]
    away = item["teams"]["away"]

    status_str = extrair_status_e_horario(fix)

    oportunidades = processar_dados_partida(
        api_key, home["id"], home["name"], away["id"], away["name"], fix["id"]
    )

    with st.container(border=True):
        st.markdown(f"<h3 style='text-align: center; margin-bottom: 2px;'>{home['name']} x {away['name']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #fbbf24; font-size: 13px; font-weight: 600;'>🏆 {league['country']} {league['name']} &nbsp;•&nbsp; {status_str}</p>", unsafe_allow_html=True)

        if oportunidades is None:
            st.warning("⚠️ Dados históricos insuficientes para os dois times nesta consulta — pulando análise para não gerar dica genérica.")
            return

        _renderizar_grade_dicas(oportunidades)
        _renderizar_embasamento(oportunidades)


def _renderizar_grade_dicas(oportunidades):
    st.markdown("#### 🎯 Dicas de Alto Valor")
    cols = st.columns(len(oportunidades))
    for col, op in zip(cols, oportunidades):
        badge_class = f"badge-{op['tipo']}"
        odd_texto = fmt_odd(op["odd"])
        with col:
            st.markdown(f"""
            <div class="opp-box">
                <div class="opp-title">{op['titulo']}</div>
                <div>
                    <span class="opp-odd">Odd {odd_texto}</span>
                    <span class="{badge_class}">{op['conf']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)


def _renderizar_embasamento(oportunidades):
    st.markdown("#### 📋 Embasamento Estatístico")
    blocos_html = []
    for op in oportunidades:
        card_class = f"analysis-card analysis-{op['tipo']}"
        topicos_html = "".join(f"<li>{t}</li>" for t in op["topicos"])
        blocos_html.append(f"""
        <div class="{card_class}">
            <div class="analysis-header">{op['titulo']} — Confiança {op['conf']}</div>
            <ul class="analysis-list">
                {topicos_html}
            </ul>
        </div>
        """)
    # Renderiza tudo em um único st.markdown, em vez de um por dica —
    # menos chamadas de render, app mais responsivo.
    st.markdown("".join(blocos_html), unsafe_allow_html=True)
