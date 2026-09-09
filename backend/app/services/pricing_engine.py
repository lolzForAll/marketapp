import statistics
from dataclasses import dataclass

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Furniture": [
        "chair", "table", "sofa", "couch", "desk", "dresser", "bookshelf",
        "bookcase", "cabinet", "nightstand", "bed frame", "mattress", "ottoman",
        "shelf", "wardrobe", "recliner",
    ],
    "Electronics": [
        "tv", "television", "monitor", "laptop", "computer", "speaker",
        "headphone", "camera", "console", "playstation", "xbox", "nintendo",
        "router", "printer", "tablet", "phone",
    ],
    "Kitchen & Dining": [
        "blender", "mixer", "toaster", "cookware", "pan", "pot", "knife set",
        "dish", "plate", "cup", "mug", "kettle", "microwave", "air fryer",
        "coffee maker", "kitchenware",
    ],
    "Home & Garden": [
        "lamp", "rug", "mirror", "vase", "planter", "grill", "patio",
        "garden", "tool", "ladder", "vacuum",
    ],
    "Clothing & Accessories": [
        "jacket", "shoes", "boots", "handbag", "purse", "watch", "jewelry",
        "dress", "coat",
    ],
    "Toys & Games": ["toy", "lego", "board game", "puzzle", "doll", "action figure"],
    "Sporting Goods": ["bike", "bicycle", "treadmill", "weights", "dumbbell", "golf", "skateboard"],
    "Baby & Kids": ["stroller", "crib", "car seat", "high chair"],
}


@dataclass
class Comp:
    title: str
    link: str
    price: float | None
    currency: str


@dataclass
class AnalysisResult:
    comps: list[Comp]
    suggested_price: float | None
    suggested_title: str
    suggested_category: str


def extract_comps(raw_serpapi_response: dict) -> list[Comp]:
    comps: list[Comp] = []
    for match in raw_serpapi_response.get("visual_matches", []):
        price_info = match.get("price") or {}
        comps.append(
            Comp(
                title=match.get("title", ""),
                link=match.get("link", ""),
                price=price_info.get("extracted_value"),
                currency=price_info.get("currency", "USD"),
            )
        )
    return comps


def guess_category(text: str) -> str:
    lowered = text.lower()
    best_category = "Other"
    best_hits = 0
    for category, keywords in CATEGORY_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in lowered)
        if hits > best_hits:
            best_hits = hits
            best_category = category
    return best_category


def suggest_price(comps: list[Comp]) -> float | None:
    prices = [c.price for c in comps if c.price and c.price > 0]
    if not prices:
        return None
    prices.sort()
    median = statistics.median(prices)
    # Trim comps that are wildly off (likely mismatched products) before
    # taking the final median, so one bad match doesn't skew the price.
    trimmed = [p for p in prices if median / 3 <= p <= median * 3] or prices
    return round(statistics.median(trimmed), 2)


def analyze(raw_serpapi_response: dict, fallback_title: str = "") -> AnalysisResult:
    comps = extract_comps(raw_serpapi_response)
    suggested_price = suggest_price(comps)

    suggested_title = fallback_title
    if not suggested_title and comps:
        suggested_title = comps[0].title

    combined_text = " ".join(c.title for c in comps) + " " + fallback_title
    suggested_category = guess_category(combined_text)

    return AnalysisResult(
        comps=comps,
        suggested_price=suggested_price,
        suggested_title=suggested_title,
        suggested_category=suggested_category,
    )


def build_description(
    title: str, category: str, condition: str, notes: str, neighborhood: str
) -> str:
    condition_label = {
        "new": "Brand new, never used",
        "like_new": "Like new, barely used",
        "good": "Good used condition",
        "fair": "Fair condition, shows some wear",
        "poor": "Well used, priced accordingly",
    }.get(condition, "Good used condition")

    lines = [title, "", condition_label + "."]
    if notes:
        lines.append(notes)
    lines.append("")
    lines.append("Pickup only" + (f" near {neighborhood}" if neighborhood else "") + ".")
    lines.append("Message me with any questions!")
    return "\n".join(lines)
