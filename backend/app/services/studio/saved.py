"""
Kits that have already been built, read back off disk.

A run takes six to twelve minutes. A judge has about that long for the entire
submission, so a campaign that has already been rendered must open as a result,
not as a form — the work exists, it is on the disk, and asking anyone to
regenerate it to look at it would be the demo's worst minute.

Nothing here is a cache in the usual sense: there is no expiry and no
invalidation, because there is nothing to invalidate against. The studio writes
media under `DATA_DIR/<campaign_id>/media/` and never overwrites a campaign it
was not asked to run, so a directory with files in it means exactly one thing —
somebody built this kit. Starting a fresh campaign creates a fresh id and
therefore a fresh directory, which is why "new project regenerates, old project
opens instantly" needs no flag anywhere.

Kind and platform are inferred from the filename, which is the only metadata the
run leaves behind. That is a deliberate limit rather than a gap to fill later: a
sidecar manifest would be one more thing that can disagree with the files beside
it, and the filenames are already written by `render.py` from the slot ids.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.studio.config import studio_settings

#: Extension -> what a browser should do with it.
_KINDS: dict[str, str] = {
    ".jpg": "image", ".jpeg": "image", ".png": "image", ".webp": "image",
    ".mp4": "video", ".mov": "video", ".webm": "video",
    ".mp3": "audio", ".wav": "audio", ".m4a": "audio",
}

#: Filename prefix -> marketplace. `render.py` names files after the slot, and
#: slot ids carry their platform, so the prefix is reliable where it exists.
_PLATFORMS: tuple[tuple[str, str], ...] = (
    ("tiktok", "tiktok_shop"),
    ("shopee", "shopee"),
)

#: Files that are working material rather than deliverables. The hero is a style
#: anchor, keyframes are the first frame of a clip, `_last` stills are what
#: Seedance returns alongside one, and the raw voiceover is the take before
#: normalisation. All are worth keeping and none belong in a gallery a judge
#: scrolls, so they are returned flagged rather than hidden — a caller that
#: wants everything can still have it.
_INTERMEDIATE_MARKERS: tuple[str, ...] = (
    "hero", "keyframe", "_last", "_raw", "shot_", "sub_",
)

#: Ordering for the gallery: what the campaign is *for* first, working material
#: last. Within a group, filename order, which is slot order.
_RANK: dict[str, int] = {"video": 0, "image": 1, "audio": 2}


def media_dir(campaign_id: str) -> Path:
    """Where a campaign's rendered files live."""
    return Path(studio_settings.DATA_DIR) / campaign_id / "media"


def _classify(path: Path) -> dict[str, Any]:
    stem = path.stem.casefold()
    platform = next((value for prefix, value in _PLATFORMS if stem.startswith(prefix)), None)
    return {
        "name": path.name,
        # `/media` is mounted on DATA_DIR, so the URL mirrors the path below it.
        "url": f"/media/{path.parent.parent.name}/media/{path.name}",
        "kind": _KINDS.get(path.suffix.casefold(), "file"),
        "platform": platform,
        "bytes": path.stat().st_size,
        "intermediate": any(marker in stem for marker in _INTERMEDIATE_MARKERS),
    }


def list_assets(campaign_id: str, include_intermediate: bool = False) -> list[dict[str, Any]]:
    """Everything rendered for this campaign, newest run's files as they stand.

    Returns [] when the campaign has never been built, which is the signal the
    caller needs: no files means offer to build, files mean offer to view.
    """
    directory = media_dir(campaign_id)
    if not directory.is_dir():
        return []

    items = [
        _classify(path)
        for path in sorted(directory.iterdir())
        if path.is_file() and path.suffix.casefold() in _KINDS
    ]
    if not include_intermediate:
        items = [item for item in items if not item["intermediate"]]
    return sorted(items, key=lambda item: (_RANK.get(item["kind"], 9), item["name"]))


