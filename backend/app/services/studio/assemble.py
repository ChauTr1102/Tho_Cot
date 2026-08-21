"""
The cutting room — every frame the studio ships passes through here.

`motion.py` produces one clip per beat; this module turns those clips into the
master video, and produces the two things Seedance cannot be trusted to make
itself: the Ken Burns move that stands in for a clip which missed its deadline,
and the Vietnamese subtitle strip.

Three measured facts shape everything below.

1. **Every Seedance clip comes back 720x1280 / 24 fps / h264 + aac 32 kHz
   stereo** (960x960 when the keyframe is square — the aspect follows the first
   frame). Because the parameters match, `-f concat -c copy` joins the beats
   losslessly and instantly, with no generation loss and no re-encode wait. The
   re-encode path exists only for the case where they *do not* match, and
   `concat` detects that by checking the joined duration rather than trusting
   ffmpeg's exit code — a mismatched stream copy frequently exits 0 and produces
   a file that stops after the first clip.

2. **This ffmpeg build has no `drawtext`.** It was compiled without freetype and
   the filter does not exist, so no amount of escaping will make it work:

       $ ffmpeg -filters | grep -c drawtext
       0

   All text rendering is therefore Pillow's job. `render_subtitle_strip` draws
   the caption onto a transparent PNG the size of the video and `mux` composites
   it with `overlay` + `enable='between(t,start,end)'`, which is a filter this
   build does have.

3. **Nothing here may ask a generative model to spell Vietnamese.** Seedance
   turned "Da khô căng, xỉn màu?" into "Da khò cáng, xỉn mau?". Pillow and a
   Unicode font get it right every time, which is why the subtitle strip is
   drawn locally and the voiceover is muxed in from Seed Audio TTS.

A Ken Burns clip is deliberately encoded to match the Seedance parameters
exactly, silent `anullsrc` audio track included, so that a fallback beat can be
stream-copied into the master alongside real clips instead of forcing the whole
video through a re-encode.
"""
from __future__ import annotations

import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.services.studio.config import studio_settings

# --------------------------------------------------------------------------
# Encoder parameters, measured from real Seedance output on 21/08/2026.
# A Ken Burns clip must match these or `-c copy` concat stops working.
# --------------------------------------------------------------------------
CLIP_FPS = 24
CLIP_TIMESCALE = 12288          # ffprobe time_base 1/12288 on every Seedance clip
CLIP_AUDIO_RATE = 32000
CLIP_AUDIO_CHANNELS = 2
CLIP_PIX_FMT = "yuv420p"

# Ken Burns move: a slow push in. Big enough to read as motion on a 5 second
# beat, small enough that nobody reads it as a mistake.
KEN_BURNS_ZOOM_END = 1.12

# Subtitle typography, as a fraction of the video width so it holds at any size.
SUBTITLE_FONT_SCALE = 0.058     # cap height ~ 42px on a 720px wide frame
SUBTITLE_MAX_WIDTH_PCT = 0.86   # keep the caption clear of the frame edges
SUBTITLE_LINE_SPACING = 1.25

# Fonts tried in order. The first must cover Vietnamese stacked diacritics
# (Ắ Ặ Ễ Ộ Ự); a font without them draws .notdef boxes and the caption is worse
# than no caption at all.
FONT_FALLBACKS = (
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)


class AssembleError(RuntimeError):
    """An ffmpeg or ffprobe invocation that failed, with its stderr attached.

    ffmpeg's diagnostics are the only useful thing it emits when a filter graph
    is wrong, so the tail of stderr travels with the exception rather than being
    swallowed by `capture_output`.
    """


@dataclass(frozen=True)
class VideoFacts:
    """What `concat` needs to know about a clip before it tries to stream-copy it."""

    width: int
    height: int
    fps: float
    duration_sec: float
    has_audio: bool


# --------------------------------------------------------------------------
# Process plumbing
# --------------------------------------------------------------------------

def _tunable(name: str, default):
    """Read a studio setting, falling back to a local default.

    `config.py` is owned by another task and carries no ffmpeg fields yet. Every
    tunable here is read through this helper so that the day `STUDIO_FFMPEG_BIN`
    or `STUDIO_VIDEO_FPS` is added to `StudioSettings` it takes effect without a
    line changing in this module — the studio's rule is that no call site
    hardcodes a value that an operator might need to change.
    """
    return getattr(studio_settings, name, default)


