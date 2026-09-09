import datetime

from pydantic import BaseModel, ConfigDict


class SellerProfileIn(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    city: str = ""
    neighborhood: str = ""
    preferred_contact_method: str = "Facebook Messenger"
    pickup_notes: str = ""


class SellerProfileOut(SellerProfileIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ItemPhotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    position: int
    url: str = ""


class PriceCompOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source_title: str
    source_link: str
    price: float | None
    currency: str
    photo_match_count: int
    thumbnail_url: str


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    category: str
    condition: str
    dimensions: str
    keywords: str
    price_suggested: float | None
    price_final: float | None
    ai_price_reasoning: str
    match_status: str
    selected_comp_id: int | None
    recommended_comp_id: int | None
    match_recommendation_reasoning: str
    status: str
    notes: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    analyzed_at: datetime.datetime | None
    approved_at: datetime.datetime | None
    posted_at: datetime.datetime | None
    photos: list[ItemPhotoOut] = []
    comps: list[PriceCompOut] = []


class ItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    condition: str | None = None
    dimensions: str | None = None
    keywords: str | None = None
    price_final: float | None = None
    notes: str | None = None


class SelectMatchIn(BaseModel):
    comp_id: int | None = None
    skip: bool = False
    reset: bool = False
