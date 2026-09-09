# Marketplace Seller Assistant

A personal tool to speed up selling a bunch of stuff on Facebook Marketplace
(e.g. when moving): upload photos of each item, get a reverse-image-search
price suggestion, review/edit the generated listing, then click through a
pre-filled Facebook Marketplace "create listing" form and publish it
yourself.

## How it works

1. **Seller profile** — enter your name, contact info, and general
   area/neighborhood once. Your full address is stored only for your own
   reference (e.g. arranging pickups); it is never sent to Facebook or shown
   in a listing.
2. **Upload photos** — drop in one or more photos of an item to create it.
3. **(optional) Keywords** — type in a brand, model, or name if you already
   know it. This can't change what the reverse image search itself finds
   (it's image-only, no text query), but it sharpens the AI recommendation
   below and gets folded into the final listing.
4. **Run price search** — calls [SerpApi](https://serpapi.com)'s Google Lens
   reverse image search once per photo of the item and pools the results into
   one list (more photos means more SerpApi calls/cost per item, but a better
   chance of finding the right match), each with a small thumbnail so the
   list is easy to scan. Results seen across more of your photos are sorted
   first, and a quick OpenAI call flags whichever one it thinks is the most
   likely match (weighing your keywords too) with a one-line reason — a hint
   only, it never picks for you.
5. **Pick the match** — choose which (if any) of the pooled results is
   actually your item. If it's not the kind of thing a search will ever find
   (a generic used towel, say), skip straight to manual entry.
6. **Condition &amp; dimensions** — set the item's condition, and optionally
   type in dimensions if they're not already on the matched product's page.
7. **Generate listing &amp; price** — one call to OpenAI (`gpt-4o-mini` by
   default) writes the title/description and proposes a price, reasoning
   from the matched product's price (or your own notes, in the manual path)
   discounted for condition. You can edit anything it produces, including
   the final price, before approving.
8. **Approve** — lock in the final price you're happy with.
9. **Publish-assist** — opens a real, visible Chrome window on your machine
   (reusing your saved Facebook login so you only log in once, even across
   multiple items' windows open at the same time) and pre-fills the
   Marketplace "create listing" form: photos, title, price, description,
   location. **It never clicks Publish.** You review the listing yourself in
   that window and publish it by hand.
10. Mark the item "posted" in the app once you've published it, so your item
   list stays an accurate to-do list of what's left.

Needs both `SERPAPI_API_KEY` (image search) and `OPENAI_API_KEY` (listing
generation) configured — see `backend/.env.example`.

## Important: read this before using the publish-assist feature

Facebook has **no public API** for creating personal Marketplace listings.
The only way to speed up posting is browser automation that drives your own
logged-in session — which is against Facebook's Terms of Service (automated
use of the platform) and carries some risk of your account being flagged,
challenged, or restricted, **even though a human always does the final
Publish click**. That's why this project:

- Never stores or handles your Facebook password. You log in by hand, once,
  in the real browser window the tool opens; your login session is then
  saved to `backend/.facebook_auth_state.json` (git-ignored, cookies only)
  and reused on future runs. Each publish-assist window is its own
  independent browser seeded from that saved login, rather than one shared
  browser profile — Chromium only allows a single live process per shared
  profile, so this is what lets you have more than one item's window open
  at once.
- Never clicks "Publish"/"List item" for you — always leaves that to you.
- Fills in whatever fields it can find and clearly logs (in the terminal)
  which fields it could/couldn't fill, since Facebook changes Marketplace's
  page structure periodically and the selectors in
  `backend/app/scripts/facebook_publish_assist.py` are best-effort. Expect to
  occasionally need to tweak that script if Facebook changes its UI.

If you'd rather not run any browser automation against Facebook at all, skip
step 5 and just use the app to generate the title/description/price, then
copy-paste into Marketplace yourself.

## Project layout

```
backend/    FastAPI app (SQLite DB, photo uploads, SerpApi pricing, publish-assist)
frontend/   React (Vite) UI
```

## Setup

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium   # only needed for the publish-assist feature
cp .env.example .env          # then fill in SERPAPI_API_KEY and PUBLIC_BASE_URL
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

`--host 0.0.0.0` makes the backend reachable from other devices on your
network, not just this machine (see [Access from other devices on your
WiFi](#access-from-other-devices-on-your-wifi) below). If you only ever plan
to use the app from this machine, `--host 127.0.0.1` is more locked-down.

`PUBLIC_BASE_URL` needs to be a URL that SerpApi's servers can reach to fetch
your uploaded photo. For local development, run a tunnel in another
terminal and point `PUBLIC_BASE_URL` at the https URL it gives you:

```bash
ngrok http 8000
```

Without `PUBLIC_BASE_URL` configured, everything works except "Run price
search" — you'll get a clear error telling you to set it up.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (default `http://127.0.0.1:5173`). It proxies
`/api` and `/uploads` to the backend on port 8000.

### Running under WSL (Windows)

The app runs fine in WSL2 — FastAPI, SQLite, Node, and Playwright's Chromium
are all normal Linux binaries. A few WSL-specific things to know:

- **`pip install` failing with `linker `cc` not found` or a `pydantic-core`/
  `greenlet` build error**: this means your WSL's default `python3` is newer
  than what the pinned dependency versions have pre-built wheels for, so pip
  tries to compile them from source (Rust for `pydantic-core`, C for
  `greenlet`) and there's no compiler installed. `requirements.txt` uses
  `>=` version bounds specifically so pip can pick a newer release with
  wheels available — if you still hit this, either run
  `pip install --upgrade pip` first (older pip resolves versions worse), or
  create the venv with an older Python you have installed, e.g.
  `python3.12 -m venv .venv` instead of `python3 -m venv .venv`.
- **Clone the repo inside WSL's own filesystem** (e.g. `~/marketapp`), not
  under `/mnt/c/...`. Crossing the Windows/WSL filesystem boundary makes
  `npm install` and Vite's file-watching noticeably slower and occasionally
  flaky.
- **Reaching the app from your phone** needs one extra step beyond
  `--host 0.0.0.0` — see [Access from other devices on your
  WiFi](#access-from-other-devices-on-your-wifi) below, WSL2 has its own
  virtual network separate from Windows' real network adapter.
- **The publish-assist browser window** needs GUI passthrough (WSLg) to
  display on your Windows desktop. This ships by default on Windows 11; on
  Windows 10 check `wsl --update` or use a third-party X server if it's not
  available.

## Access from other devices on your WiFi

Both dev servers are configured to listen on all network interfaces
(`--host 0.0.0.0` for the backend, `host: true` already set in
`frontend/vite.config.js`), so once both are running you can open the app
from your phone or another computer on the same network — handy for
snapping a photo on your phone and uploading it straight into the app.

1. Find the LAN IP of the machine running the app:
   - macOS: `ipconfig getifaddr en0` (or `en1` if you're on Wi-Fi via a
     different adapter)
   - Linux: `hostname -I`
   - Windows: `ipconfig` and look for the "IPv4 Address" under your Wi-Fi
     adapter
   - It'll look something like `192.168.1.42`.
2. On the other device (connected to the **same** WiFi network), open
   `http://<that-ip>:5173` — that's the whole frontend, working the same as
   on `localhost`.
3. Make sure both `uvicorn` (step above) and `npm run dev` are running with
   the settings already in this repo — no extra flags needed for the
   frontend, since `vite.config.js` already sets `host: true`.

If it doesn't connect, your machine's firewall may be blocking incoming
connections on ports `5173`/`8000` — allow them for your local network, or
temporarily disable the firewall to confirm that's the issue.

**Running this from WSL on Windows:** `--host 0.0.0.0` and `host: true`
alone are not enough — WSL2 has its own virtual network, separate from
Windows' real network adapter, so your phone can't reach it directly by
default.

- Easiest fix (Windows 11 / recent WSL): enable "mirrored" networking mode,
  which makes WSL share the host's network directly. Create
  `%UserProfile%\.wslconfig` with:
  ```
  [wsl2]
  networkingMode=mirrored
  ```
  then run `wsl --shutdown` and restart WSL. After that, use your Windows
  machine's normal LAN IP from `ipconfig`, same as any other setup.
- If mirrored mode isn't available, forward the ports from Windows to WSL's
  internal IP instead. From an **admin PowerShell**:
  ```powershell
  $wslIp = wsl hostname -I
  netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$wslIp
  netsh interface portproxy add v4tov4 listenport=5173 listenaddress=0.0.0.0 connectport=5173 connectaddress=$wslIp
  New-NetFirewallRule -DisplayName "MarketApp" -Direction Inbound -Protocol TCP -LocalPort 8000,5173 -Action Allow
  ```
  Your phone then hits the **Windows** machine's LAN IP, not any
  WSL-internal address. `$wslIp` changes on every WSL restart, so you'll
  need to re-run this after reboots unless you switch to mirrored mode.

**Security note:** this makes the app reachable by *any* device on that
WiFi network, with no login of any kind. That's normally fine on a home
network you trust, but avoid doing this on a shared/public/office WiFi —
anyone on it could read your contact info and item photos through the app,
or use it to open the Facebook publish-assist browser on your machine. Stop
both servers (or drop back to `--host 127.0.0.1` / remove `host: true`)
when you're not actively using this on a network you don't fully trust.

## Notes

- Photos are stored under `backend/app/static/uploads/<item_id>/` and the
  SQLite database at `backend/marketapp.db` — both are git-ignored, so your
  photos and listing data never get committed.
- The publish-assist browser window runs **on the machine running the
  backend**, not in a hosted/headless environment — it's meant to be run
  locally.
- The price suggestion comes from GPT reasoning over the specific product you
  selected (or your own manual notes); always sanity-check it before
  approving.
- There's no migration system — if you're updating an existing checkout and
  hit a database error after pulling changes, delete `backend/marketapp.db`
  and let it get recreated (you'll lose existing items/seller profile, so
  re-enter your seller profile once after).
- Comp thumbnails are read from SerpApi's `thumbnail` field (with `image` as
  a fallback). If thumbnails show up blank once you're using a real
  SERPAPI_API_KEY, the field name may differ from what's implemented in
  `backend/app/services/pricing_engine.py::extract_comps` - a one-line fix
  once you know the actual key from a real response.