def _ffmpeg() -> str:
    """Path to the ffmpeg binary."""
    return str(_tunable("FFMPEG_BIN", "ffmpeg"))


def _ffprobe() -> str:
    """Path to the ffprobe binary."""
    return str(_tunable("FFPROBE_BIN", "ffprobe"))


def _run(args: Sequence[str], label: str) -> str:
    """Run an ffmpeg/ffprobe command, raising `AssembleError` with its stderr."""
    try:
        proc = subprocess.run(list(args), capture_output=True, text=True)
    except OSError as exc:
        # The binary itself is missing or not executable (e.g. ffmpeg was
        # never installed in this environment) — subprocess.run raises
        # before there is any returncode/stderr to report, so without this
        # a caller three layers up sees a bare FileNotFoundError with no
        # indication of which binary or command was involved.
        raise AssembleError(
            f"{label} failed: could not run {args[0]!r} "
            f"(binary missing or not executable: {exc})\n"
            f"  cmd: {' '.join(str(a) for a in args)}"
        ) from exc
    if proc.returncode != 0:
        raise AssembleError(
            f"{label} failed (exit {proc.returncode})\n"
            f"  cmd: {' '.join(str(a) for a in args)}\n"
            f"  err: {proc.stderr.strip()[-1200:]}"
        )
    return proc.stdout


