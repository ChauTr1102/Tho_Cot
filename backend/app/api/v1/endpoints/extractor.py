import traceback
import sys
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.services.extractor.agent import (
    extract_text_from_file_bytes,
    run_with_document_text,
    run_with_rendered_content,
    run_with_url_context,
)

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

class ExtractFileResponse(BaseModel):
    filename: str
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


@router.post("/extract-file", response_model=ExtractFileResponse)
async def extract_file_endpoint(
    file: UploadFile = File(...),
    model: str = Form(DEFAULT_MODEL),
) -> ExtractFileResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Vui lòng chọn file tài liệu.")

    try:
        content = await file.read()
        text = extract_text_from_file_bytes(content, file.filename)
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Không thể đọc nội dung văn bản từ file (file trống hoặc định dạng không hỗ trợ).")
        result = run_with_document_text(text, filename=file.filename, model_id=model)
    except ValueError as e:
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=502, detail=f"Lỗi khi trích xuất tài liệu: {e}")

    output_dict = result.model_dump()
    return ExtractFileResponse(filename=file.filename, data=output_dict)

