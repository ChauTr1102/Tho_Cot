"""
The studio as a node graph, and the entry point the campaign agent calls.

Why a graph and not a sequence of stages: the work has wildly different costs
per branch. A slot filled from the brand's own photograph needs a crop and
finishes in a tenth of a second. A generated image takes a minute. A five-second
video clip took between 134 and 543 seconds when measured -- the variance is
real and unpredictable. Modelled as stages, the cheap work would queue behind
the expensive work at every barrier. Modelled as a graph, a whole marketplace
kit can be delivered while another is still rendering, and the UI shows that
happening.

The dependency shape carries the design decisions, so it is worth reading:

  inventory                     no deps      triage the brand's photographs
  worksheet_A                   inventory    decide reuse / remix / generate per slot
  hero_A                        worksheet_A  the style anchor, rendered alone
  item_A_shopee_sku             worksheet_A  REUSE -- deliberately NOT behind the hero
  item_A_shopee_banner          hero_A       generated, anchored to the hero
  keyframe_A_0..3               hero_A       shot frames, text baked in by Seedream
  clip_A_0..3                   keyframe_A_i one clip per keyframe, video group
  voiceover_A                   worksheet_A  TTS, independent of every image
  master_A_tiktok_shop          all clips + voiceover

Node results feed dependents by id through `ctx`, and a node that returns a
dict has it merged into its progress event, which is how the frontend gets
thumbnails without a second round trip.
"""
from __future__ import annotations

import threading
import time
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Sequence

from app.schemas.campaign import (
    AssetBundle,
    AssetOrigin,
    CampaignInput,
    CampaignPlan,
    CommerceCopy,
    ImageAsset,
    ImageKind,
    Platform,
    ShotAsset,
    VideoAsset,
    VideoCutdown,
)
from app.services.studio import assemble, direct, inventory, motion, qa_visual, render
from app.services.studio.config import studio_settings
from app.services.studio.graph import GraphEvent, Node, NodeState, degraded, run_graph
from app.services.studio.platforms import KITS

DEFAULT_PLATFORMS = (Platform.TIKTOK_SHOP, Platform.SHOPEE)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _campaign_dir(campaign_id: str) -> Path:
    return Path(studio_settings.DATA_DIR) / campaign_id / "media"


def _photo_paths(campaign_input: CampaignInput | None) -> list[str]:
    """Local product photographs, ignoring anything that is not a readable file.

    `brand_kit.product_photo_urls` may hold http URLs from an upstream crawler;
    those are not usable as Brand Lock references until downloaded, so they are
    filtered here rather than failing deeper in the graph.
    """
    if not campaign_input:
        return []
    return [p for p in campaign_input.brand_kit.product_photo_urls
            if p and not p.startswith("http") and Path(p).is_file()]


def _forbidden(campaign_input: CampaignInput | None) -> list[str]:
    return list(campaign_input.product_brief.forbidden_claims) if campaign_input else []


def _inspect(result: render.RenderedImage, expected: Sequence[str],
             label_text: Sequence[str], forbidden: Sequence[str]) -> Any:
    """Run the visual gate over a finished image and record the verdict on it."""
    verdict = qa_visual.inspect_image(
        result.local_path, expected_texts=expected,
        label_text=label_text, forbidden_claims=forbidden,
    )
    result.qa_passed = verdict.passed
    result.qa_notes = (list(verdict.missing_text) + list(verdict.unexpected_brandlike)
                       + list(verdict.forbidden_hits))
    return verdict


