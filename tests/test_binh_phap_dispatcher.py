"""Tests for Binh Phap Dispatcher — topology-to-PEV bridge."""

import json
import pytest
from pathlib import Path


@pytest.fixture
def tmp_company(tmp_path: Path):
    """Create a temporary company.json for topology engine."""
    company = tmp_path / "company.json"
    company.write_text(json.dumps({
        "binh_phap_state": {
            "topology": "3d",
            "current_dimension": "vertical",
            "cycle_number": 0,
            "cycle_history": [],
            "current_groups": {},
            "next_command": "swot",
            "auto_dispatch": False,
            "target_mrr": 1000,
        }
    }))
    return str(company)


class TestBinhPhapDispatcher:
    """Test dispatcher translates topology decisions correctly."""

    def test_vertical_dispatch(self, tmp_company: str) -> None:
        from src.core.binh_phap_dispatcher import BinhPhapDispatcher
        d = BinhPhapDispatcher(company_json=tmp_company)
        action = d.next_action()
        assert action["action"] == "execute"
        assert action["command"] == "swot"
        assert action["dimension"] == "vertical"
        assert isinstance(action["needs_approval"], bool)

    def test_report_result_advances(self, tmp_company: str) -> None:
        from src.core.binh_phap_dispatcher import BinhPhapDispatcher
        d = BinhPhapDispatcher(company_json=tmp_company)
        d.report_result("swot", success=True)
        action = d.next_action()
        assert action["command"] == "plan"

    def test_failure_tracking(self, tmp_company: str) -> None:
        from src.core.binh_phap_dispatcher import BinhPhapDispatcher
        d = BinhPhapDispatcher(company_json=tmp_company)
        d.report_result("swot", success=False, error="failed")
        assert d.topology.consecutive_failures == 1

    def test_event_handling(self, tmp_company: str) -> None:
        from src.core.binh_phap_dispatcher import BinhPhapDispatcher
        d = BinhPhapDispatcher(company_json=tmp_company)
        actions = d.handle_event("ci.failed", source="github")
        assert len(actions) > 0
        assert actions[0]["event"] == "ci.failed"
        assert "debug" in actions[0]["commands"]

    def test_status_report(self, tmp_company: str) -> None:
        from src.core.binh_phap_dispatcher import BinhPhapDispatcher
        d = BinhPhapDispatcher(company_json=tmp_company)
        status = d.get_status()
        assert status["dimension"] == "vertical"
        assert status["next_command"] == "swot"
        assert "groups" in status

    def test_cycle_lesson(self, tmp_company: str) -> None:
        from src.core.binh_phap_dispatcher import BinhPhapDispatcher
        d = BinhPhapDispatcher(company_json=tmp_company)
        d.report_cycle_lesson(
            mrr=500.0,
            customers=10,
            lessons=["Show HN drove 50 signups"],
        )
        state = d.topology.state
        assert len(state["cycle_history"]) == 1
        assert state["cycle_history"][0]["result"]["mrr"] == 500.0

    def test_stop_after_max_failures(self, tmp_company: str) -> None:
        from src.core.binh_phap_dispatcher import BinhPhapDispatcher
        d = BinhPhapDispatcher(company_json=tmp_company)
        for _ in range(3):
            d.report_result("swot", success=False)
        action = d.next_action()
        assert action["action"] == "stop"

    def test_unknown_event_returns_no_reaction(self, tmp_company: str) -> None:
        from src.core.binh_phap_dispatcher import BinhPhapDispatcher
        d = BinhPhapDispatcher(company_json=tmp_company)
        actions = d.handle_event("unknown.event.type")
        assert len(actions) == 1
        assert actions[0]["commands"] == []


