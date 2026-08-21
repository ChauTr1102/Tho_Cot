"""
Asset Studio HTTP surface.

Three endpoints, and the shape of them is dictated by one measured fact: a run
takes six to twelve minutes. A request/response call would time out, and a
spinner for ten minutes is indistinguishable from a hang. So the run is started
in the background and its progress is streamed:

    POST /api/studio/run           -> {campaign_id}, immediately
    GET  /api/studio/{id}/events   -> server-sent events, one per node transition
    GET  /api/studio/{id}/pack     -> the finished AssetBundle

The event stream is also the demo. Watching reuse nodes finish in milliseconds
while video nodes grind for minutes is what makes the studio's central idea —
real photography where a shopper inspects the product, generated imagery where
they are scrolling — visible without anyone explaining it.

Generated files live under `studio_settings.DATA_DIR` and are served from
`/media`, so every path leaving this module is rewritten to a URL the browser
can fetch.
"""
from __future__ import annotations

import json
import queue
import threading
import time
import uuid
from dataclasses import is_dataclass
from pathlib import Path
from typing import Any, Iterator

from fastapi import APIRouter, File, Form, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError

from app.core.exceptions import BadRequestException, NotFoundException
from app.schemas.studio import AssetBundle, CommerceCopy, Platform
from app.schemas.campaign_dto import (
    CampaignInputDTO,
    ProductCollectionImageSet,
    ShortFormVideoAsset,
)
from app.schemas.common import StandardResponse
from app.services.studio import (
    demo_briefs, directed, director, dto_bridge, from_research, pack, pipeline,
    saved, upstream,
)
from app.services.studio.config import studio_settings
from app.services.studio.graph import GraphEvent

router = APIRouter()

# One entry per run. Bounded in practice by how many campaigns a demo starts;
# a real deployment would move this to the campaign store.
_RUNS: dict[str, "Run"] = {}
_LOCK = threading.Lock()

_SENTINEL = object()


class StudioRunRequest(BaseModel):
    """What the studio screen sends. Deliberately tiny: the brief is assembled
    server-side from `sample_data/<brand_dir>/`, so the client never has to
    know the campaign schema."""
    brand_dir: str = Field(..., description="Directory under sample_data/, e.g. 02_oatside_barista")
    platforms: list[Platform] = Field(default_factory=lambda: [Platform.TIKTOK_SHOP, Platform.SHOPEE])
    route_id: str = Field("A", description="Which creative route to render")
    with_video: bool = Field(True, description="False renders images only — much faster")
    qa: bool | None = Field(None, description="Override the visual QA gate")


class StudioRunResponse(BaseModel):
    campaign_id: str


class DraftRequest(BaseModel):
    """Everything needed to propose a campaign.

    The normal path is `campaign_id`: the research stage has already stored the
    brief and the plan on that row, so the studio reads them rather than asking
    for the same facts twice.

    `plan` is the planning agent's output in either the nested research format
    or the flat DTO; `campaign_input` is the team's CampaignInputDTO. Both are
    optional so the demo shortcut can pass `brand_dir` instead, but a real
    caller sends the artefacts it already has.
    """
    campaign_id: str | None = Field(
        None, description="Id của campaign đã research xong — đường đi chính")
    brand_dir: str | None = None
    plan: dict[str, Any] | None = None
    campaign_input: dict[str, Any] | None = None
    direction: str = Field("", description="Điều người dùng muốn: dễ thương, điện ảnh, sale tưng bừng…")
    with_video: bool = True


class DraftResponse(BaseModel):
    campaign_id: str
    draft: dict[str, Any]
    graph: dict[str, Any]


class ApproveRequest(BaseModel):
    """Approve a draft, optionally after editing it in the UI."""
    draft: dict[str, Any] | None = Field(
        None, description="Bản draft đã sửa. Bỏ trống thì dùng bản đã đề xuất.")
    with_video: bool = True
    qa: bool | None = None


