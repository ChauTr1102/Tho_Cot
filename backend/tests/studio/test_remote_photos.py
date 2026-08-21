"""
Product photographs that arrive as URLs.

The link flow ends here or it does not end at all. An extractor reads a product
page and reports image URLs; `pipeline._photo_paths` drops anything starting
with `http` — correctly, a URL is not a Brand Lock reference — with a comment
saying they are unusable "until downloaded". Nothing downloaded them. So pasting
a link produced a campaign with no photographs at all: every slot fell to
GENERATE and the model invented the packaging, which is the precise failure the
Brand Lock exists to prevent, reached by the path a new user is likeliest to
take.

These tests use no network. What is worth pinning is the handling, not the
fetching: what is refused, and where files are allowed to land.
"""
from __future__ import annotations

import io
from pathlib import Path

import pytest

from app.services.studio import from_research
from app.services.studio.config import studio_settings

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 200


class _Response:
    """The two attributes `fetch_remote_photos` reads off a urlopen result."""

    def __init__(self, content_type: str, body: bytes):
        self.headers = {"Content-Type": content_type}
        self._body = io.BytesIO(body)

    def read(self, size: int = -1) -> bytes:
        return self._body.read(size)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(studio_settings, "DATA_DIR", tmp_path)
    return tmp_path


def _serve(monkeypatch, responses: dict[str, _Response | Exception]):
    def fake_urlopen(request, timeout=None):
        url = request.full_url if hasattr(request, "full_url") else str(request)
        result = responses.get(url)
        if isinstance(result, Exception):
            raise result
        if result is None:
            raise OSError("not found")
        return result

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)


def test_an_image_url_becomes_a_local_file(data_dir, monkeypatch):
    url = "https://shop.example/p/hero.png"
    _serve(monkeypatch, {url: _Response("image/png", PNG)})

    saved, failed = from_research.fetch_remote_photos([url], "c-1")

    assert failed == []
    assert len(saved) == 1
    assert Path(saved[0]).read_bytes() == PNG
    # Beside uploaded photographs, so nothing downstream can tell how a picture
    # arrived — `resolve_photos` searches this directory first either way.
    assert Path(saved[0]).parent == data_dir / "c-1" / "source"


def test_a_page_that_is_not_an_image_is_refused(data_dir, monkeypatch):
    """A URL that 404s to an HTML error page still answers 200 with HTML on
    plenty of sites. Content-Type is what decides, not the extension."""
    url = "https://shop.example/p/missing.jpg"
    _serve(monkeypatch, {url: _Response("text/html", b"<html>404</html>")})

    saved, failed = from_research.fetch_remote_photos([url], "c-2")

    assert saved == []
    assert failed == [url]


def test_the_remote_filename_is_never_used(data_dir, monkeypatch):
    """The last segment of a URL is attacker-controlled and often not a filename
    at all. Files are named by position."""
    url = "https://shop.example/../../etc/passwd?x=1"
    _serve(monkeypatch, {url: _Response("image/jpeg", PNG)})

    saved, _ = from_research.fetch_remote_photos([url], "c-3")

    root = (data_dir / "c-3" / "source").resolve()
    assert len(saved) == 1
    assert Path(saved[0]).name == "web_00.jpg"
    assert Path(saved[0]).resolve().is_relative_to(root)


def test_an_oversized_file_is_refused(data_dir, monkeypatch):
    """A product photo is a few hundred kilobytes. Anything past the cap is not
    one, and downloading it is someone else's bandwidth and our disk."""
    url = "https://shop.example/p/huge.png"
    body = b"\x89PNG" + b"0" * (from_research.REMOTE_PHOTO_MAX_BYTES + 10)
    _serve(monkeypatch, {url: _Response("image/png", body)})

    saved, failed = from_research.fetch_remote_photos([url], "c-4")

    assert saved == []
    assert failed == [url]


def test_one_unreachable_url_does_not_lose_the_others(data_dir, monkeypatch):
    """A page that will not give up one picture is survivable: the kit is
    duller, not absent."""
    good, bad = "https://shop.example/a.png", "https://shop.example/b.png"
    _serve(monkeypatch, {good: _Response("image/png", PNG),
                         bad: OSError("connection reset")})

    saved, failed = from_research.fetch_remote_photos([bad, good], "c-5")

    assert len(saved) == 1
    assert failed == [bad]


def test_local_paths_are_left_alone(data_dir, monkeypatch):
    """Only http(s) is fetched. A filename belongs to `resolve_photos`."""
    _serve(monkeypatch, {})
    saved, failed = from_research.fetch_remote_photos(
        ["product_01.jpg", "/tmp/x.png", "ftp://host/y.png"], "c-6"
    )
    assert saved == []
    assert failed == []


def test_the_count_is_capped(data_dir, monkeypatch):
    urls = [f"https://shop.example/{i}.png" for i in range(20)]
    _serve(monkeypatch, {u: _Response("image/png", PNG) for u in urls})

    saved, _ = from_research.fetch_remote_photos(urls, "c-7")

    assert len(saved) == from_research.REMOTE_PHOTO_MAX_COUNT
