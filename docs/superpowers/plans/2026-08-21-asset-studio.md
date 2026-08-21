# Asset Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the mock `gen_assets_agent` with a real BytePlus-powered asset studio that turns a campaign brief plus the brand's own product photos into platform-native, brand-consistent image and video kits for TikTok Shop and Shopee.

**Architecture:** A node graph, not a linear pipeline. Sources (kho) feed an inventory step that triages every existing brand photo, a worksheet step that assigns each kit slot to one of three routes (REUSE / REMIX / GENERATE), and then image, video, QA and compose nodes that execute as soon as their inputs are ready. A hero image generated first acts as the *style anchor*: every later image passes both the real product photo and the hero as references, so the whole kit inherits one art direction. Node state changes stream to the frontend over SSE, which renders the live graph.

**Tech Stack:** Python 3.14 · FastAPI · Pydantic v2 · Pillow · ffmpeg (CLI) · BytePlus ModelArk (Seedream 5.0 Pro, Seedance 2.5, Seed 2.1 Turbo vision) · Next.js 16 · React 19 · Tailwind 4 · shadcn/base-ui · @xyflow/react

---

## Global Constraints

- **Branch:** all work on `chau/asset-studio`, branched from `origin/main`. Never commit to `main` directly.
- **Do not break existing tests.** `backend/tests/test_campaigns_api.py` must keep passing after every task. Run `pytest backend/tests -q` before each commit.
- **Schema changes are additive only.** New fields on existing Pydantic models must have defaults. Never rename or remove a field another agent's code reads.
- **Docstrings on every public function**, in English, matching the existing codebase style. Every module starts with a module docstring explaining its role in the graph.
- **Every tunable value lives in `app/services/studio/config.py`**, never hardcoded at a call site. This module is both downstream and upstream of teammates' agents, so its behaviour must be configurable without editing logic.
- **Secrets from env only.** `ARK_API_KEY` via `pydantic-settings`. Never write a key into a source file, a test, or a commit.
- **Every network call goes through `ark.py`'s retry wrapper.** Venue Wi-Fi dropped DNS mid-run during research; a bare `requests.post` is a bug.
- **Never store a BytePlus URL as the source of truth.** Image URLs expire in 24h, video in 48h. Download to `data/<campaign_id>/media/` immediately and store the local path.
- **Language:** code, comments, docstrings, commit messages in English. UI copy in Vietnamese.

---

## Measured API Facts (verified 21/08/2026 — do not re-derive)

Research logs: `probe_out/` in the BHN working directory. These are experimental results, not documentation guesses.

### Seedream 5.0 Pro — `dola-seedream-5-0-pro-260628`

`POST /images/generations`

```jsonc
{
  "model": "dola-seedream-5-0-pro-260628",
  "prompt": "...",
  "size": "2048x2048",        // also "2K", "1440x2560" (9:16). Explicit WxH is safest.
  "response_format": "url",
  "watermark": false,          // MUST be false. Default true stamps "AI generated" on the image.
  "image": "data:image/jpeg;base64,..."        // image-to-image (Brand Lock)
  // OR
  "image": ["data:...ref1", "data:...ref2"]    // TWO references, BOTH are used
}
```

- Single image: **35–60s**. **Ten concurrent images: 44s total** — genuinely parallel, no queueing.
- `image` as a **list of two** works: reference 1 controls the product, reference 2 controls scene/lighting/grade. Verified by generating a mug (ref 1) onto wet stone (ref 2) and getting exactly that.
- **`reference_images` is silently ignored.** It returns HTTP 200 and produces an image identical to the single-reference case. Do not use it. HTTP 200 is not proof a parameter took effect.
- **Text rendering is reliable when every string is explicit.** Vietnamese stacked diacritics (`Ễ`, `Ậ`, `Ể`, `Ụ`, `Ồ`) render correctly. Text the model invents on its own is garbage (`LUNAÁIRA`, `EFFFECTIVE`) — in English too. The failure axis is *specified vs invented*, not Vietnamese vs English.

- **Verified end-to-end against a real brand product** (COSRX Advanced Snail 96, `sample_data/01_.../product_01.jpg`): a hero rendered from the real photo, then four kit images rendered from `image:[product_photo, hero]`. The bottle, cap and label layout carried across every image; the travertine surface, cool diffused light and airy grade stayed consistent; `PHỤC HỒI HÀNG RÀO DA` and `Tinh chất ốc sên 96%` rendered perfectly; the pure-white-background slot correctly overrode the art direction. Five images in ~100s (hero 53s, then four in parallel at ~50s).

- **⚠️ Rotated label text degrades.** In every generated image the vertical wordmark running up the bottle's black band rendered as **`COSRᴀ`** instead of `COSRX`, while the *same string* printed horizontally on the gold label rendered correctly. This is the model redrawing the product's own packaging, not a string we asked for. Two consequences:
  1. It is an independent argument for REUSE on label-critical slots. Shopee's main image and SKU close-up use the brand's real photograph not to save an API call but because regenerating a label risks misspelling the brand name on a listing.
  2. Where a slot must be generated, prefer scenes that present the label face-on, and have the QA gate check every `label_text` string explicitly — a wrong brand name is the most expensive defect this system can ship.

### Seedance 2.5 — `dreamina-seedance-2-5-260628`

`POST /contents/generations/tasks` → `{"id": "cgt-..."}`, then poll `GET /contents/generations/tasks/{id}` until `status == "succeeded"`.

**Top-level parameters are ACCEPTED by 2.5** — verified 21/08 by submitting a task with `resolution: "1080p"`, `generate_audio`, `seed`, `return_last_frame` and `watermark` at the top level; the task was created without complaint. The inline `--flag` form also works and stays available as a fallback via `STUDIO_VIDEO_USE_TOPLEVEL_PARAMS=false`.

```jsonc
// Style 1 — top-level fields (BytePlus Seedance 2.0 official guide). PREFERRED.
{
  "model": "dreamina-seedance-2-5-260628",
  "content": [
    {"type": "text", "text": "..."},
    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}, "role": "first_frame"}
  ],
  "resolution": "1080p",       // 480p | 720p | 1080p
  "ratio": "adaptive",         // 16:9 4:3 1:1 3:4 9:16 21:9 adaptive
  "duration": 5,               // [4, 15], or -1 for model's choice
  "generate_audio": true,      // synchronized audio; dialogue in "double quotes" is spoken
  "watermark": false,
  "seed": 42,                  // reproducibility — reuse on QA retry to keep the look
  "camera_fixed": false,
  "return_last_frame": true    // returns last frame PNG → chain into the next clip seamlessly
}

// Style 2 — inline flags appended to the text. VERIFIED WORKING on 2.5.
{"type": "text", "text": "<prompt> --resolution 720p --ratio adaptive --duration 5"}
```

- **`ratio: "adaptive"` is MANDATORY for first-frame input.** Any other value fails with
  `InvalidParameter.TaskTypeConstraint: For first-frame generation, the output ratio follows the first-frame image.`
- **Output aspect ratio equals the first frame's aspect ratio.** A 1440×2560 first frame gives 720×1280; a 2048×2048 first frame gives 960×960. This is how platform-native video ratios are produced — no cropping.
- **Data URIs are accepted for `image_url`.** No upload step, no public URL needed.
- **Text baked into the first frame survives the whole clip** — verified across frames 0, 55, 118: Vietnamese diacritics intact, kerning intact, product label intact.
- Clips carry **native audio** (h264 + aac).

**⚠️ Seedance must never be asked to render Vietnamese text.** The BytePlus guide advertises
in-model subtitles synchronised to the voiceover, and Seedance does produce them — but the
Vietnamese comes out mangled. Asked for *"Da khô căng, xỉn màu? Tinh chất ốc sên chín mươi sáu
phần trăm phục hồi hàng rào da"* it rendered *"Da khò cáng, xỉn mau? Tình chiật ốc sín chượi chin
mưi sáu phồn viấm việm phục hồi hàng rầu đa"* — nearly every diacritic wrong. Seedream renders the
same sentence perfectly. **All legible text comes from Seedream, baked into the keyframe, which
then survives image-to-video intact.** Because the spoken audio is produced by the same model that
mangled the captions, do not trust it either: `VIDEO_GENERATE_AUDIO` defaults to `false` and
voiceover comes from Seed Audio TTS, which was verified to speak Vietnamese correctly.
- Durations 5s / 10s / 15s all verified. Generation time **134–543s**; variance is large and unpredictable — the slowest clip sets the wall clock.
- **1080p verified**: a 9:16 request returned exactly 1080×1920, in 301s against 207s for the same clip at 720p. Worth the extra time for the master; keep 720p for drafts.
- **`return_last_frame: true` verified**: the finished task carries `content.last_frame_url` alongside `content.video_url`. Useful for a cover still, and for extending a shot. Not used to chain shots together: a four-beat ad wants hard cuts, and chaining would mean only the first shot could carry designed text.
- Four concurrent video tasks all accepted within 1 second and ran in parallel.
- **Modes are mutually exclusive:** `first_frame` / `first_frame`+`last_frame` / multimodal `reference_image` cannot be combined in one request.
- **Reference images may not contain real human faces.** Use model-generated people for UGC-style routes.
- Reference image limits: 1–9 images, aspect ratio 0.4–2.5, 300–6000 px per side, <30 MB each, request body <64 MB.

### Seed 2.1 Turbo — `dola-seed-2-1-turbo-260628`

`POST /chat/completions`. **This is the only vision-capable model this key can reach.** `skylark-vision-250515` → 404; `seed-2-0-*`, `seed-2-0-code-preview` → 403 AccessDenied. Do not plan around them.

```jsonc
{"model": "dola-seed-2-1-turbo-260628", "max_tokens": 600,
 "messages": [{"role": "user", "content": [
   {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
   {"type": "text", "text": "..."}]}]}
```

- A 2048×2048 image **times out past 180s**. A 1024×1024 image answers in **41–109s**.
- At 2048² it transcribes text faithfully including defects (`EFFFECTIVE`). At 1024² it **silently auto-corrects** them (`EFFECTIVE`). Downscaling destroys the signal the QA gate exists to detect.
- **Therefore: tile the 2048² image into four 1024² quadrants and inspect them in parallel.** Native resolution, small payloads, four concurrent calls.
- **The model must transcribe; code must judge.** Asked to render a verdict, it failed a perfectly correct image because it counted the product's own bottle label as "unexpected text". Compare strings in Python.

### Not available

- `web_search` tool and the `/responses` endpoint → **403 AccessDenied**. No live market research.
- Seed Audio 1.0 TTS works (`https://voice.ap-southeast-1.bytepluses.com/api/v3/tts/create`, header `X-Api-Key`, returns `{audio, duration, original_duration, url}`), but if Seedance `generate_audio` produces usable Vietnamese voiceover it is not needed. Task 8 decides.

### ffmpeg

- All Seedance clips share 720×1280 / 24fps / h264 / aac, so `-f concat -c copy` joins them **instantly and losslessly**. Only re-encode when burning in overlays.
- **This ffmpeg build has no `drawtext`** (compiled without freetype). Do not plan text burn-in via `drawtext`; use Pillow to render text onto frames, or rely on Seedream/Seedance text rendering.

---

## Integration Points (teammates' code — read before writing)

| File | Owner | What it means for us |
|---|---|---|
| `backend/app/schemas/campaign.py` | Minh+Nhật | `CampaignInput`, `CampaignPlan`, `AssetBundle`, `ImageAsset`, `VideoAsset`, `QAResult`. We extend additively. |
| `backend/app/services/campaign/gen_assets_agent.py` | **us** | Currently a mock. `generate_assets(plan) -> AssetBundle` is the seam. |
| `backend/app/services/campaign_service.py` | Minh+Nhật | Calls `gen_assets_agent.generate_assets(plan)` then loops QA up to 3 times, **re-calling `generate_assets` in full on failure**. |
| `backend/app/services/campaign/qa_review_agent.py` | Minh+Nhật | Rule checks on the `AssetBundle` *structure*: `MIN_PRODUCT_IMAGES=4`, required `ImageKind`s, `MIN_VIDEOS=1`, duration 15–30s, aspect `9:16`. Our visual QA inspects *pixels* — complementary, no overlap. |
| `backend/app/storage/campaign_store.py` | Minh+Nhật | JSON file store under `data/<campaign_id>/`. |
| `sample_data/0N_<brand>/assets/` | Nam | `product_01.jpg`, `product_02.jpg`, `logo.*`, `SOURCES.md`. Six brands. **This is the kho.** |

