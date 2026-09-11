"""Tests for Telemetry & Trust Subsystem.

Covers:
- src.core.telemetry_consent (ConsentPreferences, ConsentManager, get_consent_manager)
- src.core.telemetry_init (init_telemetry)
- src.core.telemetry_models (StepTrace, ExecutionTrace, SubsystemHealth, SubsystemHealthReport)
- src.core.telemetry_reporter (UsageRecord, TelemetryReporter, get_telemetry_reporter)
- src.core.telemetry_sink_adapter (TelemetrySinkAdapter)
- src.core.certificate_store (CertificateStoreError, CertificateMetadata, CertificateStore, get_certificate_store)
"""
from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.core.certificate_store import (
    CertificateMetadata,
    CertificateStore,
    CertificateStoreError,
    get_certificate_store,
)
from src.core.telemetry_consent import (
    ConsentManager,
    ConsentPreferences,
    get_consent_manager,
)
from src.core.telemetry_init import init_telemetry
from src.core.telemetry_models import (
    ExecutionTrace,
    StepTrace,
    SubsystemHealth,
    SubsystemHealthReport,
)
from src.core.telemetry_reporter import (
    TelemetryReporter,
    UsageRecord,
    get_telemetry_reporter,
)
from src.core.telemetry_sink_adapter import TelemetrySinkAdapter


# ---------------------------------------------------------------------------
# src.core.telemetry_consent
# ---------------------------------------------------------------------------
class TestTelemetryConsent:
    def test_consent_preferences_defaults(self):
        pref = ConsentPreferences()
        assert pref.consent_given is False
        assert pref.consent_timestamp == ""
        assert pref.anonymous_id == ""
        assert pref.version == "1.0"

    def test_consent_manager_ensure_config_dir(self, tmp_path):
        cfg_dir = tmp_path / "custom_config"
        mgr = ConsentManager(config_dir=str(cfg_dir))
        assert not cfg_dir.exists()
        mgr.ensure_config_dir()
        assert cfg_dir.exists()

    def test_load_consent_nonexistent(self, tmp_path):
        mgr = ConsentManager(config_dir=str(tmp_path))
        assert mgr.load_consent() is None

    def test_load_consent_corrupt_json(self, tmp_path):
        mgr = ConsentManager(config_dir=str(tmp_path))
        mgr.ensure_config_dir()
        (tmp_path / "telemetry-consent.json").write_text("invalid json{{")
        assert mgr.load_consent() is None

    def test_load_consent_key_error(self, tmp_path):
        mgr = ConsentManager(config_dir=str(tmp_path))
        mgr.ensure_config_dir()
        (tmp_path / "telemetry-consent.json").write_text(json.dumps({"unknown_field": 123}))
        assert mgr.load_consent() is None

    def test_save_and_load_consent(self, tmp_path):
        mgr = ConsentManager(config_dir=str(tmp_path))
        pref = ConsentPreferences(
            consent_given=True,
            consent_timestamp="2026-09-11T00:00:00Z",
            anonymous_id="anon-xyz",
            version="1.0",
        )
        mgr.save_consent(pref)
        assert mgr.has_consent() is True

        # Test cached load
        cached = mgr.load_consent()
        assert cached == pref

        # Test fresh load from file
        mgr2 = ConsentManager(config_dir=str(tmp_path))
        loaded = mgr2.load_consent()
        assert loaded is not None
        assert loaded.consent_given is True
        assert loaded.anonymous_id == "anon-xyz"

    def test_prompt_consent_user_agrees(self, tmp_path):
        mgr = ConsentManager(config_dir=str(tmp_path))
        with patch("rich.prompt.Confirm.ask", return_value=True):
            res = mgr.prompt_consent()
            assert res.consent_given is True
            assert len(res.anonymous_id) > 0
            assert mgr.has_consent() is True

    def test_prompt_consent_user_declines(self, tmp_path):
        mgr = ConsentManager(config_dir=str(tmp_path))
        with patch("rich.prompt.Confirm.ask", return_value=False):
            res = mgr.prompt_consent()
            assert res.consent_given is False
            assert mgr.has_consent() is False

    def test_get_anonymous_id(self, tmp_path):
        mgr = ConsentManager(config_dir=str(tmp_path))
        assert mgr.get_anonymous_id() is None

        mgr.enable()
        anon_id = mgr.get_anonymous_id()
        assert anon_id is not None

        mgr.disable()
        assert mgr.get_anonymous_id() is None

    def test_enable_and_disable(self, tmp_path):
        mgr = ConsentManager(config_dir=str(tmp_path))
        pref = mgr.enable()
        assert pref.consent_given is True
        assert len(pref.anonymous_id) > 0

        # Enable again retains or sets id
        pref2 = mgr.enable()
        assert pref2.consent_given is True
        assert pref2.anonymous_id == pref.anonymous_id

        pref3 = mgr.disable()
        assert pref3.consent_given is False

    def test_get_status_not_set(self, tmp_path):
        mgr = ConsentManager(config_dir=str(tmp_path))
        st = mgr.get_status()
        assert st["status"] == "not_set"
        assert "not set" in st["message"]

    def test_get_status_enabled_and_disabled(self, tmp_path):
        mgr = ConsentManager(config_dir=str(tmp_path))
        mgr.enable()
        st = mgr.get_status()
        assert st["status"] == "enabled"
        assert st["anonymous_id"] is not None

        mgr.disable()
        st = mgr.get_status()
        assert st["status"] == "disabled"
        assert st["anonymous_id"] is None

    def test_get_consent_manager_singleton(self):
        cm = get_consent_manager()
        assert isinstance(cm, ConsentManager)


