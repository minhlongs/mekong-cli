"""Tests for DAG graph engine: validation, DAG execution, resume, budget, parallel."""
import sys
import os
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mk7.core.graph import (
    BudgetExceeded,
    GraphExecutor,
    GraphState,
    GraphValidationError,
    Node,
    save_state,
    load_state,
)


def make_graph(title="test graph"):
    gs = GraphState(title=title)
    gs.nodes = [
        Node(id="n1", task="a"),
        Node(id="n2", task="b"),
        Node(id="n3", task="c"),
        Node(id="n4", task="d"),
        Node(id="n5", task="e"),
    ]
    gs.edges = [("n1", "n3"), ("n2", "n3"), ("n3", "n4"), ("n3", "n5")]
    return gs


def test_validate_ok():
    gs = make_graph()
    gs.validate()


def test_validate_unknown_edge():
    gs = make_graph()
    gs.edges = [("n1", "n99")]
    try:
        gs.validate()
        assert False
    except GraphValidationError:
        pass


def test_validate_cycle():
    gs = make_graph()
    gs.edges = [("n1", "n2"), ("n2", "n1")]
    try:
        gs.validate()
        assert False
    except GraphValidationError:
        pass


def test_ready_respects_deps():
    gs = make_graph()
    ready = [n.id for n in gs.ready()]
    assert ready == ["n1", "n2"]


def test_dag_execution_order():
    gs = make_graph()
    executed = []

    def exec_fn(node, shared):
        executed.append(node.id)
        return {"done": node.id}

    GraphExecutor(exec_fn).run(gs)
    assert executed.index("n3") > executed.index("n1")
    assert executed.index("n3") > executed.index("n2")
    assert executed.index("n4") > executed.index("n3")
    assert executed.index("n5") > executed.index("n3")
    assert gs.status == "done"
    assert all(n.status == "done" for n in gs.nodes)


def test_retry_then_success():
    gs = make_graph()
    fails = {"n3": 2}

    def exec_fn(node, shared):
        if node.id == "n3" and fails["n3"] > 0:
            fails["n3"] -= 1
            raise RuntimeError("boom")
        return {"ok": True}

    GraphExecutor(exec_fn).run(gs)
    assert gs.status == "done"
    assert gs.node("n3").retries == 2


def test_retry_exhausted_marks_failed():
    gs = make_graph()

    def exec_fn(node, shared):
        raise RuntimeError("always fails")

    GraphExecutor(exec_fn, max_retries=1).run(gs)
    assert gs.status == "failed"
    assert gs.node("n1").status == "failed"


def test_checkpoint_resume():
    gs = make_graph()
    calls = {"n3": 0}

    def exec_fn(node, shared):
        if node.id == "n3" and calls["n3"] == 0:
            calls["n3"] += 1
            gs.node("n1").status = "done"
            gs.node("n2").status = "done"
            gs.node("n3").status = "done"
            save_state(gs)
            raise SystemExit("simulated crash")
        return {"ok": node.id}

    # First run crashes mid-way; we emulate by raising SystemExit out of run.
    try:
        GraphExecutor(exec_fn).run(gs)
    except SystemExit:
        pass

    # Resume: load state, nodes n1-n3 done, n4/n5 pending; rerun completes.
    slug = gs.slug
    resumed = load_state(slug)
    assert resumed is not None
    assert resumed.node("n1").status == "done"
    assert resumed.node("n3").status == "done"
    GraphExecutor(exec_fn).run(resumed)
    assert resumed.status == "done"
    assert all(n.status == "done" for n in resumed.nodes)


def test_budget_llm_calls_exceeded():
    gs = GraphState(title="budget")
    gs.nodes = [Node(id=f"n{i}", task=f"t{i}") for i in range(1, 7)]

    def exec_fn(node, shared):
        return {"ok": True}

    try:
        GraphExecutor(exec_fn, max_llm_calls=3).run(gs)
        assert False, "should raise BudgetExceeded"
    except BudgetExceeded:
        pass


def test_gate_blocks():
    gs = make_graph()
    gs.node("n3").gate = "deploy"

    def exec_fn(node, shared):
        return {"ok": True}

    def gate_cb(node):
        return False  # deny

    result = GraphExecutor(exec_fn, gate_cb=gate_cb).run(gs)
    assert result.status == "blocked"
    assert result.node("n3").status == "blocked"


def test_gate_auto_pass_when_none():
    gs = make_graph()
    gs.node("n3").gate = "deploy"

    def exec_fn(node, shared):
        return {"ok": True}

    result = GraphExecutor(exec_fn, gate_cb=lambda n: None).run(gs)
    assert result.status == "done"


def test_shared_context_seeding():
    gs = make_graph()
    gs.node("n1").status = "done"
    gs.node("n1").result = {"pre": 1}

    seen = {}

    def exec_fn(node, shared):
        seen[node.id] = dict(shared)
        return {"ok": True}

    GraphExecutor(exec_fn).run(gs)
    assert seen["n3"].get("n1") == {"pre": 1}


def test_save_load_roundtrip():
    gs = make_graph()
    gs.node("n1").status = "done"
    gs.node("n1").result = {"x": 42}
    save_state(gs)
    loaded = load_state(gs.slug)
    assert loaded is not None
    assert loaded.node("n1").result == {"x": 42}
    assert loaded.edges == gs.edges


def test_parallel_branches_both_complete():
    gs = make_graph()
    gs.nodes = [Node(id="n1", task="a"), Node(id="n2", task="b"), Node(id="n3", task="c")]
    gs.edges = [("n1", "n3"), ("n2", "n3")]

    def exec_fn(node, shared):
        return {"ok": node.id}

    GraphExecutor(exec_fn).run(gs)
    assert gs.status == "done"


if __name__ == "__main__":
    import traceback

    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except Exception:
                failed += 1
                print(f"FAIL {name}")
                traceback.print_exc()
    total = sum(1 for n in globals() if n.startswith("test_"))
    print(f"\n{total - failed}/{total} passed")
    sys.exit(1 if failed else 0)