class AssetDTOResponse(BaseModel):
    """The studio's slice of `CampaignOutputDTO`.

    Both asset fields are nullable on purpose: the caller is told a field is not
    ready rather than handed a placeholder that would type-check and fail the
    brief."""
    campaign_id: str
    status: str
    #: The A/B posters by route id — `{"A": "/media/…", "B": "/media/…"}`.
    #: Empty for a run made before the studio rendered a poster per route.
    ab_variants: dict[str, str] = Field(default_factory=dict)
    product_collection_image_set: ProductCollectionImageSet | None = None
    short_form_video_asset: ShortFormVideoAsset | None = None
    commerce_copy: CommerceCopy | None = None


def _json_object(value: str, field_name: str) -> dict[str, Any]:
    """Parse a multipart form field that is meant to carry a JSON object."""
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise BadRequestException(f"Trường {field_name} phải là JSON object hợp lệ") from exc
    if not isinstance(parsed, dict):
        raise BadRequestException(f"Trường {field_name} phải là JSON object")
    return parsed


class Run:
    """One in-flight or finished studio run, plus its event backlog.

    New subscribers replay the backlog before receiving live events, so a page
    refresh three minutes into a run does not show an empty canvas.
    """

    def __init__(self, campaign_id: str) -> None:
        self.campaign_id = campaign_id
        self.backlog: list[dict[str, Any]] = []
        self.subscribers: list[queue.Queue] = []
        self.bundle: AssetBundle | None = None
        self.status = "running"
        self.error: str | None = None
        self.started_at = time.time()
        self._lock = threading.Lock()

    def publish(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self.backlog.append(payload)
            subscribers = list(self.subscribers)
        for q in subscribers:
            q.put(payload)

    def subscribe(self) -> queue.Queue:
        q: queue.Queue = queue.Queue()
        with self._lock:
            for payload in self.backlog:
                q.put(payload)
            if self.status != "running":
                q.put(_SENTINEL)
            self.subscribers.append(q)
        return q

    def finish(self, bundle: AssetBundle | None, error: str | None = None) -> None:
        with self._lock:
            self.bundle, self.error = bundle, error
            self.status = "failed" if error else "done"
            subscribers = list(self.subscribers)
        for q in subscribers:
            q.put(_SENTINEL)


def _to_url(value: Any) -> Any:
    """Rewrite a generated file path into a `/media/...` URL.

    Anything outside DATA_DIR is returned untouched — a source photograph reused
    straight from `sample_data/` is served by a different mount.
    """
    if not isinstance(value, str) or not value:
        return value
    try:
        rel = Path(value).resolve().relative_to(Path(studio_settings.DATA_DIR).resolve())
    except (ValueError, OSError):
        return value
    return f"/media/{rel.as_posix()}"


def _event_payload(event: GraphEvent) -> dict[str, Any]:
    """Translate a GraphEvent into the JSON shape the studio screen consumes."""
    if event.kind == "graph":
        return {"event": "graph", "nodes": event.payload.get("nodes", [])}

    payload: dict[str, Any] = {}
    for key, raw in (event.payload or {}).items():
        # The objects themselves never cross the wire — only the paths and text
        # pulled out of them. A node that returns an object and nothing else
        # arrives as an empty payload, which is how five of twelve nodes ended
        # up with no preview.
        if is_dataclass(raw) or key in {"image", "hero", "keyframe", "shot"}:
            continue
        payload[key] = _to_url(raw) if key in {"url", "path"} else raw

    return {
        "event": "node",
        "node_id": event.node_id,
        "kind": event.kind,
        "state": getattr(event.state, "value", str(event.state)),
        "elapsed_sec": round(float(event.elapsed_sec or 0.0), 2),
        "payload": payload,
    }


def _run_prepared(run: Run, plan, campaign_input, req: StudioRunRequest) -> None:
    """Run the studio against a brief that has already been assembled."""
    try:
        bundle = pipeline.run_studio(
            plan, campaign_input, platforms=req.platforms,
            on_event=lambda e: run.publish(_event_payload(e)),
            route_id=req.route_id, qa=req.qa, with_video=req.with_video,
        )
        run.finish(bundle)
    except Exception as exc:                                    # noqa: BLE001
        run.publish({"event": "error", "message": f"{type(exc).__name__}: {exc}"})
        run.finish(None, error=str(exc))


def _run_in_background(run: Run, req: StudioRunRequest) -> None:
    try:
        plan, campaign_input = demo_briefs.build_pair(req.brand_dir, run.campaign_id)
        bundle = pipeline.run_studio(
            plan, campaign_input, platforms=req.platforms,
            on_event=lambda e: run.publish(_event_payload(e)),
            route_id=req.route_id, qa=req.qa, with_video=req.with_video,
        )
        run.finish(bundle)
    except Exception as exc:                                    # noqa: BLE001
        # A failed run must still terminate its stream; a browser waiting
        # forever on a dead run is worse than a visible error.
        run.publish({"event": "error", "message": f"{type(exc).__name__}: {exc}"})
        run.finish(None, error=str(exc))


@router.post("/run", response_model=StandardResponse[StudioRunResponse],
             status_code=status.HTTP_202_ACCEPTED)
def start_run(payload: StudioRunRequest):
    """Start a studio run and return its id immediately.

    Returns 202, not 201: nothing has been created yet. The work happens on a
    background thread and is watched through `/events`.
    """
    if payload.brand_dir not in demo_briefs.available_brands():
        raise NotFoundException(message=f"Không có brand '{payload.brand_dir}' trong sample_data.")

    campaign_id = f"{payload.brand_dir}-{uuid.uuid4().hex[:8]}"
    run = Run(campaign_id)
    with _LOCK:
        _RUNS[campaign_id] = run

    threading.Thread(target=_run_in_background, args=(run, payload), daemon=True).start()

    return StandardResponse(
        success=True, message="Đã bắt đầu tạo bộ kit",
        data=StudioRunResponse(campaign_id=campaign_id),
    )


@router.get("/{campaign_id}/events")
def stream_events(campaign_id: str):
    """Server-sent events for one run: `graph` once, then `node` per transition, then `done`."""
    run = _RUNS.get(campaign_id)
    if run is None:
        raise NotFoundException(message=f"Không tìm thấy lượt chạy '{campaign_id}'.")

    def generate() -> Iterator[str]:
        q = run.subscribe()
        yield ": connected\n\n"          # flush headers past any proxy buffer
        while True:
            try:
                item = q.get(timeout=15)
            except queue.Empty:
                yield ": keepalive\n\n"  # a video node can be silent for minutes
                continue
            if item is _SENTINEL:
                break
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
        done = {"event": "done", "campaign_id": campaign_id,
                "status": run.status, "elapsed_sec": round(time.time() - run.started_at, 1)}
        yield f"data: {json.dumps(done, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive",
                 "X-Accel-Buffering": "no"},
    )


