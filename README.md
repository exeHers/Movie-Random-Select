# Movie Night — family movie suggester

Mobile-first web app: **nightly rotation** (stepdad → mom → you), **per-person tastes**, **seen list**, **watchlist**, **trailers**. Data comes from [TMDB](https://www.themoviedb.org/).

## Sync across phones (important)

The app does **not** sync over the air by itself. **Every device must talk to the same server** that uses the **same database**.

| Setup | Result |
|--------|--------|
| Run on your laptop, parents open your laptop’s IP | Shared only while your laptop is on and reachable. |
| Deploy to Fly/Railway/Render + **PostgreSQL** | Everyone opens the same URL — **seen, watchlist, rotation, tastes stay in sync**. |

1. Create a free Postgres database (e.g. [Neon](https://neon.tech), [Supabase](https://supabase.com), Railway).
2. Set **`DATABASE_URL`** to the Postgres connection string (the app accepts `postgresql://` or `postgres://` and uses asyncpg).
3. Set **`TMDB_API_KEY`** on the host.
4. Optional: set **`PUBLIC_BASE_URL`** to your live site (e.g. `https://movies.example.com`) so **Sync → Copy app link** always matches your deployment.

Without `DATABASE_URL`, the app uses **`data/movie_night.sqlite` on the server** — fine for one machine, not for two phones unless that server is shared.

## Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export TMDB_API_KEY=your_key
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Use **Add to Home Screen** for a standalone icon; check **Sync** in the bottom nav for the shareable link and hosting notes.

## Customize tastes

**Tastes** in the app (or the `profiles` table): TMDB genre IDs, min score, min votes, rotation order, title keyword skips. Genre list: [TMDB genre movie list](https://developer.themoviedb.org/reference/genre-movie-list).

## More ideas (not built in)

- **Where to watch** (region + streaming providers via TMDB).
- **Per-person seen** vs household seen (schema change).
- **Simple passcode** on `/profiles` if the app is public on the internet.
- **Push reminders** (“tonight is Mom’s pick”) via native wrapper or web push.
