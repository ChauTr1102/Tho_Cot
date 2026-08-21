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
            "payload": (
                {"slot": stem}
                if _KINDS.get(path.suffix.casefold()) == "audio"
                else {"url": f"/media/{campaign_id}/media/{path.name}", "slot": stem}
            ),
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