@router.get("/{campaign_id}/pack", response_model=StandardResponse[AssetBundle])
def get_pack(campaign_id: str):
    """The finished AssetBundle, with every local path rewritten to a `/media` URL."""
    run = _RUNS.get(campaign_id)
    if run is None:
        raise NotFoundException(message=f"Không tìm thấy lượt chạy '{campaign_id}'.")
    if run.bundle is None:
        raise NotFoundException(
            message=f"Lượt chạy '{campaign_id}' chưa xong (trạng thái: {run.status})."
        )

    bundle = run.bundle.model_copy(deep=True)
    for image in bundle.images:
        image.url = _to_url(image.local_path or image.url)
    for video in bundle.videos:
        video.url = _to_url(video.local_path or video.url)
        for cut in video.cutdowns:
            cut.local_path = _to_url(cut.local_path)
        for shot in video.shots:
            shot.keyframe_path = _to_url(shot.keyframe_path)
            if shot.clip_path:
                shot.clip_path = _to_url(shot.clip_path)

    return StandardResponse(success=True, message="Bộ kit đã sẵn sàng", data=bundle)


@router.post("/assets", response_model=StandardResponse[StudioRunResponse],
             status_code=status.HTTP_202_ACCEPTED)
async def generate_assets(
    campaign_input: str = Form(..., description="CampaignInputDTO as a JSON object"),
    plan: str | None = Form(None, description="Planning-agent output as JSON; optional"),
    product_photos: list[UploadFile] = File(default_factory=list),
    platforms: str = Form("tiktok_shop,shopee", description="Comma-separated platform keys"),
    route_id: str = Form("A"),
    want: str = Form("both", description="images | video | both"),
):
    """Generate the asset half of a campaign from whatever the upstream stage produced.

    This is the studio's real entry point. `/run` above is a demo shortcut that
    fills a brief from `sample_data/`; this one accepts the actual artefacts —
    the team's `CampaignInputDTO`, the planning agent's output, and the brand's
    product photographs as uploaded files — which is what a downstream stage has
    to work with.

    Returns 202 and a `campaign_id` immediately. A run takes minutes, so progress
    is watched on `/studio/{id}/events` and the result collected from
    `/studio/{id}/assets`, which answers in the DTO shapes the caller assembles
    its `CampaignOutputDTO` from.

    `want=images` skips video generation entirely, which takes a run from
    minutes to well under one — worth it while iterating on art direction.
    """
    try:
        input_dto = CampaignInputDTO.model_validate(_json_object(campaign_input, "campaign_input"))
    except ValidationError as exc:
        raise BadRequestException(f"campaign_input không khớp CampaignInputDTO: {exc.errors()[:3]}")

    plan_raw = _json_object(plan, "plan") if plan else {}
    campaign_id = f"assets-{uuid.uuid4().hex[:10]}"

    # Uploaded photographs are the Brand Lock reference, so they have to land on
    # disk before the graph starts — the studio reads them as files, not bytes.
    photo_dir = Path(studio_settings.DATA_DIR) / campaign_id / "source"
    photo_dir.mkdir(parents=True, exist_ok=True)
    stored: list[str] = []
    for index, upload in enumerate(product_photos):
        name = Path(upload.filename or f"product_{index}").name
        target = photo_dir / f"{index:02d}_{name}"
        target.write_bytes(await upload.read())
        stored.append(str(target))

    try:
        studio_input = dto_bridge.to_campaign_input(input_dto, campaign_id, stored or None)
        studio_plan = dto_bridge.plan_from_positioning(plan_raw, campaign_id, studio_input)
    except (ValueError, KeyError) as exc:
        raise BadRequestException(f"Không dựng được brief cho studio: {exc}")

    wanted = [Platform(p.strip()) for p in platforms.split(",")
              if p.strip() in {x.value for x in Platform}]
    run = Run(campaign_id)
    with _LOCK:
        _RUNS[campaign_id] = run

    request = StudioRunRequest(
        brand_dir="", platforms=wanted or [Platform.TIKTOK_SHOP],
        route_id=route_id, with_video=want in {"video", "both"},
    )
    threading.Thread(
        target=_run_prepared, args=(run, studio_plan, studio_input, request), daemon=True
    ).start()

    return StandardResponse(
        success=True,
        message=f"Đang dựng asset cho {input_dto.product_brief.product_name}",
        data=StudioRunResponse(campaign_id=campaign_id),
    )


