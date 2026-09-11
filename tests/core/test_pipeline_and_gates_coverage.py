# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests driving 100% statement and branch coverage for core pipeline and gate modules:
- src/core/binh_phap_escalation.py
- src/core/spec_templates.py
- src/core/request_logger.py
- src/core/feature_gates.py
- src/core/fallback_chain.py
- src/core/pipeline_stages.py
- src/core/routing_strategy_abc.py
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import typer
from starlette.requests import Request
from starlette.responses import Response

from src.core.binh_phap_escalation import (
    ANTHROPIC_DIRECT_BASE_URL,
    FABLE_MODEL,
    OPUS_MODEL,
    _first_env,
    _resolve,
    create_provider_for_level,
    resolve_llm_provider,
)
from src.core.fallback_chain import (
    FALLBACK_HIERARCHY,
    FallbackResult,
    RateLimitError,
    execute_with_fallback,
    get_fallback_models,
    rebuild_config,
)
from src.core.feature_gates import (
    FeatureGateError,
    get_enabled_features,
    has_feature,
    require_feature,
    show_features_status,
)
from src.core.model_selector import ModelConfig
from src.core.pipeline_stages import (
    ALL_STAGES,
    DEFAULT_PIPELINE,
    EDITOR_STAGE,
    FILE_PICKER_STAGE,
    PipelineStage,
    REVIEWER_STAGE,
    compose_pipeline,
    get_stage,
    stages_by_phase,
)
from src.core.request_logger import RequestLoggerMiddleware
from src.core.routing_strategy_abc import (
    CostOptimizedStrategy,
    LatencyFirstStrategy,
    ModelSelection,
    RoutingStrategy,
)
import src.core.spec_templates as st
from src.core.spec_templates import (
    _SafeDict,
    _load_all,
    load_template,
    render,
    write_artifact,
    write_json_artifact,
)


# ─── 1. Binh Phap Escalation ──────────────────────────────────────────────────


class TestBinhPhapEscalation:
    def test_constants_and_first_env(self):
        assert FABLE_MODEL == "claude-fable-5"
        assert OPUS_MODEL == "claude-opus-4-8"
        assert ANTHROPIC_DIRECT_BASE_URL == "https://api.anthropic.com/v1"

        with patch.dict("os.environ", {"FOO": "bar", "BAZ": "qux"}, clear=True):
            assert _first_env("NONEXISTENT", "FOO", default="fallback") == "bar"
            assert _first_env("BAZ", "FOO", default="fallback") == "qux"
            assert _first_env("NOT_HERE", default="fallback") == "fallback"

    def test_resolve_default_anthropic(self):
        with patch.dict("os.environ", {}, clear=True):
            res = _resolve("OPUS", OPUS_MODEL)
            assert res["base_url"] == ANTHROPIC_DIRECT_BASE_URL
            assert res["model"] == OPUS_MODEL
            assert res["provider_name"] == "anthropic-opus"
            assert res["api_key_env"] == "ANTHROPIC_API_KEY"

    def test_resolve_zunef_env_override(self):
        env_vars = {
            "ZUNEF_OPUS_BASE_URL": "https://gateway.zunef.com/v1",
            "ZUNEF_OPUS_MODEL": "custom-opus-zunef",
        }
        with patch.dict("os.environ", env_vars, clear=True):
            res = _resolve("OPUS", OPUS_MODEL)
            assert res["base_url"] == "https://gateway.zunef.com/v1"
            assert res["model"] == "custom-opus-zunef"
            assert res["provider_name"] == "zunef-opus"
            assert res["api_key_env"] == "ZUNEF_API_KEY"

    def test_resolve_llm_provider_tiers(self):
        with patch.dict("os.environ", {}, clear=True):
            # Opus tier
            assert resolve_llm_provider("strategic")["model"] == OPUS_MODEL
            assert resolve_llm_provider("cloud_opus")["model"] == OPUS_MODEL
            assert resolve_llm_provider("AUTONOMOUS")["model"] == OPUS_MODEL

            # Sonnet tier
            assert resolve_llm_provider("cloud_sonnet")["model"] == "claude-sonnet-4-6"
            assert resolve_llm_provider("standard")["model"] == "claude-sonnet-4-6"

            # Tactical / local tier -> Fable
            assert resolve_llm_provider("tactical")["model"] == FABLE_MODEL
            assert resolve_llm_provider("local_mlx")["model"] == FABLE_MODEL
            assert resolve_llm_provider("other_xyz")["model"] == FABLE_MODEL

    def test_create_provider_import_error(self):
        with patch.dict("sys.modules", {"src.core.providers": None}):
            res = create_provider_for_level("strategic")
            assert res is None

    def test_create_provider_missing_api_key(self):
        mock_providers = MagicMock()
        with patch.dict("sys.modules", {"src.core.providers": mock_providers}):
            with patch.dict("os.environ", {}, clear=True):
                res = create_provider_for_level("strategic")
                assert res is None

    def test_create_provider_success(self):
        mock_providers = MagicMock()
        mock_openai_provider = MagicMock()
        mock_providers.OpenAICompatibleProvider = mock_openai_provider

        with patch.dict("sys.modules", {"src.core.providers": mock_providers}):
            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"}, clear=True):
                res = create_provider_for_level("strategic")
                assert res is not None
                mock_openai_provider.assert_called_once_with(
                    base_url=ANTHROPIC_DIRECT_BASE_URL,
                    api_key="sk-ant-test",
                    model=OPUS_MODEL,
                    provider_name="anthropic-opus",
                    timeout=120,
                )