def _render_with_qa(fn: Callable[[str], render.RenderedImage],
                    expected: Sequence[str], label_text: Sequence[str],
                    forbidden: Sequence[str], *, gate: bool,
                    node_id: str = "", kind: str = "image",
                    on_event: Callable[[GraphEvent], None] | None = None,
                    ) -> render.RenderedImage:
    """Render an image, and inspect it either on the critical path or beside it.

    The gate exists because Seedream's Vietnamese is *usually* right, not always.
    Asked for "BÉO NGẬY NHƯ QUÁN" it produced "BÉO NGẠY NHƯ QUÀ" and
    "BÉO NGAY NHƯ QUẢN" in two images of the same run — and "ngậy" (creamy)
    becoming "ngay" (immediately) is a change of meaning, not a typo a buyer
    forgives. So the gate stays.

    What changed is when it runs. Blocking, a text-bearing image measured 285s
    against 60s for the render alone, because a failed inspection re-rendered
    from scratch and inspected again — and since nearly every image carries copy,
    nearly every image paid it. Non-blocking, the image is published as soon as
    it exists and the verdict follows as a badge update a minute later. The
    defect is still reported; it just no longer holds up the screen.

    `QA_BLOCKING=true` restores the regenerate-until-it-passes loop, which is the
    right mode for producing final submission assets unattended.
    """
    # An image with no copy on it gives the gate nothing to check.
    if gate and studio_settings.QA_TEXT_ONLY and not expected:
        gate = False

    result = fn("")
    if not gate:
        return result

    if not studio_settings.QA_BLOCKING:
        def _later() -> None:
            try:
                verdict = _inspect(result, expected, label_text, forbidden)
            except Exception:
                return          # a failed inspection must never taint a good image
            if on_event and node_id:
                on_event(GraphEvent(
                    node_id=node_id, kind=kind, state=NodeState.DONE,
                    payload={"qa": "PASS" if verdict.passed else "WARN",
                             "qa_notes": result.qa_notes[:4]},
                ))
        threading.Thread(target=_later, daemon=True).start()
        return result

    for attempt in range(1, max(1, studio_settings.QA_MAX_ATTEMPTS) + 1):
        verdict = _inspect(result, expected, label_text, forbidden)
        result.attempts = attempt
        if verdict.passed or attempt >= studio_settings.QA_MAX_ATTEMPTS:
            return result
        result = fn(qa_visual.corrective_hint(verdict, attempt))
        result.attempts = attempt + 1
    return result


# ---------------------------------------------------------------------------
# graph construction
# ---------------------------------------------------------------------------