@router.get("/{campaign_id}/assets", response_model=StandardResponse[AssetDTOResponse])
def get_assets(campaign_id: str):
    """The finished assets, in the DTO shapes `CampaignOutputDTO` is assembled from.

    `product_collection_image_set` is null until all four required images exist,
    and `short_form_video_asset` is null until a video does — a half-filled
    object would satisfy the type while failing the brief, so the caller is told
    plainly that the field is not ready rather than handed a placeholder.
    """
    run = _RUNS.get(campaign_id)

    # `_RUNS` is process-local, so it answers only while the process that did
    # the rendering is still alive. Restart the backend, or open a campaign
    # built in an earlier session, and this used to 404 — at which point the
    # pipeline's final report and QA gate fell back to mock URLs pointing at
    # example.com. The files never went anywhere; only the dict did. So when
    # memory has nothing, read the kit off disk.
    if run is None or run.bundle is None:
        from_disk = saved.to_dto(campaign_id)
        if from_disk["status"] == "empty":
            if run is None:
                raise NotFoundException(
                    message=f"Không tìm thấy lượt chạy '{campaign_id}'.")
            raise NotFoundException(
                message=f"Lượt chạy '{campaign_id}' chưa xong (trạng thái: {run.status}).")
        return StandardResponse(
            success=True,
            message="Asset đọc lại từ đĩa",
            data=AssetDTOResponse(
                campaign_id=campaign_id,
                status="done",
                ab_variants=from_disk["ab_variants"],
                product_collection_image_set=from_disk["product_collection_image_set"],
                short_form_video_asset=from_disk["short_form_video_asset"],
                # Copy lives on the bundle, which memory no longer has. Null is
                # the honest answer; the final report keeps the plan-derived
                # copy it already had rather than being handed an invention.
                commerce_copy=None,
            ),
        )

    return StandardResponse(
        success=True, message="Asset đã sẵn sàng",
        data=AssetDTOResponse(
            campaign_id=campaign_id,
            status=run.status,
            ab_variants=saved.ab_pair(campaign_id),
            product_collection_image_set=dto_bridge.to_image_set(run.bundle, _to_url),
            short_form_video_asset=dto_bridge.to_video_asset(run.bundle, _to_url),
            commerce_copy=run.bundle.listing_copy,
        ),
    )