# ─── 2. Spec Templates ────────────────────────────────────────────────────────


class TestSpecTemplates:
    def test_safe_dict(self):
        d = _SafeDict({"name": "Mekong"})
        assert d["name"] == "Mekong"
        assert d["unknown_key"] == "{unknown_key}"

    def test_load_all_and_cache(self, tmp_path):
        # Reset cache
        st._TEMPLATE_CACHE = None

        # Non-directory case
        with patch.object(st, "TEMPLATES_DIR", tmp_path / "nonexistent"):
            cache = _load_all()
            assert cache == {}
            assert st._TEMPLATE_CACHE == {}

        # Reset cache again
        st._TEMPLATE_CACHE = None

        # Directory with *-template.md files
        tpl_dir = tmp_path / "templates"
        tpl_dir.mkdir()
        (tpl_dir / "sample-template.md").write_text("Hello {name}! ts={timestamp}", encoding="utf-8")
        (tpl_dir / "other.txt").write_text("Ignored", encoding="utf-8")

        with patch.object(st, "TEMPLATES_DIR", tpl_dir):
            cache = _load_all()
            assert "sample" in cache
            assert cache["sample"] == "Hello {name}! ts={timestamp}"

            # Subsequent call returns early from cache
            cache2 = _load_all()
            assert cache2 is cache

    def test_load_template_and_render(self):
        with patch.object(st, "_TEMPLATE_CACHE", {"my_tpl": "Hi {user}, token={token}, ts={timestamp}!"}):
            assert load_template("my_tpl") == "Hi {user}, token={token}, ts={timestamp}!"
            assert load_template("missing") == ""

            # Render missing template returns empty string
            assert render("missing", {}) == ""

            # Render with safe placeholder substitution and automatic timestamp default
            rendered = render("my_tpl", {"user": "Long"})
            assert "Hi Long, token={token}, ts=" in rendered

    def test_render_substitution_error_fallback(self):
        # Malformed format string that triggers ValueError in str.format_map
        with patch.object(st, "_TEMPLATE_CACHE", {"bad_tpl": "Broken {unclosed"}):
            # Should catch ValueError and return unrendered template
            assert render("bad_tpl", {}) == "Broken {unclosed"

    def test_write_artifact(self, tmp_path):
        out_file = tmp_path / "nested" / "output.txt"
        with patch.object(st, "_TEMPLATE_CACHE", {"my_tpl": "Content: {name}"}):
            res = write_artifact(out_file, "my_tpl", {"name": "TestArtifact"})
            assert res == out_file.resolve()
            assert out_file.read_text(encoding="utf-8") == "Content: TestArtifact"

    def test_write_json_artifact(self, tmp_path):
        out_file = tmp_path / "nested" / "data.json"
        data = {"key": "value", "count": 42}
        res = write_json_artifact(str(out_file), data)
        assert res == out_file.resolve()
        assert '"key": "value"' in out_file.read_text(encoding="utf-8")


# ─── 3. Request Logger Middleware ─────────────────────────────────────────────


