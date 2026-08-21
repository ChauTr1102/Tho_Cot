"""
Reading a finished research campaign straight into the studio.

The research stage stores its work on the `campaigns` row: `research_input` is
the brief a person filled in, `research_result.plan` is what the planning agent
produced. Both are already there by the time anyone opens the studio, so the
studio should start from them rather than asking for the same facts twice.

This is the third shape the same brief arrives in. The research form writes
plurals and objects — `target_market` is a list, `price` is `{amount, currency,
unit}` with `promotion` beside it, `tone_of_voice` is a list of adjectives —
while `campaign_dto` writes singulars and the studio's own models write flat
strings. Rather than argue about which is right, this module translates, and
the translations are where the care goes: a list joined with the wrong
separator or a price silently dropped becomes a badge that reads "135000.0" on
a live listing.

Two things the row does not carry:

* **The photographs.** `input_assets` records what was uploaded — label, source
  filename, size, mime — but not the bytes; they went to the model and were not
  kept. So the files are resolved by name against an uploads directory and then
  `sample_data/`, and a campaign whose photos cannot be found still runs, with
  every slot falling to GENERATE. The kit is duller, not absent.
* **Marketplaces the studio can build for.** The research form offers Douyin,
  Tmall, Taobao and Shopee. The studio has kits for two, so the rest map onto
  the closest one and the unmapped names are reported rather than dropped.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
import re
from typing import Any

from app.schemas.studio import (
    AudienceBrief,
    BrandKit,
    CampaignInput,
    CampaignPlan,
    MarketSignal,
    Platform,
    ProductBrief,
)
from app.services.studio import upstream
from app.services.studio.config import studio_settings

# Douyin is vertical short-form video, so it wants the TikTok kit; the rest are
# image-first marketplaces and want Shopee's. Anything unrecognised is reported.
PLATFORM_ALIASES: dict[str, Platform] = {
    "douyin": Platform.TIKTOK_SHOP,
    "tiktok": Platform.TIKTOK_SHOP,
    "tiktok shop": Platform.TIKTOK_SHOP,
    "tiktok_shop": Platform.TIKTOK_SHOP,
    "shopee": Platform.SHOPEE,
    "lazada": Platform.SHOPEE,
    "tmall": Platform.SHOPEE,
    "taobao": Platform.SHOPEE,
    "tokopedia": Platform.SHOPEE,
    "amazon": Platform.SHOPEE,
}


_WORD_RE = re.compile(r"[a-z0-9]+")


class ResearchNotReady(Exception):
    """The campaign exists but has no plan to build from yet."""


def _first(value: Any, default: str = "") -> str:
    """A list where the studio wants one value: take the first, keep the rest for
    the joined form."""
    if isinstance(value, list):
        return str(value[0]) if value else default
    return str(value) if value not in (None, "") else default


def _join(value: Any, separator: str = ", ", limit: int = 4) -> str:
    if isinstance(value, list):
        return separator.join(str(v) for v in value[:limit] if str(v).strip())
    return str(value) if value not in (None, "") else ""


def _price_line(brief: dict[str, Any]) -> str | None:
    """`{amount, currency, unit}` plus a separate promotion, as one line of copy.

    Both halves matter and neither is optional-by-default: the amount ends up on
    a price badge, the promotion on the offer badge. Formatting the amount is
    not cosmetic either — `135000.0` on a poster is worse than no price at all.
    """
    parts: list[str] = []
    price = brief.get("price")
    if isinstance(price, dict) and price.get("amount") is not None:
        try:
            amount = f"{float(price['amount']):,.0f}".replace(",", ".")
        except (TypeError, ValueError):
            amount = str(price["amount"])
        unit = price.get("unit")
        currency = price.get("currency") or ""
        parts.append(f"{amount}{'đ' if currency.upper() == 'VND' else ' ' + currency}"
                     + (f" / {unit}" if unit else ""))
    elif isinstance(price, (int, float, str)) and str(price).strip():
        parts.append(str(price))

    if brief.get("promotion"):
        parts.append(str(brief["promotion"]))
    return " · ".join(parts) or None


def _colours(brand_kit: dict[str, Any]) -> list[str]:
    """Hex values out of `[{name, hex, verification_status}]` or a bare list."""
    out: list[str] = []
    for entry in brand_kit.get("brand_colors", []) or []:
        value = entry.get("hex") if isinstance(entry, dict) else entry
        if value and str(value).strip() and str(value) not in out:
            out.append(str(value).strip())
    return out


def _brand_score(directory: Path, product_name: str) -> int:
    """How well a sample_data directory matches a product name, in shared words."""
    words = {w for w in _WORD_RE.findall(product_name.casefold()) if len(w) > 1}
    folder = {w for w in _WORD_RE.findall(directory.name.casefold()) if len(w) > 1}
    return len(words & folder)


def resolve_photos(names: list[str], campaign_id: str,
                   product_name: str = "") -> tuple[list[str], list[str]]:
    """Find the uploaded photographs on disk by filename.

    Returns `(found, missing)`. The campaign's own upload directory comes first,
    because that is where a real deployment writes them.

    `sample_data/` is only searched as a fallback, and then **only inside the
    brand folder whose name matches the product**. Every demo brand stores its
    files under the same names — `product_01.jpg`, `logo.png` — so an
    alphabetical sweep silently resolved a G7 coffee campaign to COSRX's
    skincare bottle, and the whole kit came back as a serum bottle wearing a
    coffee label. Filename alone is not identity when six directories share the
    same filenames.
    """
    roots = [
        Path(studio_settings.DATA_DIR) / campaign_id / "source",
        Path(studio_settings.DATA_DIR) / "uploads" / campaign_id,
    ]

    sample_root = Path(__file__).resolve().parents[4] / "sample_data"
    if sample_root.is_dir() and product_name.strip():
        brands = [d for d in sample_root.iterdir() if d.is_dir()]
        best = max(brands, key=lambda d: _brand_score(d, product_name), default=None)
        # A zero score means nothing matched; borrowing a stranger's photographs
        # is worse than generating from nothing, so leave them missing.
        if best is not None and _brand_score(best, product_name) > 0:
            roots.append(best / "assets")

    found, missing = [], []
    for name in names:
        base = Path(str(name)).name
        for root in roots:
            candidate = root / base
            if candidate.is_file():
                found.append(str(candidate))
                break
        else:
            missing.append(base)
    return found, missing


def save_uploads(campaign_id: str,
                 assets: list[tuple[str, str, str | None, bytes]]) -> list[str]:
    """Write the brand's uploaded files where `resolve_photos` will look.

    The research endpoint reads each upload into memory, base64-encodes it for
    the model, and lets it go: the row records `input_assets` — label, filename,
    size, mime — but never the bytes. That is fine for research, which only
    needs to look at the pictures once, and fatal for the studio, which needs
    the actual file. Without it a campaign for a product nobody has a sample
    folder for resolves to no photographs at all, every slot falls to GENERATE,
    and the model invents the packaging — which is how a real brand name came
    back rendered as `COSRᴀ`.

    Files land in the campaign's own `source/` directory, the first root
    `resolve_photos` searches, so the writer and the reader cannot drift apart.
    Called for its side effect during research; the returned paths are for
    logging.

    `Path(...).name` is not cosmetic: the filename arrives from a browser
    upload, so `../../etc/whatever` has to lose its directories before it is
    joined to a root.
    """
    root = Path(studio_settings.DATA_DIR) / campaign_id / "source"
    root.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    for _label, filename, _mime, content in assets:
        if not content:
            continue
        name = Path(str(filename or "")).name.strip()
        if not name or name in {".", ".."}:
            continue
        target = root / name
        target.write_bytes(content)
        saved.append(str(target))
    return saved


#: Guards on anything fetched from a URL a user pasted. A product photo is a
#: few hundred kilobytes; anything past this is not one, and downloading it
#: would be someone else's bandwidth bill and our disk.
REMOTE_PHOTO_MAX_BYTES = 12 * 1024 * 1024
REMOTE_PHOTO_MAX_COUNT = 8
REMOTE_PHOTO_TIMEOUT_SEC = 20


def fetch_remote_photos(urls: list[str], campaign_id: str) -> tuple[list[str], list[str]]:
    """Download product photographs the extractor found on a page.

    Returns `(local_paths, failed_urls)`.

    The link flow ends here or it does not end at all. An extractor reads a
    product page and reports image URLs; `pipeline._photo_paths` then drops
    anything starting with `http`, correctly — a URL is not a Brand Lock
    reference — with a comment saying they are unusable "until downloaded".
    Nothing downloaded them. So pasting a link produced a campaign with no
    photographs, every slot fell to GENERATE, and the model invented the
    packaging: the exact failure the Brand Lock exists to prevent, reached by
    the one path a new user is most likely to take.

    Files land beside uploaded ones, in the campaign's own `source/`, so the
    rest of the studio cannot tell how a photograph arrived.
    """
    import urllib.request

    root = Path(studio_settings.DATA_DIR) / campaign_id / "source"
    saved_paths: list[str] = []
    failed: list[str] = []

    for index, url in enumerate(urls[:REMOTE_PHOTO_MAX_COUNT]):
        if not isinstance(url, str) or not url.lower().startswith(("http://", "https://")):
            continue
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0 (compatible; ThoCotStudio/1.0)"}
            )
            with urllib.request.urlopen(request, timeout=REMOTE_PHOTO_TIMEOUT_SEC) as response:
                kind = (response.headers.get("Content-Type") or "").split(";")[0].strip()
                if not kind.startswith("image/"):
                    failed.append(url)
                    continue
                # Read in a loop. `HTTPResponse.read(n)` returns *up to* n
                # bytes, not n — with chunked transfer encoding a single call
                # routinely returns less, and the shortfall is a truncated JPEG
                # that decodes to a half-drawn picture rather than an error.
                chunks: list[bytes] = []
                total = 0
                while total <= REMOTE_PHOTO_MAX_BYTES:
                    chunk = response.read(64 * 1024)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    total += len(chunk)
                body = b"".join(chunks)
            if not body or len(body) > REMOTE_PHOTO_MAX_BYTES:
                failed.append(url)
                continue

            # Name by position, not by the remote filename: a URL's last segment
            # is attacker-controlled and frequently not a filename at all.
            suffix = {"image/jpeg": ".jpg", "image/png": ".png",
                      "image/webp": ".webp"}.get(kind, ".jpg")
            root.mkdir(parents=True, exist_ok=True)
            target = root / f"web_{index:02d}{suffix}"
            target.write_bytes(body)
            saved_paths.append(str(target))
        except Exception:
            # A page that will not give up its pictures is survivable: the kit
            # is duller, not absent. It is reported, never raised.
            failed.append(url)

    return saved_paths, failed


def build_input(research_input: dict[str, Any], campaign_id: str,
                photos: list[str] | None = None) -> CampaignInput:
    """The research form's brief, in the studio's own shape."""
    brief = research_input.get("product_brief", {}) or {}
    brand = research_input.get("brand_kit", {}) or {}
    audience = research_input.get("audience_brief", {}) or {}
    signal = research_input.get("market_signal", {}) or {}

    names = brand.get("product_photos", []) or []
    resolved = (photos if photos is not None
                else resolve_photos(names, campaign_id,
                                    str(brief.get("product_name", "")))[0])

    return CampaignInput(
        campaign_id=campaign_id,
        product_brief=ProductBrief(
            product_name=str(brief.get("product_name", "")),
            category=str(brief.get("category", "")),
            key_selling_points=[str(x) for x in brief.get("key_selling_points", []) or []],
            price_or_promotion=_price_line(brief),
            target_market=_join(brief.get("target_market")) or "Việt Nam",
            required_claims=[str(x) for x in brief.get("required_claims", []) or []],
            # `restricted_claims` here, `restricted_or_forbidden_claims` in the
            # DTO, `forbidden_claims` internally. Same list, three names, and
            # dropping it would put a takedown-worthy claim on a listing.
            forbidden_claims=[str(x) for x in
                              (brief.get("restricted_claims")
                               or brief.get("restricted_or_forbidden_claims")
                               or []) ],
        ),
        brand_kit=BrandKit(
            logo_url=str(brand.get("logo")) if brand.get("logo") else None,
            brand_colors=_colours(brand),
            tone_of_voice=_join(brand.get("tone_of_voice"), ", ", 6) or None,
            product_photo_urls=resolved,
        ),
        audience_brief=AudienceBrief(
            target_customer=_join(audience.get("target_customer"), ", ", 3),
            language=_first(audience.get("languages"), "vi"),
            platform=[p.value for p in map_platforms(audience.get("platforms", []))[0]],
            market=_join(audience.get("markets")) or _join(brief.get("target_market")),
        ),
        market_signal=MarketSignal(
            trend=_join(signal.get("trends"), ", ", 3) or None,
            seasonal_moment=_first(signal.get("seasonal_moments")) or None,
            consumer_pain_point=_first(signal.get("consumer_pain_points")) or None,
            search_keyword=_join(signal.get("search_keywords"), ", ", 3) or None,
            competitor_angle=_join(signal.get("competitor_angles"), ", ", 3) or None,
            campaign_objective=_join(signal.get("campaign_objectives"), " + ", 2) or None,
        ),
    )


def map_platforms(names: list[str]) -> tuple[list[Platform], list[str]]:
    """Research-form marketplaces onto the two the studio has kits for.

    Returns `(mapped, unrecognised)`. Unrecognised names are handed back rather
    than swallowed: a user who asked for a marketplace the studio cannot build
    for should be told, not quietly given something else.
    """
    mapped: list[Platform] = []
    unknown: list[str] = []
    for name in names or []:
        platform = PLATFORM_ALIASES.get(str(name).strip().casefold())
        if platform is None:
            unknown.append(str(name))
        elif platform not in mapped:
            mapped.append(platform)
    return (mapped or [Platform.SHOPEE]), unknown


def load_row(campaign_id: str, db_path: str | Path | None = None) -> dict[str, Any]:
    """One campaign row, with its JSON columns already decoded.

    Read with sqlite3 directly rather than through the ORM: the studio owns no
    tables and should not acquire a session dependency to read two columns.
    """
    path = Path(db_path or "sql_app.db")
    if not path.is_file():
        raise FileNotFoundError(f"không tìm thấy database: {path}")

    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute(
            "select * from campaigns where id = ?", (campaign_id,)
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        raise KeyError(campaign_id)

    record = dict(row)
    for column in ("research_input", "research_result"):
        raw = record.get(column)
        if isinstance(raw, str) and raw.strip():
            try:
                record[column] = json.loads(raw)
            except json.JSONDecodeError:
                record[column] = {}
        elif raw is None:
            record[column] = {}
    return record


def load_pair(campaign_id: str, db_path: str | Path | None = None
              ) -> tuple[CampaignPlan, CampaignInput, dict[str, Any]]:
    """A finished research campaign as `(plan, input, notes)`.

    `notes` carries what the caller should surface: photographs that could not
    be found, and marketplaces the studio has no kit for. Both are survivable
    and both are worth saying out loud.
    """
    record = load_row(campaign_id, db_path)
    research_input = record.get("research_input") or {}
    research_result = record.get("research_result") or {}
    plan_raw = research_result.get("plan") or {}

    if not plan_raw:
        raise ResearchNotReady(
            f"Campaign '{campaign_id}' chưa có kết quả research "
            f"(trạng thái: {record.get('status')})."
        )

    names = (research_input.get("brand_kit", {}) or {}).get("product_photos", []) or []

    # The extractor reports what it found on the page, which for a pasted link
    # is a list of URLs rather than filenames. Fetch those before resolving, so
    # a link-started campaign reaches the renderer with the same thing an
    # uploaded one does: files in its own source directory.
    remote = [n for n in names if isinstance(n, str) and n.lower().startswith(("http://", "https://"))]
    fetched: list[str] = []
    unreachable: list[str] = []
    if remote:
        fetched, unreachable = fetch_remote_photos(remote, campaign_id)

    local_names = [n for n in names if n not in remote]
    photos, missing = resolve_photos(
        local_names, campaign_id,
        str((research_input.get("product_brief", {}) or {}).get("product_name", "")))
    photos = fetched + photos
    _, unknown_platforms = map_platforms(
        (research_input.get("audience_brief", {}) or {}).get("platforms", []))

    campaign_input = build_input(research_input, campaign_id, photos)

    # `parse_plan`, not `load_plan`: the adapter already works out which kho
    # photos each route named, whether upstream forbade redrawing the packaging,
    # which marketplaces it asked for per route, and what it had to repair on the
    # way. `load_plan` throws all of that away and returns the contract alone,
    # which meant the studio recomputed some of it worse and never surfaced the
    # rest — the real G7 plan points route B at Tmall and Taobao, and nothing
    # told the user those have no kit.
    parsed = upstream.parse_plan(plan_raw, campaign_id)

    route_platforms = {
        h.route_id: [p.value for p in h.platforms] for h in parsed.hints
    }
    unsupported = list(unknown_platforms)
    for name in parsed.unsupported_platforms:
        if name not in unsupported:
            unsupported.append(name)

    notes: dict[str, Any] = {
        "name": record.get("name"),
        "status": record.get("status"),
        "photos_found": photos,
        "photos_missing": missing,
        "photos_from_web": fetched,
        "photos_unreachable": unreachable,
        "platforms_unsupported": unsupported,
        "sources": (research_result.get("sources") or [])[:8],
        # From the plan itself, per route.
        "route_platforms": route_platforms,
        "routes_without_kit": [
            h.route_id for h in parsed.hints if not h.platforms
        ],
        "preserve_packaging": any(h.preserve_packaging for h in parsed.hints),
        "art_direction_notes": [
            note for h in parsed.hints for note in h.art_direction_notes
        ],
        "reference_photos": [
            name for h in parsed.hints for name in h.reference_photos
        ],
        "stripped_placeholders": parsed.stripped_placeholders,
        "warnings": parsed.warnings,
        "research_digest": research_digest(research_result),
    }
    return parsed.plan, campaign_input, notes


#: How much of the research prose the director is shown. The research stage
#: writes about thirty thousand characters across `report`, `research` and its
#: drafts; a model handed all of it spends its attention summarising rather than
#: deciding, and the structured plan is already that summary. This is a taste —
#: enough to ground the art direction in the market it is for.
RESEARCH_DIGEST_CHARS = 1400


def research_digest(research_result: dict[str, Any]) -> str:
    """A bounded excerpt of the research, for the director's brief.

    The creative draft first: it is the one written about how the campaign
    should look and feel, which is the only question the director is answering.
    The market report is the fallback, because a campaign with no creative draft
    still has an audience worth knowing about.

    None of this reaches an image prompt. Seedream renders what a prompt names
    explicitly and garbles what it has to invent, so prose belongs where a model
    is *deciding* — the register — and never where one is lettering.
    """
    drafts = research_result.get("drafts") or {}
    for source in (drafts.get("creative"), drafts.get("positioning"),
                   research_result.get("report")):
        if isinstance(source, str) and source.strip():
            return source.strip()[:RESEARCH_DIGEST_CHARS]
    return ""


def list_campaigns(db_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Campaigns that have research done, newest first — the studio's inbox."""
    path = Path(db_path or "sql_app.db")
    if not path.is_file():
        return []
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "select id, name, status, updated_at from campaigns order by updated_at desc"
        ).fetchall()
    finally:
        connection.close()
    return [dict(r) for r in rows]
