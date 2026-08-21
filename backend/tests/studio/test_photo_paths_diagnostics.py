"""
`_photo_paths` and the diagnostic it feeds must agree on what "no usable
product photo" means — see test_render_hero_missing_photo.py for what
happens downstream (in render_hero) when they don't have a photo to work
with at all.
"""
from __future__ import annotations

import logging

import pytest

from app.services.studio import demo_briefs, pipeline


@pytest.fixture
def pipeline_logs(caplog):
    """Listen where the records actually go.

    `app/main.py` sets `logging.getLogger("app").propagate = False`, and
    `conftest.py` imports the app through `TestClient`, so a record from
    `app.services.studio.pipeline` stops at the `app` logger and never reaches
    the root handler `caplog` installs. Attaching caplog's handler to `app`
    itself puts it back in the path without changing how the app logs in
    production.
    """
    app_logger = logging.getLogger("app")
    app_logger.addHandler(caplog.handler)
    previous = app_logger.level
    app_logger.setLevel(logging.WARNING)
    try:
        yield caplog
    finally:
        app_logger.removeHandler(caplog.handler)
        app_logger.setLevel(previous)


def _campaign_input():
    _, campaign_input = demo_briefs.build_pair("06_marou_chocolate", "test-campaign")
    return campaign_input


def test_photo_paths_filters_out_remote_urls(tmp_path):
    campaign_input = _campaign_input()
    local = tmp_path / "photo.jpg"
    local.write_bytes(b"fake")
    campaign_input.brand_kit.product_photo_urls = [
        "https://cdn.example.com/product.jpg", str(local),
    ]
    assert pipeline._photo_paths(campaign_input) == [str(local)]


def test_photo_paths_filters_out_unreadable_local_paths(tmp_path):
    campaign_input = _campaign_input()
    campaign_input.brand_kit.product_photo_urls = [str(tmp_path / "missing.jpg")]
    assert pipeline._photo_paths(campaign_input) == []


def test_photo_paths_empty_input_returns_empty_list():
    assert pipeline._photo_paths(None) == []


def test_warns_when_photos_were_provided_but_none_usable(pipeline_logs):
    campaign_input = _campaign_input()
    campaign_input.brand_kit.product_photo_urls = ["https://cdn.example.com/product.jpg"]

    with pipeline_logs.at_level(logging.WARNING, logger="app.services.studio.pipeline"):
        pipeline._warn_if_no_usable_photos(campaign_input, photos=[], campaign_id="c-1")

    assert any("no_usable_product_photos" in record.message for record in pipeline_logs.records)


def test_no_warning_when_a_usable_photo_exists(pipeline_logs):
    campaign_input = _campaign_input()
    campaign_input.brand_kit.product_photo_urls = ["https://cdn.example.com/product.jpg"]

    with pipeline_logs.at_level(logging.WARNING, logger="app.services.studio.pipeline"):
        pipeline._warn_if_no_usable_photos(campaign_input, photos=["/real/photo.jpg"], campaign_id="c-1")

    assert pipeline_logs.records == []


def test_no_warning_when_brief_never_provided_any_photo(pipeline_logs):
    campaign_input = _campaign_input()
    campaign_input.brand_kit.product_photo_urls = []

    with pipeline_logs.at_level(logging.WARNING, logger="app.services.studio.pipeline"):
        pipeline._warn_if_no_usable_photos(campaign_input, photos=[], campaign_id="c-1")

    assert pipeline_logs.records == []
