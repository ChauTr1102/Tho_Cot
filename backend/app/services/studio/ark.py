"""
BytePlus ModelArk client — the studio's only door to the network.

Every studio node that needs pixels, motion, a transcription or a voice comes
through here. Nothing else under `app/services/studio` may call `requests`
directly: the venue Wi-Fi dropped DNS mid-run during research, so a bare
`requests.post` is a bug waiting for the demo.

The module has three jobs.

1. **Speak the payload shapes that were measured, not the ones in the guide.**
   Several of them differ, and the measurement wins:
   - `reference_images` returns HTTP 200 and is *silently ignored*. Two
     references go in `image` as a list; one goes in `image` as a bare string.
   - `watermark` defaults to true server-side and stamps "AI generated" onto
     the picture, so it is always sent explicitly.
   - Seedance `ratio` **must** be `"adaptive"` when a first frame is supplied;
     anything else is rejected with `InvalidParameter.TaskTypeConstraint`. The
     output then inherits the first frame's aspect ratio, which is how
     platform-native ratios are produced without cropping.
   - Seedance modes are mutually exclusive: `first_frame` and multimodal
     `reference_image` may not appear in the same request.

2. **Fail in the right direction.** `_retry` retries transport failures only
   (`requests.ConnectionError`, `requests.Timeout`). An HTTP rejection — 403
   AccessDenied, 404, 400 InvalidParameter — raises `ArkError` on the spot: it
   will not become a 200 on the next attempt, and retrying an image generation
   costs 45 seconds and a credit.

3. **Never hand a caller something perishable.** A Seedance render takes
   134–543 seconds, so the task id is written to `DATA_DIR/tasks/{id}.json`
   before `create_video_task` returns and a dropped connection cannot lose it.
   Every URL the API returns is downloaded immediately — image URLs expire in
   24h, video in 48h — so callers receive bytes and the store keeps local paths.

Timeouts and retry counts come from `studio_settings`; nothing here is tuned at
the call site.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import requests

from app.services.studio.config import studio_settings

# A persisted task record keeps the prompt and the parameters, but a first-frame
# data URI is megabytes of base64 and is never replayed (resuming means
# re-polling an existing task, never resubmitting it), so long data URIs are
# collapsed to their header before the record is written.
_DATA_URI_KEEP_CHARS = 64


def _generation_timeout() -> int:
    """Per-request ceiling for a POST that *creates paid work*.

    Retrying one of these is not free. Seedream blocks until the picture exists,
    and while text-to-image answers in 38 seconds a **two-reference
    image-to-image took 122.7 seconds** (measured 21/08 — the research note of
    "35–60s" only covers the single-image case). `POLL_TIMEOUT_SEC` is 90s, so
    using it here turned a slow success into a read timeout, and `_retry`
    dutifully paid for the render again. Seedance task creation is worse still:
    a timeout while reading the response of a task that was accepted server-side
    would start a second 400-second render.

    So the ceiling is generous and the retry is the last resort, not the first.
    `config.py` has no field for this yet; the moment it gains
    `STUDIO_IMAGE_TIMEOUT_SEC` this picks it up, and until then it uses the
    widest generation budget the settings already express.
    """
    return int(getattr(studio_settings, "IMAGE_TIMEOUT_SEC", studio_settings.VISION_TIMEOUT_SEC))


class ArkError(Exception):
    """A BytePlus call that will not succeed by trying again.

    `status` is the HTTP status code when the API rejected the request, and `0`
    when the failure was not an HTTP rejection: transport retries exhausted, a
    task that came back `failed`/`cancelled`, or a task that outlived
    `TASK_MAX_WAIT_SEC`. `body` is the first 500 characters of the response, the
    part that carries BytePlus' `error.code` and request id.
    """

    def __init__(self, status: int, body: str, label: str = "call") -> None:
        self.status = status
        self.body = body
        self.label = label
        super().__init__(f"BytePlus {label} failed (status={status}): {body}")


@dataclass
class VideoResult:
    """A finished Seedance task, already downloaded.

    `last_frame_bytes` is a PNG and is only present when the task was created
    with `return_last_frame`; it is useful as a cover still or to extend a shot.
    `elapsed_sec` is measured from task *creation* when the persisted record is
    available, so it stays meaningful across a resumed poll.
    """

    video_bytes: bytes
    last_frame_bytes: bytes | None
    elapsed_sec: float


# --------------------------------------------------------------------------
# data URIs
# --------------------------------------------------------------------------

def _sniff_mime(raw: bytes) -> str:
    """Identify an image from its magic bytes (extensions lie, and QA tiles have none)."""
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    if raw[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    return ""


def bytes_to_data_uri(data: bytes, mime: str | None = None) -> str:
    """Wrap raw image bytes as a `data:` URI.

    Both Seedream (`image`) and Seedance (`content[].image_url.url`) accept data
    URIs directly — verified 21/08 — so the studio never uploads a file or needs
    a public URL. This is the in-memory counterpart of `to_data_uri`, used to
    pass a freshly rendered hero image on as the style anchor for the next
    render without a round trip through disk.
    """
    return f"data:{mime or _sniff_mime(data) or 'image/jpeg'};base64,{base64.b64encode(data).decode('ascii')}"


def to_data_uri(path: str | Path) -> str:
    """Read an image from disk and return it as a `data:` URI.

    Used for the Brand Lock reference: the brand's own product photo out of
    `sample_data/<brand>/assets/` becomes reference 1 of an image-to-image call.
    """
    p = Path(path)
    raw = p.read_bytes()
    return bytes_to_data_uri(raw, _sniff_mime(raw) or mimetypes.guess_type(p.name)[0])


# --------------------------------------------------------------------------
# transport
# --------------------------------------------------------------------------

def _headers() -> dict[str, str]:
    """Auth header for the ModelArk endpoints. Read at call time so a key
    supplied after import (tests, a re-exported env) is still picked up."""
    return {
        "Authorization": f"Bearer {studio_settings.ARK_API_KEY}",
        "Content-Type": "application/json",
    }


def _retry(fn: Callable[[], Any], label: str) -> Any:
    """Run `fn`, retrying **transport** failures with capped exponential backoff.

    Only `requests.ConnectionError` and `requests.Timeout` are retried. Those
    are the failures that recovered during research — DNS resolution vanished
    mid-run on venue Wi-Fi and came back seconds later. An HTTP error response
    is *not* retried here: `_raise_for_api` turns it into `ArkError` because a
    403 or a 404 will never become a 200, and a retried image generation costs
    another 45 seconds.
    """
    attempts = max(1, studio_settings.HTTP_RETRIES)
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            return fn()
        except (requests.ConnectionError, requests.Timeout) as exc:
            last = exc
            if attempt == attempts - 1:
                break
            time.sleep(min(2 ** attempt, studio_settings.HTTP_BACKOFF_CAP_SEC))
    raise ArkError(
        status=0,
        body=f"transport failed after {attempts} attempts: {last}",
        label=label,
    ) from last


def _raise_for_api(resp: Any, label: str) -> Any:
    """Turn a non-2xx response into `ArkError`, keeping the BytePlus error body.

    HTTP 200 is not proof a parameter took effect (see `reference_images`), but
    a non-200 is always proof the request was rejected.
    """
    if not resp.ok:
        raise ArkError(status=resp.status_code, body=str(resp.text)[:500], label=label)
    return resp


def _post_json(
    url: str,
    payload: dict[str, Any],
    *,
    label: str,
    timeout: int,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """POST JSON through the retry wrapper and return the decoded body."""
    hdrs = headers or _headers()
    resp = _retry(lambda: requests.post(url, headers=hdrs, json=payload, timeout=timeout), label)
    _raise_for_api(resp, label)
    return resp.json()


def _get_json(url: str, *, label: str, timeout: int) -> dict[str, Any]:
    """GET JSON through the retry wrapper and return the decoded body."""
    resp = _retry(lambda: requests.get(url, headers=_headers(), timeout=timeout), label)
    _raise_for_api(resp, label)
    return resp.json()


def download(url: str, label: str = "download") -> bytes:
    """Fetch a BytePlus asset URL and return its bytes.

    Called the moment a URL is handed back. The URLs are signed and short-lived
    (images 24h, video 48h), so a URL is never stored as the source of truth —
    the studio persists the downloaded file and its local path instead. No auth
    header is sent: these are pre-signed object URLs, not API endpoints.
    """
    resp = _retry(lambda: requests.get(url, timeout=studio_settings.POLL_TIMEOUT_SEC), label)
    _raise_for_api(resp, label)
    return resp.content


# --------------------------------------------------------------------------
# Seedream 5.0 Pro — images
# --------------------------------------------------------------------------

def generate_image(prompt: str, size: str, refs: list[str] | None = None) -> bytes:
    """Render one image with Seedream 5.0 Pro. `POST /images/generations`.

    `refs` are data URIs (from `to_data_uri` / `bytes_to_data_uri`) and drive the
    Brand Lock: reference 1 pins the product, reference 2 pins the scene,
    lighting and grade — verified by putting a mug from ref 1 onto the wet stone
    of ref 2 and getting exactly that. The wire shape is measured, not
    documented:

    * one reference  → `image` is a **bare string**
    * two or more    → `image` is a **list**
    * `reference_images` is never sent: it returns HTTP 200 and is silently
      ignored, producing the single-reference image while looking like it worked.

    `watermark` is always sent as `studio_settings.IMAGE_WATERMARK` (false),
    because the server-side default stamps "AI generated" across the picture.

    Text-to-image takes 35–60 seconds (38s measured), and ten concurrent
    requests finished in 44 seconds total, so callers should fan out rather than
    serialise. **A two-reference image-to-image is much slower — 122.7 seconds
    measured on 21/08** — which is why generation gets `_generation_timeout()`
    and not the poll timeout. Returns the downloaded bytes; the response URL
    expires in 24 hours.
    """
    payload: dict[str, Any] = {
        "model": studio_settings.SEEDREAM_MODEL,
        "prompt": prompt,
        "size": size,
        "response_format": "url",
        "watermark": studio_settings.IMAGE_WATERMARK,
    }
    if refs:
        payload["image"] = refs[0] if len(refs) == 1 else list(refs)

    body = _post_json(
        f"{studio_settings.ARK_BASE_URL}/images/generations",
        payload,
        label="seedream",
        timeout=_generation_timeout(),
    )
    try:
        url = body["data"][0]["url"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ArkError(status=0, body=f"unexpected response: {str(body)[:400]}", label="seedream") from exc
    return download(url, label="seedream-download")


# --------------------------------------------------------------------------
# Seedance 2.5 — video tasks
# --------------------------------------------------------------------------

def _task_dir() -> Path:
    """`DATA_DIR/tasks` — the crash-resume ledger. Resolved per call so a test
    or a per-campaign override of DATA_DIR is honoured."""
    d = Path(studio_settings.DATA_DIR) / "tasks"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _redact_data_uris(value: Any) -> Any:
    """Collapse long `data:` URIs so a task record stays a few kilobytes."""
    if isinstance(value, dict):
        return {k: _redact_data_uris(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_data_uris(v) for v in value]
    if isinstance(value, str) and value.startswith("data:") and len(value) > _DATA_URI_KEEP_CHARS:
        head = value.split(",", 1)[0]
        return f"{head},<{len(value)} chars omitted>"
    return value


def _write_task_record(task_id: str, payload: dict[str, Any]) -> None:
    """Persist a submitted video task before its id is handed to the caller."""
    record = {
        "task_id": task_id,
        "model": payload.get("model"),
        "created_at": time.time(),
        "status": "submitted",
        "payload": _redact_data_uris(payload),
    }
    (_task_dir() / f"{task_id}.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _read_task_record(task_id: str) -> dict[str, Any]:
    """Load a persisted task record, or `{}` when there is none."""
    p = _task_dir() / f"{task_id}.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _update_task_record(task_id: str, **fields: Any) -> None:
    """Best-effort status update. Bookkeeping must never break a render."""
    record = _read_task_record(task_id)
    if not record:
        return
    record.update(fields)
    try:
        (_task_dir() / f"{task_id}.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError:
        pass


def pending_video_tasks() -> list[dict[str, Any]]:
    """Every video task that was submitted and has not been seen to finish.

    A render costs up to nine minutes, so after a crash or a dropped connection
    the run resumes by re-polling these ids with `wait_video_task` instead of
    paying for them twice.
    """
    out: list[dict[str, Any]] = []
    for p in sorted(_task_dir().glob("*.json")):
        try:
            record = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if record.get("status") not in ("succeeded", "failed", "cancelled"):
            out.append(record)
    return out


def create_video_task(
    prompt: str,
    first_frame: str | None = None,
    refs: list[str] | None = None,
    duration: int | None = None,
    ratio: str | None = None,
    resolution: str | None = None,
    seed: int | None = None,
    return_last_frame: bool = False,
) -> str:
    """Submit a Seedance 2.5 render. `POST /contents/generations/tasks` → task id.

    `first_frame` and `refs` are data URIs and are **mutually exclusive** modes;
    when both are given the first frame wins and `refs` is dropped, because the
    API rejects a request that mixes them.

    Measured constraints enforced here:

    * **`ratio` is forced to `"adaptive"` whenever `first_frame` is set**, no
      matter what the caller passed. Any other value fails with
      `InvalidParameter.TaskTypeConstraint: For first-frame generation, the
      output ratio follows the first-frame image.` That inheritance is the
      feature: a 1440x2560 keyframe yields 720x1280, a 2048x2048 keyframe yields
      960x960, so platform-native ratios come out without cropping. With no
      first frame the caller's `ratio` is passed through and omitted when None.
    * Top-level `resolution`/`ratio`/`duration`/`generate_audio`/`watermark`/
      `seed`/`return_last_frame` are accepted by 2.5 (verified 21/08).
      `STUDIO_VIDEO_USE_TOPLEVEL_PARAMS=false` switches to the equally verified
      inline `--resolution ... --ratio ... --duration ...` form.
    * Reference images must be 300–6000 px per side and may not contain real
      human faces; a 129x27 logo was rejected outright.
    * `seed` makes a retry reproduce the look of the clip it replaces.

    The id is written to `DATA_DIR/tasks/{id}.json` **before this returns**, so a
    connection dropped during a 134–543 second render loses nothing.
    """
    text = prompt
    resolution = resolution or studio_settings.VIDEO_RESOLUTION
    duration = duration if duration is not None else studio_settings.VIDEO_SHOT_SECONDS
    # The one rule that makes first-frame video work at all.
    effective_ratio = "adaptive" if first_frame else ratio
    want_last_frame = bool(return_last_frame or studio_settings.VIDEO_RETURN_LAST_FRAME)

    payload: dict[str, Any] = {"model": studio_settings.SEEDANCE_MODEL}

    if studio_settings.VIDEO_USE_TOPLEVEL_PARAMS:
        payload.update(
            {
                "resolution": resolution,
                "duration": duration,
                "generate_audio": studio_settings.VIDEO_GENERATE_AUDIO,
                "watermark": studio_settings.IMAGE_WATERMARK,
                "camera_fixed": False,
                "return_last_frame": want_last_frame,
            }
        )
        if effective_ratio:
            payload["ratio"] = effective_ratio
        if seed is not None:
            payload["seed"] = seed
    else:
        text = f"{text} --resolution {resolution}"
        if effective_ratio:
            text = f"{text} --ratio {effective_ratio}"
        text = f"{text} --duration {duration}"

    content: list[dict[str, Any]] = [{"type": "text", "text": text}]
    if first_frame:
        content.insert(
            0, {"type": "image_url", "image_url": {"url": first_frame}, "role": "first_frame"}
        )
    elif refs:
        for ref in refs:
            content.append(
                {"type": "image_url", "image_url": {"url": ref}, "role": "reference_image"}
            )
    payload["content"] = content

    body = _post_json(
        f"{studio_settings.ARK_BASE_URL}/contents/generations/tasks",
        payload,
        label="seedance-create",
        timeout=_generation_timeout(),
    )
    task_id = body.get("id")
    if not task_id:
        raise ArkError(status=0, body=f"no task id in response: {str(body)[:400]}", label="seedance-create")

    _write_task_record(task_id, payload)   # on disk before the caller sees it
    return task_id


def wait_video_task(task_id: str) -> VideoResult:
    """Poll a Seedance task to completion and download what it produced.

    `GET /contents/generations/tasks/{id}` every `POLL_INTERVAL_SEC` with a
    per-request timeout of `POLL_TIMEOUT_SEC` (30s produced "Read timed out"
    during research), giving up after `TASK_MAX_WAIT_SEC`. Generation takes
    134–543 seconds and the variance is normal — the slowest clip sets the wall
    clock, so do not shorten the budget to make a run feel faster.

    A finished task carries `content.video_url` and, when the task asked for it,
    `content.last_frame_url`. Both are downloaded here: they expire in 48 hours.

    While polling, a 429 or a 5xx is treated as "ask again in a moment" rather
    than fatal — the render is already paid for and running server-side. A 4xx
    (unknown task, revoked key) raises `ArkError` immediately, as does a task
    that reports `failed` or `cancelled`.
    """
    url = f"{studio_settings.ARK_BASE_URL}/contents/generations/tasks/{task_id}"
    wait_started = time.time()
    created_at = float(_read_task_record(task_id).get("created_at") or wait_started)

    while True:
        try:
            body = _get_json(url, label="seedance-poll", timeout=studio_settings.POLL_TIMEOUT_SEC)
        except ArkError as exc:
            # The task is already running and paid for; a gateway hiccup is not
            # a reason to abandon it. A real rejection still stops the wait.
            if exc.status == 429 or exc.status >= 500:
                body = {"status": "running"}
            else:
                raise

        status = body.get("status")
        if status == "succeeded":
            content = body.get("content") or {}
            video_url = content.get("video_url")
            if not video_url:
                raise ArkError(status=0, body=f"succeeded without video_url: {str(body)[:400]}",
                               label="seedance-poll")
            video_bytes = download(video_url, label="seedance-video")
            last_url = content.get("last_frame_url")
            last_bytes = download(last_url, label="seedance-lastframe") if last_url else None
            elapsed = time.time() - created_at
            _update_task_record(task_id, status="succeeded", elapsed_sec=elapsed)
            return VideoResult(video_bytes=video_bytes, last_frame_bytes=last_bytes, elapsed_sec=elapsed)

        if status in ("failed", "cancelled"):
            _update_task_record(task_id, status=status)
            raise ArkError(status=0, body=str(body)[:500], label="seedance-poll")

        if time.time() - wait_started > studio_settings.TASK_MAX_WAIT_SEC:
            raise ArkError(
                status=0,
                body=f"task {task_id} still {status!r} after {studio_settings.TASK_MAX_WAIT_SEC}s",
                label="seedance-poll",
            )
        time.sleep(studio_settings.POLL_INTERVAL_SEC)


# --------------------------------------------------------------------------
# Seed 2.1 Turbo — vision
# --------------------------------------------------------------------------

def describe_image(image_bytes: bytes, prompt: str, max_tokens: int = 600) -> str:
    """Ask the vision model about an image. `POST /chat/completions`.

    Seed 2.1 Turbo is the only vision-capable model this key can reach
    (`skylark-vision-250515` → 404, every `seed-2-0-*` → 403 AccessDenied).

    Feed it **native-resolution tiles of `QA_TILE_PX`**, never a downscaled whole
    image: a 2048x2048 payload times out past 180 seconds, and resizing one to
    1024 makes the model silently auto-correct the very defects the QA gate
    exists to catch (it read a rendered `EFFFECTIVE` back as `EFFECTIVE`). A
    1024x1024 tile answers in 41–109 seconds, hence the long timeout.

    Ask it to *transcribe*; judge in Python. Asked for a verdict it failed a
    correct image because it counted the product's own bottle label as
    unexpected text.
    """
    payload = {
        "model": studio_settings.VISION_MODEL,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": bytes_to_data_uri(image_bytes)}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }
    body = _post_json(
        f"{studio_settings.ARK_BASE_URL}/chat/completions",
        payload,
        label="vision",
        timeout=studio_settings.VISION_TIMEOUT_SEC,
    )
    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ArkError(status=0, body=f"unexpected response: {str(body)[:400]}", label="vision") from exc


def chat(prompt: str, system: str | None = None, max_tokens: int = 2000,
         json_mode: bool = False, timeout: int = 420) -> str:
    """Ask the LLM a text-only question. `POST /chat/completions`.

    Same model as `describe_image` — Seed 2.1 Turbo is multimodal, and the only
    model this key reaches for either job. Text-only calls are fast (a few
    seconds) where image calls take a minute, so the timeout is much shorter.

    `json_mode` asks the model to answer with a JSON object and nothing else.
    It is a request, not a guarantee: callers must still be prepared for a
    fenced code block or a sentence of preamble, which is why `parse_json`
    exists beside this.
    """
    messages: list[dict[str, Any]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload: dict[str, Any] = {
        "model": studio_settings.VISION_MODEL,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    # Deliberately not routed through `_retry`. A long JSON completion measured
    # 165 seconds against a 180-second ceiling, and retrying a *timeout* six
    # times turned one slow call into eighteen minutes of hanging. A timeout
    # here means the model is thinking, not that the network blipped, so it is
    # allowed one generous attempt and one retry for a genuinely dropped
    # connection — nothing more.
    url = f"{studio_settings.ARK_BASE_URL}/chat/completions"
    last: Exception | None = None
    for attempt in range(2):
        try:
            resp = requests.post(url, headers=_headers(), json=payload, timeout=timeout)
            _raise_for_api(resp, "chat")
            body = resp.json()
            break
        except requests.Timeout as exc:
            raise ArkError(status=0, body=f"chat timed out after {timeout}s",
                           label="chat") from exc
        except requests.ConnectionError as exc:
            last = exc
            if attempt == 0:
                time.sleep(2)
                continue
            raise ArkError(status=0, body=f"chat connection failed: {exc}",
                           label="chat") from exc
    else:                                             # pragma: no cover
        raise ArkError(status=0, body=f"chat failed: {last}", label="chat")

    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ArkError(status=0, body=f"unexpected response: {str(body)[:400]}",
                       label="chat") from exc


def parse_json(text: str) -> Any:
    """Pull a JSON value out of an LLM reply.

    Models wrap JSON in ```json fences, prefix it with a sentence, or both, even
    when asked not to. Rather than fail on that, take the outermost balanced
    object or array in the string.
    """
    import json as _json

    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[1]
        if cleaned.lstrip().lower().startswith("json"):
            cleaned = cleaned.lstrip()[4:]
    cleaned = cleaned.strip()

    try:
        return _json.loads(cleaned)
    except _json.JSONDecodeError:
        pass

    for opener, closer in (("{", "}"), ("[", "]")):
        start, end = cleaned.find(opener), cleaned.rfind(closer)
        if start != -1 and end > start:
            try:
                return _json.loads(cleaned[start:end + 1])
            except _json.JSONDecodeError:
                continue
    raise ArkError(status=0, body=f"reply was not JSON: {text[:300]}", label="chat")


# --------------------------------------------------------------------------
# Seed Audio 1.0 — text to speech
# --------------------------------------------------------------------------

def synthesize_speech(text_prompt: str) -> bytes:
    """Render Vietnamese voiceover with Seed Audio 1.0. `POST {ARK_VOICE_URL}/tts/create`.

    A different host and a different auth header (`X-Api-Key`) from the ModelArk
    endpoints. The response is `{audio, duration, original_duration, url}`, where
    `audio` is base64 mp3 and `url` is a short-lived copy; the URL is preferred
    and the inline base64 is the fallback.

    This exists because Seedance mangles Vietnamese: asked for "Tinh chất ốc sên"
    it spoke and captioned "Tình chiật ốc sín". Seed Audio pronounces it
    correctly, so `VIDEO_GENERATE_AUDIO` stays false and voiceover is muxed in
    afterwards.
    """
    payload = {
        "model": studio_settings.TTS_MODEL,
        "text_prompt": text_prompt,
        "audio_config": {
            "format": "mp3",
            "sample_rate": 48000,
            "pitch_rate": 0,
            "speech_rate": 0,
            "loudness_rate": 0,
        },
        "watermark": {},
    }
    body = _post_json(
        f"{studio_settings.ARK_VOICE_URL}/tts/create",
        payload,
        label="tts",
        timeout=_generation_timeout(),
        headers={"X-Api-Key": studio_settings.ARK_VOICE_KEY, "Content-Type": "application/json"},
    )
    url = body.get("url")
    if url:
        return download(url, label="tts-download")
    audio = body.get("audio")
    if not audio:
        raise ArkError(status=0, body=f"no audio in response: {str(body)[:400]}", label="tts")
    return base64.b64decode(audio)
