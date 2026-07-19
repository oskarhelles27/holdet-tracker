"""
Fetches per-round rider stats from Holdet's public JSON API.
No auth needed. Returns a dict keyed by playerId (== rider_id in
master_riders) with that round's price/points movement.
"""

import requests

ROUND_PLAYERS_URL = "https://nexus-app-fantasy.holdet.dk/api/games/618/rounds/{round_id}/players"


def fetch_round_players(round_id):
    resp = requests.get(ROUND_PLAYERS_URL.format(round_id=round_id), timeout=30)
    resp.raise_for_status()
    data = resp.json()

    riders = {}
    for item in data.get("items", []):
        riders[str(item["playerId"])] = {
            "price": item.get("price"),
            "price_change": item.get("priceChange"),
            "points": item.get("points"),
            "points_change": item.get("pointsChange"),
        }
    return riders


if __name__ == "__main__":
    import json
    import sys
    round_id = sys.argv[1] if len(sys.argv) > 1 else "14"
    riders = fetch_round_players(round_id)
    print(f"Fetched {len(riders)} rider entries for round {round_id}")
    print(json.dumps(list(riders.items())[:3], indent=2))
