"""Load local image files (by filesystem path) into base64 data URLs for
ModelArk's multimodal `input_image` content blocks.

Unlike app/services/research/input.py's load_visual_assets (which resolves
paths relative to the backend workspace root, for user-uploaded brief
assets), this loads arbitrary local filesystem paths for already-generated
campaign assets (product images, etc.) that the frontend/generation
pipeline saved to disk and passed back as absolute paths.

Studio-generated assets specifically travel to the frontend as `/media/...`
URLs (app/api/v1/endpoints/studio.py's `_to_url` rewrites every local path
under `studio_settings.DATA_DIR` that way before it reaches the browser),
and the frontend has no reason to know or reconstruct the original
filesystem path — it only ever sees the URL. Since this QA agent runs in
the same backend process as the studio and therefore shares its DATA_DIR,
`_resolve_media_path` below reverses that rewrite so a `/media/...` value
coming back from the frontend resolves to the real file on disk instead of
being rejected as an unreadable "remote URL".
"""
from __future__ import annotations

import base64
import logging
import mimetypes
import pathlib
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp", "image/tiff"}
_MAX_IMAGE_BYTES = 20 * 1024 * 1024

# Video is not supported by ModelArk's multimodal input_image content block
# (images only) — see app/services/research/client.py._user_content. Video
# checklist items are verified from metadata/text fields only (duration,
# format, URL/path presence), not actual frame content.
_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".avi", ".mkv"}

_MEDIA_URL_PREFIX = "/media/"


def is_video_path(path: str) -> bool:
    return pathlib.Path(path).suffix.lower() in _VIDEO_EXTENSIONS


def _resolve_media_path(path: str) -> str | None:
    """Reverse the studio's `/media/...` URL rewrite back to a real local
    file path under `studio_settings.DATA_DIR`, if `path` is one of those
    URLs (absolute, e.g. "http://localhost:8000/media/<id>/media/hero.png",
    or relative, e.g. "/media/<id>/media/hero.png"). Returns None if `path`
    is not a studio media URL at all, so the caller falls through to
    treating it as a plain local path.

    Imported lazily to avoid a hard dependency from the QA agent module on
    the studio package for callers that never touch studio-generated
    assets (e.g. unit tests that stub image loading entirely).
    """
    relative = None
    parsed = urlparse(path)
    if parsed.scheme in ("http", "https"):
        if parsed.path.startswith(_MEDIA_URL_PREFIX):
            relative = parsed.path[len(_MEDIA_URL_PREFIX):]
    elif path.startswith(_MEDIA_URL_PREFIX):
        relative = path[len(_MEDIA_URL_PREFIX):]

    if relative is None:
        return None

    from app.services.studio.config import studio_settings

    return str(pathlib.Path(studio_settings.DATA_DIR) / relative)


def load_local_image(path: str) -> tuple[str | None, str]:
    """Load one local image file path into a base64 data URL.

    Returns (data_url, note). data_url is None (with an explanatory note)
    when the path is missing, unreadable, or not a supported image type —
    callers should treat that as "could not inspect the actual image" and
    let the verifier agent judge FAIL for image-dependent criteria, rather
    than raising and aborting the whole checklist run.
    """
    if not path or not path.strip():
        return None, "Đường dẫn ảnh rỗng."

    resolved = _resolve_media_path(path)
    if resolved is not None:
        path = resolved
    elif path.startswith(("http://", "https://")):
        return None, f"Đường dẫn là remote URL, không phải local file path: {path}"

    file_path = pathlib.Path(path)
    if not file_path.is_file():
        return None, f"Không tìm thấy file ảnh tại đường dẫn local: {path}"
    mime_type = mimetypes.guess_type(file_path.name)[0]
    if mime_type not in _ALLOWED_IMAGE_TYPES:
        return None, f"Định dạng ảnh không hỗ trợ: {path} ({mime_type})"
    size = file_path.stat().st_size
    if size > _MAX_IMAGE_BYTES:
        return None, f"Ảnh vượt quá 20 MB: {path}"
    try:
        encoded = base64.b64encode(file_path.read_bytes()).decode("ascii")
    except OSError as exc:
        logger.warning("qa_agent.image_load_failed path=%s error=%s", path, exc)
        return None, f"Không thể đọc file ảnh: {path} ({exc})"
    return f"data:{mime_type};base64,{encoded}", f"Đã tải ảnh thành công: {path}"


def load_local_images(paths: list[str]) -> tuple[list[str], list[str]]:
    """Load multiple local image paths. Returns (data_urls, notes) — one
    note per input path (including failures), aligned by index. Only
    successfully loaded images are included in data_urls."""
    data_urls: list[str] = []
    notes: list[str] = []
    for path in paths:
        data_url, note = load_local_image(path)
        notes.append(note)
        if data_url:
            data_urls.append(data_url)
    return data_urls, notes