# ---------------------------------------------------------------------------
# src.core.telemetry_init
# ---------------------------------------------------------------------------
class TestTelemetryInit:
    def test_init_telemetry_no_endpoint(self, monkeypatch):
        monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
        init_telemetry()

    def test_init_telemetry_with_endpoint_and_instrumentor(self, monkeypatch):
        monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        monkeypatch.setenv("APP_VERSION", "6.0.0")

        mock_provider = MagicMock()
        mock_instrumentor = MagicMock()

        with patch("src.core.telemetry_init.TracerProvider", return_value=mock_provider), \
             patch("src.core.telemetry_init.trace.set_tracer_provider") as mock_set_provider, \
             patch.dict("sys.modules", {"opentelemetry.instrumentation.fastapi": MagicMock(FastAPIInstrumentor=mock_instrumentor)}):
            init_telemetry()
            mock_set_provider.assert_called_once_with(mock_provider)
            mock_instrumentor.instrument_app.assert_called_once()

    def test_init_telemetry_import_error_handled(self, monkeypatch):
        monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        with patch("src.core.telemetry_init.TracerProvider", return_value=MagicMock()), \
             patch("src.core.telemetry_init.trace.set_tracer_provider"):
            with patch.dict("sys.modules", {"opentelemetry.instrumentation.fastapi": None}):
                init_telemetry()


