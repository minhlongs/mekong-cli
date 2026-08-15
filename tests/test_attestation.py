"""Security tests for SecurityAttestationGenerator.

Tests REAL logic in src/security/attestation_generator.py.
Subprocess calls (git, grep, find) are mocked to keep tests hermetic.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


from src.security.attestation_generator import SecurityAttestationGenerator


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_generator(tmp_path: str) -> SecurityAttestationGenerator:
    return SecurityAttestationGenerator(repo_path=tmp_path)


def _mock_run(returncode: int = 0, stdout: str = "") -> MagicMock:
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    return m


# ═══════════════════════════════════════════════════════════════════════════════
#  get_commit_info
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetCommitInfo:
    """Verify git info extraction."""

    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.gen = _make_generator(self.tmp)

    def test_returns_sha_and_branch_on_success(self):
        sha_mock = _mock_run(stdout="abc1234def5678\n")
        branch_mock = _mock_run(stdout="main\n")

        with patch("subprocess.run", side_effect=[sha_mock, branch_mock]):
            info = self.gen.get_commit_info()

        assert info["sha"] == "abc1234def5678"
        assert info["branch"] == "main"

    def test_returns_unknown_on_exception(self):
        with patch("subprocess.run", side_effect=Exception("git not found")):
            info = self.gen.get_commit_info()

        assert info["sha"] == "unknown"
        assert info["branch"] == "unknown"

    def test_handles_empty_stdout(self):
        with patch("subprocess.run", return_value=_mock_run(stdout="")):
            info = self.gen.get_commit_info()
        # No crash — returns whatever git outputs (empty strings)
        assert "sha" in info
        assert "branch" in info


# ═══════════════════════════════════════════════════════════════════════════════
#  check_hardcoded_secrets
# ═══════════════════════════════════════════════════════════════════════════════

class TestCheckHardcodedSecrets:
    """Verify secret scanning logic."""

    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.gen = _make_generator(self.tmp)

    def test_no_secrets_returns_true(self):
        with patch("subprocess.run", return_value=_mock_run(returncode=1, stdout="")):
            ok, findings = self.gen.check_hardcoded_secrets()
        assert ok is True
        assert findings == []

    def test_secret_found_returns_false_with_findings(self):
        raw_output = "src/config.py:API_KEY = 'abcdef1234567890'\n"
        with patch("subprocess.run", return_value=_mock_run(returncode=0, stdout=raw_output)):
            ok, findings = self.gen.check_hardcoded_secrets()
        assert ok is False
        assert len(findings) > 0

    def test_os_getenv_lines_are_filtered(self):
        # Lines with os.getenv should not count as hardcoded secrets
        safe_line = "src/config.py:API_KEY = os.getenv('API_KEY')\n"
        with patch("subprocess.run", return_value=_mock_run(returncode=0, stdout=safe_line)):
            ok, findings = self.gen.check_hardcoded_secrets()
        assert ok is True
        assert findings == []

    def test_os_environ_lines_are_filtered(self):
        safe_line = "src/config.py:TOKEN = os.environ['TOKEN']\n"
        with patch("subprocess.run", return_value=_mock_run(returncode=0, stdout=safe_line)):
            ok, findings = self.gen.check_hardcoded_secrets()
        assert ok is True
        assert findings == []

    def test_exception_returns_true_with_no_findings(self):
        # subprocess failure should be handled gracefully
        with patch("subprocess.run", side_effect=Exception("grep not found")):
            ok, findings = self.gen.check_hardcoded_secrets()
        assert ok is True
        assert findings == []

    def test_multiple_secrets_all_returned(self):
        raw_output = (
            "src/a.py:SECRET = 'abcdef1234567890'\n"
            "src/b.py:PASSWORD = 'xyzxyz1234567890'\n"
        )
        with patch("subprocess.run", return_value=_mock_run(returncode=0, stdout=raw_output)):
            ok, findings = self.gen.check_hardcoded_secrets()
        assert ok is False
        assert len(findings) == 2


# ═══════════════════════════════════════════════════════════════════════════════
#  check_env_file_exposure
# ═══════════════════════════════════════════════════════════════════════════════

class TestCheckEnvFileExposure:
    """Verify .env file scan scoped to src/ only."""

    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.gen = _make_generator(self.tmp)

    def test_no_env_files_returns_true(self):
        with patch("subprocess.run", return_value=_mock_run(returncode=0, stdout="")):
            ok, exposed = self.gen.check_env_file_exposure()
        assert ok is True
        assert exposed == []

    def test_exposed_env_file_returns_false(self):
        raw_output = "src/.env\n"
        with patch("subprocess.run", return_value=_mock_run(returncode=0, stdout=raw_output)):
            ok, exposed = self.gen.check_env_file_exposure()
        assert ok is False
        assert "src/.env" in exposed

    def test_env_example_is_allowed(self):
        raw_output = "src/.env.example\n"
        with patch("subprocess.run", return_value=_mock_run(returncode=0, stdout=raw_output)):
            ok, exposed = self.gen.check_env_file_exposure()
        assert ok is True
        assert exposed == []

    def test_venv_env_files_are_allowed(self):
        raw_output = "src/.venv/.env\n"
        with patch("subprocess.run", return_value=_mock_run(returncode=0, stdout=raw_output)):
            ok, exposed = self.gen.check_env_file_exposure()
        assert ok is True
        assert exposed == []

    def test_exception_treated_as_no_exposures(self):
        with patch("subprocess.run", side_effect=Exception("find failed")):
            ok, exposed = self.gen.check_env_file_exposure()
        assert ok is True
        assert exposed == []

    def test_multiple_exposed_files_all_listed(self):
        raw_output = "src/.env\nsrc/subdir/.env.prod\n"
        with patch("subprocess.run", return_value=_mock_run(returncode=0, stdout=raw_output)):
            ok, exposed = self.gen.check_env_file_exposure()
        assert ok is False
        assert len(exposed) == 2


# ═══════════════════════════════════════════════════════════════════════════════
#  check_command_sanitizer
# ═══════════════════════════════════════════════════════════════════════════════

class TestCheckCommandSanitizer:
    """Verify sanitizer file-presence check."""

    def test_returns_true_when_file_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            sanitizer_path = Path(tmp) / "src" / "security" / "command_sanitizer.py"
            sanitizer_path.parent.mkdir(parents=True)
            sanitizer_path.touch()

            gen = SecurityAttestationGenerator(repo_path=tmp)
            assert gen.check_command_sanitizer() is True

    def test_returns_false_when_file_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            gen = SecurityAttestationGenerator(repo_path=tmp)
            assert gen.check_command_sanitizer() is False


# ═══════════════════════════════════════════════════════════════════════════════
#  generate_attestation
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerateAttestation:
    """Verify attestation report structure and status logic."""

    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.gen = _make_generator(self.tmp)

    def _all_pass_results(self) -> dict:
        return {
            "secrets_ok": True,
            "env_ok": True,
            "sanitizer_ok": True,
            "secrets_findings": [],
            "env_findings": [],
        }

    def _with_commit(self):
        sha_mock = _mock_run(stdout="deadbeef\n")
        branch_mock = _mock_run(stdout="main\n")
        return [sha_mock, branch_mock]

    def test_status_attested_secure_when_all_pass(self):
        with patch("subprocess.run", side_effect=self._with_commit()):
            att = self.gen.generate_attestation(self._all_pass_results())
        assert att["status"] == "ATTESTED_SECURE"

    def test_status_attestation_failed_when_secrets_fail(self):
        results = self._all_pass_results()
        results["secrets_ok"] = False
        with patch("subprocess.run", side_effect=self._with_commit()):
            att = self.gen.generate_attestation(results)
        assert att["status"] == "ATTESTATION_FAILED"

    def test_status_attestation_failed_when_env_fail(self):
        results = self._all_pass_results()
        results["env_ok"] = False
        with patch("subprocess.run", side_effect=self._with_commit()):
            att = self.gen.generate_attestation(results)
        assert att["status"] == "ATTESTATION_FAILED"

    def test_status_attestation_failed_when_sanitizer_missing(self):
        results = self._all_pass_results()
        results["sanitizer_ok"] = False
        with patch("subprocess.run", side_effect=self._with_commit()):
            att = self.gen.generate_attestation(results)
        assert att["status"] == "ATTESTATION_FAILED"

    def test_attestation_contains_required_fields(self):
        with patch("subprocess.run", side_effect=self._with_commit()):
            att = self.gen.generate_attestation(self._all_pass_results())

        required_fields = [
            "attestation_version",
            "attestation_type",
            "timestamp",
            "commit_sha",
            "branch",
            "repository",
            "security_checks",
            "compliance",
            "status",
        ]
        for field in required_fields:
            assert field in att, f"Missing field: {field}"

    def test_security_checks_pass_values(self):
        with patch("subprocess.run", side_effect=self._with_commit()):
            att = self.gen.generate_attestation(self._all_pass_results())

        checks = att["security_checks"]
        assert checks["secret_scanning"] == "PASS"
        assert checks["command_injection_protection"] == "PASS"
        assert checks["env_file_exclusion"] == "PASS"

    def test_security_checks_fail_values(self):
        results = self._all_pass_results()
        results["secrets_ok"] = False
        results["sanitizer_ok"] = False
        with patch("subprocess.run", side_effect=self._with_commit()):
            att = self.gen.generate_attestation(results)

        checks = att["security_checks"]
        assert checks["secret_scanning"] == "FAIL"
        assert checks["command_injection_protection"] == "FAIL"

    def test_compliance_owasp_compliant_when_all_pass(self):
        with patch("subprocess.run", side_effect=self._with_commit()):
            att = self.gen.generate_attestation(self._all_pass_results())
        assert att["compliance"]["owasp_top_10"] == "COMPLIANT"

    def test_compliance_owasp_non_compliant_on_failure(self):
        results = self._all_pass_results()
        results["env_ok"] = False
        with patch("subprocess.run", side_effect=self._with_commit()):
            att = self.gen.generate_attestation(results)
        assert att["compliance"]["owasp_top_10"] == "NON_COMPLIANT"

    def test_raas_gateway_compatible_always_true(self):
        with patch("subprocess.run", side_effect=self._with_commit()):
            att = self.gen.generate_attestation(self._all_pass_results())
        assert att["raas_gateway_compatible"] is True
        assert att["jwt_auth_ready"] is True

    def test_commit_sha_in_attestation(self):
        with patch("subprocess.run", side_effect=self._with_commit()):
            att = self.gen.generate_attestation(self._all_pass_results())
        assert att["commit_sha"] == "deadbeef"


# ═══════════════════════════════════════════════════════════════════════════════
#  sign_attestation
# ═══════════════════════════════════════════════════════════════════════════════

class TestSignAttestation:
    """Verify SHA256 signature generation."""

    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.gen = _make_generator(self.tmp)

    def _sample_attestation(self) -> dict:
        return {
            "status": "ATTESTED_SECURE",
            "attestation_version": "1.0.0",
            "timestamp": "2026-04-04T00:00:00+00:00",
        }

    def test_sign_returns_hex_string(self):
        att = self._sample_attestation()
        sig = self.gen.sign_attestation(att)
        assert isinstance(sig, str)
        assert len(sig) == 64  # SHA256 hex = 64 chars

    def test_sign_is_deterministic(self):
        att = self._sample_attestation()
        assert self.gen.sign_attestation(att) == self.gen.sign_attestation(att)

    def test_different_content_gives_different_signature(self):
        att1 = {"status": "ATTESTED_SECURE"}
        att2 = {"status": "ATTESTATION_FAILED"}
        assert self.gen.sign_attestation(att1) != self.gen.sign_attestation(att2)

    def test_signature_matches_manual_sha256(self):
        att = self._sample_attestation()
        canonical = json.dumps(att, sort_keys=True, separators=(",", ":"))
        expected = hashlib.sha256(canonical.encode()).hexdigest()
        assert self.gen.sign_attestation(att) == expected

    def test_field_order_does_not_affect_signature(self):
        att_a = {"b": 2, "a": 1}
        att_b = {"a": 1, "b": 2}
        # Both should produce same sig because json.dumps uses sort_keys=True
        assert self.gen.sign_attestation(att_a) == self.gen.sign_attestation(att_b)


# ═══════════════════════════════════════════════════════════════════════════════
#  save_report
# ═══════════════════════════════════════════════════════════════════════════════

class TestSaveReport:
    """Verify report persistence."""

    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.gen = _make_generator(self.tmp)

    def _sample_attestation(self) -> dict:
        return {
            "attestation_version": "1.0.0",
            "attestation_type": "mekong-cli-security-hardening",
            "timestamp": "2026-04-04T00:00:00+00:00",
            "commit_sha": "abc12345",
            "branch": "main",
            "repository": "mekong-cli",
            "security_checks": {},
            "compliance": {},
            "status": "ATTESTED_SECURE",
            "raas_gateway_compatible": True,
            "jwt_auth_ready": True,
            "mk_api_key_format": True,
        }

    def test_saves_report_file(self):
        output_dir = os.path.join(self.tmp, "reports")
        att = self._sample_attestation()
        sig = self.gen.sign_attestation(att)
        path = self.gen.save_report(att, sig, output_dir=output_dir)
        assert path.exists()

    def test_report_contains_signature(self):
        output_dir = os.path.join(self.tmp, "reports")
        att = self._sample_attestation()
        sig = self.gen.sign_attestation(att)
        path = self.gen.save_report(att, sig, output_dir=output_dir)
        with open(path) as f:
            data = json.load(f)
        assert data["signature"] == sig
        assert data["signature_algorithm"] == "SHA256"

    def test_report_filename_uses_commit_sha(self):
        output_dir = os.path.join(self.tmp, "reports")
        att = self._sample_attestation()
        sig = self.gen.sign_attestation(att)
        path = self.gen.save_report(att, sig, output_dir=output_dir)
        assert "abc12345" in path.name

    def test_creates_output_directory(self):
        output_dir = os.path.join(self.tmp, "deep", "nested", "reports")
        att = self._sample_attestation()
        sig = self.gen.sign_attestation(att)
        self.gen.save_report(att, sig, output_dir=output_dir)
        assert Path(output_dir).exists()

    def test_report_is_valid_json(self):
        output_dir = os.path.join(self.tmp, "reports")
        att = self._sample_attestation()
        sig = self.gen.sign_attestation(att)
        path = self.gen.save_report(att, sig, output_dir=output_dir)
        with open(path) as f:
            data = json.load(f)
        assert data["status"] == "ATTESTED_SECURE"


# ═══════════════════════════════════════════════════════════════════════════════
#  run_security_checks (integration-style)
# ═══════════════════════════════════════════════════════════════════════════════

class TestRunSecurityChecks:
    """run_security_checks orchestrates all three checks."""

    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        # Create the sanitizer file so check passes
        sanitizer_path = Path(self.tmp) / "src" / "security" / "command_sanitizer.py"
        sanitizer_path.parent.mkdir(parents=True, exist_ok=True)
        sanitizer_path.touch()
        self.gen = SecurityAttestationGenerator(repo_path=self.tmp)

    def test_all_pass_when_clean(self):
        no_findings = _mock_run(returncode=1, stdout="")  # grep returncode 1 = no match
        no_env_files = _mock_run(returncode=0, stdout="")  # find returncode 0, empty

        with patch("subprocess.run", side_effect=[no_findings, no_env_files]):
            results = self.gen.run_security_checks()

        assert results["secrets_ok"] is True
        assert results["env_ok"] is True
        assert results["sanitizer_ok"] is True

    def test_sanitizer_check_fails_when_file_missing(self):
        sanitizer_path = Path(self.tmp) / "src" / "security" / "command_sanitizer.py"
        sanitizer_path.unlink()

        no_findings = _mock_run(returncode=1, stdout="")
        no_env_files = _mock_run(returncode=0, stdout="")

        with patch("subprocess.run", side_effect=[no_findings, no_env_files]):
            results = self.gen.run_security_checks()

        assert results["sanitizer_ok"] is False

    def test_result_keys_all_present(self):
        no_findings = _mock_run(returncode=1, stdout="")
        no_env_files = _mock_run(returncode=0, stdout="")

        with patch("subprocess.run", side_effect=[no_findings, no_env_files]):
            results = self.gen.run_security_checks()

        for key in ["secrets_ok", "env_ok", "sanitizer_ok", "secrets_findings", "env_findings"]:
            assert key in results
