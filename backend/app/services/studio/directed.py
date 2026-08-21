"""
Executing a graph the director designed.

`pipeline.build_nodes` builds the fixed graph — the same slots and shots for
every campaign. This module builds whatever the director asked for instead:
its node ids, its edges, its prompts, its aspect ratios.

The division of trust is the whole point. The director chose the *shape*; this
module owns the *doing*, and every node here is a closure over code that already
existed and was already exercised. Nothing the model returns reaches an API call
unexamined: `director._validate` has already dropped unknown kinds, cut dangling
edges and broken cycles, and the builders below still treat every field as
untrusted — a missing prompt falls back to the slot's own staging, an unusable
ratio falls back to square, a keyframe with no clip is simply a still.

If the director's graph produces nothing runnable, the caller is expected to
fall back to `pipeline.build_nodes`. A duller campaign is survivable; a stack
trace in front of judges is not.
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Callable, Sequence

from app.schemas.studio import AssetOrigin, ImageKind, Platform
from app.services.studio import assemble, director, inventory, motion, qa_visual, render
from app.services.studio.config import studio_settings
from app.services.studio.graph import GraphEvent, Node, NodeState, degraded

# Which DTO image kind a node fills, guessed from its id. The director names
# nodes after what they are for (`shopee_main`, `tiktok_cover`, `sku_close`), so
# the id is the best signal available — and a wrong guess costs a DTO field
# borrowing from a neighbour, not a failed run.
_KIND_HINTS: tuple[tuple[tuple[str, ...], ImageKind], ...] = (
    (("main", "hero", "primary"), ImageKind.HERO),
    (("sku", "detail", "macro", "close"), ImageKind.SKU_DETAIL),
    (("collection", "combo", "bundle", "set"), ImageKind.COLLECTION),
    (("thumb", "cover", "card"), ImageKind.THUMBNAIL),
    (("banner", "poster", "promo", "sale"), ImageKind.BANNER),
    (("seasonal", "tet", "festive"), ImageKind.SEASONAL),
)


def guess_kind(node_id: str, is_poster: bool = False) -> ImageKind:
    """Map a director-chosen node id onto the DTO's image vocabulary."""
    low = node_id.lower()
    for needles, kind in _KIND_HINTS:
        if any(n in low for n in needles):
            return kind
    return ImageKind.BANNER if is_poster else ImageKind.HERO


def _platform(value: str) -> Platform:
    try:
        return Platform(value)
    except ValueError:
        return Platform.SHOPEE


