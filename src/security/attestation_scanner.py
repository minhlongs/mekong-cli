# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Security Scanner Checks for Attestation Generator."""

import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SecurityScannerMixin:
    """Security checks for repository attestation."""

    repo_path: Path

    def get_commit_info(self) -> dict[str, str]:
        try:
            sha = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=self.repo_path,
            ).stdout.strip()
            branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, cwd=self.repo_path,
            ).stdout.strip()
            return {"sha": sha, "branch": branch}
        except Exception:
            return {"sha": "unknown", "branch": "unknown"}

    def check_hardcoded_secrets(self) -> tuple[bool, list[str]]:
        findings = []
        secret_pattern = r"(API_KEY|SECRET|PASSWORD|TOKEN)\s*=\s*['\"][a-zA-Z0-9]{16,}['\"]"
        try:
            result = subprocess.run(
                ["grep", "-rE", secret_pattern, "src/", "--include=*.py"],
                capture_output=True, text=True, cwd=self.repo_path,
            )
            if result.returncode == 0 and result.stdout:
                findings = [f for f in result.stdout.strip().split("\n") if "os.getenv" not in f and "os.environ" not in f]
        except Exception as _exc:
            logger.warning("Hardcoded-secrets scan failed: %s", _exc)
        return len(findings) == 0, findings

    def check_env_file_exposure(self) -> tuple[bool, list[str]]:
        exposed = []
        try:
            result = subprocess.run(
                ["find", "src/", "-name", ".env*", "-type", "f"],
                capture_output=True, text=True, cwd=self.repo_path,
            )
            if result.returncode == 0 and result.stdout:
                exposed = [f for f in result.stdout.strip().split("\n") if f and ".env.example" not in f and ".venv" not in f]
        except Exception as _exc:
            logger.warning("Env-file exposure scan failed: %s", _exc)
        return len(exposed) == 0, exposed

    def check_command_sanitizer(self) -> bool:
        return (self.repo_path / "src" / "security" / "command_sanitizer.py").exists()

    def run_security_checks(self) -> dict[str, Any]:
        print("=== Running Security Checks ===\n\n1. Scanning for hardcoded secrets...")
        secrets_ok, secrets_findings = self.check_hardcoded_secrets()
        print("   ✅ No hardcoded secrets found\n" if secrets_ok else f"   ❌ Found {len(secrets_findings)} potential secret(s)\n")

        print("2. Checking for exposed .env files...")
        env_ok, env_findings = self.check_env_file_exposure()
        print("   ✅ No exposed .env files\n" if env_ok else f"   ⚠️  Found {len(env_findings)} .env file(s)\n")

        print("3. Verifying command sanitizer...")
        sanitizer_ok = self.check_command_sanitizer()
        print("   ✅ Command sanitizer implemented\n" if sanitizer_ok else "   ❌ Command sanitizer NOT found\n")

        return {
            "secrets_ok": secrets_ok, "env_ok": env_ok, "sanitizer_ok": sanitizer_ok,
            "secrets_findings": secrets_findings, "env_findings": env_findings,
        }


__all__ = ["SecurityScannerMixin"]
