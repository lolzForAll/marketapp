import httpx

from ..config import SERPAPI_API_KEY

SERPAPI_URL = "https://serpapi.com/search.json"


class SerpApiError(RuntimeError):
    pass


def reverse_image_search(image_url: str) -> dict:
    """Run a Google Lens reverse image search via SerpApi for the given
    (publicly reachable) image URL and return the raw JSON response."""
    if not SERPAPI_API_KEY:
        raise SerpApiError(
            "SERPAPI_API_KEY is not configured. Set it in backend/.env "
            "(see https://serpapi.com/manage-api-key)."
        )

    params = {
        "engine": "google_lens",
        "url": image_url,
        "api_key": SERPAPI_API_KEY,
    }
    try:
        response = httpx.get(SERPAPI_URL, params=params, timeout=30.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise SerpApiError(f"SerpApi request failed: {exc}") from exc

    data = response.json()
    if data.get("error"):
        raise SerpApiError(f"SerpApi error: {data['error']}")
    return data
