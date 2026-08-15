"""Tests for L1 port: todo, session, skills, permissions."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# NOTE: other test files may import src.mk7.core.config first, freezing
# CONFIG_DIR to ~/.mekong. To stay deterministic we wipe the state files
# our fixed slugs use before each run (module import time is not enough).
from src.mk7.core.todo import Todo, TodoNotFound, TodoStore, sync_todos_from_graph
from src.mk7.core.session import SessionNotFound, SessionStore


def _reset_todo_state(*slugs: str) -> None:
    from src.mk7.core.todo import STATE_DIR

    for slug in slugs:
        f = STATE_DIR / f"{slug}-todos.json"
        if f.exists():
            f.unlink()
    if not STATE_DIR.exists():
        STATE_DIR.mkdir(parents=True, exist_ok=True)
from src.mk7.core.skills import SkillRegistry, SkillNotFound, load_skill, skill_prompt_for_hint
from src.mk7.core.gates import AgentPermissionResolver, PermissionDenied, _glob_match
from src.mk7.core.graph import Node


# ── TODO ────────────────────────────────────────────────────

def test_todo_crud():
    _reset_todo_state("t-todo-crud")
    store = TodoStore("t-todo-crud")
    t = store.add("deploy", priority="high")
    assert t.status == "pending" and t.priority == "high"
    store.update(t.id, status="in_progress")
    assert store.get(t.id).status == "in_progress"
    assert store.summary()["in_progress"] == 1
    store.update(t.id, status="completed")
    assert store.summary()["completed"] == 1
    assert store.remove(t.id)
    assert not store.remove(t.id)


def test_todo_not_found():
    store = TodoStore("t-todo-missing")
    try:
        store.get("nope")
        assert False
    except TodoNotFound:
        pass


def test_todo_invalid_values_ignored():
    store = TodoStore("t-todo-invalid")
    t = store.add("x")
    store.update(t.id, status="bogus", priority="extreme")
    assert store.get(t.id).status == "pending"
    assert store.get(t.id).priority == "medium"


def test_todo_sync_from_graph():
    _reset_todo_state("t-todo-sync")
    store = TodoStore("t-todo-sync")
    nodes = [
        Node(id="n1", task="deploy app", gate="deploy"),
        Node(id="n2", task="write code"),
        Node(id="n3", task="test"),
    ]
    nodes[1].status = "done"
    nodes[2].status = "blocked"
    sync_todos_from_graph(store, nodes, {n.id: n.task for n in nodes})
    todos = store.list()
    assert len(todos) == 3
    st = {t.content: t.status for t in todos}
    assert st["write code"] == "completed"
    assert st["test"] == "cancelled"
    assert st["deploy app"] == "pending"


def test_todo_sync_preserves_completed_on_resume():
    _reset_todo_state("t-todo-resume")
    store = TodoStore("t-todo-resume")
    nodes = [Node(id="n1", task="step a"), Node(id="n2", task="step b")]
    nodes[0].status = "done"
    sync_todos_from_graph(store, nodes, {n.id: n.task for n in nodes})
    # simulate resume: n1 stays done, n2 now done too
    nodes[1].status = "done"
    sync_todos_from_graph(store, nodes, {n.id: n.task for n in nodes})
    st = {t.content: t.status for t in store.list()}
    assert st["step a"] == "completed"
    assert st["step b"] == "completed"


# ── SESSION ─────────────────────────────────────────────────

def test_session_create_and_get():
    store = SessionStore()
    s = store.create(directory="/tmp/x", agent_id="eng", title="fix bug")
    got = store.get(s.id)
    assert got.agent_id == "eng"
    assert got.title == "fix bug"
    assert got.status == "active"


def test_session_tree():
    store = SessionStore()
    root = store.create(directory="/tmp", agent_id="ceo", title="root")
    child = store.create(directory="/tmp", agent_id="eng", title="child", parent_id=root.id)
    grand = store.create(directory="/tmp", agent_id="ops", title="grand", parent_id=child.id)
    child_ids = [c.id for c in store.children(root.id)]
    assert child.id in child_ids and grand.id not in child_ids
    assert store.ancestors(grand.id)[0].id == child.id
    sub = store.subtree_ids(root.id)
    assert root.id in sub and child.id in sub and grand.id in sub


def test_session_update_status():
    store = SessionStore()
    s = store.create(directory="/tmp", title="x")
    store.update(s.id, status="completed")
    assert store.get(s.id).status == "completed"
    store.update(s.id, status="bogus")  # ignored
    assert store.get(s.id).status == "completed"


def test_session_attach_todo():
    store = SessionStore()
    s = store.create(directory="/tmp", title="x")
    store.attach_todo(s.id, "abc123")
    assert "abc123" in store.get(s.id).todo_ids


def test_session_not_found():
    store = SessionStore()
    try:
        store.get("nope")
        assert False
    except SessionNotFound:
        pass


# ── SKILLS ──────────────────────────────────────────────────

def test_skill_registry_loads():
    reg = SkillRegistry()
    assert len(reg.list()) > 100, f"expected 100+ skills, got {len(reg.list())}"


def test_skill_find_brainstorm():
    reg = SkillRegistry()
    sk = reg.find("brainstorming")
    assert sk is not None
    assert "brainstorm" in sk.description.lower()


def test_skill_find_ak_cook():
    reg = SkillRegistry()
    sk = reg.find("ak-cook")
    assert sk is not None
    assert sk.body.strip() != ""


def test_skill_search():
    reg = SkillRegistry()
    hits = reg.search("deploy", limit=3)
    assert len(hits) >= 1


def test_skill_prompt_for_hint():
    prompt = skill_prompt_for_hint("ak-cook")
    assert "Skill:" in prompt
    assert skill_prompt_for_hint("") == ""


def test_skill_not_found():
    try:
        load_skill("definitely-not-a-skill-xyz")
        assert False
    except SkillNotFound:
        pass


# ── PERMISSIONS ─────────────────────────────────────────────

def test_permission_defaults():
    r = AgentPermissionResolver()
    assert r.mode_for("ops", "edit") == "deny"
    assert r.mode_for("eng", "edit") == "allow"
    assert r.mode_for("sun-tzu", "bash") == "deny"


def test_permission_bash_glob():
    # opencode rule: last matching rule wins — put "*" first, specifics after.
    r = AgentPermissionResolver({"eng": {"bash": {"*": "allow", "git push": "ask", "git status": "allow"}}})
    assert r.mode_for("eng", "bash", "git status") == "allow"
    assert r.mode_for("eng", "bash", "git push origin main") == "ask"
    assert r.mode_for("eng", "bash", "npm test") == "allow"


def test_permission_check_deny():
    r = AgentPermissionResolver()
    try:
        r.check("ops", "edit")
        assert False
    except PermissionDenied:
        pass
    r.check("eng", "bash")  # no raise


def test_glob_match():
    assert _glob_match("git *", "git status")
    assert _glob_match("*test*", "pytest run")
    assert not _glob_match("git push", "git pull")


if __name__ == "__main__":
    import traceback

    failed = 0
    total = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            total += 1
            try:
                fn()
                print(f"PASS {name}")
            except Exception:
                failed += 1
                print(f"FAIL {name}")
                traceback.print_exc()
    print(f"\n{total - failed}/{total} passed")
    sys.exit(1 if failed else 0)