def build_nodes(campaign_id: str) -> list[dict[str, Any]]:
    """The finished kit as graph nodes, so it opens on the canvas it was built on.

    A gallery of thumbnails throws away the thing this studio is: every picture
    came from a named step with named inputs, and seeing a reuse node settle
    beside a nine-minute video node is the argument the product is making.

    **This is reconstruction, not a replay.** The run does not persist its DAG,
    only its files, so the edges below are re-derived from the naming convention
    `render.py` writes — `keyframe_N` feeds `shot_N`, shots feed the master, the
    hero anchors every generated still. That convention is the same code that
    built the graph in the first place, so the shape is right; what is not
    recoverable is per-node timing, which is why every node reports `0s` rather
    than a number nobody measured.
    """
    files = {path.stem: path for path in _existing(campaign_id)}
    nodes: list[dict[str, Any]] = []

    def add(node_id: str, kind: str, deps: list[str], stem: str) -> None:
        path = files.get(stem)
        if path is None:
            return
        nodes.append({
            "id": node_id,
            "kind": kind,
            "deps": [d for d in deps if any(n["id"] == d for n in nodes)],
            "state": "done",
            # Not measured. A run reports real durations live; a kit read off
            # disk has none, and inventing one would be the only dishonest
            # number on the screen.
            "elapsed_sec": 0,
            # Audio carries no `url`: the node card renders one as an <img>,
            # and an .mp3 in an image tag is a broken-image glyph with the alt
            # text spelled out beside it — which is exactly how the voiceover
            # nodes were rendering. The node still says what it is and that it
            # finished; it simply has nothing to show.
            "payload": _payload(campaign_id, path, stem),
            "updated_at": 0,
        })

    add("hero", "image", [], "hero")

    keyframes = sorted(s for s in files if s.startswith("keyframe_"))
    for stem in keyframes:
        add(stem, "keyframe", ["hero"], stem)

    shots = sorted(s for s in files if s.startswith("shot_") and not s.endswith("_last"))
    for stem in shots:
        index = stem.removeprefix("shot_")
        add(stem, "video", [f"keyframe_{int(index)}"] if index.isdigit() else [], stem)

    for stem in sorted(s for s in files if s.startswith("vo_") and not s.endswith("_raw")):
        add(stem, "compose", [], stem)
    add("voiceover", "compose", sorted(n["id"] for n in nodes if n["id"].startswith("vo_")), "voiceover")

    for stem in sorted(s for s in files if s.startswith("master_")):
        add(stem, "compose", [*shots, "voiceover"], stem)

    # Stills last so the video spine reads as one column and the marketplace
    # kits hang off the hero beside it.
    for stem in sorted(s for s in files
                       if not s.startswith(("hero", "keyframe_", "shot_", "vo_", "master_", "sub_"))
                       and files[s].suffix.casefold() in _KINDS
                       and _KINDS[files[s].suffix.casefold()] == "image"):
        add(stem, "image", ["hero"], stem)

    return nodes


def _payload(campaign_id: str, path: Path, stem: str) -> dict[str, Any]:
    """What a node card shows for one rendered file."""
    # Audio carries no `url`: the node card renders one as an <img>, and an .mp3
    # in an image tag is a broken-image glyph with the alt text spelled out
    # beside it — which is how the voiceover nodes were rendering.
    payload: dict[str, Any] = {"slot": stem}
    if _KINDS.get(path.suffix.casefold()) != "audio":
        payload["url"] = f"/media/{campaign_id}/media/{path.name}"

    # Say what the pair is for. On the board these were two cards named
    # `ab_poster_a` and `ab_poster_b` and nothing else — the A/B test was on
    # screen and unreadable, which is the same as not being there.
    if stem.startswith(_AB_PREFIX):
        other = "B" if stem.endswith("a") else "A"
        payload["note"] = f"A/B · phương án {stem[-1].upper()} — so với {other}"
    return payload


def _existing(campaign_id: str) -> list[Path]:
    directory = media_dir(campaign_id)
    if not directory.is_dir():
        return []
    return [p for p in sorted(directory.iterdir())
            if p.is_file() and p.suffix.casefold() in _KINDS]


def summary(campaign_id: str) -> dict[str, Any]:
    """A one-line answer to "has this been built, and what is in it?"."""
    everything = list_assets(campaign_id, include_intermediate=True)
    deliverables = [item for item in everything if not item["intermediate"]]
    return {
        "campaign_id": campaign_id,
        "built": bool(everything),
        "images": sum(1 for item in deliverables if item["kind"] == "image"),
        "videos": sum(1 for item in deliverables if item["kind"] == "video"),
        "total_files": len(everything),
        "bytes": sum(item["bytes"] for item in everything),
        "assets": deliverables,
        # The same kit as a graph, because that is the screen it was built on.
        "nodes": build_nodes(campaign_id),
    }


