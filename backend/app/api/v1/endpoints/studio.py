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

from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.exceptions import NotFoundException
from app.schemas.campaign import AssetBundle, Platform
from app.schemas.common import StandardResponse
from app.services.studio import demo_briefs, pipeline
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
        if key == "image" or is_dataclass(raw):
            continue          # the object itself never crosses the wire
        payload[key] = _to_url(raw) if key in {"url", "path"} else raw

    return {
        "event": "node",
        "node_id": event.node_id,
        "kind": event.kind,
        "state": getattr(event.state, "value", str(event.state)),
        "elapsed_sec": round(float(event.elapsed_sec or 0.0), 2),
        "payload": payload,
    }


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


@router.get("/brands", response_model=StandardResponse[list[dict]])
def list_brands():
    """The demo catalogue, with the photo count that decides how much can be reused."""
    data = [{"dir": d, "photos": len(demo_briefs.product_photos(d))}
            for d in demo_briefs.available_brands()]
    return StandardResponse(success=True, message=f"{len(data)} brand", data=data)
