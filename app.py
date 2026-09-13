def buscar_odds_bet365(fixture_id):
    odds_data = api_get("odds", {"fixture": fixture_id, "bookmaker": 8})
    odd_1, odd_over25, odd_btts, odd_corners = None, None, None, None
    if odds_data:
        bookmakers = odds_data[0].get("bookmakers", [])
        for bm in bookmakers:
            if bm.get("id") == 8:
                for bet in bm.get("bets", []):
                    # Garante que é o mercado exato de Match Winner (id: 1)
                    if bet.get("id") == 1:
                        for val in bet.get("values", []):
                            if val["value"] == "Home": odd_1 = float(val["odd"])
                    
                    # Garante que é o mercado Goals Over/Under padrão (id: 5)
                    elif bet.get("id") == 5:
                        for val in bet.get("values", []):
                            if val["value"] == "Over 2.5":
                                val_odd = float(val["odd"])
                                # Trava de segurança: Over 2.5 raro passar de 3.50
                                if 1.10 <= val_odd <= 3.50:
                                    odd_over25 = val_odd
                    
                    # Both Teams To Score (id: 8)
                    elif bet.get("id") == 8:
                        for val in bet.get("values", []):
                            if val["value"] == "Yes": odd_btts = float(val["odd"])
                            
                    elif "corner" in str(bet.get("name", "")).lower():
                        for val in bet.get("values", []):
                            if val["value"] == "Over 8.5": odd_corners = float(val["odd"])

    return odd_1, odd_over25, odd_btts, odd_corners
