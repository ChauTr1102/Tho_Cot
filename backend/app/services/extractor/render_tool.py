"""
TikTok Shop renders its content with client-side JavaScript, so:
    - requests/BeautifulSoup often retrieves only an empty HTML shell.
    - Gemini's built-in url_context tool (running on Google's servers) may also
        be blocked or fail to see JS-rendered content.

This file provides a fallback tool that uses Playwright to open a headless
browser, wait for rendering to finish, and extract text and product image URLs.
Use it when --render is enabled in agent.py.
"""

from __future__ import annotations
import json
import re
from typing import Optional

from playwright.sync_api import sync_playwright



#: Anything under this on either side is an icon, a tracking pixel or a badge,
#: not a product photograph. Measured against real listings: the smallest useful
#: product image on a marketplace is around 300px.
MIN_IMAGE_PX = 200

#: Path fragments that mark an image as furniture rather than product. A page's
#: logo and its payment-method icons are always in the DOM and never wanted.
_IMAGE_NOISE: tuple[str, ...] = (
    "logo", "icon", "sprite", "avatar", "favicon", "placeholder",
    "banner-ad", "tracking", "pixel", "1x1", "blank",
)


def _collect_images(page) -> list[str]:
    """Product image URLs from any page, best candidates first.

    This used to keep only URLs matching `tiktokcdn|byteimg|ibyteimg`, because
    it was written for TikTok Shop. Every other site therefore returned zero
    images — the extractor read a product page, reported its name, price and
    selling points, and handed the studio no photographs at all, which sends
    every slot to GENERATE and lets the model invent the packaging.

    Three sources, in order of how much a site means them. `og:image` is what a
    page chose to show when shared, JSON-LD `image` is what it declares to
    search engines, and `<img>` is everything else — filtered by rendered size,
    because the reliable difference between a product shot and a payment icon is
    how big it is on screen.
    """
    found: list[str] = []

    def add(url: str | None) -> None:
        if not url or not isinstance(url, str):
            return
        if not url.lower().startswith(("http://", "https://")):
            return
        lowered = url.casefold()
        if any(noise in lowered for noise in _IMAGE_NOISE):
            return
        if url not in found:
            found.append(url)

    for meta in ("og:image", "og:image:secure_url", "twitter:image"):
        try:
            for value in page.eval_on_selector_all(
                f'meta[property="{meta}"], meta[name="{meta}"]',
                "els => els.map(e => e.content).filter(Boolean)",
            ):
                add(value)
        except Exception:
            pass

    try:
        for blob in page.eval_on_selector_all(
            'script[type="application/ld+json"]',
            "els => els.map(e => e.textContent).filter(Boolean)",
        ):
            try:
                data = json.loads(blob)
            except Exception:
                continue
            for node in (data if isinstance(data, list) else [data]):
                if not isinstance(node, dict):
                    continue
                image = node.get("image")
                if isinstance(image, str):
                    add(image)
                elif isinstance(image, list):
                    for item in image:
                        add(item if isinstance(item, str) else (item or {}).get("url"))
                elif isinstance(image, dict):
                    add(image.get("url"))
    except Exception:
        pass

    try:
        # `naturalWidth` is the file's real size, not the CSS box, so a large
        # photograph scaled down to a thumbnail still reads as large.
        for entry in page.eval_on_selector_all(
            "img",
            "els => els.map(e => ({src: e.currentSrc || e.src, "
            "w: e.naturalWidth || 0, h: e.naturalHeight || 0}))",
        ):
            if (entry.get("w") or 0) >= MIN_IMAGE_PX and (entry.get("h") or 0) >= MIN_IMAGE_PX:
                add(entry.get("src"))
    except Exception:
        pass

    return found[:20]

def fetch_rendered_tiktok_shop(url: str, timeout_ms: int = 30000) -> dict:
    """
    Open a TikTok Shop URL with headless Chromium, wait for rendering, and return:
      - text: all visible page text (title, price, description, reviews, etc.)
      - images: image URLs (usually product or cover images)
      - title: the page's <title>

    Install first:
        pip install playwright
        playwright install chromium
    """
    result = {"text": "", "images": [], "title": ""}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale="vi-VN",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        try:
            page.goto(url, timeout=timeout_ms, wait_until="networkidle")
        except Exception:
            # Continue with whatever content rendered before a networkidle timeout.
            pass

        # Allow lazy-loaded components such as prices and images to render.
        page.wait_for_timeout(3000)

        try:
            result["title"] = page.title()
        except Exception:
            pass

        try:
            result["text"] = page.inner_text("body")
        except Exception:
            pass

        try:
            result["images"] = _collect_images(page)
        except Exception:
            pass

        browser.close()

    return result
