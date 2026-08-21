"""
Keyframe to clip — the studio's slowest, least predictable node.

`render.py` has already drawn the shot's keyframe with Seedream, Vietnamese
on-screen text and all. This module gives that still image motion, and gives the
finished cut a voice.

**The rule that shapes the whole module: a shot must never disappear.** One 5
second Seedance render measured anywhere between 134 and 543 seconds on the same
key, on the same day, for comparable prompts. The variance is real, it is not
correlated with anything we can see, and a four-beat ad that ships as three
beats is a broken ad. So `render_shot` runs the wait under a hard deadline
(`studio_settings.VIDEO_SHOT_DEADLINE_SEC`) and, when the deadline passes or the
API raises, falls back to a Ken Burns push-in over the keyframe and returns with
`used_fallback=True`. The video keeps its length and its four-beat structure
whatever the API does. Everything else here is plumbing; that is the behaviour.

Three measured constraints are enforced, not assumed:

* **`ratio` is `"adaptive"`.** Any other value with a first frame is rejected
  outright — `InvalidParameter.TaskTypeConstraint`. The output shape then
  follows the keyframe, which is how platform-native ratios are produced without
  a crop: a 1440x2560 keyframe yields 720x1280, a 2048x2048 keyframe 960x960.
* **First-frame and multimodal-reference modes are mutually exclusive.** This
  module only ever sends a first frame, and never a `refs` list alongside it.
* **Seedance is never asked to render Vietnamese, or to speak.** Asked for "Da
  khô căng, xỉn màu?" it drew "Da khò cáng, xỉn mau?". Every legible string is
  already baked into the Seedream keyframe, where it renders correctly and
  survives image-to-video intact, and `VIDEO_GENERATE_AUDIO` is false because
  the audio comes from the same model that mangled the captions. The voice comes
  from Seed Audio TTS, which was verified to pronounce Vietnamese correctly.

`render_voiceover` synthesises one line per shot and pads each to its beat, so
the audio, the subtitle timings and the picture all run on a single clock.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from PIL import Image

from app.services.studio import ark, assemble, prompts
from app.services.studio.config import studio_settings


@dataclass
class ShotResult:
    """One finished beat, on disk and ready for `assemble.concat`.

    `used_fallback` is the field the pipeline and the UI care about: it says the
    beat is a Ken Burns move over its keyframe rather than a Seedance render,
    which is a quality note, never an error. `clip_path` is always populated —
    that is the module's contract.
    """

    index: int
    role: str
    keyframe_path: str
    clip_path: str
    duration_sec: float
    used_fallback: bool = False
    last_frame_path: str | None = None
    task_id: str | None = None
    gen_seconds: float = 0.0
    fallback_reason: str = ""


@dataclass
class VoiceoverResult:
    """The campaign's spoken track, plus where each line lands on the timeline.

    `line_timings` is `(start, end, text)` per spoken line, in video time. It is
    what `assemble.mux` gates each subtitle overlay with, so the caption and the
    voice always turn over on the same frame.
    """

    mp3_path: str
    duration_sec: float
    line_timings: list[tuple[float, float, str]] = field(default_factory=list)
    voice_hint: str = ""


# --------------------------------------------------------------------------
# The deadline
# --------------------------------------------------------------------------

def _wait_within(task_id: str, budget_sec: float) -> ark.VideoResult:
    """Wait for a Seedance task, giving up after `budget_sec`.

    `ark.wait_video_task` polls until `TASK_MAX_WAIT_SEC` (900s), which is the
    right ceiling for the *API* but far too long for a live demo: the pipeline
    renders four beats and cannot spend fifteen minutes on the unlucky one. The
    poll therefore runs on a daemon thread and is simply abandoned when the
    budget runs out. Abandoning it is safe and cheap — `ark.create_video_task`
    already wrote the id to `DATA_DIR/tasks/`, so a later run can pick the
    finished render up through `ark.pending_video_tasks()` instead of paying for
    it again — and the thread is a daemon so a forgotten poll cannot hold the
    process open at exit.

    Raises `TimeoutError` on overrun; re-raises whatever the poll raised
    otherwise, which for a rejected or failed task is `ark.ArkError`.
    """
    if budget_sec <= 0:
        raise TimeoutError(f"no time left to wait for seedance task {task_id}")

    box: dict[str, Any] = {}

    def _poll() -> None:
        try:
            box["result"] = ark.wait_video_task(task_id)
        except BaseException as exc:  # noqa: BLE001 - carried to the caller verbatim
            box["error"] = exc

    thread = threading.Thread(target=_poll, name=f"seedance-wait-{task_id}", daemon=True)
    thread.start()
    thread.join(budget_sec)

    if thread.is_alive():
        raise TimeoutError(
            f"seedance task {task_id} exceeded the {budget_sec:.0f}s shot deadline; "
            "falling back to Ken Burns (the render continues server-side and is "
            "recoverable via ark.pending_video_tasks)"
        )
    if "error" in box:
        raise box["error"]
    return box["result"]


def _fallback_size(keyframe_path: Path, resolution: str) -> tuple[int, int]:
    """The frame size a Ken Burns beat must use to match its Seedance siblings."""
    try:
        with Image.open(keyframe_path) as im:
            source = im.size
    except (OSError, ValueError):
        source = (1440, 2560)   # the studio's portrait keyframe, i.e. 720x1280 out
    return assemble.fit_size_for(source, resolution)


def _safe_duration(path: Path, default: float) -> float:
    """Probe a clip's duration, falling back to the requested length.

    A probe failure must never be the thing that sends a perfectly good clip
    down the fallback path, so it is caught here rather than in `render_shot`.
    """
    try:
        return assemble.probe_duration(path)
    except (assemble.AssembleError, OSError, ValueError):
        return float(default)


# --------------------------------------------------------------------------
# Shots
# --------------------------------------------------------------------------

def render_shot(
    shot: Any,
    keyframe_path: str | Path,
    spine: Any,
    seed: int | None = None,
    out_dir: str | Path | None = None,
    resolution: str | None = None,
    deadline_sec: float | None = None,
    resume_task_id: str | None = None,
) -> ShotResult:
    """Render one storyboard beat from its keyframe. Always returns a playable clip.

    shot            a `direct.ShotPlan`: `index`, `role`, `scene`, `onscreen_text`,
                    `vo_text`, `seconds`. Only `scene` reaches the model.
    keyframe_path   the Seedream still for this beat. It already carries the
                    on-screen Vietnamese, and its aspect ratio decides the
                    clip's — the request sends `ratio="adaptive"` because any
                    other value is rejected for first-frame input.
    spine           the route's `StyleSpine`, injected word for word so the clip
                    grades like the rest of the kit.
    seed            reuse the seed of a clip being replaced and the retry keeps
                    its look.
    resume_task_id  poll an already-submitted task instead of creating one. This
                    is the crash-resume path: a render costs up to nine minutes
                    and must never be paid for twice.

    On `TimeoutError` past `deadline_sec` (default
    `studio_settings.VIDEO_SHOT_DEADLINE_SEC`) or on any `ArkError`, the beat is
    produced instead by `assemble.ken_burns` over the keyframe and comes back
    with `used_fallback=True` and `fallback_reason` set. It is never dropped.

    `refs` is never sent: first-frame and multimodal-reference modes are
    mutually exclusive and a request carrying both is rejected.
    """
    keyframe = Path(keyframe_path)
    out = Path(out_dir) if out_dir else keyframe.parent
    out.mkdir(parents=True, exist_ok=True)

    index = int(getattr(shot, "index", 0))
    role = str(getattr(shot, "role", ""))
    seconds = int(getattr(shot, "seconds", 0) or studio_settings.VIDEO_SHOT_SECONDS)
    clip_path = out / f"shot_{index:02d}.mp4"
    effective_resolution = resolution or studio_settings.VIDEO_RESOLUTION
    deadline = float(
        deadline_sec if deadline_sec is not None else studio_settings.VIDEO_SHOT_DEADLINE_SEC
    )

    started = time.time()
    task_id = resume_task_id
    try:
        prompt = prompts.build_video_prompt(
            str(getattr(shot, "scene", "")), spine, str(getattr(shot, "vo_text", ""))
        )
        if task_id is None:
            task_id = ark.create_video_task(
                prompt=prompt,
                first_frame=ark.to_data_uri(keyframe),
                duration=seconds,
                ratio="adaptive",          # mandatory for first-frame input
                resolution=effective_resolution,
                seed=seed,
                return_last_frame=True,
            )
        result = _wait_within(task_id, deadline - (time.time() - started))

        clip_path.write_bytes(result.video_bytes)
        last_frame_path: str | None = None
        if result.last_frame_bytes:
            last = out / f"shot_{index:02d}_last.png"
            last.write_bytes(result.last_frame_bytes)
            last_frame_path = str(last)

        return ShotResult(
            index=index,
            role=role,
            keyframe_path=str(keyframe),
            clip_path=str(clip_path),
            duration_sec=_safe_duration(clip_path, seconds),
            used_fallback=False,
            last_frame_path=last_frame_path,
            task_id=task_id,
            gen_seconds=round(time.time() - started, 1),
        )
    except (TimeoutError, ark.ArkError, OSError, ValueError) as exc:
        reason = f"{type(exc).__name__}: {exc}"[:400]

    # Outside the except block on purpose: a failure in the fallback should read
    # as a fallback failure, not as a confusing chain off the original error.
    assemble.ken_burns(
        str(keyframe),
        str(clip_path),
        seconds=seconds,
        size=_fallback_size(keyframe, effective_resolution),
    )
    return ShotResult(
        index=index,
        role=role,
        keyframe_path=str(keyframe),
        clip_path=str(clip_path),
        duration_sec=float(seconds),
        used_fallback=True,
        task_id=task_id,
        gen_seconds=round(time.time() - started, 1),
        fallback_reason=reason,
    )


# --------------------------------------------------------------------------
# Voiceover
# --------------------------------------------------------------------------

def render_voiceover(
    shots: Sequence[Any],
    voice_hint: str = "",
    out_dir: str | Path | None = None,
) -> VoiceoverResult:
    """Speak the storyboard's Vietnamese lines and lay them on the video's clock.

    One `ark.synthesize_speech` call per shot — Seed Audio 1.0, the model that
    was verified to pronounce Vietnamese correctly, which is why
    `VIDEO_GENERATE_AUDIO` is false and Seedance's own audio is discarded.

    Each spoken line is then padded with silence to the length of its beat
    (`assemble.pad_audio`), and a beat with no line becomes silence of the same
    length. That is what keeps one clock: without the padding, every beat's
    caption drifts by the accumulated error of the beats before it. A line that
    runs *longer* than its beat is never truncated — cutting a voiceover
    mid-word is worse than a caption a fraction late — so the timeline stretches
    to fit it and the caller can see the overrun in `duration_sec`.

    `voice_hint` (e.g. "nữ, trẻ, thân thiện") is recorded on the result but not
    sent: the verified `/tts/create` payload carries only `text_prompt` and an
    `audio_config`, with no voice selector, and putting the hint into
    `text_prompt` would simply have the model read it aloud.

    Returns a `VoiceoverResult` whose `line_timings` drive both `assemble.mux`
    and `assemble.render_subtitle_strip`.
    """
    work = Path(out_dir) if out_dir else Path(studio_settings.DATA_DIR) / "voiceover"
    work.mkdir(parents=True, exist_ok=True)

    parts: list[str] = []
    timings: list[tuple[float, float, str]] = []
    cursor = 0.0

    for position, shot in enumerate(shots):
        index = int(getattr(shot, "index", position))
        seconds = float(getattr(shot, "seconds", 0) or studio_settings.VIDEO_SHOT_SECONDS)
        line = " ".join(str(getattr(shot, "vo_text", "") or "").split())

        if not line:
            parts.append(assemble.silent_audio(work / f"vo_{index:02d}.mp3", seconds))
            cursor += seconds
            continue

        raw = work / f"vo_{index:02d}_raw.mp3"
        raw.write_bytes(ark.synthesize_speech(line))
        spoken = _safe_duration(raw, seconds)
        slot = max(spoken, seconds)
        parts.append(assemble.pad_audio(raw, work / f"vo_{index:02d}.mp3", slot))
        timings.append((round(cursor, 3), round(cursor + spoken, 3), line))
        cursor += slot

    master = work / "voiceover.mp3"
    duration = assemble.concat_audio(parts, master)
    return VoiceoverResult(
        mp3_path=str(master),
        duration_sec=duration,
        line_timings=timings,
        voice_hint=voice_hint,
    )


def subtitle_strips(
    timings: Sequence[tuple[float, float, str]],
    size: tuple[int, int],
    out_dir: str | Path,
) -> list[str]:
    """Render one transparent subtitle PNG per timed line, in `timings` order.

    A convenience over `assemble.render_subtitle_strip` so the pipeline can hand
    `mux` two parallel lists. Pillow draws them because this ffmpeg build has no
    `drawtext` filter and Seedance cannot spell Vietnamese.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    return [
        assemble.render_subtitle_strip(text, size, out / f"sub_{i:02d}.png")
        for i, (_start, _end, text) in enumerate(timings)
    ]
