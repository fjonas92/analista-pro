"""
Motor de decisão: transforma os dados brutos (stats dos dois times +
odds, quando existirem) nas 4 dicas mostradas em cada card de jogo.

Este módulo não faz nenhuma chamada de rede — isso é responsabilidade
de core/api_client.py. Aqui só existe lógica de decisão.
"""
from core.api_client import buscar_dados_partida_paralelo
from core.config import registrar_erro_api


def fmt_odd(v):
    """Formata uma odd para exibição, ou 'N/D' quando não há valor real."""
    return f"{v:.2f}" if v is not None else "N/D"


def processar_dados_partida(api_key, home_id, home_name, away_id, away_name, fixture_id):
    """Ponto de entrada usado pela UI: busca os dados (em paralelo) e
    devolve a lista de até 4 dicas, ou None se não houver dados
    suficientes dos dois times para uma análise honesta."""
    h, a, o, tem_odds_1x2, erro_odds = buscar_dados_partida_paralelo(
        api_key, home_id, away_id, fixture_id
    )

    # Registrar o erro aqui, já de volta na thread principal do Streamlit —
    # st.session_state não pode ser tocado de dentro do ThreadPoolExecutor.
    if erro_odds:
        registrar_erro_api("odds", {"errors": erro_odds}, 200)

    if h is None or a is None:
        return None  # sinaliza pra UI renderizar "dados insuficientes"

    return _montar_dicas(h, a, o, tem_odds_1x2, home_name, away_name)


def _montar_dicas(h, a, o, tem_odds_1x2, home_name, away_name):
    exp_gols_total = (h["media_gols_pro"] + a["media_gols_contra"] + a["media_gols_pro"] + h["media_gols_contra"]) / 2.0
    dicas = []

    if tem_odds_1x2:
        home_is_fav = o["home"] < o["away"]
        away_is_fav = o["away"] < o["home"]
    else:
        # Sem odds reais: usa aproveitamento recente como critério de
        # favoritismo, e nunca finge que existe uma odd de mercado.
        home_is_fav = h["aproveitamento"] > a["aproveitamento"] + 5
        away_is_fav = a["aproveitamento"] > h["aproveitamento"] + 5

    dicas.append(_dica_resultado(h, a, o, tem_odds_1x2, home_is_fav, away_is_fav, home_name, away_name))
    dicas.append(_dica_handicap_ou_seguranca(h, a, o, tem_odds_1x2, home_is_fav, away_is_fav, home_name, away_name))
    dicas.append(_dica_total_gols(h, a, o, tem_odds_1x2, exp_gols_total))
    dicas.append(_dica_ambas_marcam_ou_escanteios(h, a, o, tem_odds_1x2))

    return dicas[:4]


def _dica_resultado(h, a, o, tem_odds_1x2, home_is_fav, away_is_fav, home_name, away_name):
    if home_is_fav:
        conf = "Alta" if (tem_odds_1x2 and o["home"] <= 1.60) or (not tem_odds_1x2 and h["aproveitamento"] >= 65) else "Média"
        return {
            "titulo": f"Vitória — {home_name}",
            "odd": o["home"] if tem_odds_1x2 else None,
            "conf": conf, "tipo": "alta" if conf == "Alta" else "media",
            "topicos": [
                (f"<b>Favoritismo pelas casas:</b> Odd {fmt_odd(o['home'])} para o mandante." if tem_odds_1x2
                 else "<b>Odds indisponíveis</b> nesta consulta — favoritismo calculado por desempenho recente."),
                f"<b>Retrospecto Local:</b> {home_name} tem {h['aproveitamento']}% de aproveitamento em ({h['jogos']} jogos analisados).",
            ],
        }
    if away_is_fav:
        conf = "Alta" if (tem_odds_1x2 and o["away"] <= 1.60) or (not tem_odds_1x2 and a["aproveitamento"] >= 65) else "Média"
        return {
            "titulo": f"Vitória — {away_name}",
            "odd": o["away"] if tem_odds_1x2 else None,
            "conf": conf, "tipo": "alta" if conf == "Alta" else "media",
            "topicos": [
                (f"<b>Favoritismo pelas casas:</b> Odd {fmt_odd(o['away'])} para o visitante." if tem_odds_1x2
                 else "<b>Odds indisponíveis</b> nesta consulta — favoritismo calculado por desempenho recente."),
                f"<b>Desempenho Recente:</b> {away_name} tem {a['aproveitamento']}% de aproveitamento em ({a['jogos']} jogos analisados).",
            ],
        }
    fav_name = home_name if h["aproveitamento"] >= a["aproveitamento"] else away_name
    return {
        "titulo": f"{fav_name} — Empate Anula (DNB)",
        "odd": None, "conf": "Média", "tipo": "media",
        "topicos": [
            "<b>Equilíbrio Técnico:</b> nenhum lado com favoritismo claro nos dados disponíveis.",
            "Proteção de aposta com devolução integral em caso de empate.",
        ],
    }


