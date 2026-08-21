"""ark.py is the only place the studio touches the network. These tests pin the
payload shapes that were verified experimentally — getting them wrong fails
silently in production (see `reference_images`, which returns 200 and does
nothing), so they are asserted here rather than trusted."""
import json

import pytest
import requests

from app.services.studio import ark


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload, self.status_code, self.ok = payload, status, status < 400
        self.text = str(payload)
        self.content = b"BINARY"

    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def task_dir(tmp_path, monkeypatch):
    """`create_video_task` writes a task record to DATA_DIR/tasks before it
    returns, so every test gets its own throwaway DATA_DIR."""
    monkeypatch.setattr(ark.studio_settings, "DATA_DIR", tmp_path)
    return tmp_path / "tasks"


def test_two_refs_are_sent_as_a_list_under_image(monkeypatch):
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured.update(json)
        return FakeResponse({"data": [{"url": "https://x/y.jpg"}]})

    monkeypatch.setattr(ark.requests, "post", fake_post)
    monkeypatch.setattr(ark.requests, "get", lambda *a, **k: FakeResponse({}))

    ark.generate_image("p", "2048x2048", refs=["data:a", "data:b"])

    assert captured["image"] == ["data:a", "data:b"]
    assert "reference_images" not in captured   # silently ignored by the API
    assert captured["watermark"] is False       # true stamps "AI generated"


def test_single_ref_is_sent_as_a_bare_string(monkeypatch):
    captured = {}
    monkeypatch.setattr(ark.requests, "post",
                        lambda url, headers=None, json=None, timeout=None:
                        (captured.update(json), FakeResponse({"data": [{"url": "u"}]}))[1])
    monkeypatch.setattr(ark.requests, "get", lambda *a, **k: FakeResponse({}))

    ark.generate_image("p", "2048x2048", refs=["data:a"])
    assert captured["image"] == "data:a"


def test_first_frame_forces_adaptive_ratio(monkeypatch):
    """The API rejects any other ratio for first-frame input:
    InvalidParameter.TaskTypeConstraint — ratio must be `adaptive`."""
    captured = {}
    monkeypatch.setattr(ark.requests, "post",
                        lambda url, headers=None, json=None, timeout=None:
                        (captured.update(json), FakeResponse({"id": "cgt-1"}))[1])

    ark.create_video_task("p", first_frame="data:a", ratio="9:16")
    assert captured["ratio"] == "adaptive"


def test_retries_then_succeeds_on_connection_error(monkeypatch):
    calls = {"n": 0}

    def flaky(*a, **k):
        calls["n"] += 1
        if calls["n"] < 3:
            raise requests.ConnectionError("DNS died")
        return FakeResponse({"data": [{"url": "u"}]})

    monkeypatch.setattr(ark.requests, "post", flaky)
    monkeypatch.setattr(ark.requests, "get", lambda *a, **k: FakeResponse({}))
    monkeypatch.setattr(ark.time, "sleep", lambda *_: None)

    ark.generate_image("p", "2048x2048")
    assert calls["n"] == 3


def test_api_rejection_raises_arkerror_without_retrying(monkeypatch):
    calls = {"n": 0}

    def rejecting(*a, **k):
        calls["n"] += 1
        return FakeResponse({"error": {"code": "AccessDenied"}}, status=403)

    monkeypatch.setattr(ark.requests, "post", rejecting)
    with pytest.raises(ark.ArkError) as exc:
        ark.generate_image("p", "2048x2048")
    assert exc.value.status == 403
    assert calls["n"] == 1   # a 403 will never succeed on retry


# --- the four rules below are the ones that fail silently or lose money ------

def test_generated_url_is_downloaded_immediately(monkeypatch):
    """Seedream returns a signed URL that expires in 24h. Callers get bytes."""
    fetched = []
    monkeypatch.setattr(ark.requests, "post",
                        lambda url, headers=None, json=None, timeout=None:
                        FakeResponse({"data": [{"url": "https://x/y.jpg"}]}))
    monkeypatch.setattr(ark.requests, "get",
                        lambda url, **k: (fetched.append(url), FakeResponse({}))[1])

    assert ark.generate_image("p", "2048x2048") == b"BINARY"
    assert fetched == ["https://x/y.jpg"]


def test_task_id_is_persisted_before_it_is_returned(monkeypatch, task_dir):
    """A 200-second render must survive a dropped connection: the id has to be
    on disk before the function returns, and the base64 first frame must not be
    (a data URI is megabytes and is never resubmitted — we only re-poll)."""
    monkeypatch.setattr(ark.requests, "post",
                        lambda url, headers=None, json=None, timeout=None:
                        FakeResponse({"id": "cgt-abc"}))

    task_id = ark.create_video_task("hook shot", first_frame="data:image/jpeg;base64," + "A" * 900)

    assert task_id == "cgt-abc"
    record = json.loads((task_dir / "cgt-abc.json").read_text(encoding="utf-8"))
    assert record["task_id"] == "cgt-abc"
    assert record["payload"]["ratio"] == "adaptive"
    assert "A" * 900 not in json.dumps(record)
    assert [t["task_id"] for t in ark.pending_video_tasks()] == ["cgt-abc"]