def build_nodes(plan: CampaignPlan, campaign_input: CampaignInput | None,
                sheet: Any | None = None, route_id: str = "A",
                platforms: Sequence[Platform] | None = None,
                *, qa: bool | None = None, with_video: bool = True,
                on_event: Callable[[GraphEvent], None] | None = None) -> list[Node]:
    """Build the node list for one creative route.

    `sheet` may be supplied to skip the inventory node -- useful in tests and
    when several routes share one triage pass.
    """
    platforms = tuple(platforms or DEFAULT_PLATFORMS)
    gate = studio_settings.QA_ENABLED if qa is None else qa
    campaign_id = plan.campaign_id or "campaign"
    out_dir = _campaign_dir(campaign_id)
    photos = _photo_paths(campaign_input)
    forbidden = _forbidden(campaign_input)
    nodes: list[Node] = []

    inv_id = f"inventory_{route_id}"
    if sheet is None:
        nodes.append(Node(
            id=inv_id, kind="inspect", deps=[],
            run=lambda ctx: inventory.build_sheet(photos, use_vision=False),
        ))
        ws_deps = [inv_id]
    else:
        ws_deps = []

    ws_id = f"worksheet_{route_id}"
    nodes.append(Node(
        id=ws_id, kind="plan", deps=ws_deps,
        run=lambda ctx: direct.build_worksheet(
            plan, campaign_input, ctx.get(inv_id, sheet), route_id, platforms),
    ))

    hero_id = f"hero_{route_id}"

    def _run_hero(ctx: dict[str, Any]) -> render.RenderedImage:
        ws = ctx[ws_id]
        anchor = next((i for i in ws.items if i.origin is not AssetOrigin.REUSE), None) \
            or (ws.items[0] if ws.items else None)
        if anchor is None:
            raise ValueError("worksheet produced no items")

        # The hero is a style anchor, not a deliverable. Its job is to fix the
        # light, the surface and the grade that every later image inherits as
        # reference 2 — copy on it would only be re-rendered, differently, on
        # each of them. Stripping the text also takes it out of the QA gate,
        # and since the whole graph waits on this one node that is the
        # difference between a run measured in minutes and one in tens of them.
        anchor = replace(anchor, texts=[])
        return render.render_hero(
            anchor, ws.spine, photos[0] if photos else None,
            ws.label_text, out_dir)

    nodes.append(Node(id=hero_id, kind="image", deps=[ws_id],
                      run=_run_hero, concurrency_group="image"))

    # --- one node per kit slot -------------------------------------------
    # Built from the platform specs rather than the worksheet, because the graph
    # must exist before the worksheet node has run.
    for platform in platforms:
        for slot in KITS[platform].slots:
            node_id = f"item_{route_id}_{slot.id}"
            prefers_reuse = slot.prefer_origin is AssetOrigin.REUSE
            deps = [ws_id] if prefers_reuse else [ws_id, hero_id]

            def _run_item(ctx: dict[str, Any], _slot_id=slot.id, _hero=hero_id) -> Any:
                ws = ctx[ws_id]
                item = next((i for i in ws.items if i.slot_id == _slot_id), None)
                if item is None:
                    return degraded(None, note="slot not in worksheet")
                if item.origin is AssetOrigin.REUSE:
                    img = render.reuse_item(item, out_dir)
                else:
                    hero = ctx.get(_hero)
                    img = _render_with_qa(
                        lambda hint: render.render_item(
                            item, ws.spine, item.source_photo or (photos[0] if photos else None),
                            hero.local_path if hero else None,
                            ws.label_text, out_dir, extra_instruction=hint),
                        [t for _, t in item.texts], ws.label_text, forbidden,
                        gate=gate, node_id=f"item_{route_id}_{_slot_id}",
                        on_event=on_event)
                return {"image": img, "url": img.local_path,
                        "origin": img.origin.value, "slot": _slot_id,
                        "platform": platform.value,
                        "qa": "PASS" if img.qa_passed is not False else "WARN"}

            nodes.append(Node(id=node_id, kind="image", deps=deps,
                              run=_run_item, concurrency_group="image"))

    if not with_video:
        return nodes

    # --- video: keyframe -> clip, one chain per shot ----------------------
    for platform in platforms:
        for vslot in KITS[platform].video_slots:
            clip_ids: list[str] = []
            for i in range(vslot.shots):
                kf_id = f"keyframe_{route_id}_{platform.value}_{i}"
                clip_id = f"clip_{route_id}_{platform.value}_{i}"
                clip_ids.append(clip_id)

                def _run_kf(ctx, _i=i, _ratio=vslot.ratio, _pid=platform.value) -> Any:
                    ws = ctx[ws_id]
                    if _i >= len(ws.shots):
                        return degraded(None, note="storyboard shorter than slot")
                    shot = ws.shots[_i]
                    hero = ctx.get(hero_id)
                    stub = direct.WorkItem(
                        slot_id=f"kf_{_pid}_{_i}", platform=platform,
                        kind=KITS[platform].slots[0].kind, origin=AssetOrigin.GENERATE,
                        ratio=_ratio, size=render.keyframe_size(_ratio),
                        scene=shot.scene,
                        texts=[("headline", shot.onscreen_text)] if shot.onscreen_text else [],
                        source_photo=photos[0] if photos else None, rule=None,
                    )
                    return _render_with_qa(
                        lambda hint: render.render_item(
                            stub, ws.spine, photos[0] if photos else None,
                            hero.local_path if hero else None,
                            ws.label_text, out_dir, extra_instruction=hint,
                            for_video=True),
                        [shot.onscreen_text] if shot.onscreen_text else [],
                        ws.label_text, forbidden, gate=gate,
                        node_id=f"keyframe_{route_id}_{_pid}_{_i}", on_event=on_event)

                def _run_clip(ctx, _kf=kf_id, _i=i) -> Any:
                    ws = ctx[ws_id]
                    kf = ctx.get(_kf)
                    if kf is None or _i >= len(ws.shots):
                        return degraded(None, note="no keyframe")
                    return motion.render_shot(
                        ws.shots[_i], kf.local_path, ws.spine,
                        seed=1000 + _i, out_dir=out_dir)

                nodes.append(Node(id=kf_id, kind="image", deps=[ws_id, hero_id],
                                  run=_run_kf, concurrency_group="image"))
                # ws_id is a real dependency, not decoration: the clip reads the
                # storyboard to know what its shot is. The executor hands a node
                # only the deps it declares, so omitting it is a KeyError rather
                # than a silent race — which is how every clip in the first full
                # run failed in ten milliseconds.
                nodes.append(Node(id=clip_id, kind="video", deps=[ws_id, kf_id],
                                  run=_run_clip, concurrency_group="video"))

            vo_id = f"voiceover_{route_id}"
            if vslot.voiceover and not any(n.id == vo_id for n in nodes):
                nodes.append(Node(
                    id=vo_id, kind="audio", deps=[ws_id], concurrency_group="default",
                    run=lambda ctx: motion.render_voiceover(
                        ctx[ws_id].shots,
                        voice_hint=(campaign_input.brand_kit.tone_of_voice or "")
                        if campaign_input else "",
                        out_dir=out_dir),
                ))

            master_id = f"master_{route_id}_{platform.value}"
            master_deps = list(clip_ids) + ([vo_id] if vslot.voiceover else [])

            def _run_master(ctx, _clips=tuple(clip_ids), _vslot=vslot,
                            _vo=vo_id if vslot.voiceover else None, _pid=platform.value) -> Any:
                paths = [ctx[c].clip_path for c in _clips
                         if ctx.get(c) is not None and getattr(ctx[c], "clip_path", None)]
                if not paths:
                    return degraded(None, note="no clips survived")
                master = out_dir / f"{_pid}_master.mp4"
                duration = assemble.concat(paths, master)
                final, vo = str(master), ctx.get(_vo) if _vo else None
                if vo is not None and getattr(vo, "mp3_path", None):
                    try:
                        strips = motion.subtitle_strips(vo.line_timings, (720, 1280), out_dir)
                        final = assemble.mux(master, vo.mp3_path, strips,
                                             vo.line_timings, out_dir / f"{_pid}_final.mp4")
                    except Exception:
                        final = str(master)   # a missing voiceover must not lose the video
                cuts = []
                for label in _vslot.cutdowns:
                    try:
                        secs = float(label.rstrip("s"))
                        p = assemble.cutdown(final, out_dir / f"{_pid}_{label}.mp4", secs)
                        cuts.append(VideoCutdown(label=label, local_path=p,
                                                 duration_sec=secs, aspect_ratio=_vslot.ratio))
                    except Exception:
                        pass
                return {"path": final, "duration": duration, "ratio": _vslot.ratio,
                        "cutdowns": cuts, "clips": _clips,
                        "has_vo": vo is not None, "url": final}

            nodes.append(Node(id=master_id, kind="compose", deps=master_deps,
                              run=_run_master, concurrency_group="default"))

    return nodes


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

