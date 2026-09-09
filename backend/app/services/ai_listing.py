import json

from openai import OpenAI

from ..config import OPENAI_API_KEY, OPENAI_MODEL

SYSTEM_PROMPT = """You help a person write a Facebook Marketplace listing for a \
single used item they're selling locally, e.g. while moving. You are given \
either a reference product (a similar item found via reverse image search, \
with its typical/listed price) or no reference at all, plus the seller's own \
condition, dimensions, keywords (brand/model/name they already know), and \
notes for THIS specific physical item.

The reference product comes in one of two trust levels, stated below it:
- CONFIRMED MATCH: a person looked at the image-search results and manually \
picked this exact product as correctly identifying the item. Its name, \
brand, and model ARE trustworthy - use them prominently and specifically in \
the title and description (e.g. the real brand/model name, not a vague \
paraphrase). Only its other specifics - exact color/finish/variant, price, \
implied condition - may not match this particular used unit, so defer to \
the seller's own dimensions/keywords/notes wherever those conflict with it.
- UNCONFIRMED / NO MATCH: no person verified this reference (it's either \
absent, or just whatever loose label the seller typed in). Treat it as a \
weak, low-confidence guess for everything, including the product identity \
itself.

Either way, the seller's own dimensions, keywords, and notes describe the \
actual item in hand and ALWAYS take priority over anything the reference \
implies when they conflict - adjust the title/description/price accordingly \
rather than just restating the reference's specs.

Pull out and mention as many concrete, buyer-relevant attributes as you can \
find: material, color/finish, original manufacturer/brand, model/model \
number, capacity/size, notable design features, and whether it's a \
recognized premium or luxury brand (call this out explicitly when it is - \
e.g. "by [designer/brand], a premium/high-end line" - buyers searching for \
a specific brand will look for that word). These are exactly what buyers \
scan listings for, and a vague description gets fewer responses than one \
that says what the item actually looks, feels, and is made of. Look for \
these in three places, in this priority order: the seller's own keywords/ \
notes (always trust these first if they mention an attribute), then the \
reference product's title/brand when those don't already cover it. Include \
every relevant detail you can support from the given information rather \
than trimming to a couple - more concrete, accurate detail is always better \
than a shorter, vaguer listing. Do not invent specifics (a serial number, an \
exact year, a warranty) that aren't implied by anything given to you.

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
If the item is from a recognized premium/luxury or highly sought-after \
brand with strong resale demand, it's reasonable to price at the high end \
of the range or slightly above it, since such brands typically hold value \
better than generic mass-market goods - say so in your reasoning when this \
applies. If no reference price is available, use the category/condition/notes \
to give your best rough estimate and say so plainly in your reasoning.

This is a pickup-only listing. Include a sentence close to this exact \
pattern: "Buyer is responsible for pickup and transportation from \
<pickup area>." - substituting the actual "Pickup area" value given below, \
verbatim, for <pickup area>. Never write a vague placeholder instead of the \
real value, such as "the specified location," "my area," or "the pickup \
location" - if a real pickup area was given, name it explicitly. Never say \
or imply that the seller will deliver, ship, or drop off the item. If any \
pickup notes are given below, fold them in naturally too.

Respond with ONLY a JSON object with these exact keys:
- "title": short listing title (no price or emojis)
- "description": plain text, no markdown. Normally 2-4 sentences, but go up \
to roughly double that (e.g. 6-8 sentences) when there's enough real detail \
- from the seller's notes/dimensions or a confirmed reference - to support \
it. Never pad it with filler or invented specifics just to make it longer.
- "category": a short category label (e.g. "Furniture", "Electronics")
- "suggested_price": a number (no currency symbol)
- "reasoning": one sentence explaining the suggested price
"""


RECOMMEND_SYSTEM_PROMPT = """You help pick which product from a reverse-image-search \
result list most likely matches a specific used item a person is selling, based on \
whatever hint they've typed so far (title/category/keywords such as brand, model, or \
name - may be blank or generic) and how many of their photos each result was \
recognized from - a higher count is a much stronger signal it's a genuine match, \
since it was recognized from multiple angles rather than a single coincidental \
resemblance. When keywords are given, a candidate whose title actually matches them \
(the right brand/model name) is a strong signal even if its photo count is lower.

Respond with ONLY a JSON object: {"recommended_id": <id or null>, "reasoning": "<one \
sentence>"}. Use null for recommended_id if nothing looks like a plausible match - \
e.g. the candidates are all clearly different categories from each other and from \
the hint, or seen_in_photos is 1 for everything with no other signal to go on. Don't \
force a pick you're not reasonably confident in; a wrong recommendation is worse \
than no recommendation.
"""


class AIListingError(RuntimeError):
    pass


def recommend_match(*, item_hint: str, comps: list[dict]) -> dict:
    """Best-effort: ask the model which pooled comp is most likely the real
    match. Never raises, regardless of what's fed in - callers treat this as
    an optional hint, not a required step, so any failure just means no
    recommendation this time rather than breaking the search itself."""
    try:
        if not OPENAI_API_KEY or not comps:
            return {"recommended_id": None, "reasoning": ""}

        lines = [f"Item hint so far: {item_hint or 'none typed yet'}", "", "Candidates:"]
        for c in comps:
            price = f"${c['price']}" if c.get("price") is not None else "price unknown"
            lines.append(
                f'- id={c["id"]}: "{c["title"]}" ({price}), seen_in_photos={c["photo_count"]}'
            )
        user_prompt = "\n".join(lines)

        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": RECOMMEND_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        data = json.loads(response.choices[0].message.content)
        recommended_id = data.get("recommended_id")
        valid_ids = {c["id"] for c in comps}
        if recommended_id not in valid_ids:
            recommended_id = None
        return {
            "recommended_id": recommended_id,
            "reasoning": str(data.get("reasoning", "")).strip() if recommended_id else "",
        }
    except Exception:
        return {"recommended_id": None, "reasoning": ""}


def generate_listing(
    *,
    reference_title: str | None,
    reference_price: float | None,
    reference_currency: str | None,
    reference_confirmed: bool = False,
    category: str,
    condition: str,
    dimensions: str,
    keywords: str = "",
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
        trust_label = "CONFIRMED MATCH" if reference_confirmed else "UNCONFIRMED / NO MATCH"
        reference_line = f"Reference product ({trust_label}): {reference_title}"
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
            f"Keywords (brand/model/name): {keywords}" if keywords else "Keywords: none",
            f"Seller notes: {notes}" if notes else "Seller notes: none",
            f"Category hint: {category}" if category else "Category hint: none",
            f"Pickup area: {neighborhood}" if neighborhood else "Pickup area: not specified",
            f"Pickup notes: {pickup_notes}" if pickup_notes else "Pickup notes: none",
            "",
            "--- Reference product from image search ---",
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
