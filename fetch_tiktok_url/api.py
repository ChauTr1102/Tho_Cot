"""
FastAPI service around agent.py: accepts a TikTok Shop URL, runs the extraction
pipeline (Agno + Gemini), saves the JSON result in the data/ directory, and
returns its file path.

Run with:

    pip install fastapi uvicorn
    uvicorn api:app --reload --port 8000

Example request:

    curl -X POST http://localhost:8000/extract \
      -H "Content-Type: application/json" \
      -d '{"url": "https://shop.tiktok.com/vn/pdp/...", "render": true}'

Response:

    {
      "path": "data/1a2b3c4d.json",
      "url": "https://shop.tiktok.com/vn/pdp/..."
    }

Note: this file directly imports the existing functions from agent.py
(run_with_url_context, run_with_rendered_content), so it should be placed in
the same directory as agent.py (along with fetch_tiktok_url/ and render_tool.py).
"""

from __future__ import annotations

import hashlib
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Reuse the logic from agent.py instead of copying it.
from fetch_tiktok_url.agent import run_with_url_context, run_with_rendered_content

DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_MODEL = "gemini-3.6-flash"

app = FastAPI(title="TikTok Shop Extractor API")


class ExtractRequest(BaseModel):
    url: str = Field(..., description="TikTok Shop product URL to extract")
    render: bool = Field(
        False,
        description="True = render the page with Playwright before sending it to Gemini (recommended, more accurate). "
        "False = let Gemini read the URL with the url_context tool.",
    )
    model: str = Field(DEFAULT_MODEL, description="Gemini model used for extraction")


class ExtractResponse(BaseModel):
    path: str
    url: str


def _make_filename(url: str) -> str:
    """Create a stable, readable filename from a URL: <timestamp>_<hash8>.json."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]
    return f"{ts}_{url_hash}.json"


@app.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest) -> ExtractResponse:
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="URL is required")

    try:
        if req.render:
            result = run_with_rendered_content(req.url, req.model)
        else:
            result = run_with_url_context(req.url, req.model)
    except Exception as e:
        # Print the traceback for debugging without leaking details in the API response.
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=502, detail=f"Error calling the Gemini API: {e}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    filename = _make_filename(req.url)
    file_path = DATA_DIR / filename

    output_dict = result.model_dump()
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(output_dict, f, ensure_ascii=False, indent=2)

    # Return a concise relative path (data/xxx.json).
    relative_path = f"{DATA_DIR.name}/{filename}"
    return ExtractResponse(path=relative_path, url=req.url)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}