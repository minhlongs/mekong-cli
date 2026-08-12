"""Tests for orchestrate pipeline + SOP engine."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mk7.core.orchestrate import GateResult, _parse_gate
from src.mk7.core.sop import SopDocument, build_ship_commands, find, load_all


def test_parse_gate_pass():
    raw = "PASS + ROUND: 1\n\nEvidence: build exit 0\n"
    g = _parse_gate(raw)
    assert g.verdict == "PASS"
    assert g.round == 1
    assert g.can_proceed


def test_parse_gate_conditional_pass():
    raw = "CONDITIONAL PASS + ROUND: 2\n\nConditions:\n- fix typo\n\nOut-of-scope observations:\n- new idea\n"
    g = _parse_gate(raw)
    assert g.verdict == "CONDITIONAL PASS"
    assert g.round == 2
    assert g.can_proceed
    assert any("fix typo" in c for c in g.conditions)
    assert any("new idea" in o for o in g.observations)


def test_parse_gate_amend_fail():
    g = _parse_gate("AMEND + ROUND: 1\n\nConditions:\n- add tests\n")
    assert g.verdict == "AMEND"
    assert not g.can_proceed
    g2 = _parse_gate("FAIL\n\nEvidence: plan impossible\n")
    assert g2.verdict == "FAIL"


def test_sop_loader():
    docs = load_all()
    assert any(d.name == "incident-response" for d in docs)
    incident = find("incident")
    assert incident is not None
    assert incident.layer == "ops"
    assert len(incident.steps) >= 3


def test_sop_extract_steps():
    from src.mk7.core.sop import _extract_steps

    steps = _extract_steps("# SOP\n## Intent\nFix things.\n\n## Response Steps\n### 1 — Detect\n### 2 — Fix\n")
    assert len(steps) >= 2


def test_ship_commands_build():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        (p / "package.json").write_text('{"scripts": {"deploy:full": "wrangler deploy"}}')
        (p / "CLAUDE.deploy.md").write_text("Deploy: run npm run deploy:full. URL https://example.com")
        steps = build_ship_commands(p)
        descs = [s[0] for s in steps]
        assert "Commit changes" in descs
        assert any("deploy:full" in s[0] for s in steps)
        assert any("example.com" in s[0] for s in steps)


def test_omni_default_schedule():
    from src.mk7.core.omni import default_config

    cfg = default_config()
    assert len(cfg.schedule) >= 5
    assert cfg.dry_run is True
    assert cfg.schedule.get("monitoring") == 60


def test_omni_config_roundtrip():
    import tempfile as tf
    from pathlib import Path as P

    from src.mk7.core import omni as m

    with tf.TemporaryDirectory() as td:
        old_dir = m.OMNI_DIR
        m.OMNI_DIR = P(td)
        try:
            from src.mk7.core.omni import OmniConfig, _load_config, _save_config

            cfg = OmniConfig(schedule={"monitoring": 30}, dry_run=False)
            _save_config(cfg)
            loaded = _load_config()
            assert loaded.schedule == {"monitoring": 30}
            assert loaded.dry_run is False
        finally:
            m.OMNI_DIR = old_dir


if __name__ == "__main__":
    import traceback

    failed = total = 0
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
