"""
Dependency-graph executor: the scheduler at the centre of the Asset Studio.

The studio's work is a dependency graph, not a sequence of stages, and the
distinction is load-bearing. A Shopee listing image that reuses an existing
brand photo needs a crop and depends on nothing; a generated collection image
depends on a hero render that takes a minute; a video clip takes two to nine
minutes. Modelled as stages, the fast work would sit behind a barrier waiting
for the slow work and the user would stare at a spinner. Modelled as a graph, a
whole marketplace kit finishes in seconds while another route is still
rendering -- and the live canvas shows it happening.

So the rule this module implements is: **a node runs the moment its
dependencies have succeeded and its concurrency group has a free slot.** It
never waits for a "stage".

Three further properties the studio depends on:

* **Failure containment.** A node whose dependency failed is marked FAILED
  without running, transitively, while every unrelated branch runs to
  completion. One dead render must not cost the demo the other platform's kit.
* **Live events.** ``on_event`` fires when a node enters RUNNING and again when
  it reaches a terminal state, from the worker thread, at the instant it
  happens -- never batched at the end. These events are the SSE stream.
* **Caching.** A node with a ``cache_key`` short-circuits on a hit under
  ``DATA_DIR/cache/``. The venue network is unreliable and a full run costs
  6-12 minutes, so a re-run after a crash has to be near-instant.

Threads, not asyncio: the workload is network-bound and ``ark.py`` is
synchronous ``requests``.

This module has no studio dependency except :mod:`config`. It performs no
network calls and knows nothing about images, video or BytePlus -- it only
knows how to run callables in the right order.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
import time
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from app.services.studio.config import studio_settings

logger = logging.getLogger(__name__)

# Fallback cap for a concurrency group nobody configured. Kept here rather than
# in config.py only because config.py is owned by another task; if a
# STUDIO_DEFAULT_CONCURRENCY field is ever added there it wins automatically
# (see _resolve_caps).
DEFAULT_GROUP_CONCURRENCY = 8

# A cache_key becomes a file name. Anything outside this alphabet is hashed
# instead of written verbatim, so a key can never escape the cache directory.
_SAFE_CACHE_KEY = re.compile(r"\A[A-Za-z0-9._-]{1,120}\Z")


class GraphError(Exception):
    """The graph itself is malformed (cycle, unknown dependency, bad cap).

    Raised before any node runs. A node raising during execution is a *node*
    failure and is contained; a GraphError is a programming error in whatever
    built the node list, so it surfaces immediately and loudly.
    """


class NodeState(str, Enum):
    """Lifecycle of a single node.

    The values are the strings the SSE contract sends to the frontend, so they
    are lowercase and must not be renamed.

    PENDING   -- not yet runnable, or waiting for a free slot in its group.
    RUNNING   -- executing (or checking the cache).
    DONE      -- succeeded; its result is available to dependents.
    RETRY     -- an attempt raised and another will follow. Not terminal.
    DEGRADED  -- produced a usable but second-choice result (a Ken Burns move
                 instead of a rendered clip). Counts as success for dependents.
    FAILED    -- exhausted its attempts, or a dependency failed.
    """

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    RETRY = "retry"
    DEGRADED = "degraded"
    FAILED = "failed"


#: States that satisfy a dependency: a degraded node still produced a result.
SUCCESS_STATES = frozenset({NodeState.DONE, NodeState.DEGRADED})
#: States a node never leaves.
TERMINAL_STATES = frozenset({NodeState.DONE, NodeState.DEGRADED, NodeState.FAILED})


@dataclass
class Node:
    """One unit of work in the studio graph.

    Attributes:
        id: Unique within the graph. Also the key its result is stored under
            and the ``node_id`` the frontend renders, so use stable, readable
            ids (``hero_A``, ``clip_A_0``, ``shopee_main``).
        kind: Coarse category for the UI (``image``, ``video``, ``qa``, ...).
            Carried verbatim on every event.
        deps: Ids of nodes that must succeed first. Their results are what this
            node's ``run`` receives.
        run: ``run(ctx) -> Any``. ``ctx`` maps **each declared dependency id**
            to its result -- nothing else. Reading an id you did not declare
            raises KeyError, which is intentional: it makes a missing edge a
            loud bug instead of a race. Return a ``dict`` and its keys are
            merged into the DONE event payload (that is how a node feeds the
            SSE stream). Return ``degraded(value, note)`` to finish DEGRADED.
        concurrency_group: Which cap this node consumes. Groups are capped
            independently, so a saturated ``video`` group never throttles
            ``image``.
        cache_key: When set and caching is enabled, a hit under
            ``DATA_DIR/cache/`` replaces execution entirely. The result must be
            JSON-serialisable to be stored -- cache local paths and metadata,
            never raw bytes.
        max_retries: Extra attempts after the first one raises. Defaults to 0;
            most studio nodes retry inside ``ark.py`` instead.
        retry_delay_sec: Sleep between attempts.
    """

    id: str
    kind: str
    deps: list[str]
    run: Callable[[dict[str, Any]], Any]
    concurrency_group: str = "default"
    cache_key: str | None = None
    max_retries: int = 0
    retry_delay_sec: float = 0.0


@dataclass(frozen=True)
class GraphEvent:
    """A node state change, emitted live.

    Mirrors the SSE ``node`` event one-for-one, so the API layer can forward it
    without reshaping.

    Attributes:
        node_id: The node's id.
        kind: The node's kind.
        state: The state just entered.
        payload: Free-form detail. Graph-supplied keys: ``cached`` on a cache
            hit, ``error``/``error_type``/``attempts`` on failure, ``reason``
            and ``failed_dep`` when a dependency failed, ``note`` when
            degraded, ``attempt`` while retrying. A node returning a dict has
            that dict merged in underneath these keys.
        elapsed_sec: Seconds since the node entered RUNNING the first time.
            0.0 on the RUNNING event and on nodes that never ran.
    """

    node_id: str
    kind: str
    state: NodeState
    payload: dict[str, Any] = field(default_factory=dict)
    elapsed_sec: float = 0.0


@dataclass(frozen=True)
class Degraded:
    """Wrapper marking a result as second-choice. Build it with :func:`degraded`."""

    value: Any
    note: str = ""


def degraded(value: Any, note: str = "") -> Degraded:
    """Finish a node DEGRADED while still handing ``value`` to its dependents.

    For fallbacks that keep the run alive: a clip that missed
    ``VIDEO_SHOT_DEADLINE_SEC`` and became a Ken Burns move over its keyframe is
    degraded, not failed -- the master still gets cut, and the UI can flag it.

    Args:
        value: The result dependents will receive, exactly as if it were DONE.
        note: Short human-readable reason, forwarded in the event payload.

    Returns:
        A :class:`Degraded` wrapper; the executor unwraps it.
    """
    return Degraded(value, note)


def cache_path(cache_key: str) -> Path:
    """Return the on-disk location of a cache entry.

    Well-formed keys map to ``DATA_DIR/cache/{cache_key}.json`` verbatim so the
    cache stays greppable by hand. Keys containing anything else (a path
    separator, ``..``, non-ASCII, or over 120 characters) are slugified and
    suffixed with a hash of the original, which keeps them unique and keeps
    every entry inside the cache directory.

    Args:
        cache_key: The node's ``cache_key``.

    Returns:
        Path to the entry. The file may not exist.
    """
    root = Path(studio_settings.DATA_DIR) / "cache"
    if _SAFE_CACHE_KEY.match(cache_key) and cache_key not in (".", ".."):
        return root / f"{cache_key}.json"
    digest = hashlib.sha1(cache_key.encode("utf-8")).hexdigest()[:10]
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", cache_key)[:100].strip("._-") or "key"
    return root / f"{slug}-{digest}.json"


def run_graph(
    nodes: list[Node],
    on_event: Callable[[GraphEvent], None] | None = None,
    groups: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Execute a node graph, running everything that can run as soon as it can.

    Each node starts the instant its dependencies have succeeded and its
    concurrency group has a free slot -- there are no stage barriers. A node
    that raises is FAILED and its dependents are FAILED transitively without
    running; every other branch continues.

    Args:
        nodes: The graph. Validated up front: duplicate ids, unknown
            dependencies, self-references and cycles all raise before any node
            runs, so a malformed graph fails fast instead of deadlocking.
        on_event: Called on entering RUNNING and on every terminal state
            (plus RETRY). Called from worker threads, but the executor holds a
            lock across the call, so **callbacks are serialised and the
            callback does not need its own lock**. It should still be quick and
            non-blocking (a ``queue.put``): it runs on the thread that just
            finished a node. Exceptions raised by the callback are logged and
            swallowed -- a disconnected SSE client must not abort a six-minute
            render. Pass ``None`` to run silently.
        groups: Per-group concurrency caps, e.g. ``{"image": 8, "video": 4}``.
            These are independent caps, not one shared pool. A group with no
            entry falls back to the ``"default"`` entry, then to
            ``studio_settings`` (``IMAGE_CONCURRENCY``, ``VIDEO_CONCURRENCY``,
            ``VISION_CONCURRENCY``).

    Returns:
        Mapping of node id to result, for successful nodes only (DONE and
        DEGRADED). A failed or skipped node is simply absent -- check
        membership, or track states through ``on_event``.

    Raises:
        GraphError: The graph is malformed or a resolved cap is below 1.
    """
    if not nodes:
        return {}
    _validate(nodes)
    caps = _resolve_caps(nodes, groups)
    return _GraphRun(nodes, on_event, caps).execute()


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------
def _validate(nodes: list[Node]) -> None:
    """Reject a malformed graph before anything runs (see :class:`GraphError`)."""
    by_id: dict[str, Node] = {}
    for node in nodes:
        if not node.id:
            raise GraphError("node id must not be empty")
        if node.id in by_id:
            raise GraphError(f"duplicate node id: {node.id!r}")
        if not callable(node.run):
            raise GraphError(f"node {node.id!r} has a non-callable run")
        if node.max_retries < 0:
            raise GraphError(f"node {node.id!r} has negative max_retries")
        by_id[node.id] = node

    for node in nodes:
        for dep in node.deps:
            if dep == node.id:
                raise GraphError(f"node {node.id!r} depends on itself (cycle)")
            if dep not in by_id:
                raise GraphError(f"node {node.id!r} has unknown dependency {dep!r}")

    # Kahn's algorithm: whatever is left when no node has zero unmet deps is a cycle.
    unmet = {nid: len(set(node.deps)) for nid, node in by_id.items()}
    dependents: dict[str, list[str]] = {nid: [] for nid in by_id}
    for node in nodes:
        for dep in set(node.deps):
            dependents[dep].append(node.id)

    ready = [nid for nid, count in unmet.items() if count == 0]
    settled = 0
    while ready:
        nid = ready.pop()
        settled += 1
        for child in dependents[nid]:
            unmet[child] -= 1
            if unmet[child] == 0:
                ready.append(child)
    if settled != len(by_id):
        stuck = sorted(nid for nid, count in unmet.items() if count > 0)
        raise GraphError(f"graph has a cycle among: {', '.join(stuck)}")


