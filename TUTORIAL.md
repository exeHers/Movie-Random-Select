# Movie Night: full tutorial (run locally → online → Android APK)

This guide walks through:

1. **Running the app on your computer** (test everything works).
2. **Putting the app on the internet** with a shared database (so phones stay in sync).
3. **Getting an installable Android package**—either the easy **Add to Home screen** path, or a real **APK** built from your live site.

**You cannot build a meaningful family APK from `http://127.0.0.1` alone.** Packagers need a **public HTTPS URL** that loads your app. Plan on completing **Part 2** before **Part 4**.

---

## What you need

| Item | Purpose |
| :--- | :--- |
| **Python 3.10+** | Run the server locally ([python.org](https://www.python.org/downloads/)) |
| **GitHub account** (optional but recommended) | Deploy to Render and similar hosts from a repo |
| **TMDB API key** (free) | [themoviedb.org → Settings → API](https://www.themoviedb.org/settings/api) |
| **Neon or Supabase account** (free tier) | Hosted PostgreSQL for multi-device sync |
| **Render / Fly.io / similar** (free tier) | HTTPS hosting for the Python app |
| **Android device** (for Part 3–4) | Install PWA or sideload APK |

---

## Part 1 — Run locally (Windows)

Use this to verify TMDB and the UI before you deploy.

### 1.1 Install Python

1. Download Python from [python.org](https://www.python.org/downloads/).
2. Run the installer. On the **first screen**, check **“Add python.exe to PATH”**, then **Install Now**.
3. Close and reopen any terminal after installing.

### 1.2 Get the code

- If you use Git: `git clone` your copy of the repo and `cd` into the project folder.
- If you have a ZIP: extract it and open the folder that contains `start.bat`, `app/`, and `requirements.txt`.

### 1.3 Start the app

1. Double-click **`start.bat`** (same as **`run.bat`**).
2. On first run, the script may create **`.venv`**, install packages, and create **`.env`** from **`.env.example`**.
3. If **Notepad** opens, set **one line** (no quotes around the key):

   ```env
   TMDB_API_KEY=paste_your_tmdb_key_here
   ```

4. Save the file, run **`start.bat`** again.
5. Your browser should open **http://127.0.0.1:8000**. The top-right pill should turn **Healthy** when the server and local DB respond.

**Stop the server:** in the black console window, press **Ctrl+C**.

**Troubleshooting:** see **`START_HERE.txt`** and the **Troubleshooting** table in **`README.md`**.

---

## Part 2 — Put the app online (shared data on every phone)

Local mode uses **SQLite** on your PC. For **one link for the whole family**, you need:

- A **PostgreSQL** database in the cloud (**`DATABASE_URL`**).
- The FastAPI app running on a host that serves **HTTPS** (**`PUBLIC_BASE_URL`**).

### 2.1 Create Postgres (Neon example)

1. Go to [neon.tech](https://neon.tech) and sign up.
2. Create a project and database.
3. Copy the **connection string** (it usually includes `?sslmode=require`). This is your **`DATABASE_URL`**.

### 2.2 Push the project to GitHub

1. Create a new repository on GitHub (empty is fine).
2. In your project folder, run (replace URL with yours):

   ```bash
   git init
   git add .
   git commit -m "Movie Night"
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git branch -M main
   git push -u origin main
   ```

   If you already cloned from GitHub, just **`git push`** after commits.

### 2.3 Deploy on Render (example)

1. Sign up at [render.com](https://render.com).
2. **New → Web Service** → **Connect** your GitHub repo → select the Movie Night repository.
3. Configure:

   | Field | Value |
   | :--- | :--- |
   | **Name** | Anything (e.g. `movie-night`) |
   | **Region** | Closest to your family |
   | **Branch** | `main` |
   | **Runtime** | Python 3 |
   | **Build command** | `pip install -r requirements.txt` |
   | **Start command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

4. **Environment → Add environment variable:**

   | Key | Value |
   | :--- | :--- |
   | `TMDB_API_KEY` | Same key as in your local `.env` |
   | `DATABASE_URL` | Full Neon connection string |
   | `PUBLIC_BASE_URL` | Your Render URL **without a trailing slash**, e.g. `https://movie-night-xxxx.onrender.com` |

   After the first deploy, Render shows your URL—copy it and set **`PUBLIC_BASE_URL`** to match, then **redeploy** or save (so “Copy app link” on the Sync page is correct).

5. Optional: set **Health Check Path** to **`/health`**.

6. Wait for the deploy to finish, then open the **https://…** URL. The status badge should show **Healthy**.

**More detail and alternatives (Fly.io, Docker):** **`DEPLOY-FREE.md`**.

---

## Part 3 — “Install” on Android without an APK (recommended first)

This is the **fastest** way to get a full-screen icon on Android—no Play Store, no build tools.

1. On the phone, open **Chrome**.
2. Go to your **deployed HTTPS URL** from Part 2.
3. Tap the **menu (⋮)** → **Add to Home screen** (or **Install app**, depending on Chrome version).
4. Confirm. You now have a **Movie Night** icon that opens like an app.

**Limitations:** This is still a **PWA shortcut**, not a separate APK file you can email—but for most families it behaves like an app.

---

## Part 4 — Build an APK from your live site

You need a **public HTTPS** URL (Part 2). The app is still your website; the APK is a **Trusted Web Activity** wrapper.

### 4.1 Prerequisites

- **Working HTTPS URL** (e.g. `https://movie-random-select.onrender.com`).
- **`PUBLIC_BASE_URL`** set on the host to that origin (no trailing slash).
- In desktop Chrome, confirm the site loads and **Sync → Copy app link** uses **https**.

### 4.2 Android Studio + Bubblewrap (full, production-style)

Use this when you want a **real Gradle project**, your own **keystore**, **Digital Asset Links** on your domain, and **Build → Generate Signed APK** inside **Android Studio**.

**Follow the complete guide:** **[docs/BUILD-APK-ANDROID-STUDIO.md](./docs/BUILD-APK-ANDROID-STUDIO.md)**

Summary of what that guide covers:

1. Install **Android Studio** + **Node.js**, then `npm i -g @bubblewrap/cli`.
2. Run **`bubblewrap init`** against `https://YOUR_DOMAIN/static/manifest.webmanifest`.
3. Create a **release keystore**; capture **SHA-256** with **`keytool -list -v`**.
4. On Render, set **`ANDROID_TWA_PACKAGE`** (same Application ID as Bubblewrap) and **`ANDROID_TWA_SHA256`**; redeploy so **`/.well-known/assetlinks.json`** returns **200** (served by this repo’s `app/asset_links.py`).
5. Open the generated project in **Android Studio**, wire **signing**, then **Build → Generate Signed App Bundle / APK**.

### 4.3 PWABuilder (faster, less control)

[PWABuilder](https://www.pwabuilder.com/) can produce an Android package in the browser. Good for quick tests; for **Android Studio** workflows, prefer §4.2.

1. Open **[pwabuilder.com](https://www.pwabuilder.com/)** and enter your **https://** homepage.
2. Fix any audit issues (often **PNG icons** if SVG is rejected); redeploy and re-run.
3. Use the **Android** flow, set package name and signing, download **APK** or **AAB**.

### 4.4 Install the APK on Android

1. Enable **Install unknown apps** for the app you use to open the file.
2. Transfer the APK and install.

**Updates:** Site-only changes usually **do not** need a new APK. New signing keys or package ID require updating **`ANDROID_TWA_***`** env vars and rebuilding.

---

## Part 5 — Checklist before you call it done

| Step | Check |
| :--- | :--- |
| Local | **`start.bat`** → **Healthy** on `127.0.0.1` |
| Cloud DB | Neon/Supabase project active; **`DATABASE_URL`** set on host |
| HTTPS | Site opens with **https://**; no certificate warnings |
| Env | **`PUBLIC_BASE_URL`** matches your real URL (no trailing slash) |
| Sync | Two phones open the **same** link; see the same watchlist |
| PWA | **Add to Home screen** works in Chrome |
| APK | `assetlinks.json` 200; Android Studio release build installs; TWA full-screen |

---

## Quick reference — environment variables

| Variable | Local | Hosted |
| :--- | :--- | :--- |
| `TMDB_API_KEY` | `.env` | Host dashboard |
| `DATABASE_URL` | Optional (omit → SQLite) | **Required** for family sync (Postgres) |
| `PUBLIC_BASE_URL` | Optional | **Recommended** (`https://your-domain`) |
| `ANDROID_TWA_PACKAGE` | No | TWA / Android Studio: same as app **Application ID** |
| `ANDROID_TWA_SHA256` | No | TWA: release keystore **SHA-256** (see **docs/BUILD-APK-ANDROID-STUDIO.md**) |

---

## More help

- **Windows setup:** `START_HERE.txt`
- **Free deploy details:** `DEPLOY-FREE.md`
- **Docker:** `Dockerfile` in this repo

If something fails, note whether the **badge** says **Offline**, **Faulty**, or **Healthy**, and whether the problem is **only on APK** or **also in Chrome**—that narrows it down quickly.