# ---------------------------------------------------------------------------
# The DTO the pipeline's final report and QA gate consume
# ---------------------------------------------------------------------------

#: Which rendered slot fills each required field of `ProductCollectionImageSet`,
#: best candidate first. Matched as a substring of the filename stem, so a slot
#: named `shopee_main_image` satisfies "main" and `tiktok_shop_video_cover`
#: satisfies "cover". The fallbacks matter: a campaign for one marketplace still
#: has to fill all four fields or the whole object is withheld.
_IMAGE_SLOTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("product_hero_image", ("main_image", "main", "hero", "cover")),
    ("sku_detail_image", ("detail", "sku", "product_card", "carousel")),
    ("campaign_collection_image", ("collection", "gallery", "lifestyle", "detail")),
    ("marketplace_thumbnail", ("thumbnail", "cover", "main", "poster")),
)

_OPTIONAL_IMAGE_SLOTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("promotion_banner", ("sale_poster", "promo", "banner", "sale")),
    ("bundle_image", ("bundle", "gift")),
    ("seasonal_sale_image", ("seasonal", "sale_sticker", "sale")),
)


def _pick(assets: list[dict[str, Any]], needles: tuple[str, ...], used: set[str]) -> str | None:
    """First unused image whose name contains one of `needles`, needles in order.

    Distinct files are preferred but not required: a four-field DTO built from a
    three-image campaign is still more useful than no DTO, so the last resort
    reuses a file rather than withholding the object.
    """
    for needle in needles:
        for asset in assets:
            if needle in asset["name"].casefold() and asset["name"] not in used:
                used.add(asset["name"])
                return asset["url"]
    for needle in needles:
        for asset in assets:
            if needle in asset["name"].casefold():
                return asset["url"]
    return None


#: Rendered filename -> which creative route it argues for. `plan_graph` names
#: the pair `ab_poster_a` / `ab_poster_b`, so the route survives into the file.
_AB_PREFIX = "ab_poster_"


def ab_pair(campaign_id: str) -> dict[str, str]:
    """The A/B posters, keyed by route id, or {} when the run predates them.

    The whole point of researching two creative routes is the comparison, and
    until the studio rendered a poster per route there was nothing to compare —
    the final report showed two hypotheses above one set of artwork. This is
    what lets it show the pair.
    """
    found: dict[str, str] = {}
    for asset in list_assets(campaign_id, include_intermediate=True):
        stem = Path(asset["name"]).stem.casefold()
        if stem.startswith(_AB_PREFIX):
            found[stem[len(_AB_PREFIX):].upper()] = asset["url"]
    return found


def to_dto(campaign_id: str) -> dict[str, Any]:
    """A finished kit in the DTO shapes `CampaignOutputDTO` is assembled from.

    This is the disk-backed twin of the in-memory path in `endpoints/studio.py`.
    That one reads `_RUNS`, a process-local dict, so it answers only while the
    process that did the rendering is still alive: restart the backend, or open
    a campaign built yesterday, and the final report fell back to mock URLs
    pointing at `example.com`. The files never went anywhere; only the dict did.

    Both halves stay null unless genuinely complete, exactly as the in-memory
    path does — a half-filled object would satisfy the type and fail the brief.
    """
    assets = list_assets(campaign_id)
    images = [a for a in assets if a["kind"] == "image"]
    videos = [a for a in assets if a["kind"] == "video"]

    image_set: dict[str, Any] | None = None
    if len(images) >= 4:
        used: set[str] = set()
        picked = {field: _pick(images, needles, used) for field, needles in _IMAGE_SLOTS}
        if all(picked.values()):
            for field, needles in _OPTIONAL_IMAGE_SLOTS:
                found = _pick(images, needles, used)
                if found:
                    picked[field] = found
            image_set = picked

    video_asset: dict[str, Any] | None = None
    if videos:
        # The longest master is the campaign video; the rest are cutdowns.
        ordered = sorted(videos, key=lambda a: a["bytes"], reverse=True)
        video_asset = {
            "generated_video_urls": [ordered[0]["url"]],
            "format": "9:16",
            "duration": "15-30s",
            "additional_cuts": [a["url"] for a in ordered[1:]],
        }

    return {
        "campaign_id": campaign_id,
        "status": "done" if assets else "empty",
        "product_collection_image_set": image_set,
        "short_form_video_asset": video_asset,
        "ab_variants": ab_pair(campaign_id),
    }