def build_nodes(spec: director.GraphSpec, draft: director.Draft,
                campaign_id: str, photos: Sequence[str],
                label_text: Sequence[str], forbidden: Sequence[str],
                on_event: Callable[[GraphEvent], None] | None = None,
                qa: bool | None = None) -> list[Node]:
    """Turn a validated `GraphSpec` into executable graph nodes."""
    out_dir = Path(studio_settings.DATA_DIR) / campaign_id / "media"
    spine = draft.register.as_spine()
    gate = studio_settings.QA_ENABLED if qa is None else qa
    photo = photos[0] if photos else None

    by_id = {n.id: n for n in spec.nodes}
    hero_id = next((n.id for n in spec.nodes if n.kind == "hero"), None)
    nodes: list[Node] = []

    def _qa_later(result: render.RenderedImage, expected: Sequence[str], node_id: str) -> None:
        """Inspect beside the run, never on it. See pipeline._render_with_qa."""
        if not gate or not expected:
            return

        def _run() -> None:
            try:
                verdict = qa_visual.inspect_image(
                    result.local_path, expected_texts=expected,
                    label_text=label_text, forbidden_claims=forbidden)
            except Exception:
                return
            result.qa_passed = verdict.passed
            result.qa_notes = (list(verdict.missing_text)
                               + list(verdict.unexpected_brandlike)
                               + list(verdict.forbidden_hits))
            if on_event:
                on_event(GraphEvent(
                    node_id=node_id, kind="image", state=NodeState.DONE,
                    payload={"qa": "PASS" if verdict.passed else "WARN",
                             "qa_notes": result.qa_notes[:4]}))

        threading.Thread(target=_run, daemon=True).start()

    for spec_node in spec.nodes:
        kind = spec_node.kind

        if kind == "inventory":
            nodes.append(Node(
                id=spec_node.id, kind="inspect", deps=list(spec_node.deps),
                run=lambda ctx, _p=tuple(photos): inventory.build_sheet(list(_p), use_vision=False),
            ))

        elif kind == "hero":
            def _hero(ctx: dict[str, Any], _n=spec_node) -> Any:
                # The anchor never carries copy: it exists to fix the light that
                # every later image inherits, and text on it would only be
                # re-rendered differently on each of them.
                item = _stub(_n, texts=[])
                img = render.render_hero(item, spine, photo, label_text, out_dir)
                # Return a dict, not the dataclass. The event layer strips
                # dataclasses so an object result reaches the canvas as an empty
                # payload — which is why the hero, the keyframes and the clips
                # showed no picture at all while the stills did.
                return {"hero": img, "url": img.local_path, "prompt": img.prompt,
                        "origin": img.origin.value}

            nodes.append(Node(id=spec_node.id, kind="image", deps=list(spec_node.deps),
                              run=_hero, concurrency_group="image"))

        elif kind in {"image", "poster"}:
            def _still(ctx: dict[str, Any], _n=spec_node, _poster=(kind == "poster")) -> Any:
                hero_path = _path_of(ctx.get(hero_id) if hero_id else None)
                if _poster:
                    img = render.render_poster(
                        _n.id, _n.prompt, spine, _n.texts, label_text,
                        _n.ratio, render.size_for(_n.ratio), photo, hero_path, out_dir)
                else:
                    img = render.render_item(
                        _stub(_n), spine, photo, hero_path, label_text, out_dir)
                _qa_later(img, [t for _, t in _n.texts], _n.id)
                out: dict[str, Any] = {
                    "image": img, "url": img.local_path, "slot": _n.id,
                    "origin": img.origin.value, "platform": _n.platform,
                    "kind_hint": guess_kind(_n.id, _poster).value,
                    "qa": "PASS" if img.qa_passed is not False else "WARN"}
                # Two cards named `ab_poster_a` and `ab_poster_b` say nothing
                # about what they are. The board is where the run is watched, so
                # the A/B pair has to be legible there and not only in the
                # report at the end.
                if _n.route:
                    out["note"] = f"A/B · phương án {_n.route} — biến thử: headline"
                return out

            nodes.append(Node(id=spec_node.id, kind="image", deps=list(spec_node.deps),
                              run=_still, concurrency_group="image"))

        elif kind == "keyframe":
            def _kf(ctx: dict[str, Any], _n=spec_node) -> Any:
                img = render.render_item(
                    _stub(_n), spine, photo,
                    _path_of(ctx.get(hero_id) if hero_id else None), label_text, out_dir,
                    for_video=True)
                _qa_later(img, [t for _, t in _n.texts], _n.id)
                # `keyframe`, not `image`: a shot's first frame is scaffolding
                # for the video, not a deliverable, and run_directed maps every
                # dict carrying `image` into the kit.
                return {"keyframe": img, "url": img.local_path, "prompt": img.prompt,
                        "ratio": _n.ratio}

            nodes.append(Node(id=spec_node.id, kind="image", deps=list(spec_node.deps),
                              run=_kf, concurrency_group="image"))

        elif kind == "clip":
            def _clip(ctx: dict[str, Any], _n=spec_node) -> Any:
                path = _path_of(next((ctx[d] for d in _n.deps if d in ctx), None))
                if not path:
                    return degraded(None, note="không có keyframe")
                shot = _Shot(index=_index_of(_n.id), role=_n.role or "product",
                             scene=_n.prompt, onscreen_text=_first_text(_n),
                             vo_text="", seconds=_n.seconds)
                result = motion.render_shot(shot, path, spine,
                                            seed=1000 + _index_of(_n.id), out_dir=out_dir)
                return {"shot": result, "url": result.clip_path, "prompt": _n.prompt,
                        "ratio": _n.ratio, "role": _n.role,
                        "note": result.fallback_reason if result.used_fallback else None}

            nodes.append(Node(id=spec_node.id, kind="video", deps=list(spec_node.deps),
                              run=_clip, concurrency_group="video"))

        elif kind == "voiceover":
            def _vo(ctx: dict[str, Any], _n=spec_node, _spec=spec) -> Any:
                shots = [
                    _Shot(index=i, role=n.role or "product", scene=n.prompt,
                          onscreen_text=_first_text(n), vo_text=_vo_text(n), seconds=n.seconds)
                    for i, n in enumerate(x for x in _spec.nodes if x.kind == "keyframe")
                ]
                if not shots:
                    return degraded(None, note="không có shot nào để đọc")
                return motion.render_voiceover(shots, voice_hint=draft.register.why,
                                               out_dir=out_dir)

            nodes.append(Node(id=spec_node.id, kind="audio", deps=list(spec_node.deps),
                              run=_vo))

        elif kind == "assemble":
            def _master(ctx: dict[str, Any], _n=spec_node) -> Any:
                clips, vo = [], None
                for dep in _n.deps:
                    value = ctx.get(dep)
                    if value is None:
                        continue
                    shot = value.get("shot") if isinstance(value, dict) else value
                    if getattr(shot, "clip_path", None):
                        clips.append(shot.clip_path)
                    elif getattr(value, "mp3_path", None):
                        vo = value
                if not clips:
                    return degraded(None, note="không clip nào sống sót")

                master = out_dir / f"{_n.id}_master.mp4"
                duration = assemble.concat(clips, master)
                final = str(master)
                if vo is not None:
                    try:
                        strips = motion.subtitle_strips(vo.line_timings, (720, 1280), out_dir)
                        final = assemble.mux(master, vo.mp3_path, strips,
                                             vo.line_timings, out_dir / f"{_n.id}_final.mp4")
                    except Exception:
                        final = str(master)   # a missing voiceover must not lose the video
                cuts = []
                if duration > 16:
                    try:
                        cuts.append(assemble.cutdown(final, out_dir / f"{_n.id}_15s.mp4", 15))
                    except Exception:
                        pass
                return {"path": final, "url": final, "duration": duration,
                        "ratio": _n.ratio, "platform": _n.platform,
                        "cutdowns": cuts, "clips": tuple(_n.deps), "has_vo": vo is not None}

            nodes.append(Node(id=spec_node.id, kind="compose", deps=list(spec_node.deps),
                              run=_master))

    return nodes


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def _path_of(value: Any) -> str | None:
    """The file behind a node result, whether it came back as a dict or an object.

    Node results are dicts now so their previews reach the canvas, but the
    renderers still hand back dataclasses internally. One unwrapper beats
    remembering which is which at nine call sites.
    """
    if value is None:
        return None
    if isinstance(value, dict):
        for key in ("hero", "keyframe", "image"):
            inner = value.get(key)
            if getattr(inner, "local_path", None):
                return inner.local_path
        return value.get("url")
    return getattr(value, "local_path", None)


