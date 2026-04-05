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

**End-to-end guide (local run → deploy → PWA → APK):** **[TUTORIAL.md](./TUTORIAL.md)**

---

## Host online so every device stays in sync (free)

Running the app **only on your PC** keeps data in a **local SQLite file**—other phones will not see it unless you deploy.

To share **one** watchlist and rotation **across phones** for **$0** (typical free tiers):

1. Create a free **PostgreSQL** database ([Neon](https://neon.tech) or [Supabase](https://supabase.com)).
2. Deploy this app to a free **web host** ([Render](https://render.com), [Fly.io](https://fly.io), etc.) with **`TMDB_API_KEY`**, **`DATABASE_URL`**, and **`PUBLIC_BASE_URL`** set.
3. Send everyone the **HTTPS link** from the **Sync** page (same URL + same DB = same data).

**Full walkthrough (Neon + Render, Docker optional):** **[DEPLOY-FREE.md](./DEPLOY-FREE.md)**

You do **not** keep `start.bat` running on your computer for family sync—the hosted service replaces that.

---

## Quick start (Windows, about 10 minutes)

Follow these in order. See **`START_HERE.txt`** for a short printable checklist.

### Before you begin

1. **Python 3.10+** — Install from [python.org](https://www.python.org/downloads/) (64-bit is fine).
2. On the installer’s first screen, enable **“Add python.exe to PATH”**, then continue and finish install.
3. If you already had Python installed without PATH, either reinstall with that option checked, or use **“Manage App Execution Aliases”** in Windows Settings and turn off the Microsoft Store placeholders for `python.exe` / `python3.exe`, then confirm `py` or `python` works in a new Command Prompt (`py --version`).

### One command to run the app

1. Double-click **`start.bat`** (same as **`run.bat`**).
2. **First launch only:** the script may create a virtual environment (`\.venv`), install dependencies from `requirements.txt`, and copy **`.env.example`** to **`.env`**. If Notepad opens, set:
   ```env
   TMDB_API_KEY=paste_your_key_here
   ```
   No quotes. Save the file, then double-click **`start.bat`** again.
3. A browser tab should open to **[http://127.0.0.1:8000](http://127.0.0.1:8000)** after a few seconds. Keep the black console window open; that process is the server. Stop with **Ctrl+C** in that window.

### Batch files

| File | Purpose |
| :--- | :--- |
| **`start.bat`** | Recommended entry point. Installs the venv and packages if missing, checks `.env`, starts the server, opens the browser. |
| **`run.bat`** | Same behavior as `start.bat`. |
| **`setup.bat`** | Manual “install only”: venv + `pip install` + `.env` from example. Normally you do **not** need this, because **`start.bat`** runs setup automatically when `.venv` is missing. Pass `silent` for scripts: `setup.bat silent`. |

### Status badge (in the app)

The pill in the **top-right** reflects **`GET /health`** (API + database):

| Label | Meaning |
| :--- | :--- |
| **Checking** | Loading / first request. |
| **Healthy** | HTTP 200 and database reachable. |
| **Faulty** | Server responded but the database check failed (e.g. bad `DATABASE_URL`, Postgres down). |
| **Offline** | The browser could not reach `/health` (server stopped, wrong URL, or network issue). |

For monitors and load balancers, call **`/health`** directly; it returns **503** when the database is unreachable.

### Get a TMDB API key

Create a free key: [TMDB → Settings → API](https://www.themoviedb.org/settings/api).

### Troubleshooting (Windows)

| Problem | What to try |
| :--- | :--- |
| **Python not found** | Reinstall Python with **Add to PATH**, open a **new** Command Prompt, or use the **Microsoft Store** Python only if `py -3` works. |
| **`pip install` fails** | Check Wi‑Fi/VPN, firewall, or corporate proxy; run `setup.bat` again when the network is stable. |
| **`No module named uvicorn`** | The venv exists but packages were not installed (interrupted setup). Run **`start.bat`** again (it now auto-installs deps), or run: `\.venv\Scripts\python.exe -m pip install -r requirements.txt` |
| **Port 8000 already in use** | Stop the other program using the port, or run uvicorn manually on another port: `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001` and open `http://127.0.0.1:8001`. |
| **Notepad keeps opening / TMDB errors in the app** | Ensure `.env` contains `TMDB_API_KEY=` with a non-empty key (no spaces around `=`). Save the file, restart **`start.bat`**. |
| **Badge shows Offline but the console is running** | Open the same URL you used in the browser (e.g. `http://127.0.0.1:8000` vs `http://localhost:8000`). Mixed content or a different machine: use the host that actually serves the app. |

The app loads variables from **`.env`** in the project root (no need to `export` in every terminal).

---

## macOS / Linux (manual)

```bash
git clone https://github.com/exeHers/Movie-Random-Select.git
cd Movie-Random-Select
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add TMDB_API_KEY=... (loaded automatically)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

→ **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## Phone / APK

This app is a **PWA** (no Android project in the repo). For **Add to Home screen**, **deployed HTTPS**, and **building an APK** with PWABuilder, follow **[TUTORIAL.md](./TUTORIAL.md)** (Parts 3–4).

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

1. Use **PostgreSQL** in production (`DATABASE_URL`). SQLite is only for **local** dev when `DATABASE_URL` is unset.
2. Deploy with `TMDB_API_KEY` and `DATABASE_URL` set; set `PUBLIC_BASE_URL` to your **live HTTPS root** (no trailing slash).
3. Send everyone the link from **Sync** (or **Copy app link**).

See **[DEPLOY-FREE.md](./DEPLOY-FREE.md)** for a free-tier, step-by-step deploy. Running only on your laptop with SQLite means data stays on that machine.

---

## Project layout

```
TUTORIAL.md    # Full walkthrough: local → online → Android APK / PWA
DEPLOY-FREE.md # Free PostgreSQL + HTTPS hosting (multi-device sync)
Dockerfile     # Optional container deploy
start.bat      # Windows: install-if-needed + run server + open browser
run.bat        # same as start.bat
setup.bat      # Windows: venv + pip install + .env (also run automatically)
START_HERE.txt # shortest Windows checklist
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
