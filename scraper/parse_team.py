"""
Parses a Holdet fantasy team page (server-rendered HTML) into structured data.

Source page: https://nexus-app-fantasy.holdet.dk/da/tour-de-france-2026/cycling/fantasyteams/{team_id}

This is NOT a JSON API -- it's the plain server-rendered HTML page. We parse
the rendered DOM directly with BeautifulSoup. Holdet may change their CSS
module class names (e.g. "ListView-module__TLh33G__item") between deploys,
so wherever possible we match on `data-testid` attributes and DOM structure
instead of exact class names, since those look intentionally stable.
"""

import re
from bs4 import BeautifulSoup


def _danish_number_to_int(text):
    """Convert a Danish-formatted number string like '20.865.000' or
    '+530.000' or '-90.000' into an int. Returns None if no number found."""
    if text is None:
        return None
    cleaned = text.strip().replace("\xa0", " ")
    match = re.search(r"[-+]?[\d.]+(?=\s*p\.?|$)", cleaned)
    if not match:
        match = re.search(r"[-+]?[\d.]+", cleaned)
        if not match:
            return None
    num_str = match.group(0).replace(".", "")
    try:
        return int(num_str)
    except ValueError:
        return None


def parse_roster(soup):
    """Extract the current rider roster from the listview section."""
    riders = []
    listview = soup.find("ul", attrs={"data-testid": "listview"})
    if listview is None:
        return riders

    items = listview.find_all("li", attrs={"data-testid": "listviewitem"})
    for item in items:
        try:
            name_div = item.find("div", title=True)
            if name_div is None:
                continue
            name = name_div["title"].strip()

            pro_team = None
            team_div = name_div.find_next_sibling("div")
            if team_div is not None:
                pro_team = team_div.get_text(strip=True)

            is_captain = "Kaptajn" in item.get_text()

            value = None
            right_col = item.find("div", class_=lambda c: c and "text-right" in c)
            if right_col is not None:
                value_span = right_col.find("span", class_=lambda c: c and "text-nowrap" in c)
                if value_span is not None:
                    value = _danish_number_to_int(value_span.get_text())

            riders.append({
                "name": name,
                "pro_team": pro_team,
                "is_captain": is_captain,
                "value": value,
            })
        except Exception as e:
            riders.append({"name": None, "pro_team": None, "is_captain": False,
                            "value": None, "_parse_error": str(e)})
    return riders


def parse_value_summary(soup):
    """Extract Spillerværdier / Bank / Total from the value summary block."""
    summary = {"player_values": None, "bank": None, "total": None}
    label_map = {
        "Spillerværdier": "player_values",
        "Bank": "bank",
        "Total": "total",
    }
    for label_div in soup.find_all("div"):
        text = label_div.get_text(strip=True)
        if text in label_map and len(label_div.contents) == 1:
            row = label_div.find_parent("div", class_=lambda c: c and "justify-between" in c)
            if row is None:
                continue
            value_span = row.find("span")
            if value_span is not None:
                summary[label_map[text]] = _danish_number_to_int(value_span.get_text())
    return summary


def parse_team_header(soup):
    """Extract team name, owner username, owner user id, tier."""
    header = {"team_name": None, "owner_username": None, "owner_user_id": None, "tier": None}
    user_links = soup.find_all("a", href=re.compile(r"/users/\d+"))
    for link in user_links:
        match = re.search(r"/users/(\d+)", link["href"])
        if match:
            header["owner_user_id"] = int(match.group(1))
        text = link.get_text(strip=True)
        if text:
            header["owner_username"] = text
            break

    tier_img = soup.find("img", alt=re.compile(r"Guld|Sølv|Bronze", re.IGNORECASE))
    if tier_img is not None:
        header["tier"] = tier_img["alt"]
        name_container = tier_img.find_parent("div")
        if name_container is not None:
            # the team name is the text content of this div; the tier badge
            # is an <img> so it contributes no text of its own
            header["team_name"] = name_container.get_text(strip=True) or None

    return header


def parse_round_history(soup):
    """Extract the full round-by-round history table (points, rank, value, overall rank)."""
    history = []
    for row in soup.find_all("div", class_=lambda c: c and "grid-cols-4" in c):
        try:
            cols = row.find_all("div", recursive=False)
            if len(cols) < 3:
                continue
            round_label = cols[0].get_text(strip=True)
            round_match = re.search(r"Runde\s*(\d+)", round_label)
            if not round_match:
                continue
            round_num = int(round_match.group(1))

            points_col = cols[1]
            points_span = points_col.find("span")
            round_points = _danish_number_to_int(points_span.get_text()) if points_span else None
            round_rank_div = points_col.find("div", title="Placering i runden")
            round_rank = _danish_number_to_int(round_rank_div.get_text()) if round_rank_div else None

            value_col = cols[2]
            value_span = value_col.find("span")
            total_value = _danish_number_to_int(value_span.get_text()) if value_span else None
            overall_rank_div = value_col.find("div", title="Placering overall")
            overall_rank = _danish_number_to_int(overall_rank_div.get_text()) if overall_rank_div else None

            history.append({
                "round": round_num,
                "round_points": round_points,
                "round_rank": round_rank,
                "total_value": total_value,
                "overall_rank": overall_rank,
            })
        except Exception:
            continue

    # de-duplicate by round number (the page structure can repeat blocks)
    seen = {}
    for entry in history:
        seen[entry["round"]] = entry
    return sorted(seen.values(), key=lambda e: e["round"])


def parse_team_page(html, team_id):
    """Main entry point: parse a full team page into one structured dict."""
    soup = BeautifulSoup(html, "lxml")
    result = {
        "team_id": team_id,
        "header": parse_team_header(soup),
        "value_summary": parse_value_summary(soup),
        "roster": parse_roster(soup),
        "history": parse_round_history(soup),
    }
    return result


if __name__ == "__main__":
    import json
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "debug/sample_team_7159885.html"
    with open(path, encoding="utf-8") as f:
        html = f.read()
    data = parse_team_page(html, team_id="7159885")
    print(json.dumps(data, indent=2, ensure_ascii=False))
