"""
Semi-automated Facebook Marketplace listing assist.

This script opens a real, visible browser window (using a persistent profile
so you only log into Facebook manually once) and pre-fills the "Create
listing" form with the item's title, price, description and photos.

It deliberately NEVER clicks "Publish" (or "Next"/"List item") for you. You
review the pre-filled listing yourself in the opened window and click publish
by hand. This keeps a human in the loop for every listing that goes out
under your account.

Heads up: Facebook regularly changes Marketplace's page structure, and
automating interactions with it is against Facebook's Terms of Service.
Using this script carries some risk of your account being flagged or
restricted, even though it never posts anything without your explicit,
manual click. Selectors here are best-effort and may need updates over time.

Usage: python -m app.scripts.facebook_publish_assist <path-to-payload.json>
The payload JSON has: title, price, description, category, neighborhood,
photo_paths (absolute paths on disk).
"""

import json
import sys
import time

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

from ..config import BROWSER_PROFILE_DIR

CREATE_LISTING_URL = "https://www.facebook.com/marketplace/create/item"


def _try_fill(page: Page, label_texts: list[str], value: str, what: str) -> bool:
    if not value:
        return False
    for label in label_texts:
        for locator in (
            page.get_by_label(label, exact=False),
            page.get_by_placeholder(label, exact=False),
        ):
            try:
                locator.first.fill(value, timeout=3000)
                print(f"  [ok] filled {what}")
                return True
            except Exception:
                continue
    print(f"  [skip] could not find a field for {what} - fill it in manually")
    return False


def _try_upload_photos(page: Page, photo_paths: list[str]) -> bool:
    if not photo_paths:
        return False
    try:
        page.locator('input[type="file"]').first.set_input_files(photo_paths, timeout=5000)
        print(f"  [ok] uploaded {len(photo_paths)} photo(s)")
        return True
    except Exception as exc:
        print(f"  [skip] could not auto-upload photos ({exc}) - add them manually")
        return False


def _wait_for_login(page: Page) -> None:
    if "login" not in page.url and "checkpoint" not in page.url:
        return
    print(
        "\nPlease log into Facebook in the opened browser window.\n"
        "Waiting up to 5 minutes for you to finish logging in...\n"
    )
    deadline = time.time() + 300
    while time.time() < deadline:
        if "login" not in page.url and "checkpoint" not in page.url:
            print("Logged in, continuing...\n")
            return
        time.sleep(1)
    print("Timed out waiting for login. You can log in and fill the form manually.")


def run(payload: dict) -> None:
    BROWSER_PROFILE_DIR_PATH = BROWSER_PROFILE_DIR
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            BROWSER_PROFILE_DIR_PATH,
            headless=False,
            viewport={"width": 1280, "height": 900},
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(CREATE_LISTING_URL, wait_until="domcontentloaded")

        _wait_for_login(page)

        if "marketplace/create" not in page.url:
            try:
                page.goto(CREATE_LISTING_URL, wait_until="domcontentloaded")
            except PlaywrightTimeoutError:
                pass

        print("Pre-filling listing form (best effort)...")
        _try_upload_photos(page, payload.get("photo_paths", []))
        _try_fill(page, ["Title"], payload.get("title", ""), "title")
        _try_fill(page, ["Price"], str(payload.get("price", "")), "price")
        _try_fill(
            page,
            ["Description", "Describe your item"],
            payload.get("description", ""),
            "description",
        )
        location = payload.get("neighborhood", "")
        if location:
            _try_fill(page, ["Location"], location, "location")

        category = payload.get("category", "")
        if category:
            print(
                f"  [manual] category dropdown left for you - pick something close to "
                f"'{category}'"
            )

        print(
            "\nDone pre-filling what we could. Please review every field, add/adjust "
            "photos or category as needed, and click Publish yourself when it looks "
            "right. This window will stay open until you close it.\n"
        )

        try:
            page.wait_for_event("close", timeout=0)
        except Exception:
            pass


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m app.scripts.facebook_publish_assist <payload.json>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        payload = json.load(f)
    run(payload)


if __name__ == "__main__":
    main()
