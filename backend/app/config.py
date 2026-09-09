import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR.parent / 'marketapp.db'}")

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Must be a publicly reachable base URL (e.g. an ngrok/cloudflared tunnel, or your
# deployment's real domain) so SerpApi's servers can fetch uploaded photos for
# reverse image search. Example: https://abcd1234.ngrok-free.app
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

# Where the Facebook publish-assist feature saves your logged-in session
# (cookies only, via Playwright's storage_state) so you only have to log into
# Facebook manually once. Never stores your Facebook password. Kept as a
# reusable auth snapshot rather than one shared persistent browser profile,
# so multiple publish-assist windows can be open at the same time - Chromium
# only allows one live process per persistent profile directory, which is
# why using a single shared profile broke the second concurrent window.
FACEBOOK_AUTH_STATE_PATH = os.getenv(
    "FACEBOOK_AUTH_STATE_PATH", str(BASE_DIR.parent / ".facebook_auth_state.json")
)
