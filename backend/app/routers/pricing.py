import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import PUBLIC_BASE_URL
from ..database import get_db
from ..services import pricing_engine
from ..services.ai_listing import AIListingError, generate_listing
from ..services.serpapi_client import SerpApiError, reverse_image_search
from .items import _serialize

router = APIRouter(prefix="/api/items", tags=["pricing"])


@router.post("/{item_id}/analyze", response_model=schemas.ItemOut)
def analyze_item(item_id: int, request: Request, db: Session = Depends(get_db)):
    item = db.get(models.Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    if not item.photos:
        raise HTTPException(400, "Add at least one photo before analyzing")

    if not PUBLIC_BASE_URL:
        raise HTTPException(
            400,
            "PUBLIC_BASE_URL is not configured. Reverse image search needs a "
            "publicly reachable URL for your uploaded photo (e.g. run "
            "`ngrok http 8000` and set PUBLIC_BASE_URL to the https URL it "
            "gives you). See the README for details.",
        )

    # Search every photo of the item and pool the results - a match might
    # only surface from one particular angle. Each photo is a separate
    # SerpApi call (and cost), so this runs once per "Run price search" click.
    pooled: list[pricing_engine.Comp] = []
    seen_links: set[str] = set()
    last_error: SerpApiError | None = None

    for photo in item.photos:
        image_url = f"{PUBLIC_BASE_URL}/uploads/{item.id}/{photo.filename}"
        try:
            raw = reverse_image_search(image_url)
        except SerpApiError as exc:
            last_error = exc
            continue
        for comp in pricing_engine.extract_comps(raw):
            key = comp.link or comp.title
            if key and key in seen_links:
                continue
            if key:
                seen_links.add(key)
            pooled.append(comp)

    if not pooled and last_error is not None:
        raise HTTPException(502, str(last_error))

    # Replace any previous comps for this item, and since they're gone,
    # any earlier match selection pointing at them is no longer valid.
    for comp in list(item.comps):
        db.delete(comp)
    for comp in pooled:
        db.add(
            models.PriceComp(
                item_id=item.id,
                source_title=comp.title,
                source_link=comp.link,
                price=comp.price,
                currency=comp.currency,
            )
        )
    item.match_status = models.MATCH_UNMATCHED
    item.selected_comp_id = None

    db.commit()
    db.refresh(item)

    return _serialize(item, request)


@router.post("/{item_id}/select-match", response_model=schemas.ItemOut)
def select_match(
    item_id: int,
    payload: schemas.SelectMatchIn,
    request: Request,
    db: Session = Depends(get_db),
):
    item = db.get(models.Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")

    if payload.reset:
        item.match_status = models.MATCH_UNMATCHED
        item.selected_comp_id = None
    elif payload.skip:
        item.match_status = models.MATCH_MANUAL
        item.selected_comp_id = None
    elif payload.comp_id is not None:
        comp = db.get(models.PriceComp, payload.comp_id)
        if not comp or comp.item_id != item.id:
            raise HTTPException(400, "That comp does not belong to this item")
        item.match_status = models.MATCH_MATCHED
        item.selected_comp_id = comp.id
    else:
        raise HTTPException(400, "Provide comp_id, skip, or reset")

    db.commit()
    db.refresh(item)
    return _serialize(item, request)


@router.post("/{item_id}/generate-listing", response_model=schemas.ItemOut)
def generate_listing_endpoint(item_id: int, request: Request, db: Session = Depends(get_db)):
    item = db.get(models.Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    if item.match_status not in (models.MATCH_MATCHED, models.MATCH_MANUAL):
        raise HTTPException(
            400, "Select a matching product (or choose to enter it manually) first"
        )

    reference_title = None
    reference_price = None
    reference_currency = None
    if item.match_status == models.MATCH_MATCHED:
        comp = db.get(models.PriceComp, item.selected_comp_id)
        if comp:
            reference_title = comp.source_title
            reference_price = comp.price
            reference_currency = comp.currency
    if not reference_title:
        reference_title = item.title or None

    seller = db.get(models.SellerProfile, 1)
    neighborhood = seller.neighborhood if seller else ""

    try:
        result = generate_listing(
            reference_title=reference_title,
            reference_price=reference_price,
            reference_currency=reference_currency,
            category=item.category,
            condition=item.condition,
            dimensions=item.dimensions,
            notes=item.notes,
            neighborhood=neighborhood,
        )
    except AIListingError as exc:
        raise HTTPException(502, str(exc)) from exc

    item.title = result["title"]
    item.description = result["description"]
    item.category = result["category"]
    item.price_suggested = result["suggested_price"]
    item.ai_price_reasoning = result["reasoning"]
    if item.price_final is None:
        item.price_final = item.price_suggested
    item.status = models.STATUS_ANALYZED
    item.analyzed_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(item)
    return _serialize(item, request)
