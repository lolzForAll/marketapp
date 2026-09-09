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
3. **Run price search** — calls [SerpApi](https://serpapi.com)'s Google Lens
   reverse image search on the first photo, collects comparable listings,
   and suggests a price (median of the comps, with outliers trimmed) plus a
   draft title/description/category. You can edit any of it.
4. **Approve** — set a final price you're happy with and approve the item.
5. **Publish-assist** — opens a real, visible Chrome window on your machine
   (using a persistent profile so you only log into Facebook once) and
   pre-fills the Marketplace "create listing" form: photos, title, price,
   description, location. **It never clicks Publish.** You review the
   listing yourself in that window and publish it by hand.
6. Mark the item "posted" in the app once you've published it, so your item
   list stays an accurate to-do list of what's left.

## Important: read this before using the publish-assist feature

Facebook has **no public API** for creating personal Marketplace listings.
The only way to speed up posting is browser automation that drives your own
logged-in session — which is against Facebook's Terms of Service (automated
use of the platform) and carries some risk of your account being flagged,
challenged, or restricted, **even though a human always does the final
Publish click**. That's why this project:

- Never stores or handles your Facebook password. You log in by hand, once,
  in the real browser window the tool opens; a local Playwright browser
  profile (`backend/.browser_profile/`, git-ignored) remembers that login
  for next time, the same way a normal Chrome profile would.
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
uvicorn app.main:app --reload --port 8000
```

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

## Notes

- Photos are stored under `backend/app/static/uploads/<item_id>/` and the
  SQLite database at `backend/marketapp.db` — both are git-ignored, so your
  photos and listing data never get committed.
- The publish-assist browser window runs **on the machine running the
  backend**, not in a hosted/headless environment — it's meant to be run
  locally.
- The price suggestion is a heuristic based on a handful of visually similar
  listings; always sanity-check it against the comps shown in the UI before
  approving.