# ---------------------------------------------------------------------------
# src.core.telemetry_models
# ---------------------------------------------------------------------------
class TestTelemetryModels:
    def test_step_trace_fields(self):
        st = StepTrace(
            step_order=1,
            title="Step 1",
            duration_seconds=1.23,
            exit_code=0,
            self_healed=True,
            agent_used="coder",
        )
        assert st.step_order == 1
        assert st.self_healed is True
        assert st.agent_used == "coder"

    def test_execution_trace_defaults(self):
        trace = ExecutionTrace(goal="Optimize database")
        assert trace.goal == "Optimize database"
        assert trace.steps == []
        assert trace.total_duration == 0.0
        assert trace.llm_calls == 0
        assert trace.errors == []

    def test_subsystem_health_recording_and_metrics(self):
        h = SubsystemHealth(subsystem="Memory")
        assert h.success_rate == 0.0

        # Record success
        h.record_activation(latency_ms=100.0, success=True)
        assert h.activation_count == 1
        assert h.error_count == 0
        assert h.avg_latency_ms == 100.0
        assert h.success_rate == 1.0
        assert h.last_activated is not None

        # Record failure
        h.record_activation(latency_ms=200.0, success=False)
        assert h.activation_count == 2
        assert h.error_count == 1
        assert h.avg_latency_ms == 150.0
        assert h.success_rate == 0.5

        d = h.to_dict()
        assert d["subsystem"] == "Memory"
        assert d["activation_count"] == 2
        assert d["avg_latency_ms"] == 150.0
        assert d["error_count"] == 1
        assert d["success_rate"] == 0.5
        assert isinstance(d["last_activated"], str)

    def test_subsystem_health_to_dict_never_activated(self):
        h = SubsystemHealth(subsystem="Reflection")
        d = h.to_dict()
        assert d["last_activated"] is None

    def test_subsystem_health_report(self):
        report = SubsystemHealthReport()
        assert report.total_activations == 0
        assert report.active_count == 0
        assert report.coverage == 0.0
        assert report.get_subsystem("Memory") is None

        h1 = SubsystemHealth(subsystem="Memory")
        h1.record_activation(50.0, True)
        h2 = SubsystemHealth(subsystem="Planner")

        report.add_subsystem(h1)
        report.add_subsystem(h2)

        assert report.total_activations == 1
        assert report.active_count == 1
        assert report.coverage == 0.5
        assert report.get_subsystem("Memory") is h1
        assert report.get_subsystem("Unknown") is None

        # Update existing subsystem
        h1_updated = SubsystemHealth(subsystem="Memory", activation_count=5)
        report.add_subsystem(h1_updated)
        assert report.get_subsystem("Memory") is h1_updated

        data = report.to_dict()
        assert data["total_activations"] == 5
        assert data["active_count"] == 1
        assert len(data["subsystems"]) == 2