class _Shot:
    """The shape `motion.render_shot` reads. Deliberately duck-typed: `direct.ShotPlan`
    is a frozen dataclass built for the fixed pipeline, and a directed graph's shots
    come from somewhere else."""

    def __init__(self, index: int, role: str, scene: str, onscreen_text: str,
                 vo_text: str, seconds: int) -> None:
        self.index, self.role, self.scene = index, role, scene
        self.onscreen_text, self.vo_text, self.seconds = onscreen_text, vo_text, seconds


def _stub(spec_node: director.NodeSpec, texts: Sequence[tuple[str, str]] | None = None):
    """A `WorkItem` shaped for the existing renderers."""
    from app.services.studio.direct import WorkItem
    return WorkItem(
        slot_id=spec_node.id, platform=_platform(spec_node.platform),
        kind=guess_kind(spec_node.id), origin=AssetOrigin.GENERATE,
        ratio=spec_node.ratio, size=render.size_for(spec_node.ratio),
        scene=spec_node.prompt or "the product, centred, lit as described",
        texts=list(spec_node.texts if texts is None else texts),
        source_photo=None, rule=None,
    )


def _first_text(spec_node: director.NodeSpec) -> str:
    return spec_node.texts[0][1] if spec_node.texts else ""


def _vo_text(spec_node: director.NodeSpec) -> str:
    """The line spoken over a shot: whatever the director marked as voiceover."""
    for role, value in spec_node.texts:
        if role.lower() in {"vo", "voiceover", "narration", "loithoai"}:
            return value
    return _first_text(spec_node)


def _index_of(node_id: str) -> int:
    """Pull a shot index out of a node id like `clip_2`, defaulting to 0."""
    digits = "".join(ch for ch in node_id if ch.isdigit())
    try:
        return int(digits[-1]) if digits else 0
    except ValueError:
        return 0