def probe_duration(path: str | Path) -> float:
    """Container duration in seconds, via `ffprobe -show_entries format=duration`."""
    out = _run(
        [_ffprobe(), "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        "ffprobe duration",
    )
    try:
        return float(out.strip())
    except ValueError as exc:
        raise AssembleError(f"ffprobe gave no duration for {path}: {out!r}") from exc


def probe_video(path: str | Path) -> VideoFacts:
    """Geometry, frame rate and audio presence for one clip.

    `concat` uses this to decide whether a stream copy is even plausible and to
    pick the geometry the re-encode path normalises everything to.
    """
    out = _run(
        [_ffprobe(), "-v", "error", "-print_format", "json",
         "-show_streams", "-show_format", str(path)],
        "ffprobe streams",
    )
    body = json.loads(out)
    streams = body.get("streams") or []
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    has_audio = any(s.get("codec_type") == "audio" for s in streams)

    rate = str(video.get("r_frame_rate") or "0/1")
    try:
        num, _, den = rate.partition("/")
        fps = float(num) / float(den or 1)
    except (ValueError, ZeroDivisionError):
        fps = 0.0

    try:
        duration = float((body.get("format") or {}).get("duration") or 0.0)
    except (TypeError, ValueError):
        duration = 0.0

    return VideoFacts(
        width=int(video.get("width") or 0),
        height=int(video.get("height") or 0),
        fps=fps,
        duration_sec=duration,
        has_audio=has_audio,
    )


# --------------------------------------------------------------------------
# concat
# --------------------------------------------------------------------------

def concat(clip_paths: Sequence[str | Path], out_path: str | Path) -> float:
    """Join clips into one file and return the resulting duration in seconds.

    Tries `-f concat -safe 0 -c copy` first. Every Seedance clip shares
    720x1280 / 24fps / h264 / aac, and a Ken Burns fallback clip is encoded to
    match, so the copy path is the normal one: it is lossless, it is instant,
    and it is why the studio can afford to rebuild a master after every QA pass.

    The copy is then **verified against the summed input durations** rather than
    trusted. A concat demuxer fed mismatched parameters routinely exits 0 and
    writes a file containing only the first clip; checking the exit code alone
    is how a four-beat ad silently ships as a five-second one. On a mismatch the
    inputs are re-encoded through the `concat` filter, normalised to the first
    clip's geometry, with a silent track synthesised for any clip that has no
    audio (the filter refuses to run if the streams do not line up).
    """
    paths = [Path(p) for p in clip_paths]
    if not paths:
        raise AssembleError("concat needs at least one clip")
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise AssembleError(f"concat inputs do not exist: {missing}")

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    expected = sum(probe_duration(p) for p in paths)

    listing = out.with_name(out.stem + ".concat.txt")
    # The concat demuxer takes single quotes literally; doubling them is the
    # documented escape.
    listing.write_text(
        "".join(f"file '{str(p.resolve()).replace(chr(39), chr(39) * 2)}'\n" for p in paths),
        encoding="utf-8",
    )

    copied = False
    try:
        _run(
            [_ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
             "-f", "concat", "-safe", "0", "-i", str(listing),
             "-c", "copy", "-movflags", "+faststart", str(out)],
            "concat -c copy",
        )
        actual = probe_duration(out)
        copied = abs(actual - expected) <= max(0.5, 0.05 * expected)
    except AssembleError:
        copied = False
    finally:
        listing.unlink(missing_ok=True)

    if not copied:
        _concat_reencode(paths, out)

    return probe_duration(out)


def _concat_reencode(paths: list[Path], out: Path) -> None:
    """Fallback join: normalise every input and run the `concat` filter.

    Slower and lossy, so it only runs when the stream copy could not produce the
    full length. Clips without an audio track get a synthesised silent one,
    because `concat=v=1:a=1` requires the same stream layout on every segment.
    """
    facts = [probe_video(p) for p in paths]
    width = next((f.width for f in facts if f.width), 720)
    height = next((f.height for f in facts if f.height), 1280)
    fps = _tunable("VIDEO_FPS", CLIP_FPS)
    rate = _tunable("VIDEO_AUDIO_RATE", CLIP_AUDIO_RATE)

    args = [_ffmpeg(), "-y", "-hide_banner", "-loglevel", "error"]
    for p in paths:
        args += ["-i", str(p)]

    silent_for: dict[int, int] = {}
    for i, fact in enumerate(facts):
        if not fact.has_audio:
            silent_for[i] = len(paths) + len(silent_for)
            args += ["-f", "lavfi", "-t", f"{max(fact.duration_sec, 0.1):.3f}",
                     "-i", f"anullsrc=channel_layout=stereo:sample_rate={rate}"]

    steps, labels = [], []
    for i, _ in enumerate(paths):
        steps.append(
            f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps}[v{i}]"
        )
        audio_in = f"{silent_for[i]}:a" if i in silent_for else f"{i}:a"
        steps.append(f"[{audio_in}]aformat=sample_rates={rate}:channel_layouts=stereo[a{i}]")
        labels.append(f"[v{i}][a{i}]")
    steps.append(f"{''.join(labels)}concat=n={len(paths)}:v=1:a=1[v][a]")

    args += [
        "-filter_complex", ";".join(steps),
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", CLIP_PIX_FMT, "-video_track_timescale", str(CLIP_TIMESCALE),
        "-c:a", "aac", "-ar", str(rate), "-ac", str(CLIP_AUDIO_CHANNELS),
        "-movflags", "+faststart", str(out),
    ]
    _run(args, "concat re-encode")


# --------------------------------------------------------------------------
# Ken Burns — the fallback that keeps a shot from disappearing
# --------------------------------------------------------------------------