# ---------------------------------------------------------------------------
# src.core.telemetry_reporter
# ---------------------------------------------------------------------------
class TestTelemetryReporter:
    @pytest.fixture
    def reporter(self, tmp_path):
        rep = TelemetryReporter(gateway_url="https://test.gateway.cc")
        rep.db_path = tmp_path / "usage.db"
        rep._ensure_db()
        return rep

    def test_usage_record_defaults(self):
        rec = UsageRecord(
            endpoint="/v1/cook",
            method="POST",
            status_code=200,
            payload_size=1024,
            timestamp=1700000000.0,
            error=None,
            tenant_id="tenant-1",
        )
        assert rec.endpoint == "/v1/cook"
        assert rec.tenant_id == "tenant-1"

    def test_record_call_and_manual_flush(self, reporter):
        reporter.record_call(
            endpoint="/v1/recipes",
            method="GET",
            status_code=200,
            payload_size=512,
            error=None,
            tenant_id="t1",
        )
        assert len(reporter._buffer) == 1

        with patch.object(reporter, "_flush_to_gateway") as mock_gw:
            reporter.flush()
            assert len(reporter._buffer) == 0
            mock_gw.assert_called_once()

        metrics = reporter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0]["endpoint"] == "/v1/recipes"
        assert metrics[0]["status_code"] == 200

    def test_record_call_auto_flush_when_buffer_full(self, reporter):
        with patch.object(reporter, "flush") as mock_flush:
            for _ in range(reporter.BATCH_SIZE):
                reporter.record_call("/api", "POST", 200, 100)
            mock_flush.assert_called_once()

    def test_flush_empty_buffer_is_noop(self, reporter):
        with patch.object(reporter, "_flush_to_gateway") as mock_gw:
            reporter.flush()
            mock_gw.assert_not_called()

    def test_flush_to_gateway_success(self, reporter):
        reporter.record_call("/v1/test", "POST", 200, 128)
        with sqlite3.connect(reporter.db_path) as conn:
            conn.execute(
                "INSERT INTO usage_records (endpoint, method, status_code, payload_size, timestamp) VALUES (?, ?, ?, ?, ?)",
                ("/v1/test", "POST", 200, 128, time.time() + 10),
            )

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("requests.post", return_value=mock_resp), \
             patch.object(reporter, "_get_auth_token", return_value="test-token"), \
             patch.object(reporter, "_mark_sent") as mock_mark:
            reporter._flush_to_gateway()
            mock_mark.assert_called_once()

    def test_flush_to_gateway_error_handled(self, reporter):
        with sqlite3.connect(reporter.db_path) as conn:
            conn.execute(
                "INSERT INTO usage_records (endpoint, method, status_code, payload_size, timestamp) VALUES (?, ?, ?, ?, ?)",
                ("/v1/test", "POST", 200, 128, time.time() + 10),
            )
        with patch("requests.post", side_effect=RuntimeError("Network down")), \
             patch.object(reporter, "_get_auth_token", return_value="token"):
            reporter._flush_to_gateway()

    def test_flush_to_gateway_empty_records(self, reporter):
        with patch.object(reporter, "_get_unsent_records", return_value=[]), \
             patch("requests.post") as mock_post:
            reporter._flush_to_gateway()
            mock_post.assert_not_called()

    def test_get_auth_token_from_credentials_file(self, tmp_path):
        rep = TelemetryReporter()
        creds_path = tmp_path / "credentials.json"
        creds_path.write_text(json.dumps({"token": "jwt-token-123"}))

        with patch("pathlib.Path.expanduser", return_value=creds_path):
            token = rep._get_auth_token()
            assert token == "jwt-token-123"

    def test_get_auth_token_corrupted_file_falls_back_to_env(self, tmp_path, monkeypatch):
        rep = TelemetryReporter()
        creds_path = tmp_path / "credentials.json"
        creds_path.write_text("invalid json")
        monkeypatch.setenv("RAAS_LICENSE_KEY", "env-key-999")

        with patch("pathlib.Path.expanduser", return_value=creds_path):
            token = rep._get_auth_token()
            assert token == "env-key-999"

    def test_mark_sent_cleans_old_records(self, reporter):
        now = time.time()
        with sqlite3.connect(reporter.db_path) as conn:
            conn.execute(
                "INSERT INTO usage_records (endpoint, method, status_code, payload_size, timestamp) VALUES (?, ?, ?, ?, ?)",
                ("/old", "GET", 200, 10, now - 100000),
            )
            conn.execute(
                "INSERT INTO usage_records (endpoint, method, status_code, payload_size, timestamp) VALUES (?, ?, ?, ?, ?)",
                ("/new", "GET", 200, 10, now),
            )
        reporter._mark_sent([])
        metrics = reporter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0]["endpoint"] == "/new"

    def test_get_current_usage_and_hourly_metrics(self, reporter):
        now = time.time()
        with sqlite3.connect(reporter.db_path) as conn:
            conn.execute(
                "INSERT INTO usage_records (endpoint, method, status_code, payload_size, timestamp) VALUES (?, ?, ?, ?, ?)",
                ("/v1/cook", "POST", 200, 200, now - 10),
            )
            conn.execute(
                "INSERT INTO usage_records (endpoint, method, status_code, payload_size, timestamp) VALUES (?, ?, ?, ?, ?)",
                ("/v1/cook", "POST", 200, 400, now - 5),
            )

        usage = reporter.get_current_usage()
        assert usage["total_requests"] == 2
        assert usage["total_payload_bytes"] == 600
        assert usage["first_request"] is not None
        assert usage["last_request"] is not None

        hourly = reporter.get_hourly_metrics()
        assert len(hourly) == 1
        assert hourly[0]["request_count"] == 2
        assert hourly[0]["endpoint"] == "/v1/cook"

    def test_get_current_usage_empty(self, reporter):
        usage = reporter.get_current_usage()
        assert usage["total_requests"] == 0
        assert usage["first_request"] is None

    def test_get_telemetry_reporter_singleton(self):
        r1 = get_telemetry_reporter()
        r2 = get_telemetry_reporter()
        assert r1 is r2


