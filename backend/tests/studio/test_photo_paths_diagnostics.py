"""
`_photo_paths` and the diagnostic it feeds must agree on what "no usable
product photo" means — see test_render_hero_missing_photo.py for what
happens downstream (in render_hero) when they don't have a photo to work
with at all.
"""
from __future__ import annotations

import logging

from app.services.studio import demo_briefs, pipeline


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


def test_warns_when_photos_were_provided_but_none_usable(caplog):
    campaign_input = _campaign_input()
    campaign_input.brand_kit.product_photo_urls = ["https://cdn.example.com/product.jpg"]

    with caplog.at_level(logging.WARNING, logger="app.services.studio.pipeline"):
        pipeline._warn_if_no_usable_photos(campaign_input, photos=[], campaign_id="c-1")

    assert any("no_usable_product_photos" in record.message for record in caplog.records)


def test_no_warning_when_a_usable_photo_exists(caplog):
    campaign_input = _campaign_input()
    campaign_input.brand_kit.product_photo_urls = ["https://cdn.example.com/product.jpg"]

    with caplog.at_level(logging.WARNING, logger="app.services.studio.pipeline"):
        pipeline._warn_if_no_usable_photos(campaign_input, photos=["/real/photo.jpg"], campaign_id="c-1")

    assert caplog.records == []


def test_no_warning_when_brief_never_provided_any_photo(caplog):
    campaign_input = _campaign_input()
    campaign_input.brand_kit.product_photo_urls = []

    with caplog.at_level(logging.WARNING, logger="app.services.studio.pipeline"):
        pipeline._warn_if_no_usable_photos(campaign_input, photos=[], campaign_id="c-1")

    assert caplog.records == []
