"""
Fetches the master rider list from Holdet's public JSON API.
No auth needed. Returns a dict keyed by riderId with name/team/price/points/popularity.
"""

import requests

PLAYERS_URL = "https://nexus-app-fantasy.holdet.dk/api/games/618/players"


def fetch_master_riders():
    resp = requests.get(PLAYERS_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    persons = data.get("_embedded", {}).get("persons", {})
    teams = data.get("_embedded", {}).get("teams", {})

    riders = {}
    for item in data.get("items", []):
        person_id = str(item.get("personId"))
        person = persons.get(person_id, {})
        team = teams.get(str(item.get("teamId")), {})

        first = person.get("firstName", "")
        last = person.get("lastName", "")
        full_name = f"{first} {last}".strip()

        riders[str(item["id"])] = {
            "rider_id": item["id"],
            "person_id": item.get("personId"),
            "name": full_name,
            "pro_team": team.get("name"),
            "pro_team_abbr": team.get("abbreviation"),
            "price": item.get("price"),
            "start_price": item.get("startPrice"),
            "points": item.get("points"),
            "global_popularity": item.get("popularity"),
            "is_out": item.get("isOut", False),
        }
    return riders


if __name__ == "__main__":
    import json
    riders = fetch_master_riders()
    print(f"Fetched {len(riders)} riders")
    print(json.dumps(list(riders.values())[:3], indent=2, ensure_ascii=False))
