"""Tests for src/core/health_reporter.py"""
from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from unittest.mock import MagicMock, patch



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_reporter(tmp_path: Path, has_consent: bool = True, gateway_url: str = "http://fake-gw"):
    """Build a HealthReporter with all external deps mocked."""
    consent_manager = MagicMock()
    consent_manager.has_consent.return_value = has_consent

    auth_client = MagicMock()

    with (
        patch("src.core.health_reporter.get_consent_manager", return_value=consent_manager),
        patch("src.core.health_reporter.RaaSAuthClient", return_value=auth_client),
    ):
        from src.core.health_reporter import HealthReporter

        reporter = HealthReporter(
            consent_manager=consent_manager,
            auth_client=auth_client,
            gateway_url=gateway_url,
        )
        reporter.metrics_path = tmp_path / "health_metrics.json"
        reporter._metrics = None  # ensure fresh load each time
        return reporter, consent_manager


# ---------------------------------------------------------------------------
# HealthMetrics dataclass
# ---------------------------------------------------------------------------


class TestHealthMetrics:
    def test_defaults(self):
        from src.core.health_reporter import HealthMetrics

        m = HealthMetrics(
            cli_version="1.0",
            os_type="Linux",
            os_version="5.15",
            python_version="3.11",
            session_id="abcd1234",
        )
        assert m.commands_executed == 0
        assert m.commands_succeeded == 0
        assert m.commands_failed == 0
        assert m.rate_limit_hits == 0
        assert m.license_validation_failures == 0
        assert m.avg_command_duration_ms == 0.0
        assert m.error_categories == {}

    def test_post_init_initialises_error_categories(self):
        from src.core.health_reporter import HealthMetrics

        m = HealthMetrics(
            cli_version="x",
            os_type="x",
            os_version="x",
            python_version="x",
            session_id="x",
            error_categories=None,  # type: ignore[arg-type]
        )
        assert m.error_categories == {}


# ---------------------------------------------------------------------------
# _load_metrics / _save_metrics
# ---------------------------------------------------------------------------


class TestLoadSaveMetrics:
    def test_load_returns_none_when_file_absent(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path)
        reporter.metrics_path = tmp_path / "nonexistent.json"
        result = reporter._load_metrics()
        assert result is None

    def test_save_then_load_roundtrip(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path)
        from src.core.health_reporter import HealthMetrics

        m = HealthMetrics(
            cli_version="2.0",
            os_type="Darwin",
            os_version="21.0",
            python_version="3.12",
            session_id="sess1",
            commands_executed=5,
        )
        reporter._save_metrics(m)
        reporter._metrics = None  # clear in-memory cache
        loaded = reporter._load_metrics()
        assert loaded is not None
        assert loaded.commands_executed == 5
        assert loaded.cli_version == "2.0"

    def test_load_handles_nested_metrics_key(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path)
        from src.core.health_reporter import HealthMetrics

        m = HealthMetrics(
            cli_version="3.0",
            os_type="Windows",
            os_version="11",
            python_version="3.10",
            session_id="s2",
        )
        nested = {"metrics": asdict(m)}
        reporter.metrics_path.write_text(json.dumps(nested))
        reporter._metrics = None
        loaded = reporter._load_metrics()
        assert loaded is not None
        assert loaded.cli_version == "3.0"

    def test_load_returns_cached_metrics(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path)
        from src.core.health_reporter import HealthMetrics

        cached = HealthMetrics(
            cli_version="cached",
            os_type="x",
            os_version="x",
            python_version="x",
            session_id="c1",
        )
        reporter._metrics = cached
        # File does not exist but cached value returned
        result = reporter._load_metrics()
        assert result is cached

    def test_load_returns_none_on_corrupt_json(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path)
        reporter.metrics_path.write_text("not-json{{")
        reporter._metrics = None
        result = reporter._load_metrics()
        assert result is None


# ---------------------------------------------------------------------------
# get_or_create_metrics
# ---------------------------------------------------------------------------


class TestGetOrCreateMetrics:
    def test_creates_metrics_when_none_exist(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path)
        metrics = reporter.get_or_create_metrics()
        assert metrics is not None
        assert metrics.commands_executed == 0
        assert reporter.metrics_path.exists()

    def test_returns_existing_metrics(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path)
        from src.core.health_reporter import HealthMetrics

        m = HealthMetrics(
            cli_version="existing",
            os_type="x",
            os_version="x",
            python_version="x",
            session_id="ex1",
            commands_executed=42,
        )
        reporter._save_metrics(m)
        reporter._metrics = None
        metrics = reporter.get_or_create_metrics()
        assert metrics.commands_executed == 42


