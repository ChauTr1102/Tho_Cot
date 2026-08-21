"""
QA agent image loading must see the same files the studio generated.

The studio writes generated assets under `studio_settings.DATA_DIR` and hands
the frontend `/media/...` URLs for them (app/api/v1/endpoints/studio.py's
`_to_url`); the frontend has no reason to ever see the real filesystem path.
When that same `/media/...` value comes back into `POST /verify-checklist`
as part of a `CampaignOutputDTO`, the QA agent (running in the same backend
process, sharing the same DATA_DIR) must resolve it back to a real file
instead of rejecting it as an unreadable remote URL.
"""
from __future__ import annotations

import pytest

from app.services.qa_agent import image_loader
from app.services.studio.config import studio_settings

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """Point DATA_DIR at a scratch directory for the duration of one test."""
    monkeypatch.setattr(studio_settings, "DATA_DIR", tmp_path)
    return tmp_path


def test_relative_media_url_resolves_to_real_file(data_dir):
    campaign_dir = data_dir / "c-1" / "media"
    campaign_dir.mkdir(parents=True)
    (campaign_dir / "hero.png").write_bytes(PNG)

    data_url, note = image_loader.load_local_image("/media/c-1/media/hero.png")

    assert data_url is not None, note
    assert data_url.startswith("data:image/png;base64,")


def test_absolute_media_url_resolves_to_real_file(data_dir):
    campaign_dir = data_dir / "c-2" / "media"
    campaign_dir.mkdir(parents=True)
    (campaign_dir / "sku.png").write_bytes(PNG)

    data_url, note = image_loader.load_local_image(
        "http://localhost:8000/media/c-2/media/sku.png"
    )

    assert data_url is not None, note
    assert data_url.startswith("data:image/png;base64,")


def test_missing_media_file_reports_not_found(data_dir):
    data_url, note = image_loader.load_local_image("/media/c-3/media/missing.png")

    assert data_url is None
    assert "Không tìm thấy" in note


def test_non_media_remote_url_is_still_rejected(data_dir):
    data_url, note = image_loader.load_local_image("https://example.com/hero.jpg")

    assert data_url is None
    assert "remote URL" in note


def test_plain_local_path_still_works(data_dir, tmp_path):
    image_path = tmp_path / "logo.png"
    image_path.write_bytes(PNG)

    data_url, note = image_loader.load_local_image(str(image_path))

    assert data_url is not None, note
    assert data_url.startswith("data:image/png;base64,")


def test_empty_path_reports_empty(data_dir):
    data_url, note = image_loader.load_local_image("")

    assert data_url is None
    assert "rỗng" in note