**Two problems in the current seam, fixed in Task 2:**

1. `generate_assets(plan)` receives no `CampaignInput`, so it cannot see `brand_kit.product_photo_urls`, `brand_colors`, or `forbidden_claims`. Without the product photos there is no Brand Lock and the entire design collapses. The signature must accept the input.
2. `campaign_service` regenerates *everything* when QA fails. With real generation that is ~7 minutes per iteration, three times. Regeneration must be targeted at the failing assets.

---

## File Structure

```
backend/app/services/studio/
├── __init__.py         public surface: run_studio()
├── config.py           EVERY tunable: model ids, sizes, durations, concurrency, timeouts, retries
├── ark.py              BytePlus client — retry, task resume, download, seedream/seedance/vision
├── graph.py            DAG executor: readiness scheduling, concurrency caps, cache, events
├── looks.py            LOOK preset library (art direction vocabulary) — DATA ONLY
├── platforms.py        KIT specs per platform: slots, ratios, hard rules — DATA ONLY
├── slots.py            SLOT scene templates + SHOT storyboard templates — DATA ONLY
├── inventory.py        triage kho photos: PIL metrics + vision tags → InventorySheet
├── direct.py           brief → StyleSpine, Storyboard, Worksheet (pure logic, no API)
├── prompts.py          the six-block prompt assembler
├── render.py           hero + kit images (Seedream)
├── motion.py           keyframe → clip (Seedance), optional voiceover
├── assemble.py         ffmpeg: concat, cutdowns, Ken Burns fallback
├── qa_visual.py        quadrant-tiled vision gate; model transcribes, code judges
└── pipeline.py         builds the graph, runs it, emits SSE events, returns AssetBundle

backend/app/api/v1/endpoints/studio.py     POST /studio/run, GET /studio/{id}/events (SSE), GET /studio/{id}/pack
backend/tests/studio/                      one test module per studio module

frontend/src/app/studio/page.tsx           the studio screen
frontend/src/components/studio/            GraphCanvas, NodeCard, AssetGrid, KitTabs, BriefPanel
frontend/src/lib/studio-events.ts          typed SSE client
frontend/src/types/studio.ts               TS mirrors of the Pydantic contracts
```

---

## Parallelisation Map (for dispatching agents)

Tasks with no dependency on each other may run concurrently in separate agents. They touch disjoint files.

```
WAVE 1 (start together)   Task 1 config   Task 3 ark   Task 4 graph   Task 5 data tables   Task 12 frontend shell
WAVE 2                    Task 2 schema+seam   Task 6 inventory   Task 7 direct+prompts
WAVE 3                    Task 8 render   Task 9 motion+assemble   Task 10 qa_visual
WAVE 4                    Task 11 pipeline+API
WAVE 5                    Task 13 frontend graph wiring   Task 14 end-to-end smoke
```

---

# Tasks

### Task 1: Studio configuration module

**Files:**
- Create: `backend/app/services/studio/__init__.py`
- Create: `backend/app/services/studio/config.py`
- Test: `backend/tests/studio/test_config.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `studio_settings: StudioSettings` — a pydantic-settings singleton. Every other studio module imports it. Field names below are contractual; later tasks reference them exactly.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/studio/test_config.py
from app.services.studio.config import StudioSettings


def test_defaults_match_measured_api_behaviour():
    s = StudioSettings(ARK_API_KEY="test-key")
    assert s.SEEDREAM_MODEL == "dola-seedream-5-0-pro-260628"
    assert s.SEEDANCE_MODEL == "dreamina-seedance-2-5-260628"
    assert s.VISION_MODEL == "dola-seed-2-1-turbo-260628"
    # watermark must default off: the API stamps "AI generated" when true
    assert s.IMAGE_WATERMARK is False
    # vision tiles must be native resolution: downscaling hides text defects
    assert s.QA_TILE_PX == 1024
    # poll timeout of 30s caused "Read timed out" during research
    assert s.POLL_TIMEOUT_SEC >= 90


def test_env_overrides_are_honoured(monkeypatch):
    monkeypatch.setenv("STUDIO_IMAGE_CONCURRENCY", "3")
    s = StudioSettings(ARK_API_KEY="test-key")
    assert s.IMAGE_CONCURRENCY == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/studio/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.studio'`

- [ ] **Step 3: Write the implementation**

```python
# backend/app/services/studio/config.py
"""
Every tunable value for the Asset Studio.

This module is the studio's control panel. The studio sits between two
teammate-owned agents (gen_plan upstream, qa_review downstream), so its
behaviour has to be adjustable without editing logic. Nothing in the studio
may hardcode a model id, a size, a timeout, or a concurrency cap: it belongs
here, and every field is overridable by environment variable using the
STUDIO_ prefix (e.g. STUDIO_IMAGE_CONCURRENCY=3).

Defaults encode API behaviour measured on 21/08/2026, not documentation
guesses. Comments explain why a value is what it is; change them knowingly.
"""
from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class StudioSettings(BaseSettings):
    # --- credentials -------------------------------------------------
    ARK_API_KEY: str
    ARK_BASE_URL: str = "https://ark.ap-southeast.bytepluses.com/api/v3"
    ARK_VOICE_URL: str = "https://voice.ap-southeast-1.bytepluses.com/api/v3"
    ARK_VOICE_KEY: str = "4169cffe-406a-4e7e-a361-f3ed6d06d363"  # supplied by organisers

    # --- models (BP-01 mandates Seedream 5.0 Pro + Seedance 2.5) ------
    SEEDREAM_MODEL: str = "dola-seedream-5-0-pro-260628"
    SEEDANCE_MODEL: str = "dreamina-seedance-2-5-260628"
    VISION_MODEL: str = "dola-seed-2-1-turbo-260628"  # the only vision model this key can reach
    TTS_MODEL: str = "seed-audio-1.0"

    # --- image generation --------------------------------------------
    IMAGE_SIZE_SQUARE: str = "2048x2048"
    IMAGE_SIZE_PORTRAIT: str = "1440x2560"   # 9:16, drives 720x1280 video via ratio=adaptive
    IMAGE_SIZE_LANDSCAPE: str = "2560x1280"  # 2:1 promo banner
    IMAGE_SIZE_FEED: str = "1638x2048"       # 4:5 social feed
    IMAGE_WATERMARK: bool = False            # true stamps "AI generated" onto the image

    # --- video generation --------------------------------------------
    VIDEO_RESOLUTION: str = "720p"           # 1080p if Task 9 confirms 2.5 accepts it
    VIDEO_SHOT_SECONDS: int = 5
    # False: Seedance mangles Vietnamese in its captions, so its audio is not
    # trusted either. Voiceover comes from Seed Audio TTS and is muxed in.
    VIDEO_GENERATE_AUDIO: bool = False
    VIDEO_SUBTITLES_FROM_SEEDANCE: bool = False  # never true: Vietnamese comes out garbled
    VIDEO_USE_TOPLEVEL_PARAMS: bool = True   # False falls back to inline "--ratio ... --duration ..."
    VIDEO_SHOT_DEADLINE_SEC: int = 300       # past this, Ken Burns from the keyframe instead

    # --- concurrency (measured: 10 images in 44s; 4 videos ran parallel)
    IMAGE_CONCURRENCY: int = 8
    VIDEO_CONCURRENCY: int = 4
    VISION_CONCURRENCY: int = 4

    # --- resilience (venue Wi-Fi dropped DNS mid-run) -----------------
    HTTP_RETRIES: int = 6
    HTTP_BACKOFF_CAP_SEC: int = 20
    POLL_TIMEOUT_SEC: int = 90               # 30s produced "Read timed out"
    POLL_INTERVAL_SEC: int = 10
    TASK_MAX_WAIT_SEC: int = 900

    # --- inventory thresholds -----------------------------------------
    # Seedance rejects any reference image under 300px on either side with
    # InvalidParameter. Audited 21/08: every sample_data product photo passes,
    # but 3 of 5 logos do not (COSRX 129x27, Oatside 800x200, Marou 205x145).
    REF_MIN_PX: int = 300
    # Shopee's hard floor for a main listing image is 500x500 (1000x1000 is the
    # recommendation). 800 is used so the flagship COSRX photos (800x1067) stay
    # eligible for REUSE — raising this to 1000 pushes the demo brand's whole
    # Shopee kit into GENERATE and throws away the real-photo story.
    SHOPEE_MIN_PX: int = 800
    SLOT_MIN_PX: int = 800                   # general floor for reusing a photo in a kit slot

    # --- QA -----------------------------------------------------------
    QA_TILE_PX: int = 1024                   # tile size; downscaling whole images hides defects
    QA_MAX_ATTEMPTS: int = 2                 # regeneration attempts per asset

    # --- storage -------------------------------------------------------
    DATA_DIR: Path = Path("data")
    CACHE_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8",
        env_prefix="STUDIO_", extra="ignore",
    )


# ARK_API_KEY has no STUDIO_ prefix in .env, so read it explicitly.
import os  # noqa: E402

studio_settings = StudioSettings(ARK_API_KEY=os.environ.get("ARK_API_KEY", ""))
```

Also create `backend/app/services/studio/__init__.py` containing only a module docstring, and `backend/tests/studio/__init__.py` (empty).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/studio/test_config.py -v`
Expected: PASS, 2 tests.

- [ ] **Step 5: Add dependencies and commit**

Append to `backend/requirements.txt`:
```
pillow>=11.0.0
requests>=2.32.0
python-dotenv>=1.0.0
```

```bash
git add backend/app/services/studio backend/tests/studio backend/requirements.txt
git commit -m "feat(studio): add configuration module with measured API defaults"
```

---

### Task 2: Extend the schema and widen the agent seam

**Files:**
- Modify: `backend/app/schemas/campaign.py` (append new models; add optional fields to `ImageAsset`, `VideoAsset`, `AssetBundle`)
- Modify: `backend/app/services/campaign/gen_assets_agent.py` (widen signature, keep mock behaviour)
- Modify: `backend/app/services/campaign_service.py:31` (pass `campaign_input` through)
- Test: `backend/tests/studio/test_schema_compat.py`

**Interfaces:**
- Consumes: existing `campaign.py` models.
- Produces:
  - `generate_assets(plan: CampaignPlan, campaign_input: CampaignInput | None = None) -> AssetBundle`
  - `Platform` (str enum): `TIKTOK_SHOP = "tiktok_shop"`, `SHOPEE = "shopee"`
  - `AssetOrigin` (str enum): `REUSE = "reuse"`, `REMIX = "remix"`, `GENERATE = "generate"`
  - `ImageAsset` gains: `platform: Platform | None`, `slot: str | None`, `origin: AssetOrigin | None`, `local_path: str | None`, `prompt: str | None`, `text_rendered: list[str]`, `source_photo: str | None`, `qa_passed: bool | None`, `qa_notes: list[str]`, `gen_seconds: float | None`
  - `VideoAsset` gains: `platform: Platform | None`, `local_path: str | None`, `shots: list[ShotAsset]`, `has_voiceover: bool`, `cutdowns: list[VideoCutdown]`
  - `ShotAsset`: `index: int`, `role: str`, `keyframe_path: str`, `clip_path: str | None`, `duration_sec: float`, `onscreen_text: str`, `vo_text: str`, `used_fallback: bool = False`
  - `VideoCutdown`: `label: str`, `local_path: str`, `duration_sec: float`, `aspect_ratio: str`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/studio/test_schema_compat.py
"""The studio extends teammate-owned schemas. Extensions must never break
existing consumers: every new field is optional with a default, and the old
call shape must keep working."""
import inspect

from app.schemas.campaign import AssetBundle, ImageAsset, ImageKind, Platform, AssetOrigin
from app.services.campaign import gen_assets_agent


def test_old_imageasset_construction_still_works():
    """qa_review_agent builds/reads ImageAsset with only the original fields."""
    a = ImageAsset(kind=ImageKind.HERO, url="mock://x/hero.jpg", width=2048, height=2048)
    assert a.platform is None
    assert a.origin is None
    assert a.text_rendered == []


def test_generate_assets_accepts_campaign_input_and_stays_optional():
    sig = inspect.signature(gen_assets_agent.generate_assets)
    assert list(sig.parameters) == ["plan", "campaign_input"]
    assert sig.parameters["campaign_input"].default is None


def test_platform_and_origin_values():
    assert Platform.TIKTOK_SHOP.value == "tiktok_shop"
    assert Platform.SHOPEE.value == "shopee"
    assert {o.value for o in AssetOrigin} == {"reuse", "remix", "generate"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/studio/test_schema_compat.py -v`
