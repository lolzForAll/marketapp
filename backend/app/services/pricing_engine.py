from dataclasses import dataclass


@dataclass
class Comp:
    title: str
    link: str
    price: float | None
    currency: str
    photo_count: int = 1


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


def pool_comps(per_photo_comps: list[list[Comp]]) -> list[Comp]:
    """Merge comps found across multiple photos of the same item, counting how
    many distinct photos each one was found in. A comp recognized from
    several angles is a much stronger match signal than one seen only once,
    so the result is sorted by that count, highest first (ties keep the
    original discovery order)."""
    pooled: dict[str, Comp] = {}
    order: list[str] = []

    for comps in per_photo_comps:
        seen_in_this_photo: set[str] = set()
        for comp in comps:
            key = comp.link or comp.title
            if not key or key in seen_in_this_photo:
                continue
            seen_in_this_photo.add(key)
            if key in pooled:
                pooled[key].photo_count += 1
            else:
                pooled[key] = Comp(comp.title, comp.link, comp.price, comp.currency)
                order.append(key)

    result = [pooled[key] for key in order]
    result.sort(key=lambda c: c.photo_count, reverse=True)
    return result