def ken_burns(
    image_path: str | Path,
    out_path: str | Path,
    seconds: float = 5.0,
    size: tuple[int, int] = (720, 1280),
) -> str:
    """Turn a still keyframe into a slow push-in clip. Returns the output path.

    This is what stands in for a Seedance clip that missed its deadline or came
    back as an error. One 5s render measured anywhere between 134 and 543
    seconds, so at some point the pipeline has to stop waiting — and when it
    does, the beat still has to exist. The keyframe already carries the shot's
    Vietnamese on-screen text, drawn correctly by Seedream, so a Ken Burns beat
    reads as a deliberate stylistic cut rather than as a hole in the edit.

    The encode deliberately mirrors real Seedance output — 24 fps, h264,
    yuv420p, 12288 timescale, and a silent stereo aac track from `anullsrc` —
    so that a master mixing fallback and real beats still joins with `-c copy`.
    Without that audio track the concat demuxer drops to the re-encode path and
    the whole video pays for one missing beat.

    The image is upscaled to twice the target before `zoompan` runs: zoompan
    samples at output resolution, and zooming a frame that is already the final
    size produces visible stair-stepping on the push-in.
    """
    img = Path(image_path)
    if not img.exists():
        raise AssembleError(f"ken_burns source does not exist: {img}")
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    width, height = int(size[0]), int(size[1])
    fps = int(_tunable("VIDEO_FPS", CLIP_FPS))
    rate = int(_tunable("VIDEO_AUDIO_RATE", CLIP_AUDIO_RATE))
    zoom_end = float(_tunable("KEN_BURNS_ZOOM_END", KEN_BURNS_ZOOM_END))

    frames = max(1, int(round(float(seconds) * fps)))
    step = (zoom_end - 1.0) / frames

    vf = (
        f"scale={width * 2}:{height * 2}:force_original_aspect_ratio=increase,"
        f"crop={width * 2}:{height * 2},"
        f"zoompan=z='min(zoom+{step:.6f},{zoom_end})':d={frames}"
        f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps},"
        f"format={CLIP_PIX_FMT}"
    )

    _run(
        [_ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
         "-loop", "1", "-i", str(img),
         "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate={rate}",
         "-map", "0:v", "-map", "1:a",
         "-vf", vf, "-t", f"{float(seconds):.3f}", "-r", str(fps),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", CLIP_PIX_FMT, "-video_track_timescale", str(CLIP_TIMESCALE),
         "-c:a", "aac", "-b:a", "128k", "-ar", str(rate), "-ac", str(CLIP_AUDIO_CHANNELS),
         "-shortest", "-movflags", "+faststart", str(out)],
        "ken_burns",
    )
    return str(out)


# --------------------------------------------------------------------------
# Subtitles — Pillow, because this ffmpeg has no drawtext
# --------------------------------------------------------------------------

