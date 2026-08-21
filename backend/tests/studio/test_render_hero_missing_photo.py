"""
render_hero must fail clearly, not crash confusingly, when no local product
photo is available.

Reported bug: in a deploy environment where `brand_kit.product_photo_urls`
resolved to nothing usable (all remote URLs, or paths that don't exist on
that filesystem — see pipeline.py's `_photo_paths`, which filters exactly
those out), `directed.build_nodes` set `photo = None` and passed it straight
through to `render_hero` -> `ark.to_data_uri(None)` -> `Path(None)`, which
raised:

    TypeError: argument should be a str or an os.PathLike object where
    __fspath__ returns a str, not 'NoneType'

three stack frames away from the actual problem. The graph executor already
catches this (graph.py's `_execute_node`) and fails just that one node
without crashing the whole run — the fix here is only about the error
message/type, making the failure self-explanatory instead of a confusing
pathlib internals leak.
"""
from __future__ import annotations

import pytest

from app.schemas.studio import AssetOrigin, ImageKind, Platform
from app.services.studio import ark, render
from app.services.studio.direct import WorkItem


def _hero_item() -> WorkItem:
    return WorkItem(
        slot_id="hero", platform=Platform.TIKTOK_SHOP, kind=ImageKind.HERO,
        origin=AssetOrigin.GENERATE, ratio="9:16", size="1024x1820",
        scene="the product, centred, lit as described",
    )


def test_render_hero_raises_clear_error_when_photo_is_none(tmp_path):
    with pytest.raises(ValueError) as exc:
        render.render_hero(_hero_item(), spine=None, product_photo=None,
                           label_text=[], out_dir=tmp_path)
    message = str(exc.value)
    assert "product photo" in message.lower()
    assert "hero" in message.lower()
    # Must not be the raw pathlib crash this replaces.
    assert "NoneType" not in message
    assert "__fspath__" not in message


def test_render_hero_raises_clear_error_when_photo_is_empty_string(tmp_path):
    with pytest.raises(ValueError):
        render.render_hero(_hero_item(), spine=None, product_photo="",
                           label_text=[], out_dir=tmp_path)


def test_to_data_uri_raises_clear_error_on_none():
    with pytest.raises(ValueError) as exc:
        ark.to_data_uri(None)
    assert "no path given" in str(exc.value)


def test_to_data_uri_raises_clear_error_on_missing_file(tmp_path):
    missing = tmp_path / "does_not_exist.jpg"
    with pytest.raises(ValueError) as exc:
        ark.to_data_uri(str(missing))
    assert "cannot read" in str(exc.value)


def test_to_data_uri_still_works_for_a_real_file(tmp_path):
    real = tmp_path / "photo.jpg"
    real.write_bytes(b"\xff\xd8\xff\xe0" + b"0" * 32)  # minimal JPEG-ish header
    data_uri = ark.to_data_uri(str(real))
    assert data_uri.startswith("data:")
