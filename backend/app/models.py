import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

# Item lifecycle: draft -> analyzed -> approved -> publish_started -> posted
STATUS_DRAFT = "draft"
STATUS_ANALYZED = "analyzed"
STATUS_APPROVED = "approved"
STATUS_PUBLISH_STARTED = "publish_started"
STATUS_POSTED = "posted"


class SellerProfile(Base):
    """Singleton row (id=1) holding the seller's own details."""

    __tablename__ = "seller_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    full_name: Mapped[str] = mapped_column(String(200), default="")
    email: Mapped[str] = mapped_column(String(200), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")

    # Full address is kept for your own records (e.g. arranging pickups) but is
    # never sent to Facebook automatically. Marketplace listings only expose an
    # approximate area, so we use city/neighborhood for the actual listing.
    address: Mapped[str] = mapped_column(String(300), default="")
    city: Mapped[str] = mapped_column(String(120), default="")
    neighborhood: Mapped[str] = mapped_column(String(120), default="")

    preferred_contact_method: Mapped[str] = mapped_column(String(50), default="Facebook Messenger")
    pickup_notes: Mapped[str] = mapped_column(Text, default="")


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    title: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(100), default="")
    condition: Mapped[str] = mapped_column(String(50), default="good")

    price_suggested: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_final: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(String(30), default=STATUS_DRAFT)
    notes: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    analyzed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    approved_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    posted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

    photos: Mapped[list["ItemPhoto"]] = relationship(
        back_populates="item", cascade="all, delete-orphan", order_by="ItemPhoto.position"
    )
    comps: Mapped[list["PriceComp"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )


class ItemPhoto(Base):
    __tablename__ = "item_photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    filename: Mapped[str] = mapped_column(String(300))
    position: Mapped[int] = mapped_column(Integer, default=0)

    item: Mapped["Item"] = relationship(back_populates="photos")


class PriceComp(Base):
    """A comparable listing found via reverse image search, kept for the user to review."""

    __tablename__ = "price_comps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    source_title: Mapped[str] = mapped_column(String(300), default="")
    source_link: Mapped[str] = mapped_column(String(1000), default="")
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD")

    item: Mapped["Item"] = relationship(back_populates="comps")
