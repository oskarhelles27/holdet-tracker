"""
Fetches the round schedule from Holdet's public JSON API.
No auth needed. Returns a list of rounds (round 1 first) with the
start/close/end timestamps for each stage.
"""

import requests

SCHEDULE_URL = "https://nexus-app-fantasy.holdet.dk/api/schedules/618"


def fetch_schedule():
    resp = requests.get(SCHEDULE_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("rounds", [])


if __name__ == "__main__":
    import json
    rounds = fetch_schedule()
    print(f"Fetched {len(rounds)} rounds")
    print(json.dumps(rounds[:3], indent=2, ensure_ascii=False))
