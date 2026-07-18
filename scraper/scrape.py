"""
Main scraper: fetches the master rider list + all configured team rosters,
computes group-popularity, and writes a dated JSON snapshot to data/.

Usage:
    python scraper/scrape.py

Configure your 10 team IDs in scraper/teams.json, e.g.:
    {
      "teams": [
        {"id": "7212424", "label": "Anders"},
        {"id": "7159885", "label": "Marcus"}
      ]
    }
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

sys.path.insert(0, os.path.dirname(__file__))
from parse_team import parse_team_page
from fetch_master_riders import fetch_master_riders

ROSTER_URL_TEMPLATE = "https://nexus-app-fantasy.holdet.dk/da/tour-de-france-2026/cycling/fantasyteams/{team_id}"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "docs", "data")
DEBUG_DIR = os.path.join(REPO_ROOT, "debug")
TEAMS_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "teams.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; holdet-tracker/1.0; personal use)"
}

# Team roster pages only server-render the actual roster HTML for an
# authenticated session -- without a valid Holdet login cookie, the
# data-testid="listviewitem" section stays a loading skeleton. Any logged-in
# session works for fetching any team's roster (not just your own). Grab the
# Cookie header value from devtools while browsing nexus-app-fantasy.holdet.dk
# (Network tab -> a request to that host -> Headers -> Cookie), and pass it
# via the HOLDET_COOKIE env var / GitHub secret.
SESSION_COOKIE = os.environ.get("HOLDET_COOKIE")


def load_team_config():
    with open(TEAMS_CONFIG_PATH, encoding="utf-8") as f:
        config = json.load(f)
    return config["teams"]


def fetch_team_roster(team_id, label):
    url = ROSTER_URL_TEMPLATE.format(team_id=team_id)
    headers = dict(HEADERS)
    if SESSION_COOKIE:
        headers["Cookie"] = SESSION_COOKIE
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        print(f"  [ERROR] Failed to fetch team {team_id} ({label}): {e}")
        return None

    try:
        parsed = parse_team_page(html, team_id=team_id)
        parsed["label"] = label
        if not parsed["roster"]:
            raise ValueError("Parsed roster is empty - page structure may have changed")
        return parsed
    except Exception as e:
        print(f"  [ERROR] Failed to parse team {team_id} ({label}): {e}")
        os.makedirs(DEBUG_DIR, exist_ok=True)
        debug_path = os.path.join(DEBUG_DIR, f"{team_id}-raw.html")
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  Raw HTML saved to {debug_path} for inspection")
        return None


def compute_group_popularity(teams_data):
    """Count how many of our tracked teams own each rider (by name+pro_team)."""
    counts = {}
    for team in teams_data:
        if team is None:
            continue
        for rider in team["roster"]:
            key = f"{rider['name']}|{rider['pro_team']}"
            if key not in counts:
                counts[key] = {
                    "name": rider["name"],
                    "pro_team": rider["pro_team"],
                    "owned_by_count": 0,
                    "owned_by_teams": [],
                }
            counts[key]["owned_by_count"] += 1
            counts[key]["owned_by_teams"].append(team.get("label") or team["team_id"])
    return sorted(counts.values(), key=lambda r: -r["owned_by_count"])


def main():
    if not SESSION_COOKIE:
        print("  [WARN] HOLDET_COOKIE is not set - team roster pages will "
              "return a loading skeleton instead of real data.")

    print("Fetching master rider list...")
    try:
        master_riders = fetch_master_riders()
        print(f"  Got {len(master_riders)} riders from the master list")
    except Exception as e:
        print(f"  [ERROR] Failed to fetch master rider list: {e}")
        master_riders = {}

    team_configs = load_team_config()
    print(f"Fetching {len(team_configs)} team rosters...")

    teams_data = []
    for entry in team_configs:
        team_id = str(entry["id"])
        label = entry.get("label", team_id)
        print(f"  Fetching {label} ({team_id})...")
        result = fetch_team_roster(team_id, label)
        teams_data.append(result)
        time.sleep(1)  # be polite between requests

    successful = [t for t in teams_data if t is not None]
    failed = [team_configs[i]["id"] for i, t in enumerate(teams_data) if t is None]

    print(f"Successfully scraped {len(successful)}/{len(team_configs)} teams")
    if failed:
        print(f"  Failed team IDs: {failed}")

    group_popularity = compute_group_popularity(successful)

    snapshot = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "master_riders": master_riders,
        "teams": successful,
        "failed_team_ids": failed,
        "group_popularity": group_popularity,
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    snapshot_path = os.path.join(DATA_DIR, f"{date_str}.json")
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    print(f"Snapshot written to {snapshot_path}")

    # also write a "latest.json" that always points to the most recent snapshot,
    # so the frontend doesn't need to know today's date
    latest_path = os.path.join(DATA_DIR, "latest.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    print(f"Latest snapshot also written to {latest_path}")


if __name__ == "__main__":
    main()
