"""Tests for intent router (JSON-strict parsing, enums, HITL threshold)."""
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mk7.core.router import Intent, IntentRouter, HitlGate, _parse_intent
from src.mk7.core.models import resolve


class _FakeClient:
    def __init__(self, reply: str):
        self.reply = reply

    def text(self, model, prompt, system=None, max_tokens=4096):
        assert "intent router" in (system or "").lower()
        return self.reply


def test_parse_intent_plain():
    d = _parse_intent('{"task_type":"code","skill_hint":"fix","target_agent":"eng","danger_level":"low","confidence":0.9}')
    assert d["task_type"] == "code"


def test_parse_intent_fenced():
    d = _parse_intent('```json\n{"task_type":"code","confidence":0.8}\n```')
    assert d["confidence"] == 0.8


def test_parse_intent_prose_wrapped():
    d = _parse_intent('Here you go: {"task_type":"docs","confidence":0.7} hope it helps')
    assert d["task_type"] == "docs"


def test_parse_intent_garbage():
    assert _parse_intent("no json here at all") is None


def test_classify_happy_path():
    r = IntentRouter(_FakeClient(
        '{"task_type":"code","skill_hint":"fix","target_agent":"eng","danger_level":"low","confidence":0.95}'
    ))
    intent = r.classify("fix bug")
    assert intent.task_type == "code"
    assert intent.target_agent == "eng"
    assert intent.confidence > 0.9


def test_classify_low_confidence_raises_hitl():
    r = IntentRouter(_FakeClient(
        '{"task_type":"other","skill_hint":"","target_agent":"ceo","danger_level":"low","confidence":0.4}'
    ))
    try:
        r.classify("ambiguous thing")
        assert False, "should raise HitlGate"
    except HitlGate as e:
        assert "0.40" in e.hint or "confidence" in e.hint


def test_classify_invalid_enum_falls_back_safe():
    r = IntentRouter(_FakeClient(
        '{"task_type":"hack_the_planet","skill_hint":"x","target_agent":"root","danger_level":"extreme","confidence":0.99}'
    ))
    intent = r.classify("weird")
    assert intent.task_type == "other"
    assert intent.target_agent == "ceo"
    assert intent.danger_level == "low"


def test_classify_unparseable_raises_hitl():
    r = IntentRouter(_FakeClient("Sorry I cannot do that."))
    try:
        r.classify("x")
        assert False
    except HitlGate:
        pass


def test_resolve_haiku_model():
    entry = resolve("haiku")
    assert entry.id == "claude-haiku-4-5"


def test_all_fixtures_shape():
    """20 fixtures parse into well-formed Intents with sane enums."""
    base = os.path.join(os.path.dirname(__file__), "fixtures", "intent_fixtures.json")
    with open(base) as f:
        fixtures = json.load(f)
    assert len(fixtures) == 20
    for fx in fixtures:
        intent = Intent(
            task_type=fx["task_type"],
            skill_hint=fx["skill_hint"],
            target_agent=fx["target_agent"],
            danger_level=fx["danger_level"],
            confidence=fx["confidence"],
        )
        assert intent.confidence >= 0.0
        assert intent.task_type in ("strategy", "approval", "client", "revenue", "product", "spec", "code", "deploy", "monitoring", "incident", "research", "docs", "other")
        assert intent.target_agent in ("sun-tzu", "ceo", "ae", "pm", "eng", "ops")
        assert intent.danger_level in ("low", "medium", "high", "critical")


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
