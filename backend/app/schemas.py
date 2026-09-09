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


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    category: str
    condition: str
    price_suggested: float | None
    price_final: float | None
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
    price_final: float | None = None
    notes: str | None = None