Expected: FAIL — `ImportError: cannot import name 'Platform'`

- [ ] **Step 3: Extend `campaign.py`**

Add after the `ImageKind` enum:

```python
class Platform(str, Enum):
    """Marketplace a kit is built for. Kit contents differ per platform."""
    TIKTOK_SHOP = "tiktok_shop"
    SHOPEE = "shopee"


class AssetOrigin(str, Enum):
    """How an asset was produced.

    REUSE    — an existing brand photo, cropped/resized only. Used where the
               shopper inspects the product and an invented pixel is a liability.
    REMIX    — image-to-image from a real product photo (new scene, added text).
    GENERATE — synthesised, anchored to the product photo and the hero image.
    """
    REUSE = "reuse"
    REMIX = "remix"
    GENERATE = "generate"


class ShotAsset(BaseModel):
    """One shot of a multi-shot video. Its keyframe carries the on-screen text."""
    index: int
    role: str                      # hook | product | benefit | cta
    keyframe_path: str
    clip_path: Optional[str] = None
    duration_sec: float = 5.0
    onscreen_text: str = ""
    vo_text: str = ""
    used_fallback: bool = False    # True when the clip missed its deadline and
                                   # a Ken Burns move over the keyframe was used


class VideoCutdown(BaseModel):
    """A derived cut of the master video (shorter, or a different aspect)."""
    label: str                     # "15s" | "1x1" | ...
    local_path: str
    duration_sec: float
    aspect_ratio: str
```

Then add optional fields to the existing models (defaults keep old constructors valid):

```python
class ImageAsset(BaseModel):
    kind: ImageKind
    url: str
    width: int
    height: int
    model: str = "dola-seedream-5-0-pro-260628"

    # --- studio extensions (all optional; older consumers ignore them) ---
    platform: Optional[Platform] = None
    slot: Optional[str] = None
    origin: Optional[AssetOrigin] = None
    local_path: Optional[str] = None
    prompt: Optional[str] = None
    text_rendered: list[str] = Field(default_factory=list)
    source_photo: Optional[str] = None
    qa_passed: Optional[bool] = None
    qa_notes: list[str] = Field(default_factory=list)
    gen_seconds: Optional[float] = None
```

```python
class VideoAsset(BaseModel):
    url: str
    duration_sec: float
    resolution: str
    aspect_ratio: str
    model: str = "dreamina-seedance-2-5-260628"
    route_id: Optional[str] = None

    # --- studio extensions ---
    platform: Optional[Platform] = None
    local_path: Optional[str] = None
    shots: list[ShotAsset] = Field(default_factory=list)
    has_voiceover: bool = False
    cutdowns: list[VideoCutdown] = Field(default_factory=list)
```

- [ ] **Step 4: Widen the agent seam without changing mock behaviour**

In `gen_assets_agent.py`, change the signature and add `CampaignInput` to the imports:

```python
def generate_assets(
    plan: CampaignPlan,
    campaign_input: CampaignInput | None = None,
) -> AssetBundle:
    """Produce the asset bundle for a campaign plan.

    `campaign_input` carries what the plan does not: the brand's real product
    photos (Brand Lock reference), brand colours, and forbidden claims. Without
    it the studio can only synthesise generic product imagery, so callers should
    always pass it. It stays optional so existing tests and callers keep working.
    """
```

In `campaign_service.py`, update both call sites (line ~31 and the regeneration call ~line 47):

```python
assets: AssetBundle = gen_assets_agent.generate_assets(plan, campaign_input)
```

- [ ] **Step 5: Run the full backend suite**

Run: `cd backend && python -m pytest tests -q`
Expected: PASS — the new tests plus every pre-existing test in `test_campaigns_api.py`.

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/campaign.py backend/app/services/campaign/gen_assets_agent.py \
        backend/app/services/campaign_service.py backend/tests/studio/test_schema_compat.py
git commit -m "feat(schema): add platform/origin/shot models and pass CampaignInput to gen_assets"
```

---

### Task 3: BytePlus client

**Files:**
- Create: `backend/app/services/studio/ark.py`
- Test: `backend/tests/studio/test_ark.py`

**Interfaces:**
- Consumes: `studio_settings` from Task 1.
- Produces:
  - `to_data_uri(path: str | Path) -> str`
  - `generate_image(prompt: str, size: str, refs: list[str] | None = None) -> bytes` — `refs` are data URIs; passed as `image` (str when one, list when two or more).
  - `create_video_task(prompt: str, first_frame: str | None = None, refs: list[str] | None = None, duration: int | None = None, ratio: str | None = None, resolution: str | None = None, seed: int | None = None, return_last_frame: bool = False) -> str` — returns task id, persisted to disk before returning.
  - `wait_video_task(task_id: str) -> VideoResult` where `VideoResult` is a dataclass with `video_bytes: bytes`, `last_frame_bytes: bytes | None`, `elapsed_sec: float`.
  - `describe_image(image_bytes: bytes, prompt: str, max_tokens: int = 600) -> str`
  - `synthesize_speech(text_prompt: str) -> bytes`
  - `ArkError(Exception)` — raised on non-retryable API rejection, carrying `.status` and `.body`.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/studio/test_ark.py
"""ark.py is the only place the studio touches the network. These tests pin the
payload shapes that were verified experimentally — getting them wrong fails
silently in production (see `reference_images`, which returns 200 and does
nothing), so they are asserted here rather than trusted."""
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/studio/test_ark.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.studio.ark'`

- [ ] **Step 3: Implement `ark.py`**

Write the module with this structure. Requirements, each traceable to a measured fact above:

1. `_retry(fn, label)` — catch only `requests.ConnectionError` and `requests.Timeout`, sleep `min(2**i, HTTP_BACKOFF_CAP_SEC)`, up to `HTTP_RETRIES`. Never retry an HTTP error response: a 403 or a 404 will not become a 200.
2. `_raise_for_api(resp)` — if `not resp.ok`, raise `ArkError(status=resp.status_code, body=resp.text[:500])`.
3. `generate_image` — POST `/images/generations` with `model`, `prompt`, `size`, `response_format: "url"`, `watermark: studio_settings.IMAGE_WATERMARK`. When `refs` has exactly one entry send `image=refs[0]`; when it has two or more send `image=refs`. Download the returned URL immediately and return the bytes — the URL expires in 24 hours.
4. `create_video_task` — build `content` as `[{"type": "text", ...}]`, prepending `{"type": "image_url", "image_url": {"url": first_frame}, "role": "first_frame"}` when a first frame is given, or appending one `{"role": "reference_image"}` entry per item in `refs` otherwise. **Never send both**: the modes are mutually exclusive. **Force `ratio="adaptive"` whenever `first_frame` is set**, ignoring any caller value. When `studio_settings.VIDEO_USE_TOPLEVEL_PARAMS` is true put `resolution`/`ratio`/`duration`/`generate_audio`/`watermark`/`seed`/`return_last_frame` at the top level; otherwise append `--resolution {r} --ratio {a} --duration {d}` to the text. Persist the returned id to `DATA_DIR/tasks/{task_id}.json` with its payload **before returning**, so a network drop cannot lose a 200-second render.
5. `wait_video_task` — poll `GET /contents/generations/tasks/{id}` every `POLL_INTERVAL_SEC` with `timeout=POLL_TIMEOUT_SEC`, up to `TASK_MAX_WAIT_SEC`. On `succeeded`, download `content.video_url` and `content.last_frame_url` when present. On `failed`/`cancelled`, raise `ArkError`.
6. `describe_image` — POST `/chat/completions` to `VISION_MODEL` with an `image_url` data URI plus a text part. Use `timeout=600`; vision is slow.
7. `synthesize_speech` — POST `{ARK_VOICE_URL}/tts/create` with header `X-Api-Key: ARK_VOICE_KEY` and body `{"model", "text_prompt", "audio_config": {"format": "mp3", "sample_rate": 48000, "pitch_rate": 0, "speech_rate": 0, "loudness_rate": 0}, "watermark": {}}`. The response is `{audio, duration, original_duration, url}`; fetch `url` and return the bytes.

Every public function needs a docstring naming the endpoint it calls and any measured constraint it enforces.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/studio/test_ark.py -v`
Expected: PASS, 5 tests.

- [ ] **Step 5: Live smoke test (network required)**

```bash
cd backend && python -c "
from app.services.studio import ark
b = ark.generate_image('a red ceramic mug on a wooden table, product photo', '2048x2048')
open('/tmp/smoke.jpg','wb').write(b); print('image bytes:', len(b))
"
```
Expected: a JPEG over 100 KB. Open it and confirm there is **no 'AI generated' watermark** in the bottom-right corner.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/studio/ark.py backend/tests/studio/test_ark.py
git commit -m "feat(studio): add BytePlus client with retry, task persistence and measured payload shapes"
```

---

### Task 4: Graph executor

**Files:**
- Create: `backend/app/services/studio/graph.py`
- Test: `backend/tests/studio/test_graph.py`

**Interfaces:**
- Consumes: `studio_settings`.
- Produces:
  - `Node` dataclass: `id: str`, `kind: str`, `deps: list[str]`, `run: Callable[[dict[str, Any]], Any]`, `concurrency_group: str = "default"`, `cache_key: str | None = None`
  - `NodeState` (str enum): `PENDING`, `RUNNING`, `DONE`, `RETRY`, `DEGRADED`, `FAILED`
  - `GraphEvent` dataclass: `node_id`, `kind`, `state`, `payload: dict`, `elapsed_sec: float`
  - `run_graph(nodes: list[Node], on_event: Callable[[GraphEvent], None], groups: dict[str, int] | None = None) -> dict[str, Any]` — returns node id → result. Runs any node whose dependencies are all `DONE`; a node whose dependency `FAILED` is skipped and marked `FAILED`.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/studio/test_graph.py
"""The graph is what makes the studio fast and resumable. Two properties matter:
independent branches must not wait on each other (Shopee's reuse nodes must not
block on the hero render), and one failing node must not take the whole run down."""
import threading
import time

from app.services.studio.graph import Node, NodeState, run_graph


def test_independent_nodes_run_concurrently():
    started = []
    lock = threading.Lock()

    def slow(_):
        with lock:
            started.append(time.time())
        time.sleep(0.3)
        return "ok"

    nodes = [Node(id=f"n{i}", kind="test", deps=[], run=slow) for i in range(4)]
    t0 = time.time()
    results = run_graph(nodes, on_event=lambda e: None, groups={"default": 4})
    assert time.time() - t0 < 0.9          # concurrent, not 4 x 0.3 = 1.2s
    assert set(results) == {"n0", "n1", "n2", "n3"}


def test_dependency_receives_upstream_results_by_id():
    nodes = [
        Node(id="a", kind="t", deps=[], run=lambda ctx: 2),
        Node(id="b", kind="t", deps=["a"], run=lambda ctx: ctx["a"] * 21),
    ]
    assert run_graph(nodes, on_event=lambda e: None)["b"] == 42


def test_failed_node_marks_dependents_failed_but_siblings_still_run():
    def boom(_):
        raise RuntimeError("render died")

    nodes = [
        Node(id="bad", kind="t", deps=[], run=boom),
        Node(id="child", kind="t", deps=["bad"], run=lambda ctx: "never"),
        Node(id="sibling", kind="t", deps=[], run=lambda ctx: "fine"),
    ]
    states = {}
    run_graph(nodes, on_event=lambda e: states.__setitem__(e.node_id, e.state))
    assert states["bad"] is NodeState.FAILED
    assert states["child"] is NodeState.FAILED
    assert states["sibling"] is NodeState.DONE