# Drafts awaiting approval. Separate from _RUNS because a draft exists before
# any work does, and a user may sit on the approve screen for a while.
_DRAFTS: dict[str, dict[str, Any]] = {}

# What the caller should be told about a research handoff: photographs that
# could not be found on disk, marketplaces with no kit. Both are survivable and
# both are worth surfacing rather than discovering in the output.
_NOTES: dict[str, dict[str, Any]] = {}


def _resolve_brief(req: DraftRequest, campaign_id: str):
    """Assemble (plan, campaign_input) from whatever the caller sent.

    Four ways in, in order of how real they are: a finished research campaign,
    an explicit DTO, a plan plus a demo brand, or a demo brand alone.
    """
    if req.campaign_id:
        try:
            plan, studio_input, notes = from_research.load_pair(req.campaign_id)
        except FileNotFoundError as exc:
            raise BadRequestException(str(exc))
        except KeyError:
            raise NotFoundException(
                message=f"Không có campaign '{req.campaign_id}' trong database.")
        except from_research.ResearchNotReady as exc:
            raise BadRequestException(str(exc))
        _NOTES[campaign_id] = notes
        return plan, studio_input

    if req.campaign_input:
        try:
            dto = CampaignInputDTO.model_validate(req.campaign_input)
        except ValidationError as exc:
            raise BadRequestException(f"campaign_input không khớp DTO: {exc.errors()[:2]}")
        studio_input = dto_bridge.to_campaign_input(dto, campaign_id, None)
        studio_plan = dto_bridge.plan_from_positioning(req.plan or {}, campaign_id, studio_input)
        return studio_plan, studio_input

    if req.plan and req.brand_dir:
        studio_input = demo_briefs.build_input(req.brand_dir, campaign_id)
        return upstream.load_plan(req.plan, campaign_id), studio_input

    if req.brand_dir:
        if req.brand_dir not in demo_briefs.available_brands():
            raise NotFoundException(message=f"Không có brand '{req.brand_dir}'.")
        return demo_briefs.build_pair(req.brand_dir, campaign_id)

    raise BadRequestException("Cần campaign_input hoặc brand_dir.")


@router.post("/draft", response_model=StandardResponse[DraftResponse],
             status_code=status.HTTP_200_OK)
