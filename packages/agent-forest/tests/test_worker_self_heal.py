"""Self-heal worker integration: FeedbackLoop vs single-pass selection."""

from __future__ import annotations


def test_feedback_rounds_defaults_to_one(settings):
    """Back-compat: default FOREST_FEEDBACK_ROUNDS=1 preserves single-pass path."""
    assert settings.feedback_rounds == 1


def test_feedback_rounds_env_override(monkeypatch, tmp_outputs):
    from agent_forest.config import ForestSettings
    from agent_forest.gateway import deps

    monkeypatch.setenv("FOREST_FEEDBACK_ROUNDS", "3")
    deps.reset_caches()
    settings = ForestSettings.from_env()
    assert settings.feedback_rounds == 3


def test_feedback_rounds_clamps_below_one(monkeypatch, tmp_outputs):
    from agent_forest.config import ForestSettings
    from agent_forest.gateway import deps

    monkeypatch.setenv("FOREST_FEEDBACK_ROUNDS", "0")
    deps.reset_caches()
    settings = ForestSettings.from_env()
    assert settings.feedback_rounds == 1


def test_process_one_forwards_feedback_rounds(fake_redis, settings, monkeypatch):
    """process_one must pass settings.feedback_rounds into the executor."""
    from agent_forest import queue as q
    from agent_forest.worker.main import process_one
    from agent_forest.worker.runner import JobOutcome

    monkeypatch.setenv("FOREST_FEEDBACK_ROUNDS", "3")
    from agent_forest.config import ForestSettings
    from agent_forest.gateway import deps
    deps.reset_caches()
    s = ForestSettings.from_env()

    q.enqueue_job(fake_redis, job_id="j1", user_id="usr_founder1", prompt="x", webhook_url=None)

    seen: dict[str, int] = {}

    def stub(_prompt: str, _sandbox: str, *, max_rounds: int = 1) -> JobOutcome:
        seen["rounds"] = max_rounds
        return JobOutcome(status="completed", result="ok")

    process_one(fake_redis, s, key="job:usr_founder1:j1", executor=stub)
    assert seen == {"rounds": 3}


def test_run_job_single_pass_back_compat(tmp_outputs, monkeypatch):
    """max_rounds=1 still exercises CEO → Developer legacy path."""
    from agent_forest.worker import runner

    sentinel: dict[str, object] = {}

    class _FakeCEO:
        def __init__(self, *a, **kw):
            pass

        def plan(self, goal):
            sentinel["plan"] = goal
            return "mock plan"

    class _FakeDev:
        def __init__(self, *a, **kw):
            pass

        def execute(self, goal, plan_context=None):
            sentinel["exec"] = (goal, plan_context)
            return '{"file_path": "out.txt", "content": "hi"}'

    class _FakeLLM:
        def chat(self, *a, **kw):
            return ""

    class _FakeMemory:
        def __init__(self, root):
            pass

    # Patch the modules that runner._run_single_pass imports.
    import agent_core.agents.ceo as ceo_mod
    import agent_core.agents.developer as dev_mod
    import agent_core.llm_client as llm_mod
    import agent_core.memory as mem_mod

    monkeypatch.setattr(ceo_mod, "CEOAgent", _FakeCEO)
    monkeypatch.setattr(dev_mod, "DeveloperAgent", _FakeDev)
    monkeypatch.setattr(llm_mod, "LLMClient", lambda *a, **kw: _FakeLLM())
    monkeypatch.setattr(mem_mod, "SeedMemory", _FakeMemory)

    out = runner.run_job("write hello", tmp_outputs / "u1", max_rounds=1)
    assert out.status == "completed"
    assert "plan" in sentinel
    assert "exec" in sentinel


def test_run_job_feedback_loop_ships_on_ship_verdict(tmp_outputs, monkeypatch):
    """max_rounds>=2 drives FeedbackLoop; ship verdict → completed."""
    from agent_forest.worker import runner

    class _FakeLLM:
        def chat(self, *a, **kw):
            return ""

    class _FakeMemory:
        def __init__(self, root):
            pass

    class _FakeRound:
        round_index = 1
        report = type(
            "R",
            (),
            {
                "review": {"verdict": "ship", "score": 9, "notes": []},
                "test": {"status": "pass", "summary": "ok", "issues": []},
                "artifact": "mock artifact output",
            },
        )()
        ops = {"severity": "info", "healthy": True, "alerts": []}
        analyst = {"summary": "ok", "recommendations": [], "trend": "flat"}

    class _FakeSession:
        rounds = [_FakeRound()]

        @property
        def final(self):
            return self.rounds[-1].report

    class _FakeLoop:
        def __init__(self, llm=None, memory=None):
            pass

        def process_goal(self, goal, max_rounds=1):
            return _FakeSession()

    import agent_core.feedback_loop as fl_mod
    import agent_core.llm_client as llm_mod
    import agent_core.memory as mem_mod

    monkeypatch.setattr(fl_mod, "FeedbackLoop", _FakeLoop)
    monkeypatch.setattr(llm_mod, "LLMClient", lambda *a, **kw: _FakeLLM())
    monkeypatch.setattr(mem_mod, "SeedMemory", _FakeMemory)

    out = runner.run_job("build x", tmp_outputs / "u2", max_rounds=2)
    assert out.status == "completed"
    assert "rounds=1" in (out.result or "")
    assert "verdict=ship" in (out.result or "")


def test_run_job_feedback_loop_fails_on_block(tmp_outputs, monkeypatch):
    """Non-ship verdict after max_rounds → failed outcome."""
    from agent_forest.worker import runner

    class _FakeLLM:
        def chat(self, *a, **kw):
            return ""

    class _FakeMemory:
        def __init__(self, root):
            pass

    class _FakeRound:
        round_index = 1
        report = type(
            "R",
            (),
            {
                "review": {"verdict": "block", "score": 2, "notes": []},
                "test": {"status": "fail", "summary": "broken", "issues": ["x"]},
                "artifact": "broken",
            },
        )()
        ops = {"severity": "critical", "healthy": False, "alerts": ["boom"]}
        analyst = {"summary": "broken", "recommendations": ["fix"], "trend": "regressing"}

    class _FakeSession:
        rounds = [_FakeRound()]

        @property
        def final(self):
            return self.rounds[-1].report

    class _FakeLoop:
        def __init__(self, llm=None, memory=None):
            pass

        def process_goal(self, goal, max_rounds=1):
            return _FakeSession()

    import agent_core.feedback_loop as fl_mod
    import agent_core.llm_client as llm_mod
    import agent_core.memory as mem_mod

    monkeypatch.setattr(fl_mod, "FeedbackLoop", _FakeLoop)
    monkeypatch.setattr(llm_mod, "LLMClient", lambda *a, **kw: _FakeLLM())
    monkeypatch.setattr(mem_mod, "SeedMemory", _FakeMemory)

    out = runner.run_job("broken goal", tmp_outputs / "u3", max_rounds=2)
    assert out.status == "failed"
    assert "verdict=block" in (out.error or "")
    assert "ops=critical" in (out.error or "")
