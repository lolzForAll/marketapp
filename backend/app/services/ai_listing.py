import json

from openai import OpenAI

from ..config import OPENAI_API_KEY, OPENAI_MODEL

SYSTEM_PROMPT = """You help a person write a Facebook Marketplace listing for a \
single used item they're selling locally, e.g. while moving. You are given \
either a reference product (a similar item found via reverse image search, \
with its typical/listed price) or no reference at all, plus the seller's own \
condition, dimensions, and notes for THIS specific physical item.

The reference product is only a rough starting point for what kind of item \
this is and a loose price anchor - it may be the wrong size, variant, \
material, or model, since it came from an automated image match, not a \
manual check. The seller's own dimensions and notes describe the actual \
item in hand and ALWAYS take priority: if they conflict with anything the \
reference product implies (a different size, a mismatched feature, a \
material called out in the notes, etc.), trust the seller's dimensions and \
notes and adjust the title/description/price accordingly - do not just \
restate the reference product's specs. If the reference and the seller's \
own details clearly describe different items, favor the seller's details \
and treat the reference price as a weak, low-confidence anchor.

Write an honest, concise marketplace listing: don't oversell or claim a \
condition better than stated. Suggest a fair resale price for this specific \
USED item, starting from the reference price (if any) and adjusting for \
condition using these typical local-resale ranges as your starting anchor, \
as a % of the reference/original price:
- new (unused, sealed/tags on): 70-90%
- like_new (used briefly, no visible wear): 55-75%
- good (normal light wear, fully functional): 40-60%
- fair (noticeable wear, still functional): 25-40%
- poor (heavy wear/damage, priced to move): 10-25%

Only go below a condition's range if the seller's notes give a concrete \
reason (e.g. broken part, missing pieces, stains) - do not default to the \
low end just because the item is used, especially for higher-value items. \
If no reference price is available, use the category/condition/notes to \
give your best rough estimate and say so plainly in your reasoning.

This is a pickup-only listing: the buyer is responsible for collecting the \
item themselves. Always state this plainly in the description (e.g. "buyer \
must pick up" / "local pickup only"), and mention the pickup area given \
below. Never say or imply that the seller will deliver, ship, or drop off \
the item.

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
    pickup_notes: str = "",
) -> dict:
    if not OPENAI_API_KEY:
        raise AIListingError(
            "OPENAI_API_KEY is not configured. Set it in backend/.env "
            "(see https://platform.openai.com/api-keys)."
        )

    if reference_title:
        reference_line = f"Reference product (rough anchor only, may not exactly match): {reference_title}"
        if reference_price:
            reference_line += f" (typically around {reference_price} {reference_currency or 'USD'} new/listed)"
    else:
        reference_line = (
            "No reference product was found or selected - estimate from the "
            "seller's own details below alone."
        )

    user_prompt = "\n".join(
        [
            "--- Seller's own details for THIS item (authoritative) ---",
            f"Condition: {condition}",
            f"Dimensions: {dimensions}" if dimensions else "Dimensions: not provided",
            f"Seller notes: {notes}" if notes else "Seller notes: none",
            f"Category hint: {category}" if category else "Category hint: none",
            f"Pickup area: {neighborhood}" if neighborhood else "Pickup area: not specified",
            f"Pickup notes: {pickup_notes}" if pickup_notes else "Pickup notes: none",
            "",
            "--- Reference product from image search (secondary, may be inexact) ---",
            reference_line,
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