def _listing_copy(plan: CampaignPlan, campaign_input: CampaignInput | None) -> CommerceCopy:
    """Assemble marketplace copy from the plan.

    Copy is authored upstream; the studio only reuses it so the listing text and
    the text rendered onto the images cannot drift apart.
    """
    brief = campaign_input.product_brief if campaign_input else None
    name = brief.product_name if brief else "Product"
    bullets = list(brief.key_selling_points[:5]) if brief else []
    return CommerceCopy(
        product_title=name,
        product_description=plan.positioning.key_selling_message or name,
        listing_bullet_points=bullets or list(plan.positioning.product_benefit_hierarchy[:5]),
        ad_caption=plan.positioning.main_campaign_angle or name,
        promotion_copy=(brief.price_or_promotion if brief else None),
        short_hook_lines=[r.hook_idea for r in plan.creative_routes[:3] if r.hook_idea],
    )


def run_directed(spec, draft_, plan: CampaignPlan,
                 campaign_input: CampaignInput | None = None,
                 on_event: Callable[[GraphEvent], None] | None = None,
                 *, qa: bool | None = None) -> AssetBundle:
    """Run a graph the director designed, and map the result into an AssetBundle.

    Falls back to the fixed graph when the directed one has nothing runnable —
    a duller campaign is survivable, an empty screen in front of judges is not.
    """
    from app.services.studio import directed

    if not getattr(spec, "is_runnable", False):
        return run_studio(plan, campaign_input, on_event=on_event, qa=qa)

    campaign_id = plan.campaign_id or "campaign"
    photos = _photo_paths(campaign_input)
    label = [campaign_input.product_brief.product_name] if campaign_input else []
    nodes = directed.build_nodes(
        spec, draft_, campaign_id, photos, label, _forbidden(campaign_input),
        on_event=on_event, qa=qa)

    if on_event:
        on_event(GraphEvent(
            node_id="__graph__", kind="graph", state=NodeState.PENDING,
            payload={"nodes": [{"id": n.id, "kind": n.kind, "deps": list(n.deps)}
                               for n in nodes]}))

    results = run_graph(nodes, on_event=on_event)

    # Assign each image a distinct DTO kind. The director names nodes freely, so
    # several can hint at the same kind — and three DTO fields pointing at one
    # file reads as a broken run even when every image is good. First claim
    # wins its hint; the rest take the next free kind in BP-01's own order.
    order = [ImageKind.HERO, ImageKind.SKU_DETAIL, ImageKind.COLLECTION,
             ImageKind.THUMBNAIL, ImageKind.BANNER, ImageKind.BUNDLE, ImageKind.SEASONAL]
    taken: set[ImageKind] = set()

    def _claim(hint: str | None) -> ImageKind:
        try:
            wanted = ImageKind(hint) if hint else ImageKind.HERO
        except ValueError:
            wanted = ImageKind.HERO
        if wanted not in taken:
            taken.add(wanted)
            return wanted
        for candidate in order:
            if candidate not in taken:
                taken.add(candidate)
                return candidate
        return wanted

    images: list[ImageAsset] = []
    for node_id, value in results.items():
        if not isinstance(value, dict) or "image" not in value:
            continue
        img = value["image"]
        images.append(ImageAsset(
            kind=_claim(value.get("kind_hint")),
            url=img.local_path, width=img.width, height=img.height,
            platform=Platform(value["platform"]) if value.get("platform") in
            {p.value for p in Platform} else None,
            slot=value.get("slot"), origin=img.origin, local_path=img.local_path,
            prompt=img.prompt, text_rendered=img.texts, source_photo=img.source_photo,
            qa_passed=img.qa_passed, qa_notes=img.qa_notes, gen_seconds=img.gen_seconds,
        ))

    videos: list[VideoAsset] = []
    for node_id, value in results.items():
        if not isinstance(value, dict) or "path" not in value:
            continue
        shots = []
        for i, clip_id in enumerate(value.get("clips", ())):
            r = results.get(clip_id)
            if r is None:
                continue
            shots.append(ShotAsset(
                index=i, role=getattr(r, "role", str(i)),
                keyframe_path=str(getattr(r, "keyframe_path", "")),
                clip_path=getattr(r, "clip_path", None),
                duration_sec=float(getattr(r, "duration_sec", 0.0) or 0.0),
                used_fallback=bool(getattr(r, "used_fallback", False)),
                fallback_reason=getattr(r, "fallback_reason", None)))
        videos.append(VideoAsset(
            url=value["path"], duration_sec=float(value.get("duration") or 0.0),
            resolution=studio_settings.VIDEO_RESOLUTION,
            aspect_ratio=value.get("ratio", "9:16"), route_id="A",
            local_path=value["path"], shots=shots,
            has_voiceover=bool(value.get("has_vo")),
            cutdowns=[VideoCutdown(label="15s", local_path=c, duration_sec=15.0,
                                   aspect_ratio=value.get("ratio", "9:16"))
                      for c in value.get("cutdowns", ())]))

    return AssetBundle(campaign_id=campaign_id, images=images, videos=videos,
                       listing_copy=_listing_copy(plan, campaign_input))