# ---------------------------------------------------------------------------
# src.core.telemetry_sink_adapter
# ---------------------------------------------------------------------------
class TestTelemetrySinkAdapter:
    def test_emit_task_completed(self):
        adapter = TelemetrySinkAdapter()
        mock_collector = MagicMock()
        adapter._collector = mock_collector

        adapter.emit({
            "event_type": "task_completed",
            "command": "run_tests",
            "metric": 1.5,
            "mission_id": "m123",
        })
        mock_collector.command_executed.assert_called_once_with(
            command_name="run_tests",
            duration_ms=1500,
            exit_code=0,
            mission_id="m123",
        )

    def test_emit_run_completed_with_error(self):
        adapter = TelemetrySinkAdapter()
        mock_collector = MagicMock()
        adapter._collector = mock_collector

        adapter.emit({
            "event_type": "run_completed",
            "error": "Failed step",
            "task_id": "step_4",
            "mission_id": "m456",
        })
        mock_collector.error_occurred.assert_called_once_with(
            error_type="runtime_error",
            error_message="Failed step",
            command_name="step_4",
            mission_id="m456",
        )

    def test_emit_run_completed_without_error(self):
        adapter = TelemetrySinkAdapter()
        mock_collector = MagicMock()
        adapter._collector = mock_collector

        adapter.emit({
            "event_type": "run_completed",
            "task_id": "step_4",
        })
        mock_collector.error_occurred.assert_not_called()

    def test_emit_session_started_and_ended(self):
        adapter = TelemetrySinkAdapter()
        mock_collector = MagicMock()
        adapter._collector = mock_collector

        adapter.emit({"event_type": "session_started", "mission_id": "m1"})
        mock_collector.session_start.assert_called_once_with(mission_id="m1")

        adapter.emit({"event_type": "session_ended", "mission_id": "m1"})
        mock_collector.session_end.assert_called_once_with(mission_id="m1")

    def test_emit_handles_exceptions_gracefully(self):
        adapter = TelemetrySinkAdapter()
        mock_collector = MagicMock()
        mock_collector.session_start.side_effect = RuntimeError("Collector failure")
        adapter._collector = mock_collector

        # Should never raise exception
        adapter.emit({"event_type": "session_started"})

    def test_flush_noop(self):
        adapter = TelemetrySinkAdapter()
        adapter.flush()