def _resolve_caps(nodes: list[Node], groups: dict[str, int] | None) -> dict[str, int]:
    """Resolve a concurrency cap for every group the graph actually uses.

    Explicit ``groups`` wins, then the ``"default"`` entry, then the studio
    settings. Every cap must be at least 1: a cap of 0 could never be scheduled.
    """
    configured: dict[str, int] = {
        "image": studio_settings.IMAGE_CONCURRENCY,
        "video": studio_settings.VIDEO_CONCURRENCY,
        "vision": studio_settings.VISION_CONCURRENCY,
        # Honour a config field if config.py ever grows one, else the constant.
        "default": getattr(studio_settings, "DEFAULT_CONCURRENCY", DEFAULT_GROUP_CONCURRENCY),
    }
    configured.update(groups or {})

    resolved: dict[str, int] = {}
    for node in nodes:
        group = node.concurrency_group or "default"
        if group in resolved:
            continue
        cap = configured.get(group, configured["default"])
        if not isinstance(cap, int) or cap < 1:
            raise GraphError(f"concurrency cap for group {group!r} must be >= 1, got {cap!r}")
        resolved[group] = cap
    return resolved


# ---------------------------------------------------------------------------
# execution
# ---------------------------------------------------------------------------
class _GraphRun:
    """One execution of one graph. Not reusable, not public.

    Two locks. ``_lock`` guards the state/result maps and is held only for
    bookkeeping, never across a node's ``run`` or across the event callback.
    ``_event_lock`` serialises calls into ``on_event`` so the caller's callback
    needs no synchronisation of its own.

    The scheduler thread owns PENDING -> RUNNING (and emits that event before
    submitting, so a node's RUNNING always precedes its terminal event).
    Worker threads own RUNNING -> terminal and emit from the worker itself, the
    moment the node finishes, so nothing waits for the scheduler to wake up.
    """

    def __init__(
        self,
        nodes: list[Node],
        on_event: Callable[[GraphEvent], None] | None,
        caps: dict[str, int],
    ) -> None:
        self._nodes: dict[str, Node] = {n.id: n for n in nodes}
        self._order: list[str] = [n.id for n in nodes]
        self._caps = caps
        self._on_event = on_event
        self._state: dict[str, NodeState] = {nid: NodeState.PENDING for nid in self._nodes}
        self._results: dict[str, Any] = {}
        self._started_at: dict[str, float] = {}
        self._lock = threading.RLock()
        self._event_lock = threading.Lock()

    # -- public entry ------------------------------------------------------
    def execute(self) -> dict[str, Any]:
        """Run the graph to completion and return the successful results."""
        # Sized to the sum of the caps so a submitted node always starts
        # immediately: if the pool were smaller, a node would queue behind an
        # unrelated one and "runs as soon as it can" would quietly stop holding.
        max_workers = max(1, min(len(self._nodes), sum(self._caps.values())))
        running: dict[Future, str] = {}

        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="studio-graph") as pool:
            while True:
                for event in self._cascade_failures():
                    self._emit_event(event)

                for node in self._claim_launchable():
                    self._emit(node, NodeState.RUNNING)
                    running[pool.submit(self._execute_node, node)] = node.id

                if not running:
                    if self._has_pending():
                        # Unreachable with a validated graph and caps >= 1, but
                        # never hang: report the stragglers and stop.
                        for event in self._abandon_pending():
                            self._emit_event(event)
                    break

                done, _ = wait(list(running), return_when=FIRST_COMPLETED)
                for future in done:
                    node_id = running.pop(future)
                    self._reap(future, node_id)

        with self._lock:
            return dict(self._results)

    # -- scheduling --------------------------------------------------------
    def _claim_launchable(self) -> list[Node]:
        """Mark every startable node RUNNING and return them, in graph order.

        Startable means: PENDING, every dependency succeeded, and the node's
        concurrency group is below its cap. Slots in use are counted from the
        live state map, so a slot frees the instant a worker finishes.
        """
        with self._lock:
            live = Counter(
                self._nodes[nid].concurrency_group or "default"
                for nid, state in self._state.items()
                if state is NodeState.RUNNING
            )
            claimed: list[Node] = []
            for nid in self._order:
                if self._state[nid] is not NodeState.PENDING:
                    continue
                node = self._nodes[nid]
                if any(self._state[dep] not in SUCCESS_STATES for dep in node.deps):
                    continue
                group = node.concurrency_group or "default"
                if live[group] >= self._caps[group]:
                    continue
                live[group] += 1
                self._state[nid] = NodeState.RUNNING
                self._started_at[nid] = time.monotonic()
                claimed.append(node)
            return claimed

    def _cascade_failures(self) -> list[GraphEvent]:
        """Fail every pending node that depends on a failure, transitively.

        Run to a fixpoint so a whole dead branch collapses in one pass and the
        UI greys it out at once instead of node by node.
        """
        events: list[GraphEvent] = []
        with self._lock:
            changed = True
            while changed:
                changed = False
                for nid in self._order:
                    if self._state[nid] is not NodeState.PENDING:
                        continue
                    dead = next(
                        (d for d in self._nodes[nid].deps if self._state[d] is NodeState.FAILED),
                        None,
                    )
                    if dead is None:
                        continue
                    self._state[nid] = NodeState.FAILED
                    events.append(
                        GraphEvent(
                            node_id=nid,
                            kind=self._nodes[nid].kind,
                            state=NodeState.FAILED,
                            payload={"reason": "dependency_failed", "failed_dep": dead},
                            elapsed_sec=0.0,
                        )
                    )
                    changed = True
        return events

    def _has_pending(self) -> bool:
        with self._lock:
            return any(state is NodeState.PENDING for state in self._state.values())

    def _abandon_pending(self) -> list[GraphEvent]:
        """Defensive: fail anything still pending when nothing can run."""
        events: list[GraphEvent] = []
        with self._lock:
            for nid, state in self._state.items():
                if state is NodeState.PENDING:
                    self._state[nid] = NodeState.FAILED
                    logger.error("graph: node %s was never schedulable", nid)
                    events.append(
                        GraphEvent(
                            node_id=nid,
                            kind=self._nodes[nid].kind,
                            state=NodeState.FAILED,
                            payload={"reason": "unschedulable"},
                        )
                    )
        return events

    def _reap(self, future: Future, node_id: str) -> None:
        """Collect a finished worker. ``_execute_node`` handles node failures
        itself, so anything surfacing here is a bug in this module."""
        try:
            future.result()
        except BaseException:  # pragma: no cover - defensive
            logger.exception("graph: executor crashed on node %s", node_id)
            with self._lock:
                already_terminal = self._state[node_id] in TERMINAL_STATES
                if not already_terminal:
                    self._state[node_id] = NodeState.FAILED
            if not already_terminal:
                self._emit(self._nodes[node_id], NodeState.FAILED, {"reason": "executor_error"})

    # -- worker ------------------------------------------------------------
    def _execute_node(self, node: Node) -> None:
        """Run one node on a worker thread: cache, attempts, terminal event."""
        if self._caching_enabled() and node.cache_key:
            hit, cached = self._cache_get(node)
            if hit:
                self._finish(node, NodeState.DONE, cached, {"cached": True})
                return

        attempt = 0
        while True:
            try:
                result = node.run(self._context(node))
            except Exception as exc:  # noqa: BLE001 - a node failure is data, not a crash
                if attempt < node.max_retries:
                    attempt += 1
                    self._emit(
                        node,
                        NodeState.RETRY,
                        {"attempt": attempt, "error": str(exc)[:500],
                         "error_type": type(exc).__name__},
                    )
                    if node.retry_delay_sec > 0:
                        time.sleep(node.retry_delay_sec)
                    self._emit(node, NodeState.RUNNING, {"attempt": attempt})
                    continue
                logger.warning("graph: node %s failed: %s", node.id, exc, exc_info=True)
                self._finish(
                    node,
                    NodeState.FAILED,
                    None,
                    {"error": str(exc)[:500], "error_type": type(exc).__name__,
                     "attempts": attempt + 1},
                )
                return

            state = NodeState.DONE
            extra: dict[str, Any] = {}
            if isinstance(result, Degraded):
                state, extra, result = NodeState.DEGRADED, {"note": result.note}, result.value
            if self._caching_enabled() and node.cache_key:
                extra["cached"] = False
                self._cache_put(node, result)
            payload = dict(result) if isinstance(result, dict) else {}
            payload.update(extra)  # graph metadata wins over the node's own keys
            self._finish(node, state, result, payload)
            return

    def _context(self, node: Node) -> dict[str, Any]:
        """Build the node's ``ctx``: exactly its declared dependencies' results."""
        with self._lock:
            return {dep: self._results[dep] for dep in node.deps}

    def _finish(self, node: Node, state: NodeState, result: Any, payload: dict[str, Any]) -> None:
        """Record a terminal state and emit it from this worker thread."""
        with self._lock:
            self._state[node.id] = state
            if state in SUCCESS_STATES:
                self._results[node.id] = result
        self._emit(node, state, payload)

    # -- events ------------------------------------------------------------
    def _emit(self, node: Node, state: NodeState, payload: dict[str, Any] | None = None) -> None:
        with self._lock:
            started = self._started_at.get(node.id)
        elapsed = 0.0 if started is None else max(0.0, time.monotonic() - started)
        self._emit_event(
            GraphEvent(
                node_id=node.id,
                kind=node.kind,
                state=state,
                payload=payload or {},
                elapsed_sec=round(elapsed, 3),
            )
        )

    def _emit_event(self, event: GraphEvent) -> None:
        """Deliver one event. Serialised, and never allowed to break the run."""
        if self._on_event is None:
            return
        with self._event_lock:
            try:
                self._on_event(event)
            except Exception:  # noqa: BLE001 - the listener is not our problem
                logger.exception("graph: on_event raised for node %s", event.node_id)

    # -- cache -------------------------------------------------------------
    @staticmethod
    def _caching_enabled() -> bool:
        # Read at call time, not import time, so a run can toggle it.
        return bool(studio_settings.CACHE_ENABLED)

    def _cache_get(self, node: Node) -> tuple[bool, Any]:
        """Look for a stored result. Any problem reading is treated as a miss."""
        path = cache_path(node.cache_key or "")
        try:
            with path.open("r", encoding="utf-8") as handle:
                document = json.load(handle)
        except FileNotFoundError:
            return False, None
        except (OSError, ValueError):
            logger.warning("graph: unreadable cache entry %s, treating as a miss", path)
            return False, None
        if not isinstance(document, dict) or "result" not in document:
            return False, None
        return True, document["result"]

    def _cache_put(self, node: Node, result: Any) -> bool:
        """Store a result, best effort.

        Written to a temp file and renamed, because a crash mid-write is exactly
        the scenario the cache exists for. A result that is not JSON-
        serialisable is skipped silently: caching is an optimisation and must
        never change whether a node succeeds. Cache local paths, not bytes.
        """
        path = cache_path(node.cache_key or "")
        try:
            blob = json.dumps(
                {
                    "cache_key": node.cache_key,
                    "node_id": node.id,
                    "kind": node.kind,
                    "created_at": time.time(),
                    "result": result,
                },
                ensure_ascii=False,
            )
        except (TypeError, ValueError):
            logger.debug("graph: result of node %s is not cacheable", node.id)
            return False
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
            tmp.write_text(blob, encoding="utf-8")
            os.replace(tmp, path)
            return True
        except OSError:
            logger.warning("graph: could not write cache entry %s", path, exc_info=True)
            return False
