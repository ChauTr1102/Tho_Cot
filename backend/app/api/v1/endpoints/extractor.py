import traceback
import sys
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.extractor.agent import run_with_rendered_content, run_with_url_context

router = APIRouter()

DEFAULT_MODEL = "gemini-3.6-flash"

class ExtractRequest(BaseModel):
    url: str = Field(..., description="TikTok Shop product URL to extract")
    render: bool = Field(
        False,
        description="True = render the page with Playwright before sending it to Gemini (recommended). "
        "False = let Gemini read the URL with the url_context tool.",
    )
    model: str = Field(DEFAULT_MODEL, description="Gemini model used for extraction")

class ExtractResponse(BaseModel):
    url: str
    data: dict

@router.post("/extract", response_model=ExtractResponse)
def extract_endpoint(req: ExtractRequest) -> ExtractResponse:
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="URL is required")

    try:
        if req.render:
            result = run_with_rendered_content(req.url, req.model)
        else:
            result = run_with_url_context(req.url, req.model)
    except ValueError as e:
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=502, detail=f"Lỗi khi xử lý trích xuất: {e}")

    output_dict = result.model_dump()
    return ExtractResponse(url=req.url, data=output_dict)
