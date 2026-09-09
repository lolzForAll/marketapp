import json

from openai import OpenAI

from ..config import OPENAI_API_KEY, OPENAI_MODEL

SYSTEM_PROMPT = """You help a person write a Facebook Marketplace listing for a \
single used item they're selling locally, e.g. while moving. You are given \
either a reference product (a similar item found via reverse image search, \
with its typical/listed price) or no reference at all, plus the item's \
condition and optional dimensions.

Write an honest, concise marketplace listing: don't oversell or claim a \
condition better than stated. Suggest a fair resale price for this specific \
USED item, discounting from any reference price for condition and typical \
local resale expectations - a used item rarely sells for close to its new \
price. If no reference price is available, use the category/condition/notes \
to give your best rough estimate and say so plainly in your reasoning.

Respond with ONLY a JSON object with these exact keys:
- "title": short listing title (no price or emojis)
- "description": 2-4 sentences, plain text, no markdown
- "category": a short category label (e.g. "Furniture", "Electronics")
- "suggested_price": a number (no currency symbol)
- "reasoning": one sentence explaining the suggested price
"""


class AIListingError(RuntimeError):
    pass


def generate_listing(
    *,
    reference_title: str | None,
    reference_price: float | None,
    reference_currency: str | None,
    category: str,
    condition: str,
    dimensions: str,
    notes: str,
    neighborhood: str,
) -> dict:
    if not OPENAI_API_KEY:
        raise AIListingError(
            "OPENAI_API_KEY is not configured. Set it in backend/.env "
            "(see https://platform.openai.com/api-keys)."
        )

    if reference_title:
        reference_line = f"Reference product: {reference_title}"
        if reference_price:
            reference_line += f" (typically around {reference_price} {reference_currency or 'USD'} new/listed)"
    else:
        reference_line = (
            "No reference product was found or selected - estimate from the "
            "details below alone."
        )

    user_prompt = "\n".join(
        [
            reference_line,
            f"Condition: {condition}",
            f"Dimensions: {dimensions}" if dimensions else "Dimensions: not provided",
            f"Category hint: {category}" if category else "Category hint: none",
            f"Seller notes: {notes}" if notes else "Seller notes: none",
            f"Pickup area: {neighborhood}" if neighborhood else "Pickup area: not specified",
        ]
    )

    client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as exc:
        raise AIListingError(f"OpenAI request failed: {exc}") from exc

    try:
        data = json.loads(response.choices[0].message.content)
        return {
            "title": str(data["title"]).strip(),
            "description": str(data["description"]).strip(),
            "category": str(data.get("category") or category).strip(),
            "suggested_price": round(float(data["suggested_price"]), 2),
            "reasoning": str(data.get("reasoning", "")).strip(),
        }
    except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise AIListingError(f"Unexpected response from OpenAI: {exc}") from exc
