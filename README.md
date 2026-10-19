# hr-nekretnine-history

A GitHub Action runs `scrape.py` daily, saves the feed as `natjecaji.json` and commits it if it changed.
The git history is the archive. New items trigger an [ntfy](https://ntfy.sh) push.

If the feed is down, returns an HTTP error, or has 0 items on the first page, the scraper sends a
high-priority "scraper error" push to the same topic and the run fails.

## Setup
1. Add the repo secret `NTFY_TOPIC` (a hard-to-guess topic you subscribe to in the ntfy app).
2. In Settings → Pages, set the source to **GitHub Actions**.
3. Push. The first run records a baseline without notifying.

Each run also publishes `index.html` and `natjecaji.json` to GitHub Pages
(`https://mmatokovic.github.io/hr-nekretnine-history/`).

## History
    git log -p natjecaji.json