def propose(req: DraftRequest):
    """Ask the director what this campaign should be, and show it for approval.

    This is the slow step by design — the model bills by output length and takes
    around a minute — but it lands while the user is about to read the proposal
    rather than while they watch an empty screen. Approving then starts
    rendering immediately, because the graph is derived in code.
    """
    campaign_id = f"c-{uuid.uuid4().hex[:10]}"
    plan, campaign_input = _resolve_brief(req, campaign_id)

    # The research prose, bounded. The structured plan is already research's own
    # summary of itself, so this is a taste rather than the thirty thousand
    # characters it wrote — enough to ground the art direction in the market the
    # campaign is actually for, and never anywhere near an image prompt.
    handoff_notes = _NOTES.get(campaign_id) or {}
    d = director.draft(plan, campaign_input, direction=req.direction,
                       research=handoff_notes.get("research_digest", ""))
    spec = director.plan_graph(d, plan, campaign_input, with_video=req.with_video)

    _DRAFTS[campaign_id] = {
        "plan": plan, "input": campaign_input, "draft": d,
        "direction": req.direction, "with_video": req.with_video,
    }
    payload = director.draft_to_dict(d)
    handoff = _NOTES.get(campaign_id)
    if handoff:
        # Fold the handoff warnings into the notes the approval screen shows, so
        # a missing photograph is read before approving rather than noticed in
        # the kit afterwards.
        extra = []
        if handoff.get("photos_missing"):
            extra.append("Không tìm thấy ảnh: "
                         + ", ".join(handoff["photos_missing"])
                         + " — những ô cần ảnh thật sẽ phải dựng mới.")
        if handoff.get("platforms_unsupported"):
            unsupported = ", ".join(handoff["platforms_unsupported"])
            orphaned = handoff.get("routes_without_kit") or []
            # Naming the route matters: a marketplace the studio cannot serve is
            # survivable, a creative route left with nowhere to run is a route
            # that silently produces nothing.
            if orphaned:
                extra.append(
                    f"Chưa có kit cho: {unsupported}. Route "
                    + ", ".join(orphaned)
                    + " chỉ nhắm vào những sàn đó nên sẽ không có sản phẩm nào.")
            else:
                extra.append(f"Chưa có kit cho: {unsupported}")
        if handoff.get("preserve_packaging"):
            extra.append("Research yêu cầu giữ nguyên bao bì — mọi ảnh đều "
                         "khoá theo ảnh sản phẩm thật, không vẽ lại nhãn.")
        # Repairs the adapter had to make. Silent repair is how a plan with no
        # A/B block turns into a kit nobody knows is untestable.
        for warning in (handoff.get("warnings") or [])[:3]:
            extra.append(warning)
        payload["notes"] = extra + list(payload.get("notes", []))
        payload["source_campaign"] = handoff.get("name")

    return StandardResponse(
        success=True, message="Đề xuất đã sẵn sàng — xem lại rồi duyệt",
        data=DraftResponse(campaign_id=campaign_id,
                           draft=payload,
                           graph=director.to_dict(spec)),
    )


@router.get("/{campaign_id}/saved", response_model=StandardResponse[dict])
def saved_result(campaign_id: str, include_intermediate: bool = False):
    """The kit this campaign already has on disk, if it has one.

    A run takes six to twelve minutes; a judge has about that long for the whole
    submission. So a campaign that was already built opens as a result rather
    than as a form, and only a campaign nobody has built yet offers to build.
    `built: false` is the signal for the second case — it is an answer, not an
    error, so this returns 200 either way.
    """
    data = saved.summary(campaign_id)
    if include_intermediate:
        data["assets"] = saved.list_assets(campaign_id, include_intermediate=True)
    return StandardResponse(
        success=True,
        message=(
            f"Đã có {data['images']} ảnh · {data['videos']} video"
            if data["built"] else "Chưa dựng lần nào"
        ),
        data=data,
    )


@router.get("/{campaign_id}/qa", response_model=StandardResponse[dict | None])
def get_qa(campaign_id: str):
    """The QA verdict this campaign already has, or null.

    Null means nobody has judged this kit yet, which is an answer rather than an
    error — the screen offers to run it. 200 either way.
    """
    stored = saved.load_qa(campaign_id)
    return StandardResponse(
        success=True,
        message="Đã có kết quả QA" if stored else "Chưa chạy QA lần nào",
        data=stored,
    )


@router.put("/{campaign_id}/qa", response_model=StandardResponse[dict])
def put_qa(campaign_id: str, result: dict[str, Any]):
    """Store a verdict so re-opening the campaign does not re-run it.

    A QA pass costs a model call and a minute, and it is sampled rather than
    deterministic: run it twice on one unchanged kit and the two reports differ
    slightly, which reads as the system being unsure instead of the model being
    sampled. A campaign that has been judged should open with its judgement.
    """
    saved.save_qa(campaign_id, result)
    return StandardResponse(success=True, message="Đã lưu kết quả QA", data=result)


@router.get("/campaigns", response_model=StandardResponse[list[dict]])
def list_research_campaigns():
    """Campaigns the research stage has finished — the studio's inbox.

    Read straight from the campaigns table rather than through the ORM: the
    studio owns no tables and should not take a session dependency to read
    three columns.
    """
    rows = from_research.list_campaigns()
    ready = [r for r in rows if r.get("status") == "researched"]
    return StandardResponse(
        success=True,
        message=f"{len(ready)}/{len(rows)} campaign đã research xong",
        data=rows,
    )


@router.post("/{campaign_id}/approve", response_model=StandardResponse[StudioRunResponse],
             status_code=status.HTTP_202_ACCEPTED)