def test_events_are_emitted_for_every_transition():
    seen = []
    nodes = [Node(id="a", kind="image", deps=[], run=lambda ctx: "x")]
    run_graph(nodes, on_event=seen.append)
    assert [e.state for e in seen] == [NodeState.RUNNING, NodeState.DONE]
    assert seen[0].kind == "image"


def test_concurrency_group_caps_are_respected():
    live, peak = [0], [0]
    lock = threading.Lock()

    def tracked(_):
        with lock:
            live[0] += 1
            peak[0] = max(peak[0], live[0])
        time.sleep(0.15)
        with lock:
            live[0] -= 1
        return 1

    nodes = [Node(id=f"v{i}", kind="video", deps=[], run=tracked,
                  concurrency_group="video") for i in range(6)]
    run_graph(nodes, on_event=lambda e: None, groups={"video": 2})
    assert peak[0] <= 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/studio/test_graph.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement `graph.py`**

Use `concurrent.futures.ThreadPoolExecutor` (the workload is network-bound, and `ark.py` is synchronous `requests`). Loop: find every `PENDING` node whose deps are all `DONE` and whose `concurrency_group` has a free slot; submit it; wait for any future to complete; repeat until nothing is pending or runnable. Emit a `GraphEvent` on entering `RUNNING` and on reaching a terminal state. Mark a node `FAILED` without running it when any dependency is `FAILED`. When `CACHE_ENABLED` and `cache_key` is set, look for `DATA_DIR/cache/{cache_key}.json` and short-circuit on a hit — this is what makes a re-run after a crash near-instant.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/studio/test_graph.py -v`
Expected: PASS, 5 tests.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/studio/graph.py backend/tests/studio/test_graph.py
git commit -m "feat(studio): add DAG executor with per-group concurrency, caching and events"
```

---

### Task 5: Art direction data tables

**Files:**
- Create: `backend/app/services/studio/looks.py`
- Create: `backend/app/services/studio/platforms.py`
- Create: `backend/app/services/studio/slots.py`
- Test: `backend/tests/studio/test_tables.py`

**Interfaces:**
- Consumes: `Platform`, `AssetOrigin`, `ImageKind` from `app.schemas.campaign`.
- Produces:
  - `looks.LOOKS: dict[str, Look]` where `Look` has `lens`, `light`, `surface`, `grade`, `palette_hint`, `axes: dict[str, str]`
  - `looks.pick_looks(category: str, tone: str, trend: str, winning_route: str | None) -> tuple[str, str]` — returns two look keys that differ on at least two axes
  - `platforms.KITS: dict[Platform, KitSpec]`; `KitSpec` has `slots: list[SlotSpec]` and `hard_rules: list[str]`
  - `slots.SLOT_SCENES: dict[str, str]` (scene templates with `{surface}` / `{light}` placeholders)
  - `slots.SHOT_TEMPLATES: list[ShotTemplate]` with `role`, `scene_from`, `text_key`, `seconds`

These three modules contain **data only** — no API calls, no branching logic beyond `pick_looks`. They are the tuning surface for the art director and must stay readable by a non-programmer.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/studio/test_tables.py
"""These tables are the studio's taste. The tests guard the properties that make
the output usable rather than the exact wording, which the art director tunes."""
from app.schemas.campaign import ImageKind, Platform
from app.services.studio.looks import LOOKS, pick_looks
from app.services.studio.platforms import KITS
from app.services.studio.slots import SHOT_TEMPLATES, SLOT_SCENES


def test_ab_looks_differ_on_at_least_two_axes():
    """Two routes that look alike make the A/B test meaningless."""
    a, b = pick_looks("Skincare", "clean, scientific", "glass skin", None)
    differing = [k for k in LOOKS[a].axes if LOOKS[a].axes[k] != LOOKS[b].axes[k]]
    assert len(differing) >= 2


def test_winning_past_route_forces_its_look():
    a, b = pick_looks("Skincare", "clean, scientific", "glass skin",
                      winning_route="testimonial_ugc")
    assert "street_ugc" in (a, b)


def test_every_look_fills_every_prompt_placeholder():
    for key, look in LOOKS.items():
        for field in ("lens", "light", "surface", "grade"):
            assert getattr(look, field).strip(), f"{key}.{field} is empty"


def test_both_demo_kits_exist_and_cover_the_bp01_minimum():
    assert set(KITS) >= {Platform.TIKTOK_SHOP, Platform.SHOPEE}
    kinds = {s.kind for kit in KITS.values() for s in kit.slots}
    assert {ImageKind.HERO, ImageKind.SKU_DETAIL,
            ImageKind.COLLECTION, ImageKind.THUMBNAIL} <= kinds


def test_shopee_main_image_demands_a_white_background_and_prefers_a_real_photo():
    """Marketplace rule, and the slot where an invented pixel costs a return."""
    main = next(s for s in KITS[Platform.SHOPEE].slots if s.id == "shopee_main")
    assert main.rule == "pure_white_bg"
    assert main.prefer_origin.value == "reuse"


def test_every_slot_scene_template_resolves():
    for slot_id, tpl in SLOT_SCENES.items():
        rendered = tpl.format(surface="stone", light="soft light")
        assert "{" not in rendered, f"{slot_id} has an unfilled placeholder"


def test_storyboard_is_hook_product_benefit_cta():
    assert [s.role for s in SHOT_TEMPLATES] == ["hook", "product", "benefit", "cta"]
    assert sum(s.seconds for s in SHOT_TEMPLATES) >= 15   # qa_review_agent's floor
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/studio/test_tables.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.studio.looks'`

- [ ] **Step 3: Write `looks.py`**

Six presets, each a complete art direction. `axes` is what `pick_looks` compares: keys `light` (`cool_diffuse` | `warm_window` | `hard_key` | `mixed_daylight` | `single_hard`), `contrast` (`low` | `mid` | `high`), `surface` (`clinical` | `domestic` | `studio` | `natural`).

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Look:
    """One complete art direction. Its four text fields are injected verbatim
    into the STYLE block of every prompt in a route — that repetition is what
    makes a kit look like a single shoot. `axes` is the machine-comparable
    summary used to guarantee A and B are visually distant."""
    lens: str
    light: str
    surface: str
    grade: str
    palette_hint: str
    axes: dict[str, str] = field(default_factory=dict)


LOOKS = {
    "clinical_lab": Look(
        lens="85mm macro, shallow depth of field",
        light="cool diffused softbox from the left, gentle falloff",
        surface="wet travertine and white acrylic",
        grade="neutral, low contrast, airy",
        palette_hint="white, pale grey, one cool accent",
        axes={"light": "cool_diffuse", "contrast": "low", "surface": "clinical"},
    ),
    "warm_home": Look(
        lens="50mm, eye level",
        light="morning window sunlight with soft falling shadow",
        surface="washed linen and light oak",
        grade="warm, mid contrast, creamy highlights",
        palette_hint="cream, oat, warm wood",
        axes={"light": "warm_window", "contrast": "mid", "surface": "domestic"},
    ),
    "street_ugc": Look(
        lens="35mm handheld, slight tilt",
        light="mixed uneven daylight, small blown highlights",
        surface="a real cluttered desk with everyday objects",
        grade="warm, high contrast, slight grain",
        palette_hint="unstyled everyday colour",
        axes={"light": "mixed_daylight", "contrast": "high", "surface": "domestic"},
    ),
    "studio_pop": Look(
        lens="50mm, straight on",
        light="hard key light with a coloured rim",
        surface="seamless coloured backdrop",
        grade="saturated, high contrast, punchy",
        palette_hint="one bold brand colour plus white",
        axes={"light": "hard_key", "contrast": "high", "surface": "studio"},
    ),
    "dark_luxe": Look(
        lens="100mm macro",
        light="single hard light with deep falloff",
        surface="black stone with a mirror reflection",
        grade="deep contrast, cool specular highlights",
        palette_hint="near-black, graphite, one metallic accent",
        axes={"light": "single_hard", "contrast": "high", "surface": "studio"},
    ),
    "fresh_market": Look(
        lens="35mm, slightly above",
        light="bright even daylight",
        surface="a wooden board with fresh ingredients",
        grade="natural, saturated, clean whites",
        palette_hint="fresh greens and warm neutrals",
        axes={"light": "mixed_daylight", "contrast": "mid", "surface": "natural"},
    ),
}
```

`pick_looks` — map category to a primary candidate (skincare → `clinical_lab`, F&B → `fresh_market`, electronics → `dark_luxe`), then choose the partner that maximises axis distance from it. When `winning_route` contains `ugc` or `testimonial`, force `street_ugc` into the pair: past performance beats category convention.

- [ ] **Step 4: Write `platforms.py`**

```python
KITS = {
    Platform.TIKTOK_SHOP: KitSpec(
        hard_rules=[
            "keep text clear of the right 15% and bottom 20% (platform UI overlay)",
            "the hook must land within the first 3 seconds",
        ],
        slots=[
            SlotSpec(id="tiktok_cover", kind=ImageKind.THUMBNAIL, ratio="9:16",
                     size_key="IMAGE_SIZE_PORTRAIT", text_keys=["headline"],
                     prefer_origin=AssetOrigin.GENERATE),
            SlotSpec(id="tiktok_product", kind=ImageKind.HERO, ratio="1:1",
                     size_key="IMAGE_SIZE_SQUARE", text_keys=[],
                     prefer_origin=AssetOrigin.REUSE),
        ],
        video_slots=[VideoSlot(id="tiktok_master", ratio="9:16", shots=4,
                               cutdowns=["15s"], voiceover=True)],
    ),
    Platform.SHOPEE: KitSpec(
        hard_rules=["main image must be a pure white background", "minimum 1000x1000"],
        slots=[
            SlotSpec(id="shopee_main", kind=ImageKind.HERO, ratio="1:1",
                     size_key="IMAGE_SIZE_SQUARE", text_keys=[], rule="pure_white_bg",
                     prefer_origin=AssetOrigin.REUSE),
            SlotSpec(id="shopee_sku", kind=ImageKind.SKU_DETAIL, ratio="1:1",
                     size_key="IMAGE_SIZE_SQUARE", text_keys=[],
                     prefer_origin=AssetOrigin.REUSE),
            SlotSpec(id="shopee_collection", kind=ImageKind.COLLECTION, ratio="1:1",
                     size_key="IMAGE_SIZE_SQUARE", text_keys=["headline"],
                     prefer_origin=AssetOrigin.REMIX),
            SlotSpec(id="shopee_banner", kind=ImageKind.BANNER, ratio="2:1",
                     size_key="IMAGE_SIZE_LANDSCAPE", text_keys=["badge", "promo"],
                     prefer_origin=AssetOrigin.REMIX),
        ],
        video_slots=[VideoSlot(id="shopee_square", ratio="1:1", shots=2,
                               cutdowns=[], voiceover=False)],
    ),
}
```

- [ ] **Step 5: Write `slots.py`**

`SLOT_SCENES` maps each `SlotSpec.id` to a scene template using `{surface}` and `{light}`. `shopee_main` is the exception: `"the product centred on a pure white seamless background, soft contact shadow"` — no look placeholders, because the marketplace rule overrides the art direction.

`SHOT_TEMPLATES` is the four-beat storyboard:

```python
SHOT_TEMPLATES = [
    ShotTemplate(role="hook",    scene_from="consumer_pain_point",   text_key="headline", seconds=5),
    ShotTemplate(role="product", scene_from="product_photo",         text_key="name_claim", seconds=5),
    ShotTemplate(role="benefit", scene_from="key_selling_points[0]", text_key="benefit",  seconds=5),
    ShotTemplate(role="cta",     scene_from="promotion",             text_key="badge_cta", seconds=5),
]
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/studio/test_tables.py -v`
Expected: PASS, 7 tests.

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/studio/looks.py backend/app/services/studio/platforms.py \
        backend/app/services/studio/slots.py backend/tests/studio/test_tables.py
git commit -m "feat(studio): add look presets, platform kit specs and storyboard templates"
```

---

### Task 6: Inventory — triage the kho

