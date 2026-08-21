"""
Every tunable value for the Asset Studio.

This module is the studio's control panel. The studio sits between two
teammate-owned agents (gen_plan upstream, qa_review downstream), so its
behaviour has to be adjustable without editing logic. Nothing in the studio
may hardcode a model id, a size, a timeout, or a concurrency cap: it belongs
here, and every field is overridable by environment variable using the
STUDIO_ prefix (e.g. STUDIO_IMAGE_CONCURRENCY=3).

Defaults encode API behaviour measured against the hackathon key on
21/08/2026, not documentation guesses. Several of them contradict the official
BytePlus guide, and the comments say why. Change them knowingly.
"""
from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class StudioSettings(BaseSettings):
    # --- credentials -------------------------------------------------
    ARK_API_KEY: str
    ARK_BASE_URL: str = "https://ark.ap-southeast.bytepluses.com/api/v3"
    ARK_VOICE_URL: str = "https://voice.ap-southeast-1.bytepluses.com/api/v3"
    ARK_VOICE_KEY: str = "4169cffe-406a-4e7e-a361-f3ed6d06d363"  # supplied by the organisers

    # --- models (BP-01 mandates Seedream 5.0 Pro + Seedance 2.5) ------
    SEEDREAM_MODEL: str = "dola-seedream-5-0-pro-260628"
    SEEDANCE_MODEL: str = "dreamina-seedance-2-5-260628"
    # The only vision-capable model this key can reach. skylark-vision -> 404,
    # every seed-2-0-* -> 403 AccessDenied. Do not plan around alternatives.
    VISION_MODEL: str = "dola-seed-2-1-turbo-260628"
    TTS_MODEL: str = "seed-audio-1.0"

    # --- image generation --------------------------------------------
    IMAGE_SIZE_SQUARE: str = "2048x2048"
    IMAGE_SIZE_PORTRAIT: str = "1440x2560"    # 9:16; drives 9:16 video via ratio=adaptive
    IMAGE_SIZE_LANDSCAPE: str = "2560x1280"   # 2:1 promo banner
    IMAGE_SIZE_FEED: str = "1638x2048"        # 4:5 social feed
    IMAGE_WATERMARK: bool = False             # true stamps "AI generated" onto the image

    # --- video generation --------------------------------------------
    # 1080p verified: a 9:16 request returned exactly 1080x1920, in 301s
    # against 207s for the same clip at 720p. Use 720p for drafts.
    VIDEO_RESOLUTION: str = "1080p"
    VIDEO_DRAFT_RESOLUTION: str = "720p"
    VIDEO_SHOT_SECONDS: int = 5
    # False: Seedance mangles Vietnamese in its captions ("Da khò cáng, xỉn mau?"
    # for "Da khô căng, xỉn màu?"), so its audio is not trusted either.
    # Voiceover comes from Seed Audio TTS, which speaks Vietnamese correctly.
    VIDEO_GENERATE_AUDIO: bool = False
    VIDEO_SUBTITLES_FROM_SEEDANCE: bool = False  # never true: Vietnamese comes out garbled
    # Top-level params are accepted by 2.5 (verified). False falls back to the
    # inline "--resolution ... --ratio ... --duration ..." form, also verified.
    VIDEO_USE_TOPLEVEL_PARAMS: bool = True
    VIDEO_RETURN_LAST_FRAME: bool = True      # yields a cover still alongside the clip
    VIDEO_SHOT_DEADLINE_SEC: int = 300        # past this, Ken Burns from the keyframe instead

    # --- concurrency (measured: 10 images in 44s; 4 videos ran in parallel)
    IMAGE_CONCURRENCY: int = 8
    VIDEO_CONCURRENCY: int = 4
    VISION_CONCURRENCY: int = 4

    # --- resilience (venue Wi-Fi dropped DNS mid-run during research) --
    HTTP_RETRIES: int = 6
    HTTP_BACKOFF_CAP_SEC: int = 20
    POLL_TIMEOUT_SEC: int = 90                # 30s produced "Read timed out"
    POLL_INTERVAL_SEC: int = 10
    TASK_MAX_WAIT_SEC: int = 900
    VISION_TIMEOUT_SEC: int = 600             # vision is slow even on a small tile

    # --- inventory thresholds -----------------------------------------
    # Seedance rejects any reference image under 300px on either side with
    # InvalidParameter. Audited 21/08: every sample_data product photo passes,
    # but 3 of 5 logos do not (COSRX 129x27, Oatside 800x200, Marou 205x145).
    REF_MIN_PX: int = 300
    # Shopee's hard floor for a main listing image is 500x500 (1000x1000 is the
    # recommendation). 800 keeps the flagship COSRX photos (800x1067) eligible
    # for REUSE; raising it to 1000 pushes the demo brand's whole Shopee kit
    # into GENERATE and throws away the real-photo story.
    SHOPEE_MIN_PX: int = 800
    SLOT_MIN_PX: int = 800                    # general floor for reusing a photo in a slot
    BG_WHITE_THRESHOLD: float = 0.9           # fraction of edge pixels that must read as white

    # --- QA -----------------------------------------------------------
    # Tile size. A whole 2048px image times out past 180s; downscaling it to
    # 1024 makes the model silently auto-correct defects (EFFFECTIVE ->
    # EFFECTIVE), destroying the signal the gate exists to detect. So: four
    # native-resolution crops instead of one resize.
    QA_TILE_PX: int = 1024
    QA_MAX_ATTEMPTS: int = 1                  # inspections per asset before giving up
    QA_ENABLED: bool = True
    # False keeps the gate off the critical path: the image is published the
    # moment it renders and the verdict arrives afterwards as a badge update.
    # Measured, blocking: a text-bearing image took 285s -- roughly two rounds of
    # render-then-inspect -- against 60s for the render alone. True restores the
    # regenerate-until-it-passes loop, which is right for a final asset run and
    # wrong for anyone watching a screen.
    QA_BLOCKING: bool = False
    # Inspect only images that carry marketing copy. A vision pass costs 41-109s
    # on top of a 60s render, and an image with no text on it has nothing the
    # gate can catch -- gating everything turned a one-minute hero into five.
    QA_TEXT_ONLY: bool = True

    # --- subtitles (rendered by Pillow; this ffmpeg has no drawtext) ---
    SUBTITLE_FONT_PATH: str = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
    SUBTITLE_SAFE_BOTTOM_PCT: float = 0.20    # platform UI overlay lives here

    # --- storage -------------------------------------------------------
    DATA_DIR: Path = Path("data")
    CACHE_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="STUDIO_",
        extra="ignore",
    )


def _ark_key() -> str:
    """The BytePlus key, from the environment or from `.env`.

    Every other field here is prefixed `STUDIO_`, but the key is conventionally
    plain `ARK_API_KEY` — it is shared with scripts and with the deploy, and
    prefixing it would mean two names for one secret. That exemption means it
    cannot ride in on the prefix, and reading `os.environ` alone is not enough:
    at import time nothing has loaded `.env` yet, so a key that is only in the
    file reads as absent and every API call fails with an empty bearer token.
    """
    from_env = os.environ.get("ARK_API_KEY", "").strip()
    if from_env:
        return from_env

    for candidate in (Path(".env"), Path(__file__).resolve().parents[3] / ".env"):
        try:
            for line in candidate.read_text(encoding="utf-8").splitlines():
                name, _, value = line.partition("=")
                if name.strip() == "ARK_API_KEY":
                    return value.strip().strip('"').strip("'")
        except OSError:
            continue
    return ""


studio_settings = StudioSettings(ARK_API_KEY=_ark_key())
