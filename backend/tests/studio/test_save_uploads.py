"""
Keeping the bytes the research stage was about to throw away.

The research endpoint reads each upload into memory, base64-encodes it for the
model, and lets it go. That is fine for research and fatal for the studio: a
campaign for a product with no folder under `sample_data/` resolved to no
photographs at all, so every slot fell to GENERATE and the model invented the
packaging — the failure that once rendered a real brand name as `COSRᴀ`.

The writer and the reader live in the same module on purpose. These tests assert
they agree: whatever `save_uploads` writes, `resolve_photos` must find.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.services.studio import from_research
from app.services.studio.config import studio_settings

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """Point DATA_DIR at a scratch directory for the duration of one test."""
    monkeypatch.setattr(studio_settings, "DATA_DIR", tmp_path)
    return tmp_path


def _asset(name: str, content: bytes = PNG):
    """One entry in the endpoint's `(label, filename, mime, bytes)` shape."""
    return ("product_photos[0]", name, "image/png", content)


def test_what_is_written_is_what_resolve_photos_finds(data_dir):
    """The whole point. Writer and reader must agree on the location, or the
    upload lands somewhere the renderer never looks."""
    from_research.save_uploads("c-1", [_asset("product_01.jpg")])

    found, missing = from_research.resolve_photos(
        ["product_01.jpg"], "c-1", "Sản Phẩm Hoàn Toàn Mới"
    )
    assert missing == []
    assert len(found) == 1
    assert Path(found[0]).read_bytes() == PNG


def test_a_campaign_with_no_uploads_resolves_nothing(data_dir):
    """Resolving nothing is the correct answer. Borrowing another brand's
    photographs is how a G7 coffee campaign became a serum bottle."""
    found, missing = from_research.resolve_photos(
        ["product_01.jpg"], "c-empty", "Sản Phẩm Hoàn Toàn Mới"
    )
    assert found == []
    assert missing == ["product_01.jpg"]


def test_filenames_cannot_escape_the_campaign_directory(data_dir):
    """The filename arrives from a browser upload and is attacker-controlled."""
    from_research.save_uploads(
        "c-2",
        [
            _asset("../../../../tmp/escaped.png"),
            _asset("/etc/passwd"),
        ],
    )
    source = data_dir / "c-2" / "source"
    written = sorted(p.name for p in source.iterdir())
    assert written == ["escaped.png", "passwd"]
    for path in source.iterdir():
        assert path.resolve().is_relative_to(source.resolve())


def test_empty_and_nameless_uploads_are_skipped(data_dir):
    saved = from_research.save_uploads(
        "c-3",
        [
            _asset("real.png"),
            _asset("empty.png", b""),
            _asset(""),
            _asset(".."),
        ],
    )
    assert [Path(p).name for p in saved] == ["real.png"]


def test_the_campaign_directory_is_created_on_demand(data_dir):
    assert not (data_dir / "c-4").exists()
    from_research.save_uploads("c-4", [_asset("a.png")])
    assert (data_dir / "c-4" / "source" / "a.png").is_file()


def test_a_second_research_run_replaces_the_files(data_dir):
    """Re-running research on the same campaign should leave one current set,
    not two generations of the same filename."""
    from_research.save_uploads("c-5", [_asset("p.png", b"first")])
    from_research.save_uploads("c-5", [_asset("p.png", b"second")])
    assert (data_dir / "c-5" / "source" / "p.png").read_bytes() == b"second"