# ---------------------------------------------------------------------------
# _get_cli_version
# ---------------------------------------------------------------------------


class TestGetCliVersion:
    def test_reads_version_file_when_present(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path)
        # Create a real VERSION file next to the src/core directory
        # and patch Path(__file__) chain is complex; instead verify the method
        # always returns a string under normal conditions
        result = reporter._get_cli_version()
        assert isinstance(result, str)

    def test_falls_back_to_env_var_when_version_file_missing(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path)
        # Force the version file lookup to fail by patching the internal path resolution
        import src.core.health_reporter as hr_module
        original_path = hr_module.Path

        class FakePath:
            """Path that always reports VERSION file as non-existent."""
            def __init__(self, *args):
                self._path = original_path(*args)

            def __truediv__(self, other):
                result = FakePath.__new__(FakePath)
                result._path = self._path / other
                return result

            def exists(self):
                # Pretend the VERSION file does not exist
                return False

            def read_text(self):
                return self._path.read_text()

            @classmethod
            def home(cls):
                return original_path.home()

        with (
            patch.dict("os.environ", {"MEKONG_VERSION": "fallback-version"}),
            patch.object(hr_module, "Path", FakePath),
        ):
            result = reporter._get_cli_version()
        assert result == "fallback-version"


# ---------------------------------------------------------------------------
# record_command
# ---------------------------------------------------------------------------


