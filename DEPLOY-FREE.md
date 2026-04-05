# Host Movie Night online (free tiers + open stack)

Your family sees the **same data on every phone** when:

1. The app runs on a **public HTTPS URL** (not your laptop).
2. You set **`DATABASE_URL`** to a **PostgreSQL** database that all devices share.

Everything below uses **$0 tiers** (limits may change—check each provider) and **open-source** runtimes (Python, Postgres). The hosting **dashboards** (Render, Fly, etc.) are proprietary, but you are not locked into paid software to run the app.

| Piece | Free option | Role |
| :--- | :--- | :--- |
| Database | [Neon](https://neon.tech), [Supabase](https://supabase.com), or self-hosted Postgres | One shared place for seen/watchlist/tastes |
| API + TMDB | This repo (FastAPI) + [TMDB API](https://www.themoviedb.org/settings/api) (free non-commercial) | Serves the web app and talks to TMDB |
| HTTPS host | [Render](https://render.com), [Fly.io](https://fly.io), [Koyeb](https://koyeb.com), etc. | Runs `uvicorn` 24/7 or on-demand |

**Costs to expect:** $0 for typical family use on free tiers. **Cold starts:** some free hosts (e.g. Render) **sleep** after idle time; the first tap after a while may take **30–60 seconds** to wake up.

---

## 1. Create a free PostgreSQL database

### Option A — Neon (simple)

1. Sign up at [neon.tech](https://neon.tech).
2. Create a project → create a database.
3. Copy the **connection string**. It usually looks like `postgresql://user:pass@ep-xxx.region.aws.neon.tech/neondb?sslmode=require`.
4. Keep this string secret; you will paste it as **`DATABASE_URL`** in your host’s dashboard.

### Option B — Supabase

1. Sign up at [supabase.com](https://supabase.com) → New project.
2. **Settings → Database → Connection string** → URI, copy the **postgres** URL (password filled in).
3. Use that as **`DATABASE_URL`** (the app accepts `postgresql://` and `postgres://`).

---

## 2. Get a TMDB API key

1. Open [TMDB → Settings → API](https://www.themoviedb.org/settings/api).
2. Create a key (free for personal / non-commercial use per TMDB terms).
3. You will set **`TMDB_API_KEY`** on the host (same as local `.env`).

---

## 3. Deploy the web app (Render example)

These steps match **Render**’s free **Web Service**; other hosts use the same **environment variables** and a similar **start command**.

### Python version on Render

This repo includes **`runtime.txt`** with **`python-3.12.8`** so Render does **not** use a bleeding-edge Python (e.g. 3.14), which can break older SQLAlchemy builds. If you remove it, set the Python version in the Render dashboard instead.

### Connect GitHub

1. Push this project to a **GitHub** repository (public or private).
2. In Render: **New → Web Service** → connect the repo.

### Build and start

| Setting | Value |
| :--- | :--- |
| **Runtime** | Python 3 |
| **Build command** | `pip install -r requirements.txt` |
| **Start command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

Render sets **`PORT`** automatically. Do **not** hard-code `8000` in production.

### Environment variables (required)

| Name | Value |
| :--- | :--- |
| `TMDB_API_KEY` | Your TMDB key |
| `DATABASE_URL` | Full Postgres URL from Neon or Supabase (include `?sslmode=require` if the provider shows it) |
| `PUBLIC_BASE_URL` | Your live site root, **no trailing slash**, e.g. `https://movie-night-xxxx.onrender.com` |

**Why `PUBLIC_BASE_URL`?** So **Sync → Copy app link** always copies your real HTTPS URL, not an internal hostname.

### Health check (optional)

In Render, set **Health Check Path** to `/health` so the dashboard knows when the app and database are OK.

### After deploy

1. Open your HTTPS URL in the browser.
2. Go to **Sync** — everyone should bookmark or **Add to Home screen** that same link.
3. Top-right badge should show **Healthy** when the server and DB respond.

---

## 4. Deploy with Docker (optional)

If your host runs containers (Fly.io, Koyeb, your own VPS with Docker, etc.):

```bash
docker build -t movie-night .
docker run -p 8000:8000 \
  -e TMDB_API_KEY=your_key \
  -e DATABASE_URL='postgresql://...' \
  -e PUBLIC_BASE_URL='https://your-domain.com' \
  -e PORT=8000 \
  movie-night
```

Pass the same **`PORT`** your platform injects (often **`8000`** locally, **`$PORT`** on Render/Fly).

---

## 5. Troubleshooting

| Symptom | What to check |
| :--- | :--- |
| Badge **Offline** | Service asleep (wait and retry), wrong URL, or deploy failed—check host logs. |
| Badge **Faulty** | **`DATABASE_URL`** wrong, DB paused, or firewall—verify connection string in Neon/Supabase. |
| TMDB errors | **`TMDB_API_KEY`** missing or invalid in host env (not only in local `.env`). |
| Data not shared | **Same URL** for everyone and **one** `DATABASE_URL`; no `DATABASE_URL` → SQLite on the server only (not for multi-device). |

---

## 6. Open source note

- **This app**: FastAPI, Uvicorn, SQLAlchemy, etc. — open-source licenses in `requirements.txt` / upstream projects.
- **Postgres**: open source; Neon/Supabase host it for you on free tiers.
- **TMDB**: API is free for personal use; follow [TMDB’s terms](https://www.themoviedb.org/documentation/api/terms-of-use).

You do **not** need to run the Windows `start.bat` on a server—those scripts are for **local development**. Production uses **`DATABASE_URL`** + **`uvicorn`** on your host.
