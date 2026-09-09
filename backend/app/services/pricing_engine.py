from dataclasses import dataclass


@dataclass
class Comp:
    title: str
    link: str
    price: float | None
    currency: str


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