# ---------------------------------------------------------------------------
# src.core.certificate_store
# ---------------------------------------------------------------------------
class TestCertificateStoreExtended:
    def test_certificate_store_error(self):
        err = CertificateStoreError("Store error")
        assert str(err) == "Store error"

    def test_metadata_serialization_roundtrip(self):
        now = datetime.now(timezone.utc)
        meta = CertificateMetadata(
            certificate_id="cid",
            device_id="did",
            valid_from=now,
            valid_until=now + timedelta(days=30),
            created_at=now,
            rotated_count=2,
        )
        d = meta.to_dict()
        restored = CertificateMetadata.from_dict(d)
        assert restored.certificate_id == "cid"
        assert restored.device_id == "did"
        assert restored.rotated_count == 2

    def test_metadata_expiry_and_rotation(self):
        now = datetime.now(timezone.utc)
        meta = CertificateMetadata(
            certificate_id="cid",
            device_id="did",
            valid_from=now - timedelta(days=30),
            valid_until=now + timedelta(days=4),
            created_at=now - timedelta(days=30),
        )
        assert meta.should_rotate is True
        assert meta.is_expired is False

        expired_meta = CertificateMetadata(
            certificate_id="cid",
            device_id="did",
            valid_from=now - timedelta(days=60),
            valid_until=now - timedelta(days=1),
            created_at=now - timedelta(days=60),
        )
        assert expired_meta.is_expired is True

    def test_secure_storage_initialization_failure(self, tmp_path):
        with patch("src.core.certificate_store.get_secure_storage", side_effect=RuntimeError("Vault unavailable")):
            store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=True)
            assert store._secure_storage is None

    def test_load_metadata_expired_clears_file(self, tmp_path):
        store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=False)
        expired_meta = CertificateMetadata(
            certificate_id="exp-cid",
            device_id="did",
            valid_from=datetime.now(timezone.utc) - timedelta(days=60),
            valid_until=datetime.now(timezone.utc) - timedelta(days=1),
            created_at=datetime.now(timezone.utc) - timedelta(days=60),
        )
        store.cert_file.write_text(json.dumps({"metadata": expired_meta.to_dict()}))
        loaded = store._load_metadata()
        assert loaded is None
        assert not store.cert_file.exists()

    def test_load_metadata_valid(self, tmp_path):
        store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=False)
        valid_meta = CertificateMetadata(
            certificate_id="valid-cid",
            device_id="did",
            valid_from=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30),
            created_at=datetime.now(timezone.utc),
        )
        store.cert_file.write_text(json.dumps({"metadata": valid_meta.to_dict()}))
        loaded = store._load_metadata()
        assert loaded is not None
        assert loaded.certificate_id == "valid-cid"

    def test_load_metadata_corrupt_file_clears(self, tmp_path):
        store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=False)
        store.cert_file.write_text("corrupted json{{")
        assert store._load_metadata() is None
        assert not store.cert_file.exists()

    def test_clear_metadata_nonexistent(self, tmp_path):
        store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=False)
        assert store._clear_metadata() is False

    def test_save_metadata_reads_existing_cert_data_or_handles_error(self, tmp_path):
        store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=False)
        store.cert_file.write_text("not json")
        meta = CertificateMetadata(
            certificate_id="cid",
            device_id="did",
            valid_from=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30),
            created_at=datetime.now(timezone.utc),
        )
        store._save_metadata(meta)
        assert store.cert_file.exists()

    def test_secure_storage_private_key_lifecycle(self, tmp_path):
        mock_storage = MagicMock()
        mock_storage.get_license.return_value = "fake-pem-content"
        mock_storage.delete_license.return_value = True

        store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=True)
        store._secure_storage = mock_storage

        key = store._load_private_key()
        assert key == b"fake-pem-content"
        mock_storage.get_license.assert_called_once()

        store._save_private_key(b"new-pem-key")
        mock_storage.store_license.assert_called_once_with("new-pem-key")

        assert store._clear_private_key() is True
        mock_storage.delete_license.assert_called_once()

    def test_secure_storage_exceptions_fallback_to_file(self, tmp_path):
        mock_storage = MagicMock()
        mock_storage.get_license.side_effect = RuntimeError("Keychain error")
        mock_storage.store_license.side_effect = RuntimeError("Keychain error")
        mock_storage.delete_license.side_effect = RuntimeError("Keychain error")

        store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=True)
        store._secure_storage = mock_storage

        store._save_private_key(b"fallback-key-pem")
        key_file = store.cert_dir / "private_key.pem"
        assert key_file.exists()
        assert key_file.read_bytes() == b"fallback-key-pem"

        loaded = store._load_private_key()
        assert loaded == b"fallback-key-pem"

        assert store._clear_private_key() is True
        assert not key_file.exists()

    def test_load_rotation_history_corrupt_or_non_list(self, tmp_path):
        store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=False)
        store.history_file.write_text(json.dumps({"not": "a list"}))
        assert store._load_rotation_history() == []

        store.history_file.write_text("invalid json{{")
        assert store._load_rotation_history() == []

    def test_save_rotation_record_caps_at_10(self, tmp_path):
        store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=False)
        for i in range(15):
            store._save_rotation_record({"index": i})
        history = store.get_rotation_history()
        assert len(history) == 10
        assert history[0]["index"] == 14

    def test_load_certificate_missing_files_or_keys(self, tmp_path):
        store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=False)
        assert store.load_certificate() is None

        store._metadata = CertificateMetadata(
            certificate_id="cid",
            device_id="did",
            valid_from=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30),
            created_at=datetime.now(timezone.utc),
        )
        assert store.load_certificate() is None

        store.cert_file.write_text(json.dumps({"certificate": {}}))
        assert store.load_certificate() is None

    def test_load_certificate_handles_corrupt_data(self, tmp_path):
        store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=False)
        store.cert_file.write_text("bad json")
        store._metadata = CertificateMetadata(
            certificate_id="cid",
            device_id="did",
            valid_from=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30),
            created_at=datetime.now(timezone.utc),
        )
        with patch.object(store, "_load_private_key", return_value=b"key"):
            assert store.load_certificate() is None

    def test_rotate_certificate_expired_forces_rotation(self, tmp_path):
        store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=False)
        store._metadata = CertificateMetadata(
            certificate_id="old-cid",
            device_id="custom-dev-id",
            valid_from=datetime.now(timezone.utc) - timedelta(days=60),
            valid_until=datetime.now(timezone.utc) - timedelta(days=1),
            created_at=datetime.now(timezone.utc) - timedelta(days=60),
        )
        new_cert = store.rotate_certificate()
        assert new_cert is not None
        assert new_cert.certificate_id != "old-cid"
        assert new_cert.device_id == "custom-dev-id"

    def test_generate_and_save_without_auto_sign(self, tmp_path):
        store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=False)
        cert = store.generate_and_save(auto_sign=False)
        assert cert.signature is None

    def test_rotate_certificate_no_metadata_generates_new(self, tmp_path):
        store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=False)
        assert store.get_metadata() is None
        cert = store.rotate_certificate()
        assert cert is not None
        assert store.get_metadata() is not None

    def test_rotate_certificate_not_needed_returns_none(self, tmp_path):
        store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=False)
        store.generate_and_save(valid_days=30)
        assert store.rotate_certificate() is None

    def test_has_certificate(self, tmp_path):
        store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=False)
        assert store.has_certificate() is False
        store.generate_and_save(valid_days=30)
        assert store.has_certificate() is True

    def test_load_certificate_success(self, tmp_path):
        store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=False)
        saved = store.generate_and_save(valid_days=30)
        loaded = store.load_certificate()
        assert loaded is not None
        assert loaded.certificate_id == saved.certificate_id
        assert loaded.device_id == saved.device_id
        assert loaded.private_key_pem is not None

    def test_clear_all_data(self, tmp_path):
        store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=False)
        store.generate_and_save(valid_days=30)
        store._save_rotation_record({"event": "rotated"})
        assert store.has_certificate() is True
        assert len(store.get_rotation_history()) == 1

        cleared = store.clear()
        assert cleared is True
        assert store.has_certificate() is False
        assert store.get_metadata() is None
        assert len(store.get_rotation_history()) == 0

    def test_export_for_request_with_and_without_cert(self, tmp_path):
        store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=False)
        assert store.export_for_request() is None

        store.generate_and_save(valid_days=30)
        headers = store.export_for_request()
        assert headers is not None
        assert "X-Cert-ID" in headers
        assert "X-Cert-Sig" in headers
        assert "X-Cert-Timestamp" in headers

    def test_oserror_handlers(self, tmp_path):
        store = CertificateStore(certificate_dir=str(tmp_path), use_secure_storage=False)
        store.generate_and_save(valid_days=30)
        store._save_rotation_record({"event": "rotated"})

        with patch("os.remove", side_effect=OSError("Permission denied")):
            assert store._clear_metadata() is False
            assert store._clear_private_key() is False
            store.clear()

        with patch("builtins.open", side_effect=OSError("Read error")):
            assert store._load_private_key() is None

    def test_get_certificate_store_singleton(self, tmp_path):
        import src.core.certificate_store as cs_mod
        cs_mod._certificate_store = None
        s1 = get_certificate_store(certificate_dir=str(tmp_path), use_secure_storage=False)
        s2 = get_certificate_store()
        assert s1 is s2
        cs_mod._certificate_store = None