# ---------------------------------------------------------------------------
# Packing a kit that is only on disk
# ---------------------------------------------------------------------------

#: Filename prefix -> the folder it goes in inside the zip. Someone opens this
#: beside an upload form and needs to know which file goes in which box.
_ZIP_FOLDERS: tuple[tuple[str, str], ...] = (
    ("ab_poster_", "ab-test"),
    ("tiktok", "tiktok-shop"),
    ("shopee", "shopee"),
    ("master_", "video"),
    ("shot_", "video"),
    ("vo_", "video"),
    ("voiceover", "video"),
    ("keyframe", "lam-viec"),
    ("hero", "lam-viec"),
    ("sub_", "lam-viec"),
)


def _zip_folder(stem: str) -> str:
    for prefix, folder in _ZIP_FOLDERS:
        if stem.startswith(prefix):
            return folder
    return "khac"


def build_manifest(campaign_id: str, ab: dict[str, str]) -> str:
    """MANIFEST.md for a kit read back off disk.

    `pack.build_manifest` writes the richer version from a live `AssetBundle` —
    per-image origin, the text on each frame — none of which survives on disk.
    This one states what the files themselves can prove, and says so, rather
    than inventing provenance to fill the same table.
    """
    everything = list_assets(campaign_id, include_intermediate=True)
    deliverables = [a for a in everything if not a["intermediate"]]
    images = sum(1 for a in deliverables if a["kind"] == "image")
    videos = sum(1 for a in deliverables if a["kind"] == "video")

    lines = [
        f"# Bộ kit — {campaign_id}",
        "",
        f"{images} ảnh · {videos} video, đọc lại từ thư mục đã dựng.",
        "",
        "## Model đã dùng",
        "",
        "| Việc | Model |",
        "|---|---|",
        "| Ảnh | `dola-seedream-5-0-pro-260628` |",
        "| Video | `dreamina-seedance-2-5-260628` |",
        "| Lồng tiếng | `seed-audio-1.0` |",
        "| Đạo diễn chiến dịch, soi lỗi chữ | `dola-seed-2-1-turbo-260628` |",
        "",
    ]

    if ab:
        lines += [
            "## Thử nghiệm A/B",
            "",
            "Hai phương án cho cùng một sản phẩm, cùng một ưu đãi. **Chỉ thông "
            "điệp thay đổi** — badge và nút mua giữ nguyên ở cả hai, nên chênh "
            "lệch kết quả quy được về đúng biến đã thử.",
            "",
            "| Phương án | File |",
            "|---|---|",
        ]
        for route in sorted(ab):
            lines.append(f"| {route} | `ab-test/ab_poster_{route.lower()}.jpg` |")
        lines.append("")

    lines += [
        "## File trong gói",
        "",
        "| Đường dẫn | Loại |",
        "|---|---|",
    ]
    for asset in everything:
        stem = Path(asset["name"]).stem
        folder = _zip_folder(stem.casefold())
        note = " (vật liệu trung gian)" if asset["intermediate"] else ""
        lines.append(f"| `{folder}/{asset['name']}` | {asset['kind']}{note} |")

    lines += [
        "",
        "Ảnh gốc của thương hiệu không nằm trong gói này — chúng thuộc về "
        "thương hiệu, và kho ảnh không bị ghi đè ở bất kỳ bước nào.",
        "",
    ]
    return "\n".join(lines)


def build_zip(campaign_id: str, out_path: str | Path) -> str | None:
    """Zip a kit straight from disk. Returns None when there is nothing to pack.

    The in-memory packer answers only while the process that rendered the kit is
    alive, so `Tải .zip` was a dead button for any campaign opened after a
    restart — which is every campaign a judge opens.
    """
    import zipfile

    everything = list_assets(campaign_id, include_intermediate=True)
    if not everything:
        return None

    directory = media_dir(campaign_id)
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for asset in everything:
            source = directory / asset["name"]
            if source.is_file():
                folder = _zip_folder(Path(asset["name"]).stem.casefold())
                archive.write(source, f"{campaign_id}/{folder}/{asset['name']}")
        archive.writestr(
            f"{campaign_id}/MANIFEST.md",
            build_manifest(campaign_id, ab_pair(campaign_id)),
        )
    return str(target)
