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
import re
from typing import Optional

from playwright.sync_api import sync_playwright


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
            srcs = page.eval_on_selector_all(
                "img", "els => els.map(e => e.src).filter(Boolean)"
            )
            # Filter out small icons and keep likely product images from TikTok CDNs.
            images = [
                s for s in dict.fromkeys(srcs)  # deduplicate while preserving order
                if re.search(r"(tiktokcdn|byteimg|ibyteimg)", s)
            ]
            result["images"] = images[:20]
        except Exception:
            pass

        browser.close()

    return result
