<div align="center">

# Movie Night

**Pick films for the whole family — rotating nights, personal tastes, no repeats.**

[TMDB](https://www.themoviedb.org/) · FastAPI · Mobile-first PWA

</div>

---

## What it does

| | |
| :--- | :--- |
| **Rotation** | Whose pick tonight cycles **stepdad → mom → you** (calendar-based; adjustable start date). |
| **Tastes** | Per-person genres, score/vote thresholds, title keywords to skip. |
| **Seen** | Mark watched titles so suggestions skip them. |
| **Watchlist** | Save for later; random pick or bias toward list on “tonight.” |
| **Blended** | Check multiple people when everyone watches together. |
| **Trailers** | YouTube embed + runtime + TMDB / IMDb links. |

Install from the browser (**Add to Home Screen**) for a standalone icon. Open **Sync** in the app for the shareable link and hosting tips.

---

## Quick start

```bash
git clone https://github.com/exeHers/Movie-Random-Select.git
cd Movie-Random-Select
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # optional; or export vars below
export TMDB_API_KEY=your_key_here
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

→ **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

Get a free API key: [TMDB → Settings → API](https://www.themoviedb.org/settings/api).

---

## Environment

| Variable | Required | Purpose |
| :--- | :---: | :--- |
| `TMDB_API_KEY` | **Yes** | Movie metadata & discovery from TMDB. |
| `DATABASE_URL` | No | **PostgreSQL** URL → one shared DB for every phone (family sync). If unset → SQLite in `data/movie_night.sqlite` (this machine only). |
| `PUBLIC_BASE_URL` | No | e.g. `https://movies.yourdomain.com` — fixes **Copy app link** on the Sync page. |

Postgres URLs can use `postgresql://` or `postgres://` (the app normalizes them for async SQLAlchemy).

---

## Syncing phones (read this once)

The app does **not** sync device-to-device. **Same URL + same database = same data.**

1. Create a free Postgres DB ([Neon](https://neon.tech), [Supabase](https://supabase.com), Railway, etc.).
2. Deploy this app (Fly, Railway, Render, VPS…) with `TMDB_API_KEY` and `DATABASE_URL` set.
3. Optional: set `PUBLIC_BASE_URL` to your live URL.
4. Send everyone the link from **Sync** in the app (or use **Copy app link**).

Running only on your laptop with SQLite means data stays on that laptop unless others use **your** server address while it’s online.

---

## Project layout

```
app/           # FastAPI app, DB, suggestion logic, TMDB client
templates/     # Jinja pages (home, movie, tastes, sync)
static/        # CSS, PWA manifest, service worker, icon
data/          # local SQLite when DATABASE_URL is not set (gitignored)
```

TMDB genre IDs for tastes: [genre movie list](https://developer.themoviedb.org/reference/genre-movie-list).

---

## Roadmap ideas

Where to watch by region · per-person “seen” vs household · PIN on tastes · push / “tonight’s pick” reminders (needs hosting + web push or native wrapper).

---

<div align="center">

**Built for dinner-table indecision.**

</div>
