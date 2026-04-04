# Movie Night — family movie suggester

Web app tuned for phones: **nightly rotation** (stepdad → mom → you by default), **per-person tastes**, **seen list**, **watchlist**, **trailers**, and optional **blended** picks when everyone watches together. Uses [The Movie Database (TMDB)](https://www.themoviedb.org/).

## Setup

1. Create a free TMDB API key: [Account settings → API](https://www.themoviedb.org/settings/api).
2. Python 3.12+.

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export TMDB_API_KEY=your_key_here
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) on your phone. Use **Add to Home Screen** for an app-like shortcut; the site registers a light **service worker** and `manifest` for a standalone icon.

Data lives in `data/movie_night.sqlite` (gitignored).

## How it works

- **Tonight**: The app picks whose turn it is from calendar days since a **rotation start date** (editable on the home screen). That person’s genres and quality thresholds drive TMDB discover; **seen** titles are excluded.
- **Tastes** (bottom nav): Edit display names, TMDB genre IDs, min score, min vote count, rotation order, and comma-separated **title keywords to skip** (e.g. genres you never want in the title match).
- **Watchlist**: Saved on a movie page; tonight’s suggestion sometimes pulls from it; you can also **random from watchlist** on the home screen.
- **Blended suggestion**: Check multiple people on the home screen to merge candidate pools.

TMDB genre IDs: [genre movie list](https://developer.themoviedb.org/reference/genre-movie-list).

## Real native apps later

This is a **mobile-first PWA** (one codebase, installable from the browser). If you later want App Store / Play Store builds, wrap the same URL with [Capacitor](https://capacitorjs.com/) or similar; the UI is already touch-first.