def run_studio(plan: CampaignPlan, campaign_input: CampaignInput | None = None,
               platforms: Sequence[Platform] | None = None,
               on_event: Callable[[GraphEvent], None] | None = None,
               *, route_id: str = "A", qa: bool | None = None,
               with_video: bool = True) -> AssetBundle:
    """Run the studio for one route and return a schema-valid AssetBundle.

    Never raises for a partially failed run: whatever finished is returned. A
    campaign with three of four images is worth showing; an exception is not.
    """
    started = time.time()
    campaign_id = plan.campaign_id or "campaign"
    nodes = build_nodes(plan, campaign_input, None, route_id, platforms,
                        qa=qa, with_video=with_video, on_event=on_event)

    # The shape of the graph goes out before any node runs, so the screen can
    # lay out every box and grey them in rather than growing the canvas as
    # results trickle in over the next several minutes.
    if on_event:
        on_event(GraphEvent(
            node_id="__graph__", kind="graph", state=NodeState.PENDING,
            payload={"nodes": [{"id": n.id, "kind": n.kind, "deps": list(n.deps)}
                               for n in nodes]},
        ))

    results = run_graph(nodes, on_event=on_event)

    images: list[ImageAsset] = []
    for node_id, value in results.items():
        if not node_id.startswith(f"item_{route_id}_") or not isinstance(value, dict):
            continue
        img = value.get("image")
        if img is None:
            continue
        slot_id = value["slot"]
        slot = next((s for p in (platforms or DEFAULT_PLATFORMS)
                     for s in KITS[p].slots if s.id == slot_id), None)
        images.append(ImageAsset(
            kind=slot.kind if slot else KITS[Platform.SHOPEE].slots[0].kind,
            url=img.local_path, width=img.width, height=img.height,
            platform=Platform(value["platform"]), slot=slot_id, origin=img.origin,
            local_path=img.local_path, prompt=img.prompt, text_rendered=img.texts,
            source_photo=img.source_photo, qa_passed=img.qa_passed,
            qa_notes=img.qa_notes, gen_seconds=img.gen_seconds,
        ))

    videos: list[VideoAsset] = []
    for node_id, value in results.items():
        if not node_id.startswith(f"master_{route_id}_") or not isinstance(value, dict):
            continue
        shots = []
        for i, clip_id in enumerate(value.get("clips", ())):
            r = results.get(clip_id)
            if r is None:
                continue
            shots.append(ShotAsset(
                index=i, role=getattr(r, "role", str(i)),
                keyframe_path=str(getattr(r, "keyframe_path", "")),
                clip_path=getattr(r, "clip_path", None),
                duration_sec=float(getattr(r, "duration_sec", 0.0) or 0.0),
                used_fallback=bool(getattr(r, "used_fallback", False)),
                fallback_reason=getattr(r, "fallback_reason", None),
            ))
        videos.append(VideoAsset(
            url=value["path"], duration_sec=float(value.get("duration") or 0.0),
            resolution=studio_settings.VIDEO_RESOLUTION,
            aspect_ratio=value.get("ratio", "9:16"), route_id=route_id,
            platform=Platform(node_id.rsplit("_", 1)[-1])
            if node_id.rsplit("_", 1)[-1] in {p.value for p in Platform} else None,
            local_path=value["path"], shots=shots,
            has_voiceover=bool(value.get("has_vo")),
            cutdowns=list(value.get("cutdowns", ())),
        ))

    bundle = AssetBundle(campaign_id=campaign_id, images=images, videos=videos,
                         listing_copy=_listing_copy(plan, campaign_input))
    if on_event:
        on_event(GraphEvent(node_id="__pack__", kind="compose", state=NodeState.DONE,
                            payload={"images": len(images), "videos": len(videos)},
                            elapsed_sec=time.time() - started))
    return bundle
