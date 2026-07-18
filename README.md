# Holdet league tracker

A small static site that tracks a private Tour de France 2026 "Holdet" fantasy
league (10 teams): rider popularity within the group, team standings, and
full rosters.

## How it works

- `scraper/scrape.py` fetches:
  - the public master rider list (`/api/games/618/players`)
  - each configured team's roster page (server-rendered HTML, parsed with BeautifulSoup)
  - writes a combined snapshot to `data/latest.json` (and a dated copy in `data/`)
- `docs/index.html` is a plain HTML/JS page that reads `data/latest.json` and renders it.
  No build step, no framework.
- `.github/workflows/scrape.yml` runs the scraper once a day and commits the new snapshot.

## 1. Configure your teams

Edit `scraper/teams.json` and replace the placeholder IDs with your 10 real
team IDs (the number at the end of each team's URL, e.g.
`.../cycling/fantasyteams/7212424` → `7212424`).

```json
{
  "teams": [
    {"id": "7212424", "label": "Your name"},
    {"id": "7159885", "label": "Friend 2"}
  ]
}
```

## 2. Run the scraper locally (optional, to test)

```bash
cd scraper
pip install -r requirements.txt
python scrape.py
```

This writes `data/latest.json`. Open `docs/index.html` directly in a browser
to preview (or run a local server: `python -m http.server` from the repo root,
then visit `http://localhost:8000/docs/`).

A sample `data/latest.json` is already included so you can see the site
working before you plug in your real team IDs.

## 3. Put this on GitHub (personal account, free)

You don't need GitHub Copilot or any paid tooling for this part — just a
free personal GitHub account and either the web UI or plain `git`.

**Option A — no command line, just the browser:**
1. Go to https://github.com/new, create a new **public** repository (e.g. `holdet-tracker`)
2. On the new repo's page, click "uploading an existing file"
3. Drag the entire contents of this project folder in, commit

**Option B — using git:**
```bash
cd holdet-tracker
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/holdet-tracker.git
git push -u origin main
```

## 4. Turn on GitHub Pages

1. In your repo on GitHub: **Settings → Pages**
2. Under "Build and deployment", set **Source** to "Deploy from a branch"
3. Set **Branch** to `main` and folder to **`/docs`**
4. Save. Your site will be live at `https://YOUR_USERNAME.github.io/holdet-tracker/`
   within a minute or two.

## 5. Turn on the scraper automation

The GitHub Action in `.github/workflows/scrape.yml` runs automatically once a
day (20:00 UTC) once it's on GitHub — no extra setup needed, since it uses the
built-in `GITHUB_TOKEN` to commit back to your repo.

To run it manually (e.g. right after setup, to get real data immediately):
1. Go to your repo's **Actions** tab
2. Click "Scrape Holdet data" in the left sidebar
3. Click **Run workflow**

Each successful run commits an updated `data/latest.json`, which the site
picks up automatically (just refresh the page).

## Notes on fragility

The roster parser (`scraper/parse_team.py`) depends on Holdet's current page
structure. It's written to match on stable-looking attributes
(`data-testid`, element structure) rather than exact CSS class names where
possible, but Holdet could still change things. If a team fails to parse:
- it's logged and skipped (the rest of the scrape continues)
- the raw HTML is saved to `debug/{team_id}-raw.html` for inspection
- check that file against `scraper/parse_team.py` to see what changed

## Extending this later

Ideas for v2, once v1 is working:
- Charts of team value / rank over time (the `history` data is already collected per team)
- A "biggest movers" view (who gained/lost the most value this round)
- Compare your own picks against the group's popular riders
- Move off GitHub Pages + JSON files to a real backend if this grows
