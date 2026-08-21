# QA Checklist — Commerce Campaign Launch Copilot (BP-01)

This is a **fully self-contained module** — everything it needs lives in this
`QA_checklist/` folder. It does not import from, or depend on, `backend/` or
`frontend/`, and can be copied elsewhere and still run as-is.

**Each testcase's `user_input.json` is the only file the agents read as data.**
The campaign plan and asset bundle are always produced by running the real
`GenPlanAgent`/`GenAssetsAgent` logic against that input — never by loading
a pre-baked "output" fixture. `planning_output.json` and
`assets_model_output.json` inside a testcase folder are kept only as
**reference examples** for documentation (what a plan/asset bundle looks
like); they are not read by `QA_checklist.py` at runtime.

**No fake remote URLs.** Any image referenced from `user_input.json`
(`brand_kit.logo_url`, `brand_kit.product_photo_urls`) is a real local file
path pointing into that testcase's `brand_assets/` folder — real images
generated once via `generate_testcase_assets.py` (which calls
`byteplus_ark.py` / Seedream 5.0 Pro), not a placeholder `https://...` URL.

```
QA_checklist/                       # <- run everything from inside here
├── QA_checklist.py                 # prompts + agent flow + QA rules engine + CLI
├── byteplus_ark.py                 # real BytePlus ModelArk client (Seedream 5.0 Pro / Seedance 2.5 / Seed 2.1)
├── generate_testcase_assets.py     # one-off script: generates a testcase's brand_assets/ via byteplus_ark.py
├── .env                            # ARK_API_KEY (gitignored, only needed for --live)
├── .env.example
├── README.md                       # this file
└── testcases/
    └── bp01_fnb_sparkling_tea/     # one self-contained testcase = one scenario
        ├── user_input.json            # CampaignInput sample — the ONLY input file read by the agents
        ├── planning_output.json       # reference example of a CampaignPlan (docs only, not loaded)
        ├── assets_model_output.json   # reference example of an AssetBundle (docs only, not loaded)
        ├── brand_assets/               # real, committed brand logo/product photos (generated once)
        │   ├── brand_logo.jpg
        │   ├── product_photo_studio.jpg
        │   └── product_photo_lifestyle.jpg
        └── ark_out/                    # disposable per-run output (gitignored, regenerated every run)
            ├── product_hero_image.jpg
            ├── sku_detail_image.jpg
            ├── campaign_collection_image.jpg
            ├── marketplace_thumbnail.jpg
            └── route_A.mp4
```

Adding a new testcase = add a new folder under `testcases/` with its own
`user_input.json` (and, if it needs brand-kit photos, register its prompts
in `generate_testcase_assets.py` and run that script once).

## 1. How to run it

```bash
cd QA_checklist

# DEFAULT: real API calls (Seed 2.1 / Seedream 5.0 Pro / Seedance 2.5) via
# byteplus_ark.py, running the default testcase (bp01_fnb_sparkling_tea).
# Requires ARK_API_KEY (put it in QA_checklist/.env — see .env.example).
python QA_checklist.py

# Run a specific testcase folder (still --live by default)
python QA_checklist.py --testcase bp01_fnb_sparkling_tea

# Built-in generator instead — no API key needed, synthesizes local
# placeholder image/video files instead of calling the paid API.
python QA_checklist.py --mock
python QA_checklist.py --mock --testcase bp01_fnb_sparkling_tea

# Deliberately inject a compliance drift on iteration 1 (drops SKU detail image,
# distorts video duration/aspect, injects a forbidden claim / drops a required
# claim) to exercise the unhappy-path and watch the retry loop self-correct.
python QA_checklist.py --inject-drift
python QA_checklist.py --mock --inject-drift

# Bypass testcases/ entirely and point at an arbitrary CampaignInput file
# (output then goes to REPO_ROOT/ark_out/<campaign_id>/ instead of a testcase folder)
python QA_checklist.py --input path/to/other_user_input.json

# One-off: (re)generate real brand-kit reference photos for a testcase
python generate_testcase_assets.py bp01_fnb_sparkling_tea
```

You can also run it from the repo root without `cd`-ing in:
`python QA_checklist/QA_checklist.py`. All paths (testcases, .env,
generated output) are always resolved relative to this file's own location,
regardless of your current working directory.

Exit code is `0` when the final QA result passes, `1` when it fails after
exhausting `MAX_ITERATIONS`, or when an unknown `--testcase` name is given —
usable in CI.

## 2. How it works

Everything is in `QA_checklist.py`, organized top-to-bottom into 4 sections:

1. **Data contracts** — Pydantic models mirroring BP-01's "Expected Output"
   (`CampaignInput`, `CampaignPlan`, `AssetBundle`, `QAResult`, ...).
2. **Prompts** — the LLM prompt templates for positioning (`PLANNING_PROMPT_TEMPLATE`)
   and commerce copy (`COPY_PROMPT_TEMPLATE`), plus image/video prompt templates
   (`IMAGE_PROMPT_TEMPLATES`, `VIDEO_PROMPT_TEMPLATE`) handed to Seedream/Seedance.