class TestEscalationRouting:
    """Test LLM escalation routing — all cloud (local LLM removed)."""

    _ROUTING_ENV_VARS = (
        "ZUNEF_FABLE_BASE_URL", "ZUNEF_FABLE_MODEL", "ZUNEF_OPUS_BASE_URL",
        "ZUNEF_OPUS_MODEL", "ZUNEF_SONNET_BASE_URL", "ZUNEF_SONNET_MODEL",
        "ZUNEF_API_KEY", "FABLE_BASE_URL", "FABLE_MODEL", "OPUS_BASE_URL",
        "OPUS_MODEL", "SONNET_BASE_URL", "SONNET_MODEL",
        "LLM_BASE_URL", "LLM_MODEL", "LLM_API_KEY",
        "ANTHROPIC_BASE_URL", "ANTHROPIC_API_KEY",
    )

    def _clean_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Drop all LLM routing env vars so tests assert code defaults."""
        for key in self._ROUTING_ENV_VARS:
            monkeypatch.delenv(key, raising=False)

    def test_resolve_local_mlx_is_cloud_fable(self, monkeypatch) -> None:
        # Legacy "local_mlx" level now resolves to cloud Fable via omnimbp proxy
        from src.core.binh_phap_escalation import resolve_llm_provider
        self._clean_env(monkeypatch)
        config = resolve_llm_provider("local_mlx")
        # Default is omnimbp proxy v1 endpoint
        assert config["base_url"] == "http://omnimbp.local:20128/api/v1"
        assert config["provider_name"] == "anthropic-fable"
        assert "fable" in config["model"]
        assert "api_key_env" in config

    def test_resolve_cloud_sonnet(self, monkeypatch) -> None:
        from src.core.binh_phap_escalation import resolve_llm_provider
        self._clean_env(monkeypatch)
        config = resolve_llm_provider("cloud_sonnet")
        # Default is omnimbp proxy v1 endpoint
        assert config["base_url"] == "http://omnimbp.local:20128/api/v1"
        assert "sonnet" in config["model"]

    def test_resolve_cloud_opus(self, monkeypatch) -> None:
        from src.core.binh_phap_escalation import resolve_llm_provider
        self._clean_env(monkeypatch)
        config = resolve_llm_provider("cloud_opus")
        # Default is omnimbp proxy v1 endpoint
        assert config["base_url"] == "http://omnimbp.local:20128/api/v1"
        assert "opus" in config["model"]

    def test_resolve_unknown_defaults_to_fable(self, monkeypatch) -> None:
        from src.core.binh_phap_escalation import resolve_llm_provider
        self._clean_env(monkeypatch)
        config = resolve_llm_provider("unknown_level")
        assert config["provider_name"] == "anthropic-fable"
        assert config["model"] == "claude-fable-5"

    def test_get_llm_for_command(self, tmp_company: str, monkeypatch) -> None:
        from src.core.binh_phap_dispatcher import BinhPhapDispatcher
        self._clean_env(monkeypatch)
        d = BinhPhapDispatcher(company_json=tmp_company)
        # standup = AUTONOMOUS → cloud_sonnet (was local_mlx)
        config = d.get_llm_for_command("standup")
        assert config["escalation_level"] == "cloud_sonnet"
        # launch = APPROVE → cloud_sonnet
        config = d.get_llm_for_command("launch")
        assert config["escalation_level"] == "cloud_sonnet"
        # pivot = STRATEGIC → cloud_opus
        config = d.get_llm_for_command("pivot")
        assert config["escalation_level"] == "cloud_opus"

    def test_escalation_provider_configs_complete(self, monkeypatch) -> None:
        from src.core.binh_phap_escalation import resolve_llm_provider
        self._clean_env(monkeypatch)
        for level in ("strategic", "cloud_opus", "cloud_sonnet", "standard",
                      "local_mlx", "tactical", "unknown_level"):
            config = resolve_llm_provider(level)
            assert "base_url" in config, f"{level} missing base_url"
            assert "model" in config, f"{level} missing model"
            assert "provider_name" in config, f"{level} missing provider_name"
            # Default is omnimbp proxy (cloud), not localhost
            assert config["base_url"] == "http://omnimbp.local:20128/api/v1", f"{level} not omnimbp proxy"