def test_refs_become_reference_image_roles_and_never_mix_with_a_first_frame(monkeypatch):
    """Seedance modes are mutually exclusive: first_frame / first_frame+last_frame
    / multimodal reference_image cannot be combined in one request."""
    captured = {}
    monkeypatch.setattr(ark.requests, "post",
                        lambda url, headers=None, json=None, timeout=None:
                        (captured.update(json), FakeResponse({"id": "cgt-2"}))[1])

    ark.create_video_task("p", refs=["data:a", "data:b"], ratio="9:16")
    roles = [c.get("role") for c in captured["content"] if c["type"] == "image_url"]
    assert roles == ["reference_image", "reference_image"]
    assert captured["ratio"] == "9:16"          # no first frame, so no forcing

    captured.clear()
    ark.create_video_task("p", first_frame="data:ff", refs=["data:a"])
    roles = [c.get("role") for c in captured["content"] if c["type"] == "image_url"]
    assert roles == ["first_frame"]             # refs dropped, never both


def test_inline_flag_fallback_when_toplevel_params_are_disabled(monkeypatch):
    captured = {}
    monkeypatch.setattr(ark.studio_settings, "VIDEO_USE_TOPLEVEL_PARAMS", False)
    monkeypatch.setattr(ark.requests, "post",
                        lambda url, headers=None, json=None, timeout=None:
                        (captured.update(json), FakeResponse({"id": "cgt-3"}))[1])

    ark.create_video_task("a mug rotating", first_frame="data:a", duration=10, resolution="720p")

    text = next(c["text"] for c in captured["content"] if c["type"] == "text")
    assert text.endswith("--resolution 720p --ratio adaptive --duration 10")
    assert "ratio" not in captured               # flags only, no top-level fields


def test_wait_video_task_downloads_both_urls_and_reports_elapsed(monkeypatch):
    monkeypatch.setattr(ark.time, "sleep", lambda *_: None)
    monkeypatch.setattr(ark.requests, "post",
                        lambda url, headers=None, json=None, timeout=None:
                        FakeResponse({"id": "cgt-4"}))
    ark.create_video_task("p", first_frame="data:a")

    polls = {"n": 0}

    def fake_get(url, headers=None, timeout=None, **k):
        if "/tasks/" in url:
            polls["n"] += 1
            if polls["n"] == 1:
                return FakeResponse({"status": "running"})
            return FakeResponse({"status": "succeeded", "content": {
                "video_url": "https://v/clip.mp4",
                "last_frame_url": "https://v/last.png"}})
        return FakeResponse({})

    monkeypatch.setattr(ark.requests, "get", fake_get)

    result = ark.wait_video_task("cgt-4")
    assert result.video_bytes == b"BINARY"
    assert result.last_frame_bytes == b"BINARY"
    assert result.elapsed_sec >= 0
    assert polls["n"] == 2


def test_a_paid_post_gets_a_ceiling_well_past_the_measured_latency(monkeypatch):
    """A two-reference image-to-image took 122.7s live on 21/08, against 38s for
    text-to-image. Under the 90s poll timeout that slow success read as a
    transport failure and `_retry` bought the render a second time, so a POST
    that creates paid work must clear the measured latency by a wide margin. A
    poll, which is a free GET, keeps the short timeout."""
    seen = {}
    monkeypatch.setattr(ark.requests, "post",
                        lambda url, headers=None, json=None, timeout=None:
                        (seen.update(post=timeout), FakeResponse({"data": [{"url": "u"}]}))[1])
    monkeypatch.setattr(ark.requests, "get",
                        lambda url, headers=None, timeout=None, **k:
                        (seen.update(get=timeout), FakeResponse(
                            {"status": "succeeded", "content": {"video_url": "u"}}))[1])

    ark.generate_image("p", "2048x2048", refs=["data:a", "data:b"])
    assert seen["post"] >= 300

    ark.wait_video_task("cgt-poll")
    assert seen["get"] == ark.studio_settings.POLL_TIMEOUT_SEC


def test_wait_video_task_raises_on_a_failed_task(monkeypatch):
    monkeypatch.setattr(ark.time, "sleep", lambda *_: None)
    monkeypatch.setattr(ark.requests, "get", lambda *a, **k: FakeResponse(
        {"status": "failed", "error": {"code": "InternalServiceError"}}))

    with pytest.raises(ark.ArkError):
        ark.wait_video_task("cgt-dead")
