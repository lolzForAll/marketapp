from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import models
from .config import UPLOAD_DIR
from .database import Base, engine
from .routers import items, pricing, publish, seller

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Marketplace Seller Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(seller.router)
app.include_router(items.router)
app.include_router(pricing.router)
app.include_router(publish.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
