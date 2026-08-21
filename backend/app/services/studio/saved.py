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
    "hero", "keyframe", "_last", "_raw", "shot_",
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
    }