def _dica_handicap_ou_seguranca(h, a, o, tem_odds_1x2, home_is_fav, away_is_fav, home_name, away_name):
    if tem_odds_1x2 and away_is_fav and o["away"] <= 1.65:
        return {
            "titulo": f"Handicap Asiático {away_name} (-1.0)",
            "odd": round(o["away"] * 1.45, 2), "conf": "Alta", "tipo": "alta",
            "topicos": [
                f"Projeção de vitória confortável do favorito visitante ({away_name}).",
                "Reembolso de aposta caso vença por apenas 1 gol de diferença.",
            ],
        }
    if tem_odds_1x2 and home_is_fav and o["home"] <= 1.65:
        return {
            "titulo": f"Handicap Asiático {home_name} (-1.0)",
            "odd": round(o["home"] * 1.45, 2), "conf": "Alta", "tipo": "alta",
            "topicos": [
                f"Projeção de domínio do mandante ({home_name}) em seus domínios.",
                "Devolução de aposta em caso de vitória por margem mínima.",
            ],
        }
    return {
        "titulo": "Mais de 1.5 Gols no Jogo",
        "odd": o.get("over15") if tem_odds_1x2 else None, "conf": "Alta", "tipo": "alta",
        "topicos": [
            "Linha de alta frequência estatística para partidas com forças emparelhadas.",
            f"Médias combinadas de gols recentes: {home_name} {h['media_gols_pro']} g/j, {away_name} {a['media_gols_pro']} g/j.",
        ],
    }


def _dica_total_gols(h, a, o, tem_odds_1x2, exp_gols_total):
    if exp_gols_total >= 2.6:
        return {
            "titulo": "Mais de 2.5 Gols",
            "odd": o.get("over25") if tem_odds_1x2 else None, "conf": "Média", "tipo": "media",
            "topicos": [
                f"<b>Expectativa de Gols:</b> média combinada projetada em {exp_gols_total:.2f} gols.",
                f"Ataque do mandante ({h['media_gols_pro']} g/j) e visitante ({a['media_gols_pro']} g/j) ativos.",
            ],
        }
    return {
        "titulo": "Menos de 2.5 Gols (Under)",
        "odd": o.get("under25") if tem_odds_1x2 else None, "conf": "Média", "tipo": "media",
        "topicos": [
            f"<b>Projeção Truncada:</b> média combinada estimada em apenas {exp_gols_total:.2f} gols.",
            "Defesas bem postadas nos jogos recentes analisados.",
        ],
    }


def _dica_ambas_marcam_ou_escanteios(h, a, o, tem_odds_1x2):
    if h["media_gols_pro"] >= 1.1 and a["media_gols_pro"] >= 1.1:
        return {
            "titulo": "Ambas as Equipes Marcam (SIM)",
            "odd": o.get("btts_yes") if tem_odds_1x2 else None, "conf": "Média", "tipo": "media",
            "topicos": [
                "Ambos os times balançaram as redes na maioria dos seus últimos jogos.",
                f"Mandante marca {h['media_gols_pro']} g/j e Visitante marca {a['media_gols_pro']} g/j.",
            ],
        }
    return {
        "titulo": "Mais de 8.5 Escanteios",
        "odd": None, "conf": "Baixa", "tipo": "baixa",
        "topicos": [
            "Estimativa por volume de jogo — sem dado direto de escanteios na fonte atual.",
            "Trate como mercado especulativo, confiança mais baixa que os demais.",
        ],
    }