3. **Agent flow** — `GenPlanAgent` → `GenAssetsAgent` → `review()`, orchestrated
   by `run_campaign()`.
4. **CLI entry point** — `main()`, runnable via `python QA_checklist.py`.

```
CampaignInput (testcases/<name>/user_input.json — the only data file read)
     │
     ▼
GenPlanAgent.generate(...)      → CampaignPlan
     │   live      : Seed 2.1 call for positioning, reasoning over the real
     │                product_brief/audience_brief/market_signal fields
     │   built-in  : deterministic rule-based generator (_generate_builtin)
     │                that still reasons over those same input fields —
     │                no fixture file is read
     ▼
GenAssetsAgent.generate(...)    → AssetBundle
     │   live      : Seed 2.1 (copy) + Seedream 5.0 Pro (images) + Seedance 2.5 (video),
     │                real network calls, real generated files
     │   built-in  : rule-based copy generator that weaves in required_claims and
     │                respects forbidden_claims, + local placeholder image/video
     │                files synthesized to disk (ark_out/<campaign_id>/) — still a
     │                real generation step, not a fixture replay
     ▼
review(input, plan, assets)     → QAResult
     │
     ├─ passed = True  → stop, campaign ready
     └─ passed = False → append issue remediations as extra_context,
                          regenerate plan+assets from scratch, re-review
                          (up to MAX_ITERATIONS = 3)
```

`review()` never raises — it always returns a `QAResult` with `passed: bool`
and a list of `QAIssue` (`rule_id`, `severity`, `message`, `field`,
`remediation`). **`passed` is `True` only when there are zero `BLOCKER`
issues.** `WARNING` issues are surfaced but do not block. Each issue carries
a `remediation` string — this is the "additional context" fed back into
`GenPlanAgent`/`GenAssetsAgent` on the next iteration. Because both agents
always regenerate from the actual `CampaignInput` (never replay a static
fixture), a drift injected only on iteration 1 (`--inject-drift`) is
naturally absent on iteration 2+, demonstrating a genuine detect-and-
self-correct loop rather than a canned pass/fail toggle.

## 3. Checklist buckets (mirrors draft_idea.txt)

### Bucket A — Internal system criteria (`_check_internal_*`)
Structural / spec completeness checks against BP-01's "Expected Output" schema.

| Rule ID | Severity | Checks |
|---|---|---|
| `PLAN.ANGLE_EMPTY` | BLOCKER | `positioning.main_campaign_angle` is non-empty |
| `PLAN.ROUTE_COUNT` | BLOCKER | `creative_routes` has ≥ 2 entries (A/B testing requirement) |
| `PLAN.ROUTE_ID_DUP` | BLOCKER | `route_id` values are unique |
| `PLAN.AB_ROUTE_MISMATCH` | BLOCKER | `ab_test_plan.route_a`/`route_b` reference real route IDs |
| `PLAN.AB_NO_METRICS` | WARNING | `ab_test_plan.success_metrics` is non-empty |
| `ASSETS.IMAGE_COUNT` | BLOCKER | ≥ 4 images total |
| `ASSETS.MISSING_IMAGE_KIND` | BLOCKER | All 4 required kinds present: `product_hero_image`, `sku_detail_image`, `campaign_collection_image`, `marketplace_thumbnail` |
| `ASSETS.VIDEO_COUNT` | BLOCKER | ≥ 1 video asset |
| `ASSETS.VIDEO_DURATION` | WARNING | Duration within 15–30s |
| `ASSETS.VIDEO_ASPECT` | WARNING | Aspect ratio == `9:16` |
| `ASSETS.COPY_INCOMPLETE` | BLOCKER | `product_title` and `product_description` non-empty |
| `ASSETS.COPY_NO_BULLETS` | WARNING | `listing_bullet_points` non-empty |

### Bucket B — Market research criteria (`_check_market_*`)
Ensures the campaign angle is backed by cited sources.

| Rule ID | Severity | Checks |
|---|---|---|
| `MARKET.NO_SOURCES` | WARNING | `positioning.sources` is non-empty (citations backing the angle) |

### Bucket C — User-provided criteria (`_check_user_brief_compliance`)
Compliance against the brand/product brief — the highest-stakes bucket
(legal/claims risk).

| Rule ID | Severity | Checks |
|---|---|---|
| `USER.FORBIDDEN_CLAIM` | BLOCKER | None of `product_brief.forbidden_claims` appear anywhere in generated copy |
| `USER.MISSING_REQUIRED_CLAIM` | BLOCKER | Every entry in `product_brief.required_claims` appears somewhere in generated copy |

## 4. Verified behavior (evidence)

Ran directly:

```bash
python QA_checklist.py
#  -> passed=True, iteration=1, 0 issues                       (exit code 0)
#     Plan positioning/copy genuinely derived from user_input.json fields;
#     4 real placeholder image files + 1 placeholder video file written to
#     testcases/bp01_fnb_sparkling_tea/ark_out/.

python QA_checklist.py --inject-drift
#  -> Iteration 1: FAIL, 7 issues detected against genuinely generated content:
#       BLOCKER  PLAN.ROUTE_COUNT          (dropped to 1 creative route)
#       BLOCKER  PLAN.AB_ROUTE_MISMATCH    (ab_test_plan now points at a route_id that no longer exists)
#       BLOCKER  ASSETS.IMAGE_COUNT        (dropped to 3 images)
#       BLOCKER  ASSETS.MISSING_IMAGE_KIND (sku_detail_image removed)
#       WARNING  ASSETS.VIDEO_DURATION     (34s, outside 15-30s)
#       WARNING  ASSETS.VIDEO_ASPECT       (1:1 instead of 9:16)
#       BLOCKER  USER.FORBIDDEN_CLAIM      ('cures bloating' injected into description)
#     Iteration 2: PASS, 0 issues — agent regenerated from scratch (drift only
#     applied on iteration 1) and passed cleanly.               (exit code 0)
```

This confirms the loop genuinely detects real problems and genuinely
self-corrects, rather than replaying a static "happy"/"unhappy" fixture.

## 5. Mapping to BP-01 submission checklist

| BP-01 requirement | Enforced by |
|---|---|
| 1 main campaign angle | `PLAN.ANGLE_EMPTY` |
| ≥ 2 A/B creative routes | `PLAN.ROUTE_COUNT`, `PLAN.ROUTE_ID_DUP` |
| ≥ 1 short-form video (15–30s, 9:16) | `ASSETS.VIDEO_COUNT` (blocker) + `ASSETS.VIDEO_DURATION`/`ASSETS.VIDEO_ASPECT` (warning) |
| ≥ 4 product/marketplace images (hero, SKU detail, collection, thumbnail) | `ASSETS.IMAGE_COUNT`, `ASSETS.MISSING_IMAGE_KIND` |
| Listing copy + ad copy | `ASSETS.COPY_INCOMPLETE`, `ASSETS.COPY_NO_BULLETS` |
| A/B testing plan | `PLAN.AB_ROUTE_MISMATCH`, `PLAN.AB_NO_METRICS` |
| Required/forbidden claims (policy & compliance safety) | `USER.MISSING_REQUIRED_CLAIM`, `USER.FORBIDDEN_CLAIM` |
| Market-signal sourcing ("trích nguồn cụ thể") | `MARKET.NO_SOURCES` |

## 6. Known gaps (not yet implemented)

- **Built-in copy generator is template-based, not reasoned.** It correctly
  weaves in `required_claims` and never emits `forbidden_claims`, but the
  actual sentence construction is a simple template, not real language
  generation — use `--live` for genuinely LLM-written copy.
- **Built-in image/video are placeholder files**, not real generated
  visuals — they exist so the QA rules engine has real files with correct
  metadata (kind/dimensions/duration/aspect) to check, not to look like a
  real product. Use `--live` for real Seedream 5.0 Pro / Seedance 2.5 output.
- **No brand-kit consistency checks** (logo/colors/tone-of-voice matching) —
  `BrandKit` fields exist in the schema but no rule currently validates
  generated assets against them.
- **No real visual QA** — generated images/video are not inspected for
  actually matching product photos or brand style; `width`/`height`/
  `duration_sec` are trusted as given by the generator, not measured from
  the file.
- **Market-source validity is not verified** — `MARKET.NO_SOURCES` only
  checks the list isn't empty, not that sources are real/relevant.

## 7. History: how this module ended up here

The following files previously implemented this same feature spread across
the FastAPI backend; they were deleted and folded into a single
`QA_checklist.py` (originally at the repo root, now moved into this
self-contained `QA_checklist/` folder alongside `byteplus_ark.py` and a
per-scenario `testcases/` structure):

- `backend/app/services/campaign/` (`gen_plan_agent.py`, `gen_assets_agent.py`, `qa_review_agent.py`)
- `backend/app/services/campaign_service.py`
- `backend/app/schemas/campaign.py`
- `backend/app/storage/` (`campaign_store.py`)
- `backend/app/api/v1/endpoints/campaigns.py` (and its router registration)
- `backend/tests/test_campaigns_api.py`, `backend/tests/test_qa_review_agent.py`, `backend/tests/fixtures/`
- `backend/run_qa_check.py`, `backend/run_qa_check_live.py`, `backend/validate_bp01_fixture.py`

The FastAPI backend (`backend/app/...`) still exists for the unrelated
Items/health demo endpoints from the base template, but no longer hosts any
campaign/QA logic. This `QA_checklist/` folder has no import dependency on
`backend/` or `frontend/` in either direction — it is independently runnable
and independently deployable/copyable.
