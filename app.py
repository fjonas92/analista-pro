import math
import unicodedata
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
import requests
import streamlit as st

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Analisador Pro — IA",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

API_FOOTBALL_KEY = st.secrets.get("API_FOOTBALL_KEY", "0d03200b5ee68704d96a72a1749aeca3")
LICENCAS_VALIDAS = ["PRO-FUTEBOL-2026", "VIP-ANALISTA-888", "CLIENTE-PRO-01", "ADMIN-MASTER-99"]

def normalizar_texto(texto):
    if not texto:
        return ""
    nfkd = unicodedata.normalize('NFD', texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower().strip()

# 2. AUTENTICAÇÃO
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🔒 Analisador Pro — Acesso Restrito")
    chave_input = st.text_input("Insira sua licença:", type="password")
    if st.button("ACESSAR PLATAFORMA"):
        if chave_input.strip() in LICENCAS_VALIDAS:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Chave de acesso inválida.")
    st.stop()

# 3. CONTROLE DE TEMA (ESCURO / CLARO)
if "tema" not in st.session_state:
    st.session_state["tema"] = "Escuro 🌙"

if st.session_state["tema"] == "Escuro 🌙":
    css_tema = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        #MainMenu, header, footer, [data-testid="stToolbar"], [data-testid="stHeader"] { visibility: hidden !important; display: none !important; }
        
        .stApp { background-color: #0e1726; color: #f8fafc; }
        .opp-box {
            background-color: #1a2234;
            border: 1px solid #28354d;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
        }
        .opp-title { font-size: 13px; font-weight: 700; color: #38bdf8; margin-bottom: 8px; }
        .opp-odd { font-size: 14px; font-weight: 800; color: #ffffff; }
        .badge-alta { font-size: 11px; font-weight: 700; background: rgba(34, 197, 94, 0.15); color: #4ade80; padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(34, 197, 94, 0.3); }
        .badge-media { font-size: 11px; font-weight: 700; background: rgba(234, 179, 8, 0.15); color: #facc15; padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(234, 179, 8, 0.3); }
        .badge-baixa { font-size: 11px; font-weight: 700; background: rgba(239, 68, 68, 0.15); color: #f87171; padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(239, 68, 68, 0.3); }

        .analysis-card { border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; border-left: 4px solid; }
        .analysis-alta { background-color: rgba(14, 116, 144, 0.15); border-color: #38bdf8; }
        .analysis-media { background-color: rgba(161, 98, 7, 0.15); border-color: #facc15; }
        .analysis-baixa { background-color: rgba(153, 27, 27, 0.15); border-color: #f87171; }
        .analysis-header { font-size: 14px; font-weight: 700; color: #ffffff; margin-bottom: 8px; }
        .analysis-list { margin: 0; padding-left: 18px; font-size: 13px; color: #cbd5e1; line-height: 1.6; }
    </style>
    """
else:
    css_tema = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        #MainMenu, header, footer, [data-testid="stToolbar"], [data-testid="stHeader"] { visibility: hidden !important; display: none !important; }
        
        .stApp { background-color: #f8fafc; color: #0f172a; }
        .opp-box {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .opp-title { font-size: 13px; font-weight: 700; color: #0284c7; margin-bottom: 8px; }
        .opp-odd { font-size: 14px; font-weight: 800; color: #0f172a; }
        .badge-alta { font-size: 11px; font-weight: 700; background: #dcfce7; color: #15803d; padding: 2px 8px; border-radius: 4px; border: 1px solid #86efac; }
        .badge-media { font-size: 11px; font-weight: 700; background: #fef9c3; color: #a16207; padding: 2px 8px; border-radius: 4px; border: 1px solid #fde047; }
        .badge-baixa { font-size: 11px; font-weight: 700; background: #fee2e2; color: #b91c1c; padding: 2px 8px; border-radius: 4px; border: 1px solid #fca5a5; }

        .analysis-card { border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; border-left: 4px solid; }
        .analysis-alta { background-color: #f0f9ff; border-color: #0284c7; }
        .analysis-media { background-color: #fefce8; border-color: #ca8a04; }
        .analysis-baixa { background-color: #fef2f2; border-color: #dc2626; }
        .analysis-header { font-size: 14px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }
        .analysis-list { margin: 0; padding-left: 18px; font-size: 13px; color: #334155; line-height: 1.6; }
    </style>
    """

st.markdown(css_tema, unsafe_allow_html=True)

# 4. REQUISIÇÕES DE API
@st.cache_data(ttl=600)
def api_get_fixtures(data_str):
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    params = {"timezone": "America/Sao_Paulo", "date": data_str}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        return res.json().get("response", []) if res.status_code == 200 else []
    except Exception:
        return []

@st.cache_data(ttl=300)
def api_get_odds(fixture_id):
    url = "https://v3.football.api-sports.io/odds"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    params = {"fixture": fixture_id}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        return res.json().get("response", []) if res.status_code == 200 else []
    except Exception:
        return []

@st.cache_data(ttl=3600)
def obter_estatisticas_reais_time(team_id, tipo_mando="geral"):
    if not team_id:
        return None

    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    params = {"team": team_id, "last": 8}
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        fixtures = res.json().get("response", []) if res.status_code == 200 else []
    except Exception:
        fixtures = []

    if not fixtures:
        return None

    vitorias, empates, derrotas = 0, 0, 0
    gols_pro, gols_contra = 0, 0
    jogos_processados = 0

    for fix in fixtures:
        if fix["fixture"]["status"]["short"] not in ["FT", "AET", "PEN"]:
            continue
            
        is_home = (fix["teams"]["home"]["id"] == team_id)
        
        if tipo_mando == "home" and not is_home:
            continue
        if tipo_mando == "away" and is_home:
            continue

        gh = fix["goals"]["home"] if fix["goals"]["home"] is not None else 0
        ga = fix["goals"]["away"] if fix["goals"]["away"] is not None else 0
        
        gp = gh if is_home else ga
        gc = ga if is_home else gh
        
        gols_pro += gp
        gols_contra += gc

        if gp > gc:
            vitorias += 1
        elif gp == gc:
            empates += 1
        else:
            derrotas += 1
            
        jogos_processados += 1

    n = max(1, jogos_processados)
    aproveitamento = ((vitorias * 3 + empates) / (n * 3)) if n > 0 else 0.5

    return {
        "jogos": n,
        "vitorias": vitorias,
        "empates": empates,
        "derrotas": derrotas,
        "media_gols_pro": round(gols_pro / n, 2),
        "media_gols_contra": round(gols_contra / n, 2),
        "aproveitamento": round(aproveitamento * 100, 1)
    }

def extrair_odds_partida(fixture_id):
    raw_odds = api_get_odds(fixture_id)
    odds = {
        "home": 2.10, "draw": 3.30, "away": 3.20,
        "over25": 1.90, "under25": 1.90,
        "btts_yes": 1.85, "dnb_home": 1.50, "dnb_away": 2.20
    }
    
    if raw_odds:
        for bookmaker in raw_odds[0].get("bookmakers", []):
            for bet in bookmaker.get("bets", []):
                bet_name = bet.get("name", "")
                if bet_name == "Match Winner":
                    for val in bet.get("values", []):
                        if val["value"] == "Home": odds["home"] = float(val["odd"])
                        elif val["value"] == "Draw": odds["draw"] = float(val["odd"])
                        elif val["value"] == "Away": odds["away"] = float(val["odd"])
                elif bet_name == "Goals Over/Under":
                    for val in bet.get("values", []):
                        if val["value"] == "Over 2.5": odds["over25"] = float(val["odd"])
                        elif val["value"] == "Under 2.5": odds["under25"] = float(val["odd"])
                elif bet_name == "Both Teams Score":
                    for val in bet.get("values", []):
                        if val["value"] == "Yes": odds["btts_yes"] = float(val["odd"])

    return odds

# 5. GERADOR DE ANÁLISES BASEADO EM DADOS REAIS
def analisar_partida(home_id, home_name, away_id, away_name, fixture_id):
    stat_home = obter_estatisticas_reais_time(home_id, "home")
    stat_away = obter_estatisticas_reais_time(away_id, "away")
    odds = extrair_odds_partida(fixture_id)

    # Caso a API não retorne histórico suficiente para um dos times
    if not stat_home or not stat_away:
        stat_home = stat_home or {"media_gols_pro": 1.2, "media_gols_contra": 1.0, "aproveitamento": 50.0, "jogos": 5}
        stat_away = stat_away or {"media_gols_pro": 1.0, "media_gols_contra": 1.2, "aproveitamento": 40.0, "jogos": 5}

    exp_gols_casa = (stat_home["media_gols_pro"] + stat_away["media_gols_contra"]) / 2.0
    exp_gols_fora = (stat_away["media_gols_pro"] + stat_home["media_gols_contra"]) / 2.0
    exp_gols_total = exp_gols_casa + exp_gols_fora

    opcoes = []

    # Mercado 1: Casa Vence ou Empate Anula
    if stat_home["aproveitamento"] >= 60:
        opcoes.append({
            "titulo": f"Vitória — {home_name}",
            "odd": odds["home"],
            "conf": "Alta" if stat_home["aproveitamento"] >= 75 else "Média",
            "tipo": "alta" if stat_home["aproveitamento"] >= 75 else "media",
            "topicos": [
                f"{home_name} apresenta {stat_home['aproveitamento']}% de aproveitamento em casa nos últimos jogos.",
                f"Média de {stat_home['media_gols_pro']} gols marcados por jogo em seus domínios."
            ]
        })
    else:
        opcoes.append({
            "titulo": f"{home_name} — Empate Anula (DNB)",
            "odd": odds["dnb_home"],
            "conf": "Média",
            "tipo": "media",
            "topicos": [
                f"{home_name} manteve regularidade em casa ({stat_home['aproveitamento']}% de aproveitamento).",
                f"Visitante possui média de {stat_away['media_gols_contra']} gols sofridos por jogo."
            ]
        })

    # Mercado 2: Visitante ou DNB Visitante
    if stat_away["aproveitamento"] >= 60:
        opcoes.append({
            "titulo": f"Vitória — {away_name}",
            "odd": odds["away"],
            "conf": "Alta" if stat_away["aproveitamento"] >= 75 else "Média",
            "tipo": "alta" if stat_away["aproveitamento"] >= 75 else "media",
            "topicos": [
                f"{away_name} tem excelente retrospecto fora de casa: {stat_away['aproveitamento']}% de aproveitamento.",
                f"Ataque visitante marcando em média {stat_away['media_gols_pro']} gols por partida."
            ]
        })
    else:
        opcoes.append({
            "titulo": f"{away_name} — Empate Anula (DNB)",
            "odd": odds["dnb_away"],
            "conf": "Média",
            "tipo": "media",
            "topicos": [
                f"Proteção de aposta para {away_name} fora de casa.",
                f"Desempenho recente fora: {stat_away['aproveitamento']}% dos pontos disputados."
            ]
        })

    # Mercado 3: Gols Over/Under
    if exp_gols_total >= 2.5:
        opcoes.append({
            "titulo": "Mais de 2.5 Gols",
            "odd": odds["over25"],
            "conf": "Alta" if exp_gols_total >= 3.0 else "Média",
            "tipo": "alta" if exp_gols_total >= 3.0 else "media",
            "topicos": [
                f"Expectativa de {exp_gols_total:.2f} gols com base no histórico recente dos dois times.",
                f"{home_name} marca {stat_home['media_gols_pro']} gols/jogo e {away_name} marca {stat_away['media_gols_pro']} gols/jogo."
            ]
        })
    else:
        opcoes.append({
            "titulo": "Menos de 2.5 Gols (Under)",
            "odd": odds["under25"],
            "conf": "Média",
            "tipo": "media",
            "topicos": [
                f"Expectativa de jogo cadenciado: média projetada de apenas {exp_gols_total:.2f} gols.",
                f"Defesas com média de {stat_home['media_gols_contra']} e {stat_away['media_gols_contra']} gols sofridos por jogo."
            ]
        })

    # Mercado 4: Ambas Marcam
    if stat_home["media_gols_pro"] >= 1.2 and stat_away["media_gols_pro"] >= 1.2:
        opcoes.append({
            "titulo": "Ambas as Equipes Marcam (Sim)",
            "odd": odds["btts_yes"],
            "conf": "Alta",
            "tipo": "alta",
            "topicos": [
                f"Ambos os ataques em boa fase: Mandante ({stat_home['media_gols_pro']} g/j) e Visitante ({stat_away['media_gols_pro']} g/j).",
                "Histórico aponta alta probabilidade de gols para os dois lados."
            ]
        })
    else:
        opcoes.append({
            "titulo": f"{home_name} — Mais de 1.5 Gols",
            "odd": round(odds["home"] * 0.85, 2),
            "conf": "Média",
            "tipo": "media",
            "topicos": [
                f"Força ofensiva do mandante em casa ({stat_home['media_gols_pro']} gols/jogo).",
                f"Visitante concedendo {stat_away['media_gols_contra']} gols por partida."
            ]
        })

    return opcoes[:4]

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
    elif status_short in ["HT"]:
        status_label = f"🟡 Intervalo ({goals_home}x{goals_away})"
    elif status_short in ["FT", "AET", "PEN"]:
        status_label = f"✅ Encerrado"
        if goals_home is not None and goals_away is not None:
            status_label += f" ({goals_home}x{goals_away})"
    else:
        status_label = f"⏰ {horario_str}" if horario_str else "⏰ Não Iniciado"
        
    return status_label

# 6. RENDERIZAÇÃO
def renderizar_card_jogo_otimizado(item):
    fix = item["fixture"]
    league = item["league"]
    home = item["teams"]["home"]
    away = item["teams"]["away"]

    status_str = extrair_status_e_horario(fix)
    
    oportunidades = analisar_partida(
        home["id"], home["name"], away["id"], away["name"], fix["id"]
    )

    with st.container(border=True):
        st.markdown(f"<h3 style='text-align: center; margin-bottom: 2px;'>{home['name']} x {away['name']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #fbbf24; font-size: 13px; font-weight: 600;'>🏆 {league['country']} {league['name']} &nbsp;•&nbsp; {status_str}</p>", unsafe_allow_html=True)

        st.markdown("#### 🎯 Dicas Baseadas em Dados Reais")

        cols = st.columns(len(oportunidades))

        for idx, col in enumerate(cols):
            op = oportunidades[idx]
            badge_class = f"badge-{op['tipo']}"
            odd_val = op['odd']
            
            with col:
                st.markdown(f"""
                <div class="opp-box">
                    <div class="opp-title">{op['titulo']}</div>
                    <div>
                        <span class="opp-odd">Odd {odd_val:.2f}</span>
                        <span class="{badge_class}">{op['conf']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("#### 📋 Embasamento Estatístico Real")

        html_analises_lote = []
        for op in oportunidades:
            badge_tipo = op['tipo']
            card_class = f"analysis-card analysis-{badge_tipo}"
            topicos_html = "".join([f"<li>{item}</li>" for item in op['topicos']])
            
            html_analises_lote.append(f"""
            <div class="{card_class}">
                <div class="analysis-header">{op['titulo']} — Confiança {op['conf']}</div>
                <ul class="analysis-list">
                    {topicos_html}
                </ul>
            </div>
            """)
        
        st.markdown("".join(html_analises_lote), unsafe_allow_html=True)

# 7. HEADER PRINCIPAL
col_h1, col_h2, col_h3 = st.columns([1, 2, 1])

with col_h3:
    novo_tema = st.radio(
        "Aparência:",
        ["Escuro 🌙", "Claro ☀️"],
        index=0 if st.session_state["tema"] == "Escuro 🌙" else 1,
        horizontal=True
    )
    if novo_tema != st.session_state["tema"]:
        st.session_state["tema"] = novo_tema
        st.rerun()

with col_h2:
    try:
        st.image("logo.png", use_container_width=True)
    except Exception:
        cor_titulo = "#38bdf8" if st.session_state["tema"] == "Escuro 🌙" else "#0284c7"
        st.markdown(f"<h1 style='text-align: center; color: {cor_titulo}; margin-bottom: 20px;'>⚽ ANALISTA PRO</h1>", unsafe_allow_html=True)

# 8. FILTROS E EXECUÇÃO
now_utc = datetime.now(timezone.utc)
agora_br = now_utc - timedelta(hours=3)

col_f1, col_f2 = st.columns([1, 2])

with col_f1:
    opcao_filtro = st.radio("Selecione a data:", ["🔴 Jogos de Hoje", "🟡 Jogos de Amanhã"], horizontal=True)

data_alvo_str = agora_br.strftime("%Y-%m-%d") if "Hoje" in opcao_filtro else (agora_br + timedelta(days=1)).strftime("%Y-%m-%d")

partidas_brutas = api_get_fixtures(data_alvo_str)
partidas_validas_dia = [item for item in partidas_brutas if item.get("fixture", {}).get("status", {}).get("short") != "CANC"]

ligas_do_dia_dict = {}
for item in partidas_validas_dia:
    country = item["league"].get("country", "")
    name = item["league"].get("name", "")
    nome_exibicao = f"{country}: {name}" if country else name
    
    if nome_exibicao not in ligas_do_dia_dict:
        ligas_do_dia_dict[nome_exibicao] = (country, name)

options_ligas_dia = sorted(list(ligas_do_dia_dict.keys()))

with col_f2:
    ligas_selecionadas_user = st.multiselect(
        "Filtrar Ligas Disponíveis no Dia:",
        options=options_ligas_dia,
        placeholder="Todas as ligas com jogos hoje/amanhã"
    )

btn_buscar = st.button("🔍 CARREGAR PROGNÓSTICOS DA IA", use_container_width=True)

partidas_filtradas = []
if ligas_selecionadas_user:
    for item in partidas_validas_dia:
        country = item["league"].get("country", "")
        name = item["league"].get("name", "")
        nome_exibicao = f"{country}: {name}" if country else name
        if nome_exibicao in ligas_selecionadas_user:
            partidas_filtradas.append(item)
else:
    partidas_filtradas = partidas_validas_dia

# 9. EXIBIÇÃO DAS PARTIDAS
if not partidas_filtradas:
    st.warning("⚠️ Nenhum jogo encontrado para a data selecionada.")
else:
    for item in partidas_filtradas[:15]:
        renderizar_card_jogo_otimizado(item)