**Files:**
- Create: `backend/app/services/studio/inventory.py`
- Test: `backend/tests/studio/test_inventory.py`

**Interfaces:**
- Consumes: `ark.describe_image`, `studio_settings`.
- Produces:
  - `PhotoFacts` dataclass: `path: str`, `width: int`, `height: int`, `aspect: float`, `bg_whiteness: float` (0–1), `sharpness: float`, `tags: list[str]`, `eligible_slots: list[str]`
  - `InventorySheet` dataclass: `photos: list[PhotoFacts]`, `by_slot: dict[str, list[str]]`
  - `measure(path: str) -> PhotoFacts` — Pillow only, no network, instant
  - `build_sheet(paths: list[str], use_vision: bool = True) -> InventorySheet`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/studio/test_inventory.py
"""Inventory decides which slots can be filled with the brand's real photos.
Getting `bg_whiteness` wrong sends an off-white photo to Shopee's main slot and
breaks a marketplace rule, so it is measured, not guessed."""
from PIL import Image

from app.services.studio.inventory import build_sheet, measure


def _make(tmp_path, name, size=(1200, 1200), bg=(255, 255, 255), blob=(80, 40, 40)):
    im = Image.new("RGB", size, bg)
    w, h = size
    for x in range(w // 3, 2 * w // 3):
        for y in range(h // 3, 2 * h // 3):
            im.putpixel((x, y), blob)
    p = tmp_path / name
    im.save(p, quality=95)
    return str(p)


def test_white_background_photo_scores_near_one(tmp_path):
    facts = measure(_make(tmp_path, "white.jpg"))
    assert facts.bg_whiteness > 0.9
    assert facts.width == 1200 and abs(facts.aspect - 1.0) < 0.01


def test_coloured_background_photo_scores_low(tmp_path):
    facts = measure(_make(tmp_path, "beige.jpg", bg=(180, 150, 110)))
    assert facts.bg_whiteness < 0.5


def test_white_square_photo_is_eligible_for_shopee_main(tmp_path):
    sheet = build_sheet([_make(tmp_path, "a.jpg")], use_vision=False)
    assert "shopee_main" in sheet.photos[0].eligible_slots
    assert sheet.by_slot["shopee_main"] == [sheet.photos[0].path]


def test_small_photo_is_not_eligible_for_shopee_main(tmp_path):
    """Shopee requires at least 1000x1000."""
    sheet = build_sheet([_make(tmp_path, "small.jpg", size=(600, 600))], use_vision=False)
    assert "shopee_main" not in sheet.photos[0].eligible_slots


def test_by_slot_is_empty_not_missing_when_nothing_qualifies(tmp_path):
    sheet = build_sheet([_make(tmp_path, "beige.jpg", bg=(180, 150, 110))], use_vision=False)
    assert sheet.by_slot.get("shopee_main", []) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/studio/test_inventory.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement `inventory.py`**

`measure` — open with Pillow, convert to RGB. `bg_whiteness`: sample a 12-pixel-wide band along all four edges and return the fraction of pixels whose min channel exceeds 235. `sharpness`: variance of the Laplacian, approximated with `ImageFilter.FIND_EDGES` then `ImageStat.Stat(...).stddev[0]`. No network.

`build_sheet` — call `measure` on every path. When `use_vision`, batch through `ark.describe_image` (respecting `VISION_CONCURRENCY`) with:

> "Describe this product photo for an e-commerce asset librarian. Answer as JSON: {\"angle\": \"front|side|top|macro|lifestyle\", \"has_people\": bool, \"has_text\": bool, \"product_count\": int, \"background\": \"white|plain|scene\", \"label_readable\": bool}"

Merge the tags into `PhotoFacts.tags`. Then apply eligibility rules — pure functions, easy to tune:

| Slot | Requires |
|---|---|
| `shopee_main` | `bg_whiteness > 0.9`, `min(w,h) >= SHOPEE_MIN_PX`, `product_count == 1`, `not has_text` |
| `shopee_sku` | `min(w,h) >= SLOT_MIN_PX`, angle in `{macro, front}`, `label_readable` |
| `shopee_collection` | `product_count >= 2` |
| `tiktok_product` | `min(w,h) >= SLOT_MIN_PX`, `not has_people` |

Two hard disqualifications, both measured rather than assumed:

- **`min(w, h) < REF_MIN_PX` (300) → the photo can never be a video reference.** Seedance returns
  `InvalidParameter: expected the width to be at least 300px`. Set `PhotoFacts.tags += ["too_small_for_ref"]`
  and exclude it from every reference list. This is why the COSRX logo (129×27) cannot be pinned into video.
- **`has_people` → excluded from every video reference slot.** Seedance rejects reference images
  containing real human faces.

Also skip `.svg` entirely: Pillow cannot open it and the API accepts only jpeg/png/webp/bmp/tiff/gif/heic/heif.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/studio/test_inventory.py -v`
Expected: PASS, 5 tests.

- [ ] **Step 5: Run against the real kho**

```bash
cd backend && python -c "
from app.services.studio.inventory import build_sheet
import glob
sheet = build_sheet(sorted(glob.glob('../sample_data/01_cosrx_snail_essence/assets/product_*')), use_vision=False)
for p in sheet.photos:
    print(f'{p.path.split(\"/\")[-1]:<18} {p.width}x{p.height} white={p.bg_whiteness:.2f} -> {p.eligible_slots}')
"
```
Expected: both COSRX photos measured, with eligibility reflecting their real backgrounds. Record the output in the commit message — it tells the art director how much of the Shopee kit can be filled from real photos.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/studio/inventory.py backend/tests/studio/test_inventory.py
git commit -m "feat(studio): triage brand photos into slot eligibility with PIL metrics and vision tags"
```

---

### Task 7: Art direction and the prompt assembler

**Files:**
- Create: `backend/app/services/studio/direct.py`
- Create: `backend/app/services/studio/prompts.py`
- Test: `backend/tests/studio/test_direct.py`
- Test: `backend/tests/studio/test_prompts.py`

**Interfaces:**
- Consumes: `looks`, `platforms`, `slots`, `InventorySheet`, `CampaignInput`, `CampaignPlan`.
- Produces:
  - `direct.StyleSpine`: `look_key`, `lens`, `light`, `surface`, `grade`, `palette: list[str]`
  - `direct.WorkItem`: `slot_id`, `platform`, `kind`, `origin`, `source_photo: str | None`, `ratio`, `size`, `texts: list[tuple[str, str]]`
  - `direct.ShotPlan`: `index: int`, `role: str`, `scene: str`, `onscreen_text: str`, `vo_text: str`, `seconds: int` — one resolved storyboard beat; Task 9's `motion.render_shot` consumes exactly this type
  - `direct.Worksheet`: `route_id`, `spine`, `items: list[WorkItem]`, `shots: list[ShotPlan]`
  - `direct.build_worksheet(plan, campaign_input, sheet, route_id, platforms) -> Worksheet`
  - `prompts.build_image_prompt(scene, spine, texts, label_text, ratio, rule) -> str`
  - `prompts.build_video_prompt(shot, spine, vo_text, want_subtitles) -> str`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/studio/test_prompts.py
"""The prompt assembler is where the golden rule lives: every string that
appears in the frame must be named. Research showed text the model invents is
reliably garbled (LUNAÁIRA, EFFFECTIVE) while named text is reliably correct,
in Vietnamese as well as English."""
from app.services.studio.direct import StyleSpine
from app.services.studio.prompts import build_image_prompt, build_video_prompt

SPINE = StyleSpine(look_key="clinical_lab", lens="85mm macro",
                   light="cool diffused softbox", surface="wet travertine",
                   grade="neutral, low contrast", palette=["#FFFFFF", "#00A19A"])


def test_every_named_string_appears_with_an_exactness_instruction():
    p = build_image_prompt(
        scene="the product on {surface}, {light}", spine=SPINE,
        texts=[("headline", "PHỤC HỒI HÀNG RÀO DA"), ("badge", "GIẢM 25%")],
        label_text=["COSRX", "100ml"], ratio="1:1", rule=None,
    )
    assert 'reading exactly "PHỤC HỒI HÀNG RÀO DA"' in p
    assert 'reading exactly "GIẢM 25%"' in p
    assert "COSRX" in p                       # the real label, so none is invented
    assert "no invented brand name" in p.lower()
    assert "{" not in p                       # every placeholder resolved


def test_style_block_carries_the_whole_spine():
    p = build_image_prompt(scene="a scene on {surface} with {light}", spine=SPINE,
                           texts=[], label_text=[], ratio="1:1", rule=None)
    for fragment in ("85mm macro", "cool diffused softbox", "wet travertine", "neutral, low contrast"):
        assert fragment in p


def test_white_background_rule_reaches_the_prompt():
    p = build_image_prompt(scene="the product centred", spine=SPINE, texts=[],
                           label_text=[], ratio="1:1", rule="pure_white_bg")
    assert "pure white background" in p.lower()


def test_video_prompt_never_asks_seedance_for_vietnamese_text():
    """Seedance mangles Vietnamese captions ("Da khò cáng, xỉn mau?"). All legible
    text is baked into the Seedream keyframe instead, where it renders correctly
    and survives image-to-video intact."""
    p = build_video_prompt(shot_scene="the bottle on wet stone", spine=SPINE,
                           vo_text="Da khô căng, xỉn màu?")
    assert "subtitle" not in p.lower()
    assert "Da khô căng" not in p              # the line is spoken by TTS, not drawn
    assert "do not add any text" in p.lower()  # explicit: keep the keyframe's text only


def test_video_prompt_carries_camera_and_style_but_preserves_the_frame():
    p = build_video_prompt(shot_scene="the bottle on wet stone", spine=SPINE, vo_text="")
    assert "85mm macro" in p
    assert "wet travertine" in p
```

```python
# backend/tests/studio/test_direct.py
"""The worksheet is the studio's commercial judgement: where the shopper
inspects the product, use the brand's real photo; where the viewer is scrolling,
generate."""
from app.schemas.campaign import AssetOrigin, Platform
from app.services.studio.direct import build_worksheet


def test_shopee_main_reuses_a_real_photo_when_the_kho_has_one(sample_plan, sample_input, rich_sheet):
    ws = build_worksheet(sample_plan, sample_input, rich_sheet, route_id="A",
                         platforms=[Platform.SHOPEE])
    main = next(i for i in ws.items if i.slot_id == "shopee_main")
    assert main.origin is AssetOrigin.REUSE
    assert main.source_photo is not None


def test_shopee_main_falls_back_to_generate_when_the_kho_is_empty(sample_plan, sample_input, empty_sheet):
    ws = build_worksheet(sample_plan, sample_input, empty_sheet, route_id="A",
                         platforms=[Platform.SHOPEE])
    main = next(i for i in ws.items if i.slot_id == "shopee_main")
    assert main.origin is AssetOrigin.GENERATE


def test_tiktok_cover_is_always_generated(sample_plan, sample_input, rich_sheet):
    """No stock product photo is a vertical hook frame with a headline on it."""
    ws = build_worksheet(sample_plan, sample_input, rich_sheet, route_id="A",
                         platforms=[Platform.TIKTOK_SHOP])
    cover = next(i for i in ws.items if i.slot_id == "tiktok_cover")
    assert cover.origin is AssetOrigin.GENERATE


def test_routes_a_and_b_get_visually_distant_spines(sample_plan, sample_input, rich_sheet):
    a = build_worksheet(sample_plan, sample_input, rich_sheet, "A", [Platform.SHOPEE]).spine
    b = build_worksheet(sample_plan, sample_input, rich_sheet, "B", [Platform.SHOPEE]).spine
    assert a.look_key != b.look_key


def test_forbidden_claims_never_enter_rendered_text(sample_plan, sample_input, rich_sheet):
    ws = build_worksheet(sample_plan, sample_input, rich_sheet, "A", [Platform.SHOPEE])
    rendered = " ".join(t for item in ws.items for _, t in item.texts).lower()
    for claim in sample_input.product_brief.forbidden_claims:
        assert claim.lower() not in rendered
```

Add `backend/tests/studio/conftest.py` providing `sample_plan`, `sample_input`, `rich_sheet`, `empty_sheet`. Build `sample_input` from `sample_data/01_cosrx_snail_essence`, with `forbidden_claims=["trị mụn dứt điểm", "trắng da vĩnh viễn"]`. `rich_sheet` is an `InventorySheet` whose `by_slot` maps `shopee_main`, `shopee_sku` and `tiktok_product` to a fake path; `empty_sheet` has `photos=[]` and `by_slot={}`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/studio/test_prompts.py tests/studio/test_direct.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement `prompts.py`**

Six blocks, always in this order. Four are constant across a route, two vary per slot — that invariance *is* the consistency mechanism.

```python
IMAGE_PROMPT = """SUBJECT: The product from reference image 1, exactly unchanged — same shape, \
same cap, same label artwork and proportions. Do not restyle the product.

SCENE: {scene}

TEXT — render exactly these strings and nothing else:
{text_lines}

STYLE: {lens}, {light}, {grade}, palette {palette}

FORMAT: {ratio}, e-commerce ready{rule_clause}

NEGATIVE: no invented brand name, no invented tagline, no text beyond the list \
above, no watermark, no distorted or doubled lettering."""
```

`text_lines` is one `  · {role} text reading exactly "{value}"` line per entry, plus a final `  · product label reading exactly {label_text}` line whenever `label_text` is non-empty. When there is no text at all, emit `  · no text anywhere in the image` — an explicit instruction, never an empty section.

`build_video_prompt(shot_scene, spine, vo_text) -> str` follows the BytePlus formula *Subject + Action + Camera + Style + Constraints*, minus the audio block. It describes only **motion and camera**, because the frame's content and all of its text already exist in the keyframe:

```
SUBJECT: the product shown in the first frame, unchanged and in focus
ACTION + CAMERA: {shot_scene}, slow push-in, the product stays sharp and centred
STYLE: {lens}, {light}, {grade}
CONSTRAINTS: preserve the first frame's composition and any text already in it.
Do not add any text, caption, subtitle or watermark.
```

`vo_text` is accepted so callers can pass the line through to TTS, but **it is never written into the prompt** — Seedance would try to draw it and mangle the diacritics.

- [ ] **Step 4: Implement `direct.py`**

`build_worksheet`:
1. `spine` — `looks.pick_looks(...)[0 if route_id == "A" else 1]`, using `plan.performance_learning.keep` to detect a winning route.
2. For each requested platform, walk `KITS[platform].slots`. Choose the origin: if `slot.prefer_origin is REUSE` and `sheet.by_slot.get(slot.id)` is non-empty → `REUSE` with that photo. Else if `prefer_origin is REMIX` and any product photo exists → `REMIX`. Else `GENERATE`.
3. `texts` — pull from `plan.creative_routes[route].hook_idea`, `plan.positioning.key_selling_message`, and `campaign_input.product_brief.price_or_promotion`, keyed by the slot's `text_keys`. **Filter every candidate string against `forbidden_claims` (casefold substring match) and drop matches**; a claim that reaches the image is a takedown.
4. `shots` — expand `SHOT_TEMPLATES`, resolving `scene_from` against `campaign_input.market_signal.consumer_pain_point`, `product_brief.key_selling_points[0]`, and `price_or_promotion`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/studio/test_prompts.py tests/studio/test_direct.py -v`
Expected: PASS, 9 tests.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/studio/direct.py backend/app/services/studio/prompts.py \
        backend/tests/studio/test_direct.py backend/tests/studio/test_prompts.py \
        backend/tests/studio/conftest.py
git commit -m "feat(studio): add style spine, worksheet routing and six-block prompt assembler"
```

---

### Task 8: Image rendering

**Files:**
- Create: `backend/app/services/studio/render.py`
- Test: `backend/tests/studio/test_render.py`

**Interfaces:**
- Consumes: `ark`, `prompts`, `direct.WorkItem`, `direct.StyleSpine`.
- Produces:
  - `render_hero(item, spine, product_photo, label_text) -> RenderedImage`
  - `render_item(item, spine, product_photo, hero_path, label_text) -> RenderedImage`
  - `reuse_item(item) -> RenderedImage` — Pillow crop/resize of an existing photo, no API call
  - `RenderedImage` dataclass: `local_path`, `width`, `height`, `prompt`, `origin`, `texts`, `gen_seconds`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/studio/test_render.py
"""The hero is the style anchor: every later image passes BOTH the product photo
and the hero as references, which is what makes a kit look like one shoot."""
from app.schemas.campaign import AssetOrigin
from app.services.studio import render


def test_hero_uses_only_the_product_photo_as_reference(monkeypatch, tmp_path, work_item, spine, fake_photo):
    seen = {}
    monkeypatch.setattr(render.ark, "generate_image",
                        lambda prompt, size, refs=None: seen.update(refs=refs) or b"JPEGBYTES")
    render.render_hero(work_item, spine, fake_photo, label_text=["COSRX"])
    assert len(seen["refs"]) == 1


def test_other_items_pass_product_photo_and_hero_in_that_order(monkeypatch, work_item, spine, fake_photo, tmp_path):
    hero = tmp_path / "hero.jpg"
    hero.write_bytes(b"HERO")
    seen = {}
    monkeypatch.setattr(render.ark, "generate_image",
                        lambda prompt, size, refs=None: seen.update(refs=refs) or b"JPEGBYTES")
    monkeypatch.setattr(render.ark, "to_data_uri", lambda p: f"data:{p}")
    render.render_item(work_item, spine, fake_photo, str(hero), label_text=["COSRX"])
    assert len(seen["refs"]) == 2
    assert str(hero) in seen["refs"][1]     # hero is reference 2, the style anchor


def test_reuse_makes_no_api_call_and_produces_the_slot_aspect(monkeypatch, work_item_reuse):
    def forbidden(*a, **k):
        raise AssertionError("REUSE must not call the API")

    monkeypatch.setattr(render.ark, "generate_image", forbidden)
    out = render.reuse_item(work_item_reuse)
    assert out.origin is AssetOrigin.REUSE
    assert out.width == out.height          # the slot is 1:1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/studio/test_render.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement `render.py`**

`render_hero` — build the prompt with `prompts.build_image_prompt`, call `ark.generate_image` with `refs=[to_data_uri(product_photo)]`, write the bytes to `DATA_DIR/<campaign>/media/<slot_id>.jpg`, return `RenderedImage`.

`render_item` — identical, except `refs=[to_data_uri(product_photo), to_data_uri(hero_path)]`. **Order matters**: reference 1 is the product, reference 2 is the style. Never send `reference_images`.

`reuse_item` — open the source photo with Pillow, centre-crop to the slot's aspect ratio, resize to the slot's target size, save as JPEG quality 92. No network.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/studio/test_render.py -v`
Expected: PASS, 3 tests.

- [ ] **Step 5: Live check — hero anchoring is visible**

Generate a hero plus two kit images from a real COSRX photo and open all three. The product must be recognisably the same bottle, and the surface and light must match across all three. If they do not, the spine is not reaching the prompt — inspect `RenderedImage.prompt` before changing anything else.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/studio/render.py backend/tests/studio/test_render.py
git commit -m "feat(studio): render hero as style anchor and kit images with dual references"
```

---

### Task 9: Video and assembly

**Files:**
- Create: `backend/app/services/studio/motion.py`
- Create: `backend/app/services/studio/assemble.py`
- Test: `backend/tests/studio/test_motion.py`
- Test: `backend/tests/studio/test_assemble.py`

**Interfaces:**
- Consumes: `ark`, `prompts`, `direct.ShotPlan`.
- Produces:
  - `motion.render_shot(shot, keyframe_path, spine, seed=None) -> ShotResult` with `clip_path`, `last_frame_path | None`, `duration_sec`, `used_fallback`
  - `motion.render_voiceover(shots, voice_hint) -> VoiceoverResult` with `mp3_path`, `duration_sec`, `line_timings: list[tuple[float, float, str]]` — one Seed Audio call per shot line, concatenated; timings drive the subtitle strip
  - `assemble.concat(clip_paths, out_path) -> float` — stream-copy concat, returns duration
  - `assemble.ken_burns(image_path, out_path, seconds, size) -> str` — the fallback move
  - `assemble.render_subtitle_strip(text, size, out_png) -> str` — **Pillow** renders the Vietnamese caption to a transparent PNG; this build of ffmpeg has no `drawtext`, and Seedance cannot spell Vietnamese
  - `assemble.mux(master_path, vo_path, subtitle_pngs, timings, out_path) -> str` — overlays each subtitle PNG for its line's time window and muxes the voiceover
  - `assemble.cutdown(master_path, out_path, seconds) -> str`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/studio/test_motion.py
"""Video is the studio's slowest and least predictable step (134-543s measured for
one 5s clip). The pipeline must never hang on it."""
from app.services.studio import motion


def test_first_frame_input_forces_adaptive_ratio(monkeypatch, shot_plan, spine, tmp_path):
    kf = tmp_path / "k.jpg"; kf.write_bytes(b"K")
    captured = {}
    monkeypatch.setattr(motion.ark, "create_video_task",
                        lambda **kw: captured.update(kw) or "cgt-1")
    monkeypatch.setattr(motion.ark, "wait_video_task",
                        lambda tid: motion.ark.VideoResult(b"MP4", None, 12.0))
    motion.render_shot(shot_plan, str(kf), spine)
    assert captured["first_frame"] is not None
    assert captured.get("refs") in (None, [])   # modes are mutually exclusive


def test_deadline_overrun_falls_back_to_ken_burns(monkeypatch, shot_plan, spine, tmp_path):
    kf = tmp_path / "k.jpg"; kf.write_bytes(b"K")
    monkeypatch.setattr(motion.ark, "create_video_task", lambda **kw: "cgt-1")

    def too_slow(tid):
        raise TimeoutError("shot deadline exceeded")

    monkeypatch.setattr(motion.ark, "wait_video_task", too_slow)
    monkeypatch.setattr(motion.assemble, "ken_burns",
                        lambda img, out, seconds, size: str(out))
    result = motion.render_shot(shot_plan, str(kf), spine)
    assert result.used_fallback is True
    assert result.clip_path                     # the shot still exists
```

```python
# backend/tests/studio/test_assemble.py
"""ffmpeg checks run against real files: every Seedance clip shares 720x1280 /
24fps / h264 / aac, so concat can stream-copy. This build has NO drawtext filter."""
import subprocess

from app.services.studio import assemble


def _probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def test_concat_sums_durations(tmp_path, two_test_clips):
    out = tmp_path / "master.mp4"
    duration = assemble.concat(two_test_clips, out)
    assert out.exists()
    assert abs(duration - sum(_probe_duration(c) for c in two_test_clips)) < 0.3


def test_ken_burns_produces_a_clip_of_the_requested_length(tmp_path, still_image):
    out = tmp_path / "kb.mp4"
    assemble.ken_burns(still_image, out, seconds=5, size=(720, 1280))
    assert abs(_probe_duration(out) - 5.0) < 0.3


def test_cutdown_is_shorter_than_the_master(tmp_path, two_test_clips):
    master = tmp_path / "m.mp4"
    assemble.concat(two_test_clips, master)
    out = tmp_path / "cut.mp4"
    assemble.cutdown(master, out, seconds=3)
    assert _probe_duration(out) < _probe_duration(master)
```

Add fixtures `two_test_clips` and `still_image` to `conftest.py`, generating them with `ffmpeg -f lavfi -i testsrc=size=720x1280:duration=N -f lavfi -i sine -c:v libx264 -c:a aac`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/studio/test_motion.py tests/studio/test_assemble.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement `motion.py` and `assemble.py`**

`render_shot` — build the prompt, call `create_video_task(first_frame=..., ratio="adaptive", duration=shot.seconds, seed=seed, return_last_frame=True)`, then `wait_video_task`. Catch `TimeoutError` and `ArkError`, call `assemble.ken_burns` on the keyframe, and return with `used_fallback=True`. **A shot never disappears** — the video keeps its four-beat structure and its length whatever the API does.

`concat` — write a concat list file and run `ffmpeg -f concat -safe 0 -i list.txt -c copy out.mp4`. If that fails (mismatched parameters), fall back to the `concat` filter with `-c:v libx264 -preset veryfast -crf 20 -c:a aac`.

`ken_burns` — `ffmpeg -loop 1 -i img -vf "scale=...,zoompan=z='min(zoom+0.0015,1.12)':d=...,format=yuv420p" -t N -r 24 -c:v libx264 -pix_fmt yuv420p`, plus `-f lavfi -i anullsrc -c:a aac -shortest` so the audio track matches the real clips and concat can stream-copy.

`render_subtitle_strip` — Pillow only. Load a Vietnamese-capable font (`Inter` or `Be Vietnam Pro`; verify the glyphs by rendering `ẮẶỄỘỰ` and checking no `.notdef` boxes appear), draw the caption centred on a transparent RGBA canvas the width of the video, with a soft dark shadow for legibility, and keep it clear of the bottom 20% reserved for platform UI. Return the PNG path.

`mux` — one `overlay` filter per subtitle PNG gated by `enable='between(t,start,end)'`, plus `-i vo.mp3 -map 0:v -map 1:a -c:v libx264 -crf 20 -c:a aac`.

**Do not use `drawtext`** anywhere: this ffmpeg build was compiled without freetype and the filter does not exist. Pillow does all text rendering.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/studio/test_motion.py tests/studio/test_assemble.py -v`
Expected: PASS, 5 tests.

- [ ] **Step 5: Confirm the top-level parameter path against Seedance 2.5**

```bash
cd backend && python -c "
from app.services.studio import ark
tid = ark.create_video_task('a white bottle on wet stone, slow push in',
                            duration=5, ratio='9:16', resolution='1080p')
print('accepted:', tid)
"
```
If this raises `ArkError`, set `STUDIO_VIDEO_USE_TOPLEVEL_PARAMS=false` in `backend/.env` and re-run — the inline `--flag` form is verified working. Record which path was taken in the commit message; Task 11 needs to know whether `generate_audio` and `return_last_frame` are available.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/studio/motion.py backend/app/services/studio/assemble.py \
        backend/tests/studio/test_motion.py backend/tests/studio/test_assemble.py
git commit -m "feat(studio): render shots with Ken Burns fallback and assemble masters with ffmpeg"
```

---

### Task 10: Visual QA gate

**Files:**
- Create: `backend/app/services/studio/qa_visual.py`
- Test: `backend/tests/studio/test_qa_visual.py`

**Interfaces:**
- Consumes: `ark.describe_image`, `studio_settings`.
- Produces:
  - `VisualVerdict` dataclass: `passed: bool`, `missing_text: list[str]`, `unexpected_brandlike: list[str]`, `forbidden_hits: list[str]`, `transcript: list[str]`
  - `inspect_image(path, expected_texts, label_text, forbidden_claims) -> VisualVerdict`
  - `corrective_hint(verdict, attempt) -> str` — the instruction appended to the prompt on retry

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/studio/test_qa_visual.py
"""The model transcribes; Python judges. Asked to render a verdict itself, the
vision model failed a perfectly correct image because it counted the product's
own bottle label as unexpected text."""
from app.services.studio import qa_visual


def _fake_transcript(strings):
    import json
    return lambda image_bytes, prompt, max_tokens=600: json.dumps(strings)


def test_exact_match_passes(monkeypatch, tmp_path, jpeg_2048):
    monkeypatch.setattr(qa_visual.ark, "describe_image",
                        _fake_transcript(["PHỤC HỒI HÀNG RÀO DA", "COSRX", "100ml"]))
    v = qa_visual.inspect_image(jpeg_2048, expected_texts=["PHỤC HỒI HÀNG RÀO DA"],
                                label_text=["COSRX", "100ml"], forbidden_claims=[])
    assert v.passed and not v.missing_text


def test_wrong_diacritic_is_reported_missing(monkeypatch, jpeg_2048):
    monkeypatch.setattr(qa_visual.ark, "describe_image",
                        _fake_transcript(["PHUC HOI HANG RAO DA"]))
    v = qa_visual.inspect_image(jpeg_2048, expected_texts=["PHỤC HỒI HÀNG RÀO DA"],
                                label_text=[], forbidden_claims=[])
    assert not v.passed
    assert "PHỤC HỒI HÀNG RÀO DA" in v.missing_text


def test_invented_brand_name_is_flagged(monkeypatch, jpeg_2048):
    monkeypatch.setattr(qa_visual.ark, "describe_image",
                        _fake_transcript(["RESTORE YOUR SKIN BARRIER", "LUNAÁIRA",
                                          "CLEAN. GENTLE. EFFFECTIVE."]))
    v = qa_visual.inspect_image(jpeg_2048, expected_texts=["RESTORE YOUR SKIN BARRIER"],
                                label_text=["COSRX"], forbidden_claims=[])
    assert not v.passed
    assert "LUNAÁIRA" in v.unexpected_brandlike


def test_product_label_text_is_never_treated_as_unexpected(monkeypatch, jpeg_2048):
    monkeypatch.setattr(qa_visual.ark, "describe_image",
                        _fake_transcript(["COSRX", "ADVANCED SNAIL 96", "100ml"]))
    v = qa_visual.inspect_image(jpeg_2048, expected_texts=[],
                                label_text=["COSRX", "ADVANCED SNAIL 96", "100ml"],
                                forbidden_claims=[])
    assert v.passed


def test_forbidden_claim_in_the_image_fails_hard(monkeypatch, jpeg_2048):
    monkeypatch.setattr(qa_visual.ark, "describe_image",
                        _fake_transcript(["TRỊ MỤN DỨT ĐIỂM"]))
    v = qa_visual.inspect_image(jpeg_2048, expected_texts=[], label_text=[],
                                forbidden_claims=["trị mụn dứt điểm"])
    assert not v.passed
    assert v.forbidden_hits


def test_image_is_tiled_at_native_resolution_not_downscaled(monkeypatch, jpeg_2048):
    """Downscaling a 2048px image to 1024 made the model silently correct
    EFFFECTIVE to EFFECTIVE, destroying the signal the gate exists to find."""
    sizes = []
    def spy(image_bytes, prompt, max_tokens=600):
        from PIL import Image; import io
        sizes.append(Image.open(io.BytesIO(image_bytes)).size)
        return "[]"
    monkeypatch.setattr(qa_visual.ark, "describe_image", spy)
    qa_visual.inspect_image(jpeg_2048, [], [], [])
    assert len(sizes) == 4                       # four quadrants
    assert all(s == (1024, 1024) for s in sizes) # native crops, not resizes
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/studio/test_qa_visual.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement `qa_visual.py`**

`inspect_image` — open with Pillow, crop into four `QA_TILE_PX` quadrants at native resolution (pad the source if smaller than `2 * QA_TILE_PX`). Call `ark.describe_image` on each quadrant concurrently (`VISION_CONCURRENCY`) with:

> "Transcribe every piece of text visible in this image, character by character, exactly as rendered. Preserve misspellings, doubled letters and wrong diacritics. Do not correct anything. Return a JSON array of strings and nothing else."

Union the four transcripts. Then judge **in Python**:
- `missing_text` — every expected string with no NFC-normalised, casefolded, whitespace-collapsed exact match in the transcript.
- `unexpected_brandlike` — transcript strings that match neither an expected string nor a `label_text` entry, and are longer than three characters and mostly uppercase or title case. Ignore obvious units and numerals.
- `forbidden_hits` — any forbidden claim appearing as a substring of any transcript entry, casefolded.
- `passed` — all three lists empty.

`corrective_hint` — attempt 1 on missing text: `"Reduce the amount of text. Render only: <the strings>. Make them larger and unobstructed."` Attempt 2: `"Render exactly one text string: <first>. No other text anywhere."` For `unexpected_brandlike`: `"Do not render the words <hits>. No text on background surfaces or packaging other than the product's own label."`

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/studio/test_qa_visual.py -v`
Expected: PASS, 6 tests.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/studio/qa_visual.py backend/tests/studio/test_qa_visual.py
git commit -m "feat(studio): add quadrant-tiled visual QA gate with code-side judgement"
```

---

### Task 11: Pipeline, agent swap and API

**Files:**
- Create: `backend/app/services/studio/pipeline.py`
- Create: `backend/app/api/v1/endpoints/studio.py`
- Modify: `backend/app/api/v1/api.py` (register the router)
- Modify: `backend/app/services/campaign/gen_assets_agent.py` (call the studio)
- Test: `backend/tests/studio/test_pipeline.py`
- Test: `backend/tests/studio/test_studio_api.py`

**Interfaces:**
- Consumes: every module above.
- Produces:
  - `pipeline.run_studio(plan, campaign_input, platforms=None, on_event=None) -> AssetBundle`
  - `pipeline.build_nodes(...) -> list[Node]` — exposed so tests can assert graph shape without running it
  - `GET /api/studio/{campaign_id}/events` — SSE stream of graph events
  - `GET /api/studio/{campaign_id}/pack` — the finished `AssetBundle`
  - `POST /api/studio/run` — body `CampaignInput`, starts a run, returns `{campaign_id}` immediately

**SSE event contract (Task 13's frontend depends on this exactly):**

```jsonc
{"event": "node", "node_id": "shopee_main", "kind": "image",
 "state": "pending|running|done|retry|degraded|failed",
 "elapsed_sec": 42.1,
 "payload": {"url": "/media/cosrx/shopee_main.jpg", "origin": "reuse", "qa": "PASS"}}
{"event": "graph", "nodes": [{"id": "...", "kind": "...", "deps": ["..."]}]}   // sent once, first
{"event": "done", "campaign_id": "cosrx-1111"}
{"event": "error", "node_id": "tiktok_shot2", "message": "..."}
```

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/studio/test_pipeline.py
"""The graph shape carries the design decisions. These assertions are the
design, written down: reuse must not wait on the hero, and every generated
image must be anchored to it."""
from app.schemas.campaign import Platform
from app.services.studio.pipeline import build_nodes


def test_reuse_nodes_do_not_depend_on_the_hero(sample_plan, sample_input, rich_sheet):
    nodes = {n.id: n for n in build_nodes(sample_plan, sample_input, rich_sheet,
                                          route_id="A", platforms=[Platform.SHOPEE])}
    assert "hero_A" not in nodes["shopee_main"].deps


def test_generated_images_depend_on_the_hero(sample_plan, sample_input, empty_sheet):
    nodes = {n.id: n for n in build_nodes(sample_plan, sample_input, empty_sheet,
                                          route_id="A", platforms=[Platform.SHOPEE])}
    assert "hero_A" in nodes["shopee_main"].deps


def test_each_clip_depends_only_on_its_own_keyframe(sample_plan, sample_input, rich_sheet):
    nodes = {n.id: n for n in build_nodes(sample_plan, sample_input, rich_sheet,
                                          "A", [Platform.TIKTOK_SHOP])}
    assert nodes["clip_A_0"].deps == ["keyframe_A_0"]


def test_master_waits_for_every_clip(sample_plan, sample_input, rich_sheet):
    nodes = {n.id: n for n in build_nodes(sample_plan, sample_input, rich_sheet,
                                          "A", [Platform.TIKTOK_SHOP])}
    assert set(nodes["master_A_tiktok"].deps) == {f"clip_A_{i}" for i in range(4)}


def test_video_nodes_are_in_the_video_concurrency_group(sample_plan, sample_input, rich_sheet):
    nodes = {n.id: n for n in build_nodes(sample_plan, sample_input, rich_sheet,
                                          "A", [Platform.TIKTOK_SHOP])}
    assert nodes["clip_A_0"].concurrency_group == "video"


def test_bundle_meets_the_qa_agent_minimums(monkeypatch, sample_plan, sample_input):
    """qa_review_agent requires >=4 images, >=1 video, 15-30s, 9:16."""
    from app.services.studio import pipeline
    bundle = pipeline.run_studio(sample_plan, sample_input,
                                 platforms=[Platform.TIKTOK_SHOP, Platform.SHOPEE],
                                 on_event=None)   # fixtures stub ark
    assert len(bundle.images) >= 4
    assert len(bundle.videos) >= 1
    v = bundle.videos[0]
    assert 15 <= v.duration_sec <= 30
    assert v.aspect_ratio == "9:16"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/studio/test_pipeline.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement `pipeline.py`**

`build_nodes` assembles, per route:
- `inventory` (no deps) → `worksheet` (deps `inventory`)
- `hero_{route}` (deps `worksheet`, group `image`)
- one node per `WorkItem`: `REUSE` items depend only on `worksheet`; `REMIX` and `GENERATE` items depend on `hero_{route}`. Each runs render → `qa_visual.inspect_image` → up to `QA_MAX_ATTEMPTS` re-renders with `corrective_hint` appended, keeping the same `seed`.
- `keyframe_{route}_{i}` (deps `hero_{route}`, group `image`)
- `clip_{route}_{i}` (deps `keyframe_{route}_{i}`, group `video`)
- `master_{route}_{platform}` (deps every clip of that platform)
- `cutdown_*` (deps master)

`run_studio` calls `graph.run_graph`, then maps results into an `AssetBundle`. Set `listing_copy` from `plan` where available; leave the existing mock copy as the fallback so the bundle always validates.

Then replace the mock body of `gen_assets_agent.generate_assets`: when `campaign_input` is `None` **keep returning the mock bundle** (teammates' tests depend on it); otherwise delegate to `run_studio`. Document this branch — it is what lets the two agents develop independently.

- [ ] **Step 4: Implement `studio.py` endpoints**

Follow the existing `StandardResponse` envelope for `/pack`. For `/events` return `fastapi.responses.StreamingResponse` with `media_type="text/event-stream"`, reading from a per-campaign `queue.Queue` that `run_studio`'s `on_event` writes to. Send the `graph` event first so the frontend can lay out nodes before any of them start. Every endpoint gets a docstring stating who consumes it — this module is the seam teammates integrate against.

- [ ] **Step 5: Run the whole suite**

Run: `cd backend && python -m pytest tests -q`
Expected: PASS, including `test_campaigns_api.py`.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/studio/pipeline.py backend/app/api/v1/endpoints/studio.py \
        backend/app/api/v1/api.py backend/app/services/campaign/gen_assets_agent.py \
        backend/tests/studio/test_pipeline.py backend/tests/studio/test_studio_api.py
git commit -m "feat(studio): wire the node graph, expose SSE endpoints and swap the mock agent"
```

---

### Task 12: Frontend shell and design tokens

**Files:**
- Modify: `frontend/src/app/globals.css` (add the hackathon token block)
- Create: `frontend/src/types/studio.ts`
- Create: `frontend/src/lib/studio-events.ts`
- Create: `frontend/src/app/studio/page.tsx`
- Create: `frontend/src/components/studio/BriefPanel.tsx`

**Interfaces:**
- Consumes: the SSE contract from Task 11.
- Produces: TS types `NodeState`, `StudioNode`, `StudioEvent`, `AssetPack`; hook `useStudioStream(campaignId)` returning `{nodes, assets, status}`.

**Design direction — match the hackathon identity.** Reference: `assets/style-guide.md` and the twelve screenshots in `assets/reference/screenshots/` of the BHN working directory. The visual language, taken from the live event site:

- Background `#001708` (near-black forest green); cards `#00220e`; muted surface `#012a14`
- Foreground `#f4faf5`; muted text `#a1c1a7`; borders `rgba(107,239,117,.18)`
- Primary `#35ea52`, accent lime `#7ef962`, gold `#fcbb00` for sponsor/premium, CTA coral `#fe6e00`
- Display font **Space Grotesk** (500/600/700), body **Inter** (400/500/600), monospace for numerals and timings
- Radius `.75rem` base, `1rem` large; glow `0 0 40px rgba(53,234,82,.5)`
- Section pattern: a small uppercase lime kicker with wide letter-spacing, then a very large two-line Space Grotesk headline mixing white and lime, then one muted sub-line
- Cards: dark fill, faint lime border, square rounded icon tile with a lime-tinted background, lime dot bullets
- Very generous vertical rhythm; a faint 1px grid overlay `linear-gradient(#ffffff0a 1px, transparent 1px)`

Adapt density for a working tool — the event site is a marketing page — but keep palette, type, radius, glow and the kicker/headline pattern exactly.

- [ ] **Step 1: Add the token block to `globals.css`**

```css
:root {
  --bg: #001708;          --fg: #f4faf5;
  --card: #00220e;        --muted: #012a14;      --muted-fg: #a1c1a7;
  --border: rgba(107,239,117,.18);
  --primary: #35ea52;     --primary-glow: #90fd77;
  --accent: #7ef962;      --gold: #fcbb00;       --cta: #fe6e00;
  --danger: #fd393f;
  --font-display: "Space Grotesk", ui-sans-serif, system-ui, sans-serif;
  --font-body: "Inter", ui-sans-serif, system-ui, sans-serif;
  --radius: .75rem;
  --glow: 0 0 40px rgba(53,234,82,.5);
}
```

Load both fonts via `next/font/google` in `layout.tsx`.

- [ ] **Step 2: Write `types/studio.ts` mirroring the SSE contract**

Mirror the Task 11 contract exactly: `NodeState = "pending" | "running" | "done" | "retry" | "degraded" | "failed"`, plus `StudioNode`, `StudioEvent`, `ImageAsset`, `VideoAsset`, `AssetPack`.

- [ ] **Step 3: Write `lib/studio-events.ts`**

`useStudioStream(campaignId)` opens an `EventSource` on `/api/studio/{id}/events`, keeps a `Map<string, StudioNode>` in state, applies each `node` event, and closes on `done`. Reconnect once on error, then surface the failure — do not retry silently.

- [ ] **Step 4: Build the studio page shell**

Left: `BriefPanel` — brand picker over the six `sample_data` brands, platform toggles (TikTok Shop / Shopee), and a Run button using the coral CTA. Right: a placeholder for the graph canvas that Task 13 fills. Header follows the event site: logo left, title centre, `EN/VI` pill and CTA right.

- [ ] **Step 5: Verify it renders**

Run: `cd frontend && npm install && npm run dev`, open `http://localhost:3000/studio`.
Expected: dark forest background, lime kicker, large Space Grotesk headline, brand picker populated. Compare side by side with `assets/reference/screenshots/06-thu-thach-3-tracks.jpg` — the type scale, spacing and card treatment should read as the same family.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/app/globals.css frontend/src/app/layout.tsx frontend/src/types/studio.ts \
        frontend/src/lib/studio-events.ts frontend/src/app/studio frontend/src/components/studio
git commit -m "feat(ui): add studio shell with hackathon design tokens and SSE client"
```

---

### Task 13: Live graph canvas and asset gallery

**Files:**
- Create: `frontend/src/components/studio/GraphCanvas.tsx`
- Create: `frontend/src/components/studio/NodeCard.tsx`
- Create: `frontend/src/components/studio/KitTabs.tsx`
- Create: `frontend/src/components/studio/AssetGrid.tsx`
- Modify: `frontend/src/app/studio/page.tsx`

**Interfaces:**
- Consumes: `useStudioStream`, `StudioNode`, `AssetPack`.
- Produces: the screen the judges watch.

- [ ] **Step 1: Install React Flow**

```bash
cd frontend && npm install @xyflow/react
```

- [ ] **Step 2: Build `NodeCard`**

A custom React Flow node. Node kind sets the icon (image / video / inspect / compose / plan). State sets the treatment:

| State | Treatment |
|---|---|
| `pending` | muted border, 40% opacity |
| `running` | lime border with `--glow`, slow pulse, elapsed seconds in mono |
| `done` | solid lime border; **thumbnail fills the card** |
| `retry` | gold border, attempt counter |
| `degraded` | gold border, "Ken Burns" tag |
| `failed` | `--danger` border |

An `origin` badge on image nodes — `REUSE` in gold, `REMIX` and `GENERATE` in lime — so the reuse-versus-generate decision is visible on screen. That single badge is the clearest expression of the studio's commercial judgement; do not hide it.

Respect `prefers-reduced-motion`: replace the pulse with a static border.

- [ ] **Step 3: Build `GraphCanvas`**

Lay nodes out in dependency layers left to right using the `graph` event's `deps`. Animate edges only while the downstream node is `running`. Fit view on mount; do not re-fit on every update, which would yank the canvas while a judge is looking at it.

- [ ] **Step 4: Build `KitTabs` and `AssetGrid`**

Tabs per platform. Each grid item shows the asset, its slot name, and its origin badge. Clicking opens the existing shadcn `Dialog` at full size with the prompt and QA notes beneath — this is how a judge checks that the system did what it claims.

- [ ] **Step 5: Verify against a real run**

Start the backend, run a campaign from the UI, and watch: Shopee reuse nodes should turn `done` within seconds while `hero_A` is still `running`; TikTok clip nodes should stay `running` for minutes. If every node lights up in lockstep, the graph is being executed as stages and Task 11's dependency wiring is wrong.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/studio frontend/src/app/studio/page.tsx frontend/package.json
git commit -m "feat(ui): add live graph canvas, kit tabs and asset gallery"
```

---

### Task 14: End-to-end run and packaging

**Files:**
- Create: `backend/app/services/studio/pack.py`
- Create: `backend/tests/studio/test_e2e_smoke.py`
- Create: `README-studio.md` (repo root)

- [ ] **Step 1: Write the packaging test**

```python
# backend/tests/studio/test_e2e_smoke.py
"""Names in the zip are the deliverable a seller drags onto a marketplace.
They must say what each file is without opening it."""
import zipfile

from app.services.studio.pack import build_zip


def test_zip_is_grouped_by_platform_with_descriptive_names(sample_bundle, tmp_path):
    out = build_zip(sample_bundle, tmp_path / "kit.zip")
    names = zipfile.ZipFile(out).namelist()
    assert any(n.startswith("tiktok_shop/") for n in names)
    assert any(n.startswith("shopee/") for n in names)
    assert any("9x16" in n and n.endswith(".mp4") for n in names)
    assert any("main_1x1" in n for n in names)
    assert "MANIFEST.md" in names
```

- [ ] **Step 2: Implement `pack.py`**

`build_zip` writes `<platform>/<slot>_<ratio>.<ext>` for every asset plus a `MANIFEST.md` table listing each file with its slot, origin, source photo, prompt and QA verdict. The manifest is the model-usage explanation BP-01's submission checklist asks for, generated rather than written by hand.

- [ ] **Step 3: Full live run**

```bash
cd backend && ARK_API_KEY=$ARK_API_KEY python -m app.services.studio.pipeline \
  --brand sample_data/01_cosrx_snail_essence --platforms tiktok_shop,shopee --route A
```

Expected, and check each: at least 4 images; at least one 9:16 video between 15 and 30 seconds; product recognisably identical across every asset; no `AI generated` watermark anywhere; no garbled text; Shopee's main image on a genuinely white background.

- [ ] **Step 4: Write `README-studio.md`**

Cover: what the studio does, the graph diagram, the REUSE/REMIX/GENERATE rule and why it exists, which BytePlus model does what and why that model was chosen (BP-01 requires this explanation), every `STUDIO_*` environment variable, and how to run it. Embed the graph as Mermaid so it renders on GitHub — the plan's own diagram is the architecture graph the submission asks for.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/studio/pack.py backend/tests/studio/test_e2e_smoke.py README-studio.md
git commit -m "feat(studio): package platform kits as zip with generated manifest"
```

---

## Risks

| Risk | Mitigation | Owner |
|---|---|---|
| A 5s clip takes 543s | `VIDEO_SHOT_DEADLINE_SEC` then Ken Burns; the video always completes | Task 9 |
| Venue Wi-Fi drops mid-render | retry with backoff; `task_id` persisted before return | Task 3 |
| Seedance 2.5 rejects top-level params | `VIDEO_USE_TOPLEVEL_PARAMS=false` falls back to the verified inline form | Task 9 |
| Vision QA too slow to run on every asset | four native-resolution tiles in parallel; gate hero and text-bearing slots first | Task 10 |
| The kho has only two photos per brand | REUSE degrades to GENERATE per slot; the pipeline never blocks on it | Task 7 |
| Teammates change `campaign.py` underneath us | additive fields only; `test_schema_compat.py` fails loudly if the seam moves | Task 2 |
| QA loop regenerates everything, three times | targeted per-asset retry inside the node, not a whole-bundle re-run | Task 11 |
