import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services.facebook_publisher import launch_publish_assist
from .items import _serialize

router = APIRouter(prefix="/api/items", tags=["publish"])


@router.post("/{item_id}/publish-assist", response_model=schemas.ItemOut)
def publish_assist(item_id: int, request: Request, db: Session = Depends(get_db)):
    item = db.get(models.Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    if item.status != models.STATUS_APPROVED:
        raise HTTPException(400, "Approve the item (with a final price) before publishing")

    seller = db.get(models.SellerProfile, 1)
    neighborhood = seller.neighborhood if seller else ""

    launch_publish_assist(item, neighborhood)

    item.status = models.STATUS_PUBLISH_STARTED
    db.commit()
    db.refresh(item)
    return _serialize(item, request)


@router.post("/{item_id}/mark-published", response_model=schemas.ItemOut)
def mark_published(item_id: int, request: Request, db: Session = Depends(get_db)):
    item = db.get(models.Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    item.status = models.STATUS_POSTED
    item.posted_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(item)
    return _serialize(item, request)
