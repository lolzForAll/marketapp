from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/seller-profile", tags=["seller"])


def _get_or_create(db: Session) -> models.SellerProfile:
    profile = db.get(models.SellerProfile, 1)
    if profile is None:
        profile = models.SellerProfile(id=1)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("", response_model=schemas.SellerProfileOut)
def get_profile(db: Session = Depends(get_db)):
    return _get_or_create(db)


@router.put("", response_model=schemas.SellerProfileOut)
def update_profile(payload: schemas.SellerProfileIn, db: Session = Depends(get_db)):
    profile = _get_or_create(db)
    for field, value in payload.model_dump().items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile
