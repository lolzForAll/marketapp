import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import PUBLIC_BASE_URL
from ..database import get_db
from ..services import pricing_engine
from ..services.serpapi_client import SerpApiError, reverse_image_search
from .items import _serialize

router = APIRouter(prefix="/api/items", tags=["pricing"])


def _base_url(request: Request) -> str:
    return PUBLIC_BASE_URL or str(request.base_url).rstrip("/")


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

    primary_photo = item.photos[0]
    image_url = f"{PUBLIC_BASE_URL}/uploads/{item.id}/{primary_photo.filename}"

    try:
        raw = reverse_image_search(image_url)
    except SerpApiError as exc:
        raise HTTPException(502, str(exc)) from exc

    result = pricing_engine.analyze(raw, fallback_title=item.title)

    seller = db.get(models.SellerProfile, 1)
    neighborhood = seller.neighborhood if seller else ""

    # Replace any previous comps for this item with the fresh results.
    for comp in list(item.comps):
        db.delete(comp)
    for comp in result.comps:
        db.add(
            models.PriceComp(
                item_id=item.id,
                source_title=comp.title,
                source_link=comp.link,
                price=comp.price,
                currency=comp.currency,
            )
        )

    item.price_suggested = result.suggested_price
    if not item.title:
        item.title = result.suggested_title
    if not item.category:
        item.category = result.suggested_category
    if not item.description:
        item.description = pricing_engine.build_description(
            title=item.title,
            category=item.category,
            condition=item.condition,
            notes="",
            neighborhood=neighborhood,
        )
    if item.price_final is None:
        item.price_final = item.price_suggested
    item.status = models.STATUS_ANALYZED
    item.analyzed_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(item)

    return _serialize(item, request)
