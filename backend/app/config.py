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

# Where Playwright keeps the persistent browser profile (cookies/session) used
# for the Facebook publish-assist feature, so you only have to log into
# Facebook manually once. Never stores your Facebook password.
BROWSER_PROFILE_DIR = os.getenv(
    "BROWSER_PROFILE_DIR", str(BASE_DIR.parent / ".browser_profile")
)