def approve(campaign_id: str, req: ApproveRequest):
    """Approve a draft and start building it. Returns immediately."""
    held = _DRAFTS.get(campaign_id)
    if held is None:
        raise NotFoundException(message=f"Không tìm thấy đề xuất '{campaign_id}'.")

    d = _apply_edits(held["draft"], req.draft)
    plan, campaign_input = held["plan"], held["input"]
    with_video = req.with_video and held["with_video"]
    spec = director.plan_graph(d, plan, campaign_input, with_video=with_video)

    run = Run(campaign_id)
    with _LOCK:
        _RUNS[campaign_id] = run

    def _go() -> None:
        try:
            bundle = pipeline.run_directed(
                spec, d, plan, campaign_input,
                on_event=lambda e: run.publish(_event_payload(e)), qa=req.qa)
            run.finish(bundle)
        except Exception as exc:                                # noqa: BLE001
            run.publish({"event": "error", "message": f"{type(exc).__name__}: {exc}"})
            run.finish(None, error=str(exc))

    threading.Thread(target=_go, daemon=True).start()
    return StandardResponse(success=True, message="Đã duyệt — bắt đầu dựng",
                            data=StudioRunResponse(campaign_id=campaign_id))


def _apply_edits(original, edited: dict[str, Any] | None):
    """Fold the user's edits into the proposal.

    Only the fields a person can sensibly change are honoured; anything else in
    the payload is ignored rather than trusted, because this body comes from a
    browser.
    """
    if not edited:
        return original
    from dataclasses import replace as _replace

    reg = original.register
    raw_reg = edited.get("register") or {}
    if isinstance(raw_reg, dict):
        reg = _replace(
            reg,
            lens=str(raw_reg.get("lens", reg.lens))[:160],
            light=str(raw_reg.get("light", reg.light))[:300],
            surface=str(raw_reg.get("surface", reg.surface))[:300],
            grade=str(raw_reg.get("grade", reg.grade))[:200],
        )

    deliverables = original.deliverables
    raw_items = edited.get("deliverables")
    if isinstance(raw_items, list) and raw_items:
        keep = {str(x.get("id")) for x in raw_items if isinstance(x, dict)}
        deliverables = [x for x in original.deliverables if x.id in keep] or original.deliverables

    return _replace(
        original, register=reg, deliverables=deliverables,
        video_shots=int(edited.get("video_shots", original.video_shots) or original.video_shots),
        video_seconds=int(edited.get("video_seconds", original.video_seconds) or original.video_seconds),
    )


@router.get("/{campaign_id}/zip")
def download_zip(campaign_id: str):
    """The finished kit as a zip, grouped by marketplace.

    Filenames carry the marketplace, the slot and the shape, because someone
    opens this beside an upload form and has to know which file goes in which
    box without opening any of them. MANIFEST.md inside doubles as BP-01's
    model-usage explanation, generated from what actually ran.
    """
    from fastapi.responses import FileResponse

    run = _RUNS.get(campaign_id)
    target = Path(studio_settings.DATA_DIR) / campaign_id / f"{campaign_id}_kit.zip"

    if run is not None and run.bundle is not None:
        pack.build_zip(run.bundle, target)
        return FileResponse(target, media_type="application/zip", filename=target.name)

    # Same process-local problem as `/assets`: `_RUNS` empties on restart, so
    # "Tải .zip" was a dead button for every campaign a judge opens. The files
    # are still there, so pack them from disk. The manifest is thinner — a
    # bundle carries each image's origin and the text on it, and none of that
    # survives on disk — and says so rather than inventing provenance.
    if saved.build_zip(campaign_id, target):
        return FileResponse(target, media_type="application/zip", filename=target.name)

    if run is None:
        raise NotFoundException(message=f"Không tìm thấy lượt chạy '{campaign_id}'.")
    raise NotFoundException(
        message=f"Lượt chạy '{campaign_id}' chưa xong (trạng thái: {run.status}).")


@router.get("/brands", response_model=StandardResponse[list[dict]])
def list_brands():
    """The demo catalogue, with the photo count that decides how much can be reused."""
    data = [{"dir": d, "photos": len(demo_briefs.product_photos(d))}
            for d in demo_briefs.available_brands()]
    return StandardResponse(success=True, message=f"{len(data)} brand", data=data)
