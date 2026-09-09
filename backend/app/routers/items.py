import datetime
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session, selectinload

from .. import models, schemas
from ..config import PUBLIC_BASE_URL, UPLOAD_DIR
from ..database import get_db

router = APIRouter(prefix="/api/items", tags=["items"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


def _item_dir(item_id: int) -> Path:
    d = UPLOAD_DIR / str(item_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _save_photo(item_id: int, upload: UploadFile, position: int) -> str:
    ext = Path(upload.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {upload.filename}")
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = _item_dir(item_id) / filename
    with dest.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    return filename


def _base_url(request: Request) -> str:
    return PUBLIC_BASE_URL or str(request.base_url).rstrip("/")


def _serialize(item: models.Item, request: Request) -> schemas.ItemOut:
    out = schemas.ItemOut.model_validate(item)
    base = _base_url(request)
    for photo, src in zip(out.photos, item.photos):
        photo.url = f"{base}/uploads/{item.id}/{src.filename}"
    return out


@router.get("", response_model=list[schemas.ItemOut])
def list_items(request: Request, db: Session = Depends(get_db)):
    items = (
        db.query(models.Item)
        .options(selectinload(models.Item.photos), selectinload(models.Item.comps))
        .order_by(models.Item.created_at.desc())
        .all()
    )
    return [_serialize(i, request) for i in items]


@router.post("", response_model=schemas.ItemOut)
def create_item(
    request: Request,
    files: list[UploadFile] = File(...),
    title: str = Form(""),
    db: Session = Depends(get_db),
):
    if not files:
        raise HTTPException(400, "At least one photo is required")
    item = models.Item(title=title)
    db.add(item)
    db.commit()
    db.refresh(item)

    for position, upload in enumerate(files):
        filename = _save_photo(item.id, upload, position)
        db.add(models.ItemPhoto(item_id=item.id, filename=filename, position=position))
    db.commit()
    db.refresh(item)
    return _serialize(item, request)


@router.get("/{item_id}", response_model=schemas.ItemOut)
def get_item(item_id: int, request: Request, db: Session = Depends(get_db)):
    item = db.get(models.Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    return _serialize(item, request)


@router.patch("/{item_id}", response_model=schemas.ItemOut)
def update_item(
    item_id: int,
    payload: schemas.ItemUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    item = db.get(models.Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return _serialize(item, request)


@router.post("/{item_id}/photos", response_model=schemas.ItemOut)
def add_photos(
    item_id: int,
    request: Request,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    item = db.get(models.Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    next_position = len(item.photos)
    for offset, upload in enumerate(files):
        filename = _save_photo(item.id, upload, next_position + offset)
        db.add(
            models.ItemPhoto(
                item_id=item.id, filename=filename, position=next_position + offset
            )
        )
    db.commit()
    db.refresh(item)
    return _serialize(item, request)


@router.post("/{item_id}/approve", response_model=schemas.ItemOut)
def approve_item(item_id: int, request: Request, db: Session = Depends(get_db)):
    item = db.get(models.Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    if item.price_final is None:
        raise HTTPException(400, "Set a final price before approving")
    item.status = models.STATUS_APPROVED
    item.approved_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(item)
    return _serialize(item, request)


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    db.delete(item)
    db.commit()
    item_dir = UPLOAD_DIR / str(item_id)
    if item_dir.exists():
        shutil.rmtree(item_dir, ignore_errors=True)
    return None