class TestRequestLogger:
    @pytest.mark.asyncio
    async def test_dispatch_success_with_client(self):
        app = MagicMock()
        middleware = RequestLoggerMiddleware(app)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/test",
            "headers": [],
            "client": ("127.0.0.1", 12345),
        }
        request = Request(scope)

        async def call_next(req: Request) -> Response:
            return Response("OK", status_code=200)

        response = await middleware.dispatch(request, call_next)
        assert "X-Request-ID" in response.headers
        assert request.state.request_id == response.headers["X-Request-ID"]
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_dispatch_success_without_client(self):
        app = MagicMock()
        middleware = RequestLoggerMiddleware(app)

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/data",
            "headers": [],
            "client": None,
        }
        request = Request(scope)

        async def call_next(req: Request) -> Response:
            return Response("Created", status_code=201)

        response = await middleware.dispatch(request, call_next)
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 10
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_dispatch_exception_handled_and_reraised(self):
        app = MagicMock()
        middleware = RequestLoggerMiddleware(app)

        scope = {
            "type": "http",
            "method": "DELETE",
            "path": "/api/v1/error",
            "headers": [],
            "client": ("192.168.1.1", 80),
        }
        request = Request(scope)

        async def failing_call_next(req: Request) -> Response:
            raise ValueError("Server calculation exploded")

        with pytest.raises(ValueError, match="Server calculation exploded"):
            await middleware.dispatch(request, failing_call_next)


# ─── 4. Feature Gates ─────────────────────────────────────────────────────────


class TestFeatureGates:
    def test_feature_gate_error(self):
        err = FeatureGateError("advanced_agents", "free")
        assert err.feature == "advanced_agents"
        assert err.tier == "free"
        assert "advanced_agents" in str(err)
        assert "free" in str(err)

    def test_get_enabled_features_with_tenant(self):
        tenant_mock = MagicMock(features=["cli_commands", "advanced_agents"])
        auth_client = MagicMock()
        auth_client.get_tenant_context.return_value = tenant_mock

        with patch("src.core.feature_gates.get_auth_client", return_value=auth_client):
            assert get_enabled_features() == ["cli_commands", "advanced_agents"]

        # tenant with features=None returns []
        tenant_mock.features = None
        with patch("src.core.feature_gates.get_auth_client", return_value=auth_client):
            assert get_enabled_features() == []

    def test_get_enabled_features_without_tenant_unauthenticated(self):
        session_mock = MagicMock(authenticated=False)
        auth_client = MagicMock()
        auth_client.get_tenant_context.return_value = None
        auth_client.get_session.return_value = session_mock

        with patch("src.core.feature_gates.get_auth_client", return_value=auth_client):
            assert get_enabled_features() == []

    def test_get_enabled_features_authenticated_session(self):
        session_mock = MagicMock(authenticated=True)
        auth_client = MagicMock()
        auth_client.get_tenant_context.return_value = None
        auth_client.get_session.return_value = session_mock

        # No token in credentials
        auth_client._load_credentials.return_value = {}
        with patch("src.core.feature_gates.get_auth_client", return_value=auth_client):
            assert get_enabled_features() == []

        # Token present and validation succeeds with tenant
        auth_client._load_credentials.return_value = {"token": "jwt-token"}
        validation_result = MagicMock(valid=True, tenant=MagicMock(features=["cli_commands"]))
        auth_client.validate_credentials.return_value = validation_result
        with patch("src.core.feature_gates.get_auth_client", return_value=auth_client):
            assert get_enabled_features() == ["cli_commands"]

        # Token present and validation succeeds with tenant.features is None
        validation_result.tenant.features = None
        with patch("src.core.feature_gates.get_auth_client", return_value=auth_client):
            assert get_enabled_features() == []

        # Token present and validation fails
        validation_result.valid = False
        with patch("src.core.feature_gates.get_auth_client", return_value=auth_client):
            assert get_enabled_features() == []

    def test_has_feature(self):
        with patch("src.core.feature_gates.get_enabled_features", return_value=["all_features"]):
            assert has_feature("any_feature") is True

        with patch("src.core.feature_gates.get_enabled_features", return_value=["cli_commands"]):
            assert has_feature("cli_commands") is True
            assert has_feature("advanced_agents") is False

    def test_require_feature_decorator_allowed(self):
        @require_feature("cli_commands")
        def sample_cmd(x: int) -> int:
            return x * 2

        with patch("src.core.feature_gates.has_feature", return_value=True):
            assert sample_cmd(21) == 42

    def test_require_feature_decorator_denied_with_tenant(self):
        @require_feature("advanced_agents")
        def premium_cmd():
            return "ok"

        auth_client = MagicMock()
        auth_client.get_tenant_context.return_value = MagicMock(tier="basic")

        with patch("src.core.feature_gates.has_feature", return_value=False):
            with patch("src.core.feature_gates.get_auth_client", return_value=auth_client):
                with pytest.raises(typer.Exit) as exc_info:
                    premium_cmd()
                assert exc_info.value.exit_code == 1

    def test_require_feature_decorator_denied_without_tenant(self):
        @require_feature("advanced_agents")
        def premium_cmd():
            return "ok"

        auth_client = MagicMock()
        auth_client.get_tenant_context.return_value = None

        with patch("src.core.feature_gates.has_feature", return_value=False):
            with patch("src.core.feature_gates.get_auth_client", return_value=auth_client):
                with pytest.raises(typer.Exit) as exc_info:
                    premium_cmd()
                assert exc_info.value.exit_code == 1

    def test_show_features_status_authenticated_and_unauthenticated(self):
        auth_client = MagicMock()
        session_mock = MagicMock(authenticated=True, tier="premium", tenant_id="tenant-123")
        auth_client.get_session.return_value = session_mock

        with patch("src.core.feature_gates.get_auth_client", return_value=auth_client):
            with patch("src.core.feature_gates.get_enabled_features", return_value=["cli_commands", "advanced_agents"]):
                show_features_status()

        # Unauthenticated
        session_mock.authenticated = False
        with patch("src.core.feature_gates.get_auth_client", return_value=auth_client):
            with patch("src.core.feature_gates.get_enabled_features", return_value=[]):
                show_features_status()


