# Build a release APK in Android Studio (Trusted Web Activity)

This is the **proper** path: a real Gradle project, your own keystore, **Digital Asset Links** on your domain, and **Android Studio** producing a signed **APK** (or **AAB** for Play).

Your web app stays on the server; the Android package is a thin **Trusted Web Activity (TWA)** shell that opens your **HTTPS** site full screen.

**Requirements**

- **Deployed** Movie Night at a stable **`https://`** URL (e.g. Render).
- **`PUBLIC_BASE_URL`** set on the host to that same origin (no trailing slash).
- A Windows or macOS machine with **~15 GB** free for Android SDK + Studio.

---

## 1. Install tooling

### Android Studio

1. Install [Android Studio](https://developer.android.com/studio) (current stable).
2. First launch: complete the wizard and install **Android SDK**, **SDK Platform** for a recent API (e.g. **35** or **34**), and **Android SDK Build-Tools**.
3. **Settings → Build, Execution, Deployment → Build Tools → Gradle**: use the **bundled JDK** (17+) unless you know you need another.

### Node.js (for Bubblewrap)

1. Install [Node.js LTS](https://nodejs.org/).
2. Install Bubblewrap globally:

```bash
npm install -g @bubblewrap/cli
```

3. Run `bubblewrap doctor` and fix anything it reports (often **JDK** path).

---

## 2. Pick your Android package name

Choose a **unique** application ID, reverse-DNS style, never change it after Play users install (unless you ship a new app).

Example: `com.yourfamily.movienight`

You will use this **exact** string everywhere: Bubblewrap, Render env `ANDROID_TWA_PACKAGE`, and Play Console later.

---

## 3. Generate the Android project with Bubblewrap

Bubblewrap is Google’s CLI; it emits a **full Android Studio / Gradle** project wired for TWA.

1. In an empty parent folder (not inside your FastAPI repo if you prefer), run:

```bash
bubblewrap init --manifest=https://YOUR_DOMAIN/static/manifest.webmanifest
```

Replace `YOUR_DOMAIN` with your real host, e.g. `movie-random-select.onrender.com` (no path except the manifest path).

2. Answer the prompts. Critical fields:

| Prompt | What to enter |
| :--- | :--- |
| **Host** | Your site origin, e.g. `movie-random-select.onrender.com` |
| **Name** | `Movie Night` (display name) |
| **Launcher name** | Short label for the home screen |
| **Application ID** | Same as §2, e.g. `com.yourfamily.movienight` |
| **Signing key** | Create a **new** keystore when asked (or point to an existing one). **Back up the keystore file and passwords**; losing them blocks updates forever. |

3. When it finishes, you will have a directory (often named after the app) containing **`app/`**, **`build.gradle`**, **`settings.gradle`**, **`gradlew`**, etc.

**Open this folder** in Android Studio: **File → Open** → select the **project root** Bubblewrap created (the one with `settings.gradle`).

---

## 4. Create your release keystore (if you have not already)

If Bubblewrap already created a keystore, skip to §5.

Otherwise, in Android Studio:

**Build → Generate Signed App Bundle or APK → APK → Create new…**

Or from a terminal:

```bash
keytool -genkey -v -keystore movienight-release.jks -keyalg RSA -keysize 2048 -validity 10000 -alias movienight
```

Store **`movienight-release.jks`**, the **alias**, and **passwords** in a password manager.

---

## 5. SHA-256 fingerprint (required for Digital Asset Links)

Google must see a **SHA-256 certificate fingerprint** that matches the key that signs your **release** APK.

List the keystore (use your path, alias, and store password):

```bash
keytool -list -v -keystore movienight-release.jks -alias movienight
```

Under **Certificate fingerprints**, copy the **SHA256** line, e.g.:

`SHA256: AA:BB:CC:DD:...`

You will paste that value into Render (next section). This repo’s server strips the `SHA256:` prefix if you include it.

**Google Play App Signing:** If you later upload an **AAB**, Google may re-sign with an **app signing key**. You must add **both** fingerprints to `ANDROID_TWA_SHA256` (comma- or newline-separated): your **upload** key and the **app signing** key from Play Console → **Setup → App signing**. Until then, one fingerprint is enough for sideloaded APKs signed with your local keystore.

---

## 6. Publish Digital Asset Links from Movie Night

The app exposes:

`https://YOUR_DOMAIN/.well-known/assetlinks.json`

when these **environment variables** are set on **Render** (or any host):

| Variable | Example |
| :--- | :--- |
| `ANDROID_TWA_PACKAGE` | `com.yourfamily.movienight` (must match Bubblewrap Application ID) |
| `ANDROID_TWA_SHA256` | `AA:BB:CC:...` (from §5; multiple allowed, comma-separated) |

1. In Render → your Web Service → **Environment**, add both variables.
2. **Save** and **redeploy** (or wait for auto-deploy).
3. Verify in a browser:

`https://YOUR_DOMAIN/.well-known/assetlinks.json`

You should see **HTTP 200** and a JSON **array** with `relation` and `target.package_name` / `sha256_cert_fingerprints`.

If you see **404**, the vars are missing or empty.

Optional check: [Statement List Generator / Google asset links](https://developers.google.com/digital-asset-links/tools/generator) (or search “digital asset links statement list tool”).

---

## 7. Configure signing in Android Studio

1. Open the Bubblewrap project in Android Studio.
2. Put your **`movienight-release.jks`** somewhere **outside** public git (e.g. `~/keys/`).
3. **Recommended:** use **`keystore.properties`** (gitignored locally) referenced from `app/build.gradle` — Bubblewrap’s generated project may already include signing stubs; follow [Android sign your release](https://developer.android.com/studio/publish/app-signing#sign_release) if you need to wire the keystore manually.

Typical pattern:

- `keystore.properties`:

```properties
storePassword=****
keyPassword=****
keyAlias=movienight
storeFile=C:/Users/you/keys/movienight-release.jks
```

- Read that file in `app/build.gradle` for `signingConfigs.release`.

**Do not commit** `keystore.properties` or `.jks` to GitHub.

---

## 8. Build the release APK

In Android Studio:

1. **Build → Select Build Variant…** → **release** (if applicable).
2. **Build → Generate Signed App Bundle / APK**.
3. Choose **APK** (or **Android App Bundle** for Play).
4. Select your release keystore, alias, passwords.
5. Finish; the **APK** path is shown in the **Build** output (often `app/release/app-release.apk`).

CLI alternative from the project directory:

```bash
./gradlew assembleRelease
```

(Use `gradlew.bat` on Windows.)

---

## 9. Install and verify TWA behavior

1. Copy **`app-release.apk`** to a device (USB, Drive, etc.).
2. Enable **Install unknown apps** for your file manager / browser.
3. Install and open **Movie Night**. It should open your **site** in a **trusted** full-screen web layer (no browser address bar) **after** Digital Asset Links validate.

If it falls back to a normal browser tab, recheck:

- `assetlinks.json` **200** on the **exact** host the TWA uses.
- **Package name** and **SHA-256** match the **signing key** of the installed APK.
- Wait a few minutes after deploy (CDN / cache).

---

## 10. Ongoing updates

- **Website-only changes** (HTML, CSS, API): redeploy the FastAPI app; users get updates on next launch—**no new APK** required.
- **Change package name, launcher icon, or signing identity**: treat as a new app or new signing setup; update **`ANDROID_TWA_***`** env vars and rebuild the APK.

---

## Troubleshooting

| Issue | What to check |
| :--- | :--- |
| Bubblewrap **init** fails | Manifest URL must be **https** and reachable: `/static/manifest.webmanifest` |
| **assetlinks** 404 | `ANDROID_TWA_PACKAGE` + `ANDROID_TWA_SHA256` on Render; redeploy |
| TWA shows Chrome toolbar | Asset Links mismatch (wrong fingerprint or package) |
| Gradle sync errors | SDK Platform + Build-Tools installed; JDK 17 |
| **405** on `HEAD /` in Render logs | Harmless probe; **GET /health** matters |

---

## Reference links

- [Trusted Web Activity overview](https://developer.chrome.com/docs/android/trusted-web-activity/overview/)
- [Bubblewrap GitHub](https://github.com/GoogleChromeLabs/bubblewrap)
- [Digital Asset Links](https://developers.google.com/digital-asset-links/v1/getting-started)

Your FastAPI app serves **`/.well-known/assetlinks.json`** from `app/asset_links.py` using the env vars above—no separate static file host required.
