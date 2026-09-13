import json
from quant_engine import QuantitativeEngine

# Dados simulados no formato JSON que simulam a resposta da API do Bet365/Match Data
JSON_MOCK_DATA = """
[
    {
        "status": "NS",
        "home_team": "Palmeiras",
        "away_team": "Santos",
        "home_recent_goals_scored": [2, 3, 1, 2, 4],
        "home_recent_goals_conceded": [0, 1, 0, 1, 0],
        "away_recent_goals_scored": [1, 0, 1, 2, 0],
        "away_recent_goals_conceded": [2, 1, 3, 1, 2],
        "odds_bet365": {
            "home_win": 1.45,
            "draw": 4.20,
            "away_win": 7.50,
            "over_15": 1.25,
            "over_25": 1.85,
            "btts_yes": 2.10
        }
    },
    {
        "status": "NS",
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "home_recent_goals_scored": [3, 2, 2, 1, 3],
        "home_recent_goals_conceded": [1, 0, 1, 2, 1],
        "away_recent_goals_scored": [2, 1, 3, 0, 2],
        "away_recent_goals_conceded": [1, 2, 2, 1, 1],
        "odds_bet365": {
            "home_win": 1.95,
            "draw": 3.60,
            "away_win": 3.80,
            "over_15": 1.22,
            "over_25": 1.70,
            "btts_yes": 1.65
        }
    },
    {
        "status": "NS",
        "home_team": "Real Madrid",
        "away_team": "Getafe",
        "home_recent_goals_scored": [4, 2, 3, 3, 1],
        "home_recent_goals_conceded": [1, 0, 1, 0, 0],
        "away_recent_goals_scored": [0, 1, 0, 0, 1],
        "away_recent_goals_conceded": [2, 2, 1, 3, 1],
        "odds_bet365": {
            "home_win": 1.28,
            "draw": 5.50,
            "away_win": 11.00,
            "over_15": 1.18,
            "over_25": 1.60,
            "btts_yes": 2.20
        }
    }
]
"""

def main():
    engine = QuantitativeEngine()
    fixtures = json.loads(JSON_MOCK_DATA)

    analyzed_matches = []
    all_ev_opportunities = []

    for fix in fixtures:
        result = engine.analyze_fixture(fix)
        if "error" not in result:
            analyzed_matches.append(result)
            all_ev_opportunities.extend(result["ev_opportunities"])

    # 1. RANKINGS DE MANDANTES E VISITANTES (Ordenados por menor Odd da Bet365)
    top_mandantes = sorted(analyzed_matches, key=lambda x: x["home_odd"])
    top_visitantes = sorted(analyzed_matches, key=lambda x: x["away_odd"])

    print("\n" + "=" * 60)
    print("🏆 TOP MANDANTES (Ordenados por favoritismo na Bet365)")
    print("=" * 60)
    for m in top_mandantes:
        print(f"- {m['match'].split(' x ')[0]}: Odd Vitória Bet365 @{m['home_odd']:.2f}")

    print("\n" + "=" * 60)
    print("✈️ TOP VISITANTES (Ordenados por favoritismo na Bet365)")
    print("=" * 60)
    for v in top_visitantes:
        print(f"- {v['match'].split(' x ')[1]}: Odd Vitória Bet365 @{v['away_odd']:.2f}")

    # 2. OPORTUNIDADES EV+ ENCONTRADAS
    print("\n" + "=" * 60)
    print("🎯 OPORTUNIDADES COM VALOR ESPERADO POSITIVO (+EV)")
    print("=" * 60)
    for opp in all_ev_opportunities:
        print(json.dumps(opp.to_dict(), ensure_ascii=False, indent=2))

    # 3. GERADOR DE DUPLAS (ODD 1.60 - 2.00)
    combos = QuantitativeEngine.generate_combos(all_ev_opportunities)
    print("\n" + "=" * 60)
    print("🚀 DUPLAS PRO EV+ GERADAS (ODD TOTAL: 1.60 - 2.00)")
    print("=" * 60)
    for idx, c in enumerate(combos, 1):
        print(f"\nBilhete #{idx} (Odd Final: @{c['odd_combinada']})")
        print(f"  ├─ {c['selecao_1']}")
        print(f"  └─ {c['selecao_2']}")


if __name__ == "__main__":
    main()
