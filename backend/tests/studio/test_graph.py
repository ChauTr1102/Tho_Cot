"""The graph is what makes the studio fast and resumable. Two properties matter:
independent branches must not wait on each other (Shopee's reuse nodes must not
block on the hero render), and one failing node must not take the whole run down.

The timing assertions below are deliberately loose: they only need to separate
"ran in parallel" from "ran one after another", never to measure throughput.
"""
import json
import threading
import time

import pytest

from app.services.studio import graph
from app.services.studio.graph import (
    GraphError,
    Node,
    NodeState,
    cache_path,
    degraded,
    run_graph,
)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
@pytest.fixture
def isolated_cache(tmp_path, monkeypatch):
    """Point the cache at a tmp dir so tests never touch the repo's data/."""
    monkeypatch.setattr(graph.studio_settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(graph.studio_settings, "CACHE_ENABLED", True)
    return tmp_path


class EventLog:
    """Thread-safe recorder standing in for the SSE stream."""

    def __init__(self):
        self.events = []
        self._lock = threading.Lock()

    def __call__(self, event):
        with self._lock:
            self.events.append((time.monotonic(), event))

    def states(self, node_id):
        return [e.state for _, e in self.events if e.node_id == node_id]

    def at(self, node_id, state):
        return next(t for t, e in self.events if e.node_id == node_id and e.state is state)

    def payload(self, node_id, state):
        return next(e.payload for _, e in self.events if e.node_id == node_id and e.state is state)


# --------------------------------------------------------------------------
# the plan's five properties
# --------------------------------------------------------------------------
def test_independent_nodes_run_concurrently():
    started = []
    lock = threading.Lock()

    def slow(_):
        with lock:
            started.append(time.time())
        time.sleep(0.3)
        return "ok"

    nodes = [Node(id=f"n{i}", kind="test", deps=[], run=slow) for i in range(4)]
    t0 = time.time()
    results = run_graph(nodes, on_event=lambda e: None, groups={"default": 4})
    assert time.time() - t0 < 0.9          # concurrent, not 4 x 0.3 = 1.2s
    assert set(results) == {"n0", "n1", "n2", "n3"}


def test_dependency_receives_upstream_results_by_id():
    nodes = [
        Node(id="a", kind="t", deps=[], run=lambda ctx: 2),
        Node(id="b", kind="t", deps=["a"], run=lambda ctx: ctx["a"] * 21),
    ]
    assert run_graph(nodes, on_event=lambda e: None)["b"] == 42


def test_failed_node_marks_dependents_failed_but_siblings_still_run():
    def boom(_):
        raise RuntimeError("render died")

    nodes = [
        Node(id="bad", kind="t", deps=[], run=boom),
        Node(id="child", kind="t", deps=["bad"], run=lambda ctx: "never"),
        Node(id="sibling", kind="t", deps=[], run=lambda ctx: "fine"),
    ]
    states = {}
    run_graph(nodes, on_event=lambda e: states.__setitem__(e.node_id, e.state))
    assert states["bad"] is NodeState.FAILED
    assert states["child"] is NodeState.FAILED
    assert states["sibling"] is NodeState.DONE


def test_events_are_emitted_for_every_transition():
    seen = []
    nodes = [Node(id="a", kind="image", deps=[], run=lambda ctx: "x")]
    run_graph(nodes, on_event=seen.append)
    assert [e.state for e in seen] == [NodeState.RUNNING, NodeState.DONE]
    assert seen[0].kind == "image"


def test_concurrency_group_caps_are_respected():
    live, peak = [0], [0]
    lock = threading.Lock()

    def tracked(_):
        with lock:
            live[0] += 1
            peak[0] = max(peak[0], live[0])
        time.sleep(0.15)
        with lock:
            live[0] -= 1
        return 1

    nodes = [Node(id=f"v{i}", kind="video", deps=[], run=tracked,
                  concurrency_group="video") for i in range(6)]
    run_graph(nodes, on_event=lambda e: None, groups={"video": 2})
    assert peak[0] <= 2


# --------------------------------------------------------------------------
# graph shape: the studio's real topology is a diamond, not a chain
# --------------------------------------------------------------------------
def test_diamond_dependencies_run_in_the_right_order():
    """A -> B, A -> C, B+C -> D. The two middle branches must overlap, and D
    must not start until both have finished."""
    log = EventLog()

    def work(_):
        time.sleep(0.1)
        return "ok"

    nodes = [
        Node(id="A", kind="t", deps=[], run=work),
        Node(id="B", kind="t", deps=["A"], run=work),
        Node(id="C", kind="t", deps=["A"], run=work),
        Node(id="D", kind="t", deps=["B", "C"], run=lambda ctx: ctx["B"] + ctx["C"]),
    ]
    results = run_graph(nodes, on_event=log)

    assert results["D"] == "okok"
    a_done = log.at("A", NodeState.DONE)
    assert log.at("B", NodeState.RUNNING) >= a_done
    assert log.at("C", NodeState.RUNNING) >= a_done
    assert log.at("D", NodeState.RUNNING) >= max(log.at("B", NodeState.DONE),
                                                 log.at("C", NodeState.DONE))
    # B and C are siblings: the second must start before the first finishes
    assert log.at("C", NodeState.RUNNING) < log.at("B", NodeState.DONE)


def test_fast_branch_finishes_while_a_slow_branch_is_still_rendering():
    """The whole point of the graph: a marketplace kit built from reused photos
    is finished and on screen while a video is still rendering."""
    fast_done = threading.Event()
    observed = []

    def on_event(event):
        if event.node_id == "reuse" and event.state is NodeState.DONE:
            fast_done.set()

    def slow(_):
        # If events were batched until the end, this wait would time out.
        observed.append(fast_done.wait(timeout=2.0))
        return "clip"

    nodes = [
        Node(id="reuse", kind="image", deps=[], run=lambda ctx: "crop",
             concurrency_group="image"),
        Node(id="clip", kind="video", deps=[], run=slow, concurrency_group="video"),
    ]
    run_graph(nodes, on_event=on_event)
    assert observed == [True]


# --------------------------------------------------------------------------
# failure containment
# --------------------------------------------------------------------------
def test_failure_cascades_transitively_without_running_dependents():
    ran = []

    nodes = [
        Node(id="root", kind="t", deps=[], run=lambda ctx: (_ for _ in ()).throw(IOError("dns"))),
        Node(id="mid", kind="t", deps=["root"], run=lambda ctx: ran.append("mid")),
        Node(id="leaf", kind="t", deps=["mid"], run=lambda ctx: ran.append("leaf")),
        Node(id="far", kind="t", deps=["leaf"], run=lambda ctx: ran.append("far")),
        Node(id="other", kind="t", deps=[], run=lambda ctx: "unaffected"),
    ]
    log = EventLog()
    results = run_graph(nodes, on_event=log)

    assert ran == []                       # nothing downstream was executed
    assert results == {"other": "unaffected"}
    for nid in ("root", "mid", "leaf", "far"):
        assert log.states(nid)[-1] is NodeState.FAILED
    assert log.states("mid") == [NodeState.FAILED]      # never entered RUNNING
    assert log.payload("mid", NodeState.FAILED)["failed_dep"] == "root"
    assert "dns" in log.payload("root", NodeState.FAILED)["error"]


def test_one_failure_does_not_stop_unrelated_branches_from_completing():
    nodes = [
        Node(id="bad", kind="t", deps=[], run=lambda ctx: 1 / 0),
        Node(id="bad_child", kind="t", deps=["bad"], run=lambda ctx: "no"),
    ]
    nodes += [Node(id=f"ok{i}", kind="t", deps=[], run=lambda ctx: i) for i in range(5)]
    nodes.append(Node(id="join", kind="t", deps=[f"ok{i}" for i in range(5)],
                      run=lambda ctx: sorted(ctx)))

    results = run_graph(nodes, on_event=lambda e: None)
    assert results["join"] == ["ok0", "ok1", "ok2", "ok3", "ok4"]
    assert "bad" not in results and "bad_child" not in results


def test_a_broken_event_callback_cannot_kill_the_run():
    """The callback is the SSE bridge; a disconnected browser must not abort a
    six-minute render."""
    def hostile(_event):
        raise RuntimeError("client disconnected")

    nodes = [Node(id="a", kind="t", deps=[], run=lambda ctx: "still fine")]
    assert run_graph(nodes, on_event=hostile) == {"a": "still fine"}


# --------------------------------------------------------------------------
# concurrency groups are per-group, not one shared pool
# --------------------------------------------------------------------------
def test_groups_are_capped_independently_of_each_other():
    lock = threading.Lock()
    live = {"image": 0, "video": 0}
    peak = {"image": 0, "video": 0}

    def tracked(group):
        def _run(_):
            with lock:
                live[group] += 1
                peak[group] = max(peak[group], live[group])
            time.sleep(0.12)
            with lock:
                live[group] -= 1
            return group
        return _run

    nodes = [Node(id=f"i{i}", kind="image", deps=[], run=tracked("image"),
                  concurrency_group="image") for i in range(4)]
    nodes += [Node(id=f"v{i}", kind="video", deps=[], run=tracked("video"),
                   concurrency_group="video") for i in range(3)]

    run_graph(nodes, on_event=lambda e: None, groups={"image": 4, "video": 1})
    assert peak["image"] == 4      # a throttled video group must not throttle images
    assert peak["video"] == 1


def test_unknown_group_falls_back_to_the_default_cap():
    lock = threading.Lock()
    live, peak = [0], [0]

    def tracked(_):
        with lock:
            live[0] += 1
            peak[0] = max(peak[0], live[0])
        time.sleep(0.1)
        with lock:
            live[0] -= 1
        return 1

    nodes = [Node(id=f"x{i}", kind="t", deps=[], run=tracked,
                  concurrency_group="ffmpeg") for i in range(5)]
    run_graph(nodes, on_event=lambda e: None, groups={"default": 2, "image": 8})
    assert peak[0] <= 2


def test_group_caps_default_to_studio_settings(monkeypatch):
    monkeypatch.setattr(graph.studio_settings, "VIDEO_CONCURRENCY", 1)
    lock = threading.Lock()
    live, peak = [0], [0]

    def tracked(_):
        with lock:
            live[0] += 1
            peak[0] = max(peak[0], live[0])
        time.sleep(0.05)
        with lock:
            live[0] -= 1
        return 1

    nodes = [Node(id=f"v{i}", kind="video", deps=[], run=tracked,
                  concurrency_group="video") for i in range(3)]
    run_graph(nodes, on_event=lambda e: None)   # no explicit groups
    assert peak[0] == 1


# --------------------------------------------------------------------------
# events
# --------------------------------------------------------------------------
def test_terminal_events_carry_elapsed_time_and_the_node_result():
    log = EventLog()

    def work(_):
        time.sleep(0.05)
        return {"url": "/media/x.jpg", "origin": "reuse"}

    run_graph([Node(id="shopee_main", kind="image", deps=[], run=work)], on_event=log)

    running = log.payload("shopee_main", NodeState.RUNNING)
    assert running == {}
    done_event = next(e for _, e in log.events if e.state is NodeState.DONE)
    assert done_event.elapsed_sec >= 0.05
    assert done_event.payload["url"] == "/media/x.jpg"     # dict results reach the SSE payload
    assert done_event.payload["origin"] == "reuse"


def test_event_callback_is_never_invoked_concurrently():
    """on_event is called from worker threads. The executor serialises the calls
    so the SSE writer does not need its own lock."""
    overlaps = []
    inside = [0]

    def on_event(event):
        inside[0] += 1
        if inside[0] > 1:
            overlaps.append(event.node_id)
        time.sleep(0.005)
        inside[0] -= 1

    nodes = [Node(id=f"n{i}", kind="t", deps=[], run=lambda ctx: "x",
                  concurrency_group="image") for i in range(12)]
    run_graph(nodes, on_event=on_event, groups={"image": 8})
    assert overlaps == []


def test_events_are_optional():
    assert run_graph([Node(id="a", kind="t", deps=[], run=lambda ctx: 1)])["a"] == 1


# --------------------------------------------------------------------------
# degraded and retry
# --------------------------------------------------------------------------
def test_degraded_node_satisfies_its_dependents():
    """A clip that missed its deadline and fell back to a Ken Burns move is
    degraded, not failed: the master still gets cut."""
    log = EventLog()
    nodes = [
        Node(id="clip", kind="video", deps=[],
             run=lambda ctx: degraded("/media/kenburns.mp4", note="deadline missed")),
        Node(id="master", kind="video", deps=["clip"], run=lambda ctx: ctx["clip"]),
    ]
    results = run_graph(nodes, on_event=log)

    assert results["clip"] == "/media/kenburns.mp4"
    assert results["master"] == "/media/kenburns.mp4"
    assert log.states("clip") == [NodeState.RUNNING, NodeState.DEGRADED]
    assert log.payload("clip", NodeState.DEGRADED)["note"] == "deadline missed"


def test_node_retries_a_flaky_call_before_giving_up():
    attempts = []

    def flaky(_):
        attempts.append(1)
        if len(attempts) < 3:
            raise ConnectionError("venue wifi dropped DNS")
        return "ok"

    log = EventLog()
    results = run_graph([Node(id="a", kind="image", deps=[], run=flaky, max_retries=2)],
                        on_event=log)

    assert results["a"] == "ok"
    assert len(attempts) == 3
    assert log.states("a") == [NodeState.RUNNING, NodeState.RETRY, NodeState.RUNNING,
                              NodeState.RETRY, NodeState.RUNNING, NodeState.DONE]


def test_retries_are_exhausted_then_the_node_fails():
    calls = []

    def always_bad(_):
        calls.append(1)
        raise ConnectionError("still down")

    log = EventLog()
    run_graph([Node(id="a", kind="t", deps=[], run=always_bad, max_retries=1)], on_event=log)
    assert len(calls) == 2
    assert log.states("a")[-1] is NodeState.FAILED
    assert log.payload("a", NodeState.FAILED)["attempts"] == 2


# --------------------------------------------------------------------------
# cache — what makes a re-run after a crash near-instant
# --------------------------------------------------------------------------
def test_cache_hit_short_circuits_the_node(isolated_cache):
    calls = []
    first = run_graph([Node(id="hero", kind="image", deps=[], cache_key="hero-A-abc123",
                            run=lambda ctx: {"path": "media/hero.jpg"})])
    assert first["hero"] == {"path": "media/hero.jpg"}
    assert (isolated_cache / "cache" / "hero-A-abc123.json").exists()

    log = EventLog()
    second = run_graph([Node(id="hero", kind="image", deps=[], cache_key="hero-A-abc123",
                             run=lambda ctx: calls.append("ran"))], on_event=log)
    assert calls == []                                   # never executed
    assert second["hero"] == {"path": "media/hero.jpg"}  # value came from disk
    assert log.payload("hero", NodeState.DONE)["cached"] is True
    assert log.states("hero") == [NodeState.RUNNING, NodeState.DONE]


def test_cache_is_ignored_when_disabled(isolated_cache, monkeypatch):
    run_graph([Node(id="a", kind="t", deps=[], cache_key="k1", run=lambda ctx: "v1")])
    monkeypatch.setattr(graph.studio_settings, "CACHE_ENABLED", False)
    assert run_graph([Node(id="a", kind="t", deps=[], cache_key="k1",
                           run=lambda ctx: "v2")])["a"] == "v2"


def test_nodes_without_a_cache_key_never_touch_the_cache(isolated_cache):
    run_graph([Node(id="a", kind="t", deps=[], run=lambda ctx: "v")])
    assert not (isolated_cache / "cache").exists()


def test_failed_nodes_are_not_cached(isolated_cache):
    def boom(_):
        raise RuntimeError("nope")

    run_graph([Node(id="a", kind="t", deps=[], cache_key="k2", run=boom)])
    assert not cache_path("k2").exists()


def test_unserialisable_results_are_not_cached_and_do_not_fail_the_node(isolated_cache):
    sentinel = object()
    results = run_graph([Node(id="a", kind="t", deps=[], cache_key="k3",
                              run=lambda ctx: sentinel)])
    assert results["a"] is sentinel
    assert not cache_path("k3").exists()


def test_a_corrupt_cache_entry_is_treated_as_a_miss(isolated_cache):
    path = cache_path("k4")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not json", encoding="utf-8")
    assert run_graph([Node(id="a", kind="t", deps=[], cache_key="k4",
                           run=lambda ctx: "fresh")])["a"] == "fresh"
    assert json.loads(path.read_text(encoding="utf-8"))["result"] == "fresh"


def test_cache_keys_cannot_escape_the_cache_directory(isolated_cache):
    run_graph([Node(id="a", kind="t", deps=[], cache_key="../../etc/passwd",
                    run=lambda ctx: "v")])
    cache_root = (isolated_cache / "cache").resolve()
    assert cache_path("../../etc/passwd").resolve().parent == cache_root
    assert not (isolated_cache.parent / "etc").exists()


# --------------------------------------------------------------------------
# validation — a malformed graph must fail loudly, never hang
# --------------------------------------------------------------------------
def test_cycles_are_rejected():
    nodes = [
        Node(id="a", kind="t", deps=["b"], run=lambda ctx: 1),
        Node(id="b", kind="t", deps=["a"], run=lambda ctx: 1),
    ]
    with pytest.raises(GraphError, match="cycle"):
        run_graph(nodes, on_event=lambda e: None)


def test_unknown_dependency_is_rejected():
    with pytest.raises(GraphError, match="unknown dependency"):
        run_graph([Node(id="a", kind="t", deps=["ghost"], run=lambda ctx: 1)])


def test_duplicate_node_ids_are_rejected():
    nodes = [Node(id="a", kind="t", deps=[], run=lambda ctx: 1) for _ in range(2)]
    with pytest.raises(GraphError, match="duplicate"):
        run_graph(nodes)


def test_a_zero_concurrency_cap_is_rejected():
    with pytest.raises(GraphError, match="concurrency"):
        run_graph([Node(id="a", kind="t", deps=[], run=lambda ctx: 1)],
                  groups={"default": 0})


def test_empty_graph_is_a_no_op():
    assert run_graph([], on_event=lambda e: None) == {}