def load_subtitle_font(px: int) -> ImageFont.FreeTypeFont:
    """Load a Vietnamese-capable font at `px`, trying the configured path first.

    `studio_settings.SUBTITLE_FONT_PATH` wins; `FONT_FALLBACKS` covers the case
    where the studio runs on a machine without it. Pillow's last-resort bitmap
    font is *not* used silently — it cannot draw `Ắ Ặ Ễ Ộ Ự` and a caption full
    of .notdef boxes is worse than no caption — so a total failure raises.
    """
    candidates = [str(_tunable("SUBTITLE_FONT_PATH", ""))] + list(FONT_FALLBACKS)
    for path in candidates:
        if not path:
            continue
        try:
            return ImageFont.truetype(path, px)
        except (OSError, ValueError):
            continue
    raise AssembleError(
        "no Vietnamese-capable TrueType font found; set STUDIO_SUBTITLE_FONT_PATH "
        f"(tried {[c for c in candidates if c]})"
    )


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_px: int) -> list[str]:
    """Greedy word wrap against real glyph metrics, not a character count."""
    words = text.split()
    if not words:
        return []
    lines, current = [], words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if font.getlength(trial) <= max_px:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def render_subtitle_strip(
    text: str,
    size: tuple[int, int],
    out_png: str | Path,
    font_px: int | None = None,
) -> str:
    """Draw one Vietnamese caption onto a transparent PNG. Returns its path.

    The PNG is the full size of the video so `mux` can composite it at 0,0 with
    no arithmetic — one `overlay` per caption, gated by `enable='between(t,…)'`.

    Pillow does this rather than ffmpeg because **this ffmpeg build has no
    `drawtext` filter** (compiled without freetype), and rather than Seedance
    because Seedance cannot spell Vietnamese. Pillow plus a Unicode font renders
    stacked diacritics exactly.

    The caption block sits above `studio_settings.SUBTITLE_SAFE_BOTTOM_PCT` of
    the frame, which is the strip TikTok and Shopee cover with their own UI. It
    is drawn white, with a black stroke and a blurred dark shadow beneath, so it
    stays legible over both the bright and the dark parts of a clip.
    """
    width, height = int(size[0]), int(size[1])
    out = Path(out_png)
    out.parent.mkdir(parents=True, exist_ok=True)

    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    caption = " ".join(str(text).split())
    if not caption:
        canvas.save(out, "PNG")
        return str(out)

    px = int(font_px or max(18, round(width * float(_tunable("SUBTITLE_FONT_SCALE", SUBTITLE_FONT_SCALE)))))
    font = load_subtitle_font(px)
    lines = _wrap(caption, font, int(width * SUBTITLE_MAX_WIDTH_PCT))

    line_h = int(px * SUBTITLE_LINE_SPACING)
    block_h = line_h * len(lines)
    safe_bottom = float(_tunable("SUBTITLE_SAFE_BOTTOM_PCT", 0.20))
    baseline_top = max(0, int(height * (1.0 - safe_bottom)) - block_h)

    # Shadow first, on its own layer, so the blur does not eat the glyph edges.
    shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    text_draw = ImageDraw.Draw(canvas)
    stroke = max(2, px // 14)

    for i, line in enumerate(lines):
        x = (width - font.getlength(line)) / 2
        y = baseline_top + i * line_h
        shadow_draw.text((x, y + stroke), line, font=font, fill=(0, 0, 0, 190),
                         stroke_width=stroke * 2, stroke_fill=(0, 0, 0, 190))
        text_draw.text((x, y), line, font=font, fill=(255, 255, 255, 255),
                       stroke_width=stroke, stroke_fill=(0, 0, 0, 235))

    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=max(2, px // 8)))
    Image.alpha_composite(shadow, canvas).save(out, "PNG")
    return str(out)


# --------------------------------------------------------------------------
# mux and cutdown
# --------------------------------------------------------------------------

def mux(
    master_path: str | Path,
    vo_path: str | Path | None,
    subtitle_pngs: Sequence[str | Path],
    timings: Sequence[tuple[float, float, str]],
    out_path: str | Path,
) -> str:
    """Burn the subtitle PNGs onto the master and mux the voiceover. Returns the path.

    One `overlay` per caption, each gated by `enable='between(t,start,end)'` from
    the matching entry in `timings` — the same timings `motion.render_voiceover`
    derived from the actual spoken length of each line, so caption and voice turn
    over together. `drawtext` is never used: it does not exist in this build.

    When `vo_path` is given its audio replaces the master's, because the master's
    own track is either silence (from a Ken Burns beat) or Seedance audio, which
    is produced by the model that mangles Vietnamese. `-shortest` keeps a
    slightly-long voiceover from stretching the video past its last frame.
    """
    master = Path(master_path)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    pngs = [Path(p) for p in subtitle_pngs]
    rate = int(_tunable("VIDEO_AUDIO_RATE", CLIP_AUDIO_RATE))

    args = [_ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(master)]
    audio_map = "0:a?"
    if vo_path:
        args += ["-i", str(vo_path)]
        audio_map = "1:a"
    # Input 0 is the master, input 1 is the voiceover when there is one, and the
    # subtitle PNGs follow. The overlay filter addresses them by that index.
    first_png_index = 1 + (1 if vo_path else 0)
    for p in pngs:
        # `-loop 1` is required, not cosmetic. A PNG is a single-frame stream, so
        # by the time a later caption's `enable` window opens its input has long
        # ended and the overlay draws nothing. Measured: without it the first
        # caption appeared and every subsequent one was silently dropped.
        args += ["-loop", "1", "-i", str(p)]

    if pngs:
        steps, current = [], "0:v"
        for i, _ in enumerate(pngs):
            start, end = (timings[i][0], timings[i][1]) if i < len(timings) else (0.0, 1e6)
            label = f"ov{i}"
            steps.append(
                f"[{current}][{first_png_index + i}:v]"
                f"overlay=0:0:enable='between(t,{float(start):.3f},{float(end):.3f})'[{label}]"
            )
            current = label
        args += ["-filter_complex", ";".join(steps), "-map", f"[{current}]"]
    else:
        args += ["-map", "0:v"]

    args += [
        "-map", audio_map,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", CLIP_PIX_FMT, "-video_track_timescale", str(CLIP_TIMESCALE),
        "-c:a", "aac", "-ar", str(rate), "-ac", str(CLIP_AUDIO_CHANNELS),
        "-shortest", "-movflags", "+faststart", str(out),
    ]
    _run(args, "mux")
    return str(out)


def cutdown(master_path: str | Path, out_path: str | Path, seconds: float) -> str:
    """Cut the first `seconds` of the master into a shorter edit. Returns the path.

    Platforms want the same ad at several lengths — a 30s master and a 15s cut
    for the feed. The cut is re-encoded rather than stream-copied because a copy
    can only cut at a keyframe, which on a 24fps h264 clip can miss the mark by
    over a second and land mid-word in the voiceover.
    """
    master = Path(master_path)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    rate = int(_tunable("VIDEO_AUDIO_RATE", CLIP_AUDIO_RATE))
    _run(
        [_ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
         "-i", str(master), "-t", f"{float(seconds):.3f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", CLIP_PIX_FMT, "-video_track_timescale", str(CLIP_TIMESCALE),
         "-c:a", "aac", "-ar", str(rate), "-ac", str(CLIP_AUDIO_CHANNELS),
         "-movflags", "+faststart", str(out)],
        "cutdown",
    )
    return str(out)


def concat_audio(parts: Sequence[str | Path], out_path: str | Path) -> float:
    """Join audio segments end to end and return the total duration.

    Used by `motion.render_voiceover` to stitch one Seed Audio call per shot
    into a single track whose clock matches the video's.
    """
    paths = [Path(p) for p in parts]
    if not paths:
        raise AssembleError("concat_audio needs at least one part")
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    listing = out.with_name(out.stem + ".alist.txt")
    listing.write_text(
        "".join(f"file '{str(p.resolve()).replace(chr(39), chr(39) * 2)}'\n" for p in paths),
        encoding="utf-8",
    )
    try:
        _run(
            [_ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
             "-f", "concat", "-safe", "0", "-i", str(listing),
             "-c", "copy", str(out)],
            "concat_audio",
        )
    finally:
        listing.unlink(missing_ok=True)
    return probe_duration(out)


def pad_audio(src: str | Path, out_path: str | Path, seconds: float) -> str:
    """Re-encode an audio file to exactly `seconds` long, padding with silence.

    A spoken line is never exactly as long as the beat it belongs to. Padding
    each line out to its beat is what keeps the voiceover, the subtitles and the
    cuts on one clock — without it every beat drifts by the error of the one
    before it.
    """
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    rate = int(_tunable("VIDEO_AUDIO_RATE", CLIP_AUDIO_RATE))
    _run(
        [_ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
         "-af", f"apad=whole_dur={float(seconds):.3f}", "-t", f"{float(seconds):.3f}",
         "-ar", str(rate), "-ac", "1", "-c:a", "libmp3lame", "-b:a", "128k", str(out)],
        "pad_audio",
    )
    return str(out)


def silent_audio(out_path: str | Path, seconds: float) -> str:
    """Produce `seconds` of silence, for a beat that carries no spoken line."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    rate = int(_tunable("VIDEO_AUDIO_RATE", CLIP_AUDIO_RATE))
    _run(
        [_ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
         "-f", "lavfi", "-i", f"anullsrc=channel_layout=mono:sample_rate={rate}",
         "-t", f"{float(seconds):.3f}", "-c:a", "libmp3lame", "-b:a", "128k", str(out)],
        "silent_audio",
    )
    return str(out)


def fit_size_for(image_size: tuple[int, int], resolution: str) -> tuple[int, int]:
    """Predict the frame size Seedance returns for a keyframe of `image_size`.

    Seedance holds the **pixel count** of the requested resolution and takes the
    shape from the first frame — measured: a 1440x2560 keyframe at 720p came
    back 720x1280, and a 2048x2048 keyframe came back 960x960. Both are exactly
    921,600 pixels, which is 720x1280.

    A Ken Burns fallback must land on the same numbers or the master can no
    longer be stream-copied, so the arithmetic lives here next to the encoder
    parameters it has to agree with.
    """
    area = {
        "480p": 480 * 854,
        "720p": 720 * 1280,
        "1080p": 1080 * 1920,
    }.get(str(resolution).lower(), 720 * 1280)

    src_w, src_h = max(1, int(image_size[0])), max(1, int(image_size[1]))
    aspect = src_w / src_h
    height = math.sqrt(area / aspect)
    width = aspect * height

    def _snap(value: float) -> int:
        return max(16, int(round(value / 16.0)) * 16)

    return _snap(width), _snap(height)