# ─── 5. Fallback Chain ────────────────────────────────────────────────────────


class TestFallbackChain:
    def test_fallback_result_and_rebuild_config(self):
        res = FallbackResult(success=True, model_used="test-model", tokens_output=10, attempts=["m1"])
        assert res.success is True
        assert res.model_used == "test-model"

        cfg = rebuild_config("ollama:qwen3.5-4b", temperature=0.7, max_tokens=2048)
        assert cfg.model_id == "ollama:qwen3.5-4b"
        assert cfg.temperature == 0.7
        assert cfg.max_tokens == 2048
        assert cfg.context_window == 32000

    def test_get_fallback_models_public_vs_sensitive(self):
        # Public
        models = get_fallback_models("claude-sonnet-4-6", attempted=[])
        assert "ollama:qwen3.6-35b" in models

        # Attempted model excluded
        models_filtered = get_fallback_models("claude-sonnet-4-6", attempted=["ollama:qwen3.6-35b"])
        assert "ollama:qwen3.6-35b" not in models_filtered

        # Sensitive: filters out non-ollama models
        with patch.dict(FALLBACK_HIERARCHY, {"test-parent": ["claude-opus-4-6", "ollama:qwen3.5-4b"]}):
            sensitive_models = get_fallback_models("test-parent", attempted=[], data_sensitivity="sensitive")
            assert sensitive_models == ["ollama:qwen3.5-4b"]

    @pytest.mark.asyncio
    async def test_execute_with_fallback_ollama_success(self):
        tokens_seen = []

        async def token_cb(t: str):
            tokens_seen.append(t)

        async def fake_tokens(*args, **kwargs):
            yield "Hello"
            yield " "
            yield "World"

        mock_adapter = MagicMock()
        mock_adapter.generate.return_value = fake_tokens()

        with patch("src.core.local_adapter.OllamaAdapter", return_value=mock_adapter):
            cfg = ModelConfig(
                model_id="ollama:qwen3.5-4b",
                provider="ollama",
                max_tokens=100,
                temperature=0.2,
                context_window=4096,
                cost_per_mtok_input=0.0,
                cost_per_mtok_output=0.0,
            )
            res = await execute_with_fallback(
                model_config=cfg,
                messages=[{"role": "user", "content": "hi"}],
                system_prompt="sys",
                on_token_cb=token_cb,
            )
            assert res.success is True
            assert res.output == "Hello World"
            assert res.tokens_output == 3
            assert tokens_seen == ["Hello", " ", "World"]

    @pytest.mark.asyncio
    async def test_execute_with_fallback_api_success_without_callback(self):
        tokens_seen = []

        async def token_cb(t: str):
            tokens_seen.append(t)

        async def fake_tokens(*args, **kwargs):
            yield "API"
            yield " Response"

        mock_api_adapter = MagicMock()
        mock_api_adapter.generate.return_value = fake_tokens()

        with patch("src.core.api_adapter.APIAdapter", return_value=mock_api_adapter):
            cfg = ModelConfig(
                model_id="claude-haiku-4-5",
                provider="anthropic",
                max_tokens=100,
                temperature=0.2,
                context_window=4096,
                cost_per_mtok_input=1.0,
                cost_per_mtok_output=5.0,
            )
            res = await execute_with_fallback(
                model_config=cfg,
                messages=[{"role": "user", "content": "hi"}],
                system_prompt="system",
                on_token_cb=token_cb,
            )
            assert res.success is True
            assert res.output == "API Response"
            assert res.tokens_output == 2
            assert tokens_seen == ["API", " Response"]

    @pytest.mark.asyncio
    async def test_execute_with_fallback_rate_limit_retry(self):
        call_count = 0

        async def fake_generator(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RateLimitError("429 Too Many Requests")
            yield "Recovered"

        mock_adapter = MagicMock()
        mock_adapter.generate.side_effect = fake_generator

        with patch("src.core.local_adapter.OllamaAdapter", return_value=mock_adapter):
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                cfg = ModelConfig(
                    model_id="ollama:qwen3.5-4b",
                    provider="ollama",
                    max_tokens=100,
                    temperature=0.2,
                    context_window=4096,
                    cost_per_mtok_input=0.0,
                    cost_per_mtok_output=0.0,
                )
                res = await execute_with_fallback(
                    model_config=cfg,
                    messages=[{"role": "user", "content": "hi"}],
                    system_prompt=None,
                    on_token_cb=None,
                )
                assert res.success is True
                assert res.output == "Recovered"
                assert mock_sleep.called

    @pytest.mark.asyncio
    async def test_execute_with_fallback_connection_error_switches_model(self):
        call_models = []

        async def fake_generator_ollama(model, *args, **kwargs):
            call_models.append(model)
            if model == "ollama:qwen3.6-35b":
                raise ConnectionError("Port offline")
            yield "Fallback OK"

        mock_adapter = MagicMock()
        mock_adapter.generate.side_effect = fake_generator_ollama

        with patch("src.core.local_adapter.OllamaAdapter", return_value=mock_adapter):
            cfg = ModelConfig(
                model_id="ollama:qwen3.6-35b",
                provider="ollama",
                max_tokens=100,
                temperature=0.2,
                context_window=4096,
                cost_per_mtok_input=0.0,
                cost_per_mtok_output=0.0,
            )
            res = await execute_with_fallback(
                model_config=cfg,
                messages=[{"role": "user", "content": "hi"}],
                system_prompt=None,
                on_token_cb=None,
            )
            assert res.success is True
            assert res.output == "Fallback OK"
            assert "ollama:qwen3.6-35b" in call_models
            assert "ollama:qwen3.5-9b" in call_models

    @pytest.mark.asyncio
    async def test_execute_with_fallback_all_fail_no_more_models(self):
        async def fail_generator(*args, **kwargs):
            raise OSError("Network broken")
            yield "never"

        mock_adapter = MagicMock()
        mock_adapter.generate.side_effect = fail_generator

        with patch("src.core.local_adapter.OllamaAdapter", return_value=mock_adapter):
            with patch.dict(FALLBACK_HIERARCHY, {"ollama:lonely": []}, clear=True):
                cfg = ModelConfig(
                    model_id="ollama:lonely",
                    provider="ollama",
                    max_tokens=100,
                    temperature=0.2,
                    context_window=4096,
                    cost_per_mtok_input=0.0,
                    cost_per_mtok_output=0.0,
                )
                res = await execute_with_fallback(
                    model_config=cfg,
                    messages=[{"role": "user", "content": "hi"}],
                    system_prompt=None,
                    on_token_cb=None,
                )
                assert res.success is False
                assert res.error == "all_models_failed"


# ─── 6. Pipeline Stages ───────────────────────────────────────────────────────


class TestPipelineStages:
    def test_pipeline_stage_defaults(self):
        stg = PipelineStage(name="custom", agent_class="agents.CustomAgent")
        assert stg.name == "custom"
        assert stg.agent_class == "agents.CustomAgent"
        assert stg.allowed_tools == []
        assert stg.phase == "execute"
        assert stg.optional is True
        assert stg.description == ""

    def test_predefined_stages(self):
        assert FILE_PICKER_STAGE.phase == "plan"
        assert EDITOR_STAGE.phase == "execute"
        assert REVIEWER_STAGE.phase == "verify"
        assert DEFAULT_PIPELINE == ["file-picker", "editor", "reviewer"]
        assert set(ALL_STAGES.keys()) == {"file-picker", "editor", "reviewer"}

    def test_get_stage(self):
        assert get_stage("file-picker") == FILE_PICKER_STAGE
        assert get_stage("editor") == EDITOR_STAGE
        assert get_stage("reviewer") == REVIEWER_STAGE

        with pytest.raises(KeyError, match="Unknown pipeline stage: 'nonexistent'"):
            get_stage("nonexistent")

    def test_compose_pipeline_default(self):
        pipeline = compose_pipeline()
        assert len(pipeline) == 3
        assert pipeline[0] == FILE_PICKER_STAGE
        assert pipeline[1] == EDITOR_STAGE
        assert pipeline[2] == REVIEWER_STAGE

    def test_compose_pipeline_with_filter_and_invalid(self):
        # enabled_phases filter
        pipeline = compose_pipeline(enabled_phases=["plan", "verify"])
        assert len(pipeline) == 2
        assert pipeline[0] == FILE_PICKER_STAGE
        assert pipeline[1] == REVIEWER_STAGE

        # Unknown stage is skipped
        pipeline_with_unknown = compose_pipeline(stage_names=["file-picker", "bogus", "reviewer"])
        assert len(pipeline_with_unknown) == 2
        assert pipeline_with_unknown[0] == FILE_PICKER_STAGE
        assert pipeline_with_unknown[1] == REVIEWER_STAGE

    def test_stages_by_phase(self):
        assert stages_by_phase("plan") == [FILE_PICKER_STAGE]
        assert stages_by_phase("execute") == [EDITOR_STAGE]
        assert stages_by_phase("verify") == [REVIEWER_STAGE]
        assert stages_by_phase("unknown") == []


# ─── 7. Routing Strategy ABC ──────────────────────────────────────────────────


class TestRoutingStrategyABC:
    def test_model_selection_dataclass(self):
        sel = ModelSelection(model_id="gpt-4o", provider="openai", tier="PREMIUM", fallback=False)
        assert sel.model_id == "gpt-4o"
        assert sel.provider == "openai"
        assert sel.tier == "PREMIUM"
        assert sel.fallback is False

    def test_cost_optimized_strategy_known_tiers_and_tasks(self):
        strat = CostOptimizedStrategy()
        assert isinstance(strat, RoutingStrategy)

        # BASIC
        res = strat.select_model("basic", "chat")
        assert res.model_id == "gpt-4o-mini"
        assert res.provider == "openai"
        assert res.tier == "BASIC"

        # PREMIUM
        res = strat.select_model("PREMIUM", "code")
        assert res.model_id == "claude-sonnet-4"
        assert res.provider == "anthropic"

        # ENTERPRISE
        res = strat.select_model("ENTERPRISE", "chat")
        assert res.model_id == "claude-sonnet-4"
        assert res.provider == "anthropic"

        # MASTER
        res = strat.select_model("MASTER", "code")
        assert res.model_id == "claude-opus-4"
        assert res.provider == "anthropic"

        # Unknown task type falls back to tier default
        res_def = strat.select_model("BASIC", "unknown_task")
        assert res_def.model_id == "gpt-4o-mini"

        # Unknown tier falls back to global default
        res_unknown_tier = strat.select_model("NONEXISTENT_TIER", "chat")
        assert res_unknown_tier.model_id == "fable-5o-mini"
        assert res_unknown_tier.provider == "openai"

    def test_latency_first_strategy_known_tiers_and_tasks(self):
        strat = LatencyFirstStrategy()
        assert isinstance(strat, RoutingStrategy)

        # BASIC
        res = strat.select_model("basic", "chat")
        assert res.model_id == "gpt-4o-mini"
        assert res.provider == "openai"

        # PREMIUM
        res = strat.select_model("PREMIUM", "code")
        assert res.model_id == "gpt-4o"

        # ENTERPRISE
        res = strat.select_model("ENTERPRISE", "code")
        assert res.model_id == "claude-sonnet-4"

        # MASTER
        res = strat.select_model("MASTER", "code")
        assert res.model_id == "claude-sonnet-4"

        # Unknown task type falls back to tier default
        res_def = strat.select_model("MASTER", "unknown_task")
        assert res_def.model_id == "claude-sonnet-4"

        # Unknown tier falls back to global default
        res_unknown = strat.select_model("STRANGE_TIER", "vision")
        assert res_unknown.model_id == "gpt-4o-mini"
        assert res_unknown.provider == "openai"