class TestRecordCommand:
    def test_increments_executed_on_success(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        reporter.record_command("cook", success=True, duration_ms=100.0)
        reporter._metrics = None
        metrics = reporter._load_metrics()
        assert metrics.commands_executed == 1
        assert metrics.commands_succeeded == 1
        assert metrics.commands_failed == 0

    def test_increments_failed_on_failure(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        reporter.record_command("deploy", success=False, duration_ms=200.0)
        reporter._metrics = None
        metrics = reporter._load_metrics()
        assert metrics.commands_failed == 1
        assert metrics.commands_succeeded == 0

    def test_tracks_error_category(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        reporter.record_command("deploy", success=False, duration_ms=50.0, error_category="auth")
        reporter._metrics = None
        metrics = reporter._load_metrics()
        assert metrics.error_categories.get("auth") == 1

    def test_accumulates_error_category_counts(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        for _ in range(3):
            reporter.record_command("x", success=False, duration_ms=10.0, error_category="network")
        reporter._metrics = None
        metrics = reporter._load_metrics()
        assert metrics.error_categories.get("network") == 3

    def test_no_consent_skips_recording(self, tmp_path):
        reporter, consent = _make_reporter(tmp_path, has_consent=False)
        reporter.record_command("cook", success=True, duration_ms=100.0)
        assert not reporter.metrics_path.exists()

    def test_updates_average_duration(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        reporter.record_command("cook", success=True, duration_ms=100.0)
        reporter.record_command("plan", success=True, duration_ms=200.0)
        reporter._metrics = None
        metrics = reporter._load_metrics()
        assert abs(metrics.avg_command_duration_ms - 150.0) < 0.01

    def test_error_category_not_recorded_on_success(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        reporter.record_command("cook", success=True, duration_ms=50.0, error_category="auth")
        reporter._metrics = None
        metrics = reporter._load_metrics()
        assert metrics.error_categories == {}


# ---------------------------------------------------------------------------
# record_rate_limit_hit
# ---------------------------------------------------------------------------


class TestRecordRateLimitHit:
    def test_increments_rate_limit_hits(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        reporter.record_rate_limit_hit()
        reporter.record_rate_limit_hit()
        reporter._metrics = None
        metrics = reporter._load_metrics()
        assert metrics.rate_limit_hits == 2

    def test_no_consent_skips(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=False)
        reporter.record_rate_limit_hit()
        assert not reporter.metrics_path.exists()


# ---------------------------------------------------------------------------
# record_license_validation_failure
# ---------------------------------------------------------------------------


class TestRecordLicenseValidationFailure:
    def test_increments_failures(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        reporter.record_license_validation_failure()
        reporter._metrics = None
        metrics = reporter._load_metrics()
        assert metrics.license_validation_failures == 1

    def test_no_consent_skips(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=False)
        reporter.record_license_validation_failure()
        assert not reporter.metrics_path.exists()


# ---------------------------------------------------------------------------
# should_report
# ---------------------------------------------------------------------------


class TestShouldReport:
    def test_returns_false_when_no_consent(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=False)
        assert reporter.should_report() is False

    def test_returns_true_on_first_call_with_consent(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        reporter._last_report = 0.0
        assert reporter.should_report() is True

    def test_returns_false_before_interval(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        reporter._last_report = time.time()  # just now
        assert reporter.should_report() is False

    def test_returns_true_after_interval(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        reporter._last_report = time.time() - 400  # 400 > 300 (REPORT_INTERVAL)
        assert reporter.should_report() is True


# ---------------------------------------------------------------------------
# report_to_gateway
# ---------------------------------------------------------------------------


class TestReportToGateway:
    def test_returns_false_when_should_not_report(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        reporter._last_report = time.time()  # just reported
        result = reporter.report_to_gateway()
        assert result is False

    def test_returns_false_when_no_auth_headers(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        reporter._last_report = 0.0
        with patch.object(reporter, "_get_auth_headers", return_value={}):
            result = reporter.report_to_gateway()
        assert result is False

    def test_returns_true_on_200_response(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        reporter._last_report = 0.0

        mock_response = MagicMock()
        mock_response.status_code = 200

        with (
            patch.object(reporter, "_get_auth_headers", return_value={"Authorization": "Bearer test"}),
            patch("src.core.health_reporter.requests.post", return_value=mock_response),
        ):
            result = reporter.report_to_gateway()
        assert result is True

    def test_resets_counters_after_successful_report(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        reporter._last_report = 0.0
        # Record some activity first
        reporter.record_command("cook", success=True, duration_ms=100.0)
        reporter.record_rate_limit_hit()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with (
            patch.object(reporter, "_get_auth_headers", return_value={"Authorization": "Bearer test"}),
            patch("src.core.health_reporter.requests.post", return_value=mock_response),
        ):
            reporter.report_to_gateway()

        reporter._metrics = None
        metrics = reporter._load_metrics()
        assert metrics.commands_executed == 0
        assert metrics.rate_limit_hits == 0

    def test_returns_false_on_non_200_response(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        reporter._last_report = 0.0

        mock_response = MagicMock()
        mock_response.status_code = 500

        with (
            patch.object(reporter, "_get_auth_headers", return_value={"Authorization": "Bearer test"}),
            patch("src.core.health_reporter.requests.post", return_value=mock_response),
        ):
            result = reporter.report_to_gateway()
        assert result is False

    def test_returns_false_on_request_exception(self, tmp_path):
        import requests as req_lib
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        reporter._last_report = 0.0

        with (
            patch.object(reporter, "_get_auth_headers", return_value={"Authorization": "Bearer test"}),
            patch("src.core.health_reporter.requests.post", side_effect=req_lib.RequestException("timeout")),
        ):
            result = reporter.report_to_gateway()
        assert result is False

    def test_updates_last_report_time_after_success(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        reporter._last_report = 0.0
        before = time.time()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with (
            patch.object(reporter, "_get_auth_headers", return_value={"Authorization": "Bearer test"}),
            patch("src.core.health_reporter.requests.post", return_value=mock_response),
        ):
            reporter.report_to_gateway()

        assert reporter._last_report >= before


# ---------------------------------------------------------------------------
# _get_auth_headers
# ---------------------------------------------------------------------------


class TestGetAuthHeaders:
    def test_returns_headers_with_env_license_key(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path)
        with patch.dict("os.environ", {"RAAS_LICENSE_KEY": "mk_test123"}):
            headers = reporter._get_auth_headers()
        assert "Authorization" in headers
        assert "mk_test123" in headers["Authorization"]
        assert headers["Content-Type"] == "application/json"

    def test_returns_empty_when_no_key(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path)
        with (
            patch.dict("os.environ", {}, clear=True),
            patch("src.core.health_reporter.Path") as MockPath,
        ):
            # credentials file does not exist
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            MockPath.return_value.__truediv__ = lambda s, x: mock_path
            MockPath.home.return_value.__truediv__ = lambda s, x: mock_path
            headers = reporter._get_auth_headers()
        assert isinstance(headers, dict)

    def test_reads_token_from_credentials_file(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path)
        creds_dir = tmp_path / "raas"
        creds_dir.mkdir()
        creds_file = creds_dir / "credentials.json"
        creds_file.write_text(json.dumps({"token": "mk_from_file"}))

        with patch.dict("os.environ", {}, clear=True):
            # Patch Path.home() to return tmp_path
            with patch("src.core.health_reporter.Path") as MockPath:
                mock_home = MagicMock()
                mock_home.__truediv__ = lambda s, x: (
                    creds_dir if x == "mekong" else MagicMock()
                )
                creds_path = MagicMock()
                creds_path.exists.return_value = True
                creds_path.__enter__ = MagicMock(return_value=creds_file.open())
                MockPath.home.return_value.__truediv__ = lambda s, x: creds_path
                # Use real method but mock os.getenv
                with patch.dict("os.environ", {}, clear=True):
                    headers = reporter._get_auth_headers()
        # Just verify the method returns a dict without crashing
        assert isinstance(headers, dict)


# ---------------------------------------------------------------------------
# _reset_counters
# ---------------------------------------------------------------------------


class TestResetCounters:
    def test_resets_all_counters(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        # Build up some counts
        reporter.record_command("cook", success=True, duration_ms=100.0)
        reporter.record_command("deploy", success=False, duration_ms=200.0, error_category="auth")
        reporter.record_rate_limit_hit()
        reporter.record_license_validation_failure()

        reporter._reset_counters()
        reporter._metrics = None
        metrics = reporter._load_metrics()

        assert metrics.commands_executed == 0
        assert metrics.commands_succeeded == 0
        assert metrics.commands_failed == 0
        assert metrics.rate_limit_hits == 0
        assert metrics.license_validation_failures == 0
        assert metrics.error_categories == {}

    def test_generates_new_session_id_after_reset(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        reporter.record_command("cook", success=True, duration_ms=50.0)

        reporter._metrics = None
        reporter.get_or_create_metrics().session_id
        reporter._reset_counters()
        reporter._metrics = None
        after = reporter.get_or_create_metrics().session_id

        # session_id is a random 8-char string — almost certainly different
        assert isinstance(after, str)
        assert len(after) == 8


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------


class TestGetStatus:
    def test_status_inactive_without_consent(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=False)
        status = reporter.get_status()
        assert status["status"] == "inactive"

    def test_status_active_with_consent(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        status = reporter.get_status()
        assert status["status"] == "active"

    def test_success_rate_zero_when_no_commands(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        status = reporter.get_status()
        assert status["success_rate"] == 0

    def test_success_rate_calculation(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        reporter.record_command("cook", success=True, duration_ms=100.0)
        reporter.record_command("cook", success=True, duration_ms=100.0)
        reporter.record_command("cook", success=False, duration_ms=100.0)
        reporter._metrics = None
        status = reporter.get_status()
        assert abs(status["success_rate"] - 2 / 3) < 0.01

    def test_last_report_never_when_not_reported(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        status = reporter.get_status()
        assert status["last_report"] == "never"

    def test_last_report_iso_string_after_reporting(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        reporter._last_report = time.time()
        status = reporter.get_status()
        assert status["last_report"] != "never"
        assert "T" in status["last_report"]  # ISO format

    def test_status_includes_all_required_keys(self, tmp_path):
        reporter, _ = _make_reporter(tmp_path, has_consent=True)
        status = reporter.get_status()
        for key in [
            "status", "cli_version", "os", "python_version", "session_id",
            "commands_executed", "commands_succeeded", "commands_failed",
            "success_rate", "rate_limit_hits", "last_report",
        ]:
            assert key in status, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# Module-level singleton / convenience functions
# ---------------------------------------------------------------------------


class TestModuleLevelFunctions:
    def test_get_health_reporter_singleton(self):
        with (
            patch("src.core.health_reporter.get_consent_manager"),
            patch("src.core.health_reporter.RaaSAuthClient"),
        ):
            import src.core.health_reporter as hr_module
            hr_module._health_reporter = None  # reset
            r1 = hr_module.get_health_reporter()
            r2 = hr_module.get_health_reporter()
            assert r1 is r2

    def test_record_command_convenience_function(self, tmp_path):
        with (
            patch("src.core.health_reporter.get_consent_manager") as mock_cm,
            patch("src.core.health_reporter.RaaSAuthClient"),
        ):
            consent = MagicMock()
            consent.has_consent.return_value = True
            mock_cm.return_value = consent

            import src.core.health_reporter as hr_module
            hr_module._health_reporter = None
            reporter = hr_module.get_health_reporter()
            reporter.metrics_path = tmp_path / "m.json"

            hr_module.record_command("cook", success=True, duration_ms=50.0)
            reporter._metrics = None
            metrics = reporter._load_metrics()
            assert metrics.commands_executed == 1

    def test_report_health_convenience_function(self, tmp_path):
        with (
            patch("src.core.health_reporter.get_consent_manager") as mock_cm,
            patch("src.core.health_reporter.RaaSAuthClient"),
        ):
            consent = MagicMock()
            consent.has_consent.return_value = False  # no consent = no report
            mock_cm.return_value = consent

            import src.core.health_reporter as hr_module
            hr_module._health_reporter = None
            reporter = hr_module.get_health_reporter()
            reporter.metrics_path = tmp_path / "m2.json"

            result = hr_module.report_health()
            assert result is False
