import json
import subprocess
import sys
import tempfile
from pathlib import Path

from .. import models
from ..config import BASE_DIR, UPLOAD_DIR


def launch_publish_assist(item: models.Item, neighborhood: str) -> None:
    """Kick off the semi-automated Facebook Marketplace publish-assist script
    as a separate, detached process. It opens a real visible browser on this
    machine, pre-fills the listing form, and always leaves the final
    'Publish' click to the human. Never runs headless and never handles
    Facebook credentials directly - login happens in the opened window."""

    photo_paths = [
        str(UPLOAD_DIR / str(item.id) / photo.filename) for photo in item.photos
    ]

    payload = {
        "title": item.title,
        "price": item.price_final,
        "description": item.description,
        "category": item.category,
        "neighborhood": neighborhood,
        "photo_paths": photo_paths,
    }

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=f"_item{item.id}.json", delete=False
    )
    json.dump(payload, tmp)
    tmp.close()
    payload_path = Path(tmp.name)

    backend_dir = BASE_DIR.parent  # .../backend
    subprocess.Popen(
        [sys.executable, "-m", "app.scripts.facebook_publish_assist", str(payload_path)],
        cwd=str(backend_dir),
        start_new_session=True,
    )
