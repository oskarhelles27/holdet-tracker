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

## 2. Get a Holdet session cookie

Team roster pages (`nexus-app-fantasy.holdet.dk/.../cycling/fantasyteams/{id}`)
only server-render the real roster HTML for an authenticated session —
without a valid cookie, the roster section stays a client-side loading
skeleton, so the scraper has nothing to parse. Any logged-in session works
for fetching any team's roster, not just your own.

1. Log into holdet.dk in your browser, then open one of your team roster
   pages at `nexus-app-fantasy.holdet.dk/.../cycling/fantasyteams/{id}`.
2. Open devtools → Network tab, find the document request to
   `nexus-app-fantasy.holdet.dk`, and copy the full `Cookie:` request header
   value (all `name=value` pairs, semicolon separated).
3. Set it as the `HOLDET_COOKIE` environment variable when running the
   scraper locally, and add it as a repo secret
   (**Settings → Secrets and variables → Actions → New repository secret**,
   name `HOLDET_COOKIE`) so the daily GitHub Action can use it too.

Session cookies expire, so you'll need to refresh this secret periodically
if scrapes start failing again. Treat this cookie like a password — it's
equivalent to your Holdet login. Never commit it to the repo.

## 3. Run the scraper locally (optional, to test)

```bash
cd scraper
pip install -r requirements.txt
HOLDET_COOKIE='paste-your-cookie-here' python scrape.py
```

This writes `docs/data/latest.json`. Open `docs/index.html` directly in a
browser to preview (or run a local server: `python -m http.server` from the
repo root, then visit `http://localhost:8000/docs/`).

A sample `docs/data/latest.json` is already included so you can see the site
working before you plug in your real team IDs.

## 4. Put this on GitHub (personal account, free)

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

## 5. Turn on GitHub Pages

1. In your repo on GitHub: **Settings → Pages**
2. Under "Build and deployment", set **Source** to "Deploy from a branch"
3. Set **Branch** to `main` and folder to **`/docs`**
4. Save. Your site will be live at `https://YOUR_USERNAME.github.io/holdet-tracker/`
   within a minute or two.

## 6. Turn on the scraper automation

The GitHub Action in `.github/workflows/scrape.yml` runs automatically once a
day (20:00 UTC) once it's on GitHub and the `HOLDET_COOKIE` secret is
set (step 2) — no extra setup needed beyond that, since it uses the built-in
`GITHUB_TOKEN` to commit back to your repo.

To run it manually (e.g. right after setup, to get real data immediately):
1. Go to your repo's **Actions** tab
2. Click "Scrape Holdet data" in the left sidebar
3. Click **Run workflow**

Each successful run commits an updated `data/latest.json`, which the site
picks up automatically (just refresh the page).

## 7. Add pro team jersey icons (optional)

The site shows a small jersey icon next to each rider's pro team, if one is
available. Holdet's own pages/API don't provide these images, so they're not
fetched automatically — drop your own square icon files (e.g. 40x40px PNG)
into `docs/assets/jerseys/`, named by the team's abbreviation:

```
docs/assets/jerseys/UAD.png   (UAE Team Emirates - XRG)
docs/assets/jerseys/TVL.png   (Team Visma | Lease a Bike)
docs/assets/jerseys/SOQ.png   (Soudal Quick-Step)
...
```

The current Tour de France 2026 pro teams and their abbreviations (from
`master_riders` in the scraped data):

| Abbr | Team |
|------|------|
| APT | Alpecin-Premier Tech |
| TBV | Bahrain - Victorious |
| CJR | Caja Rural - Seguros RGA |
| COF | Cofidis |
| DAT | Decathlon CMA CGM Team |
| EFE | EF Education - EasyPost |
| GFC | Groupama - FDJ United |
| LIT | Lidl - Trek |
| LOI | Lotto Intermarché |
| MOV | Movistar Team |
| NSN | NSN Cycling Team |
| IGD | Netcompany INEOS Cycling Team |
| Q36 | Pinarello Q36.5 Pro Cycling Team |
| RBH | Red Bull - BORA - hansgrohe |
| SOQ | Soudal Quick-Step |
| JAY | Team Jayco AlUla |
| DFP | Team Picnic PostNL |
| TVL | Team Visma \| Lease a Bike |
| TEN | TotalEnergies |
| TUD | Tudor Pro Cycling Team |
| UAD | UAE Team Emirates - XRG |
| UXM | Uno-X Mobility |
| XAT | XDS Astana Team |

Any team without a matching file just shows no icon (no broken-image
placeholder) — you don't need all 23 before this works.

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
