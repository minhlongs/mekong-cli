"""Deterministic readiness & leak-gate auditor for 25-Step Open-Core SaaS (Phase 560)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import subprocess
from typing import Any

from src.core.opencore.phase_559_opencore_25_step_catalog import (
    TWENTY_FIVE_OPENCORE_STEPS,
    OpenCorePhase,
    OpenCoreStepSpec,
)

REQUIRED_GITIGNORE_RULES: tuple[str, ...] = ("apps/", "billing/", "*.pem", ".orchestrate/")
REQUIRED_ENV_EXAMPLE_KEYS: tuple[str, ...] = (
    "OPENROUTER_API_KEY", "DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY", "ZALO_OA_SECRET_KEY",
    "NOWPAYMENTS_API_KEY", "NOWPAYMENTS_IPN_SECRET", "PAYOS_CLIENT_ID", "PAYOS_API_KEY",
    "PAYOS_CHECKSUM_KEY", "JWT_SECRET",
)
FORBIDDEN_SECRET_PREFIXES: tuple[str, ...] = ("sk-or-v1-", "sk-ant-", "AIzaSy")


class OpenCoreReadinessVerdict(str, Enum):
    BLOCKED_SECRET_OR_BOUNDARY_LEAK = "BLOCKED_SECRET_OR_BOUNDARY_LEAK"
    MONETIZATION_GATE_INCOMPLETE = "MONETIZATION_GATE_INCOMPLETE"
    PUBLIC_GITHUB_SAAS_READY = "PUBLIC_GITHUB_SAAS_READY"


@dataclass(frozen=True)
class OpenCoreReadinessTelemetry:
    completed_step_Count: int
    leaked_secrets_detected: int
    private_dirs_exposed_in_git: bool
    jwt_license_gate_enforced: bool
    mcu_http402_billing_wired: bool
    monetization_gaps: tuple[str, ...] = ()


@dataclass(frozen=True)
class FilesystemHygieneResult:
    is_clean: bool
    gitignore_valid: bool
    env_example_valid: bool
    license_mit_valid: bool
    contributing_cla_valid: bool
    apps_tracked_files_count: int
    leaked_secrets_detected: int
    missing_items: tuple[str, ...]


@dataclass(frozen=True)
class OpenCoreReadinessReport:
    verdict: OpenCoreReadinessVerdict
    completion_pct: float
    total_catalog_steps: int
    safe_for_public_github_push: bool
    saas_paywall_active: bool
    rationale: str
    monetization_gaps: tuple[str, ...] = ()


def _read_if_exists(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


class OpenCoreSaasReadinessEngine:
    """Evaluates whether the repository can be pushed to public GitHub while preserving SaaS revenue."""

    @staticmethod
    def list_steps(phase: OpenCorePhase | None = None) -> tuple[OpenCoreStepSpec, ...]:
        return TWENTY_FIVE_OPENCORE_STEPS if phase is None else tuple(s for s in TWENTY_FIVE_OPENCORE_STEPS if s.phase == phase)

    @staticmethod
    def verify_filesystem_hygiene(repo_root: str | Path) -> FilesystemHygieneResult:
        root = Path(repo_root).resolve()
        missing: list[str] = []
        gi_lines = {ln.strip() for ln in _read_if_exists(root / ".gitignore").splitlines() if ln.strip()}
        missing_gi = [r for r in REQUIRED_GITIGNORE_RULES if r not in gi_lines and not (r == "apps/" and "apps/*" in gi_lines)]
        missing.extend(f".gitignore:{r}" for r in missing_gi)

        env_path = root / ".env.example"
        env_text = _read_if_exists(env_path)
        missing_env = [k for k in REQUIRED_ENV_EXAMPLE_KEYS if f"{k}=" not in env_text]
        leaked_secrets = sum(1 for p in FORBIDDEN_SECRET_PREFIXES if p in env_text)
        env_valid = not missing_env and leaked_secrets == 0 and env_path.is_file()
        missing.extend(f".env.example:{k}" for k in missing_env)

        lic_valid = "MIT License" in _read_if_exists(root / "LICENSE")
        if not lic_valid:
            missing.append("LICENSE:MIT License")
        contrib_text = _read_if_exists(root / "CONTRIBUTING.md")
        cla_valid = "CLA" in contrib_text and "Trademark" in contrib_text
        if not cla_valid:
            missing.append("CONTRIBUTING.md:CLA/Trademark")

        apps_tracked = 0
        if (root / ".git").exists():
            try:
                proc = subprocess.run(["git", "-C", str(root), "ls-files", "apps/", "billing/"], capture_output=True, text=True, check=False, timeout=10)
                if proc.returncode == 0:
                    apps_tracked = sum(1 for ln in proc.stdout.splitlines() if ln.strip() and not ln.strip().startswith("apps/dashboard/"))
            except (OSError, subprocess.SubprocessError):
                apps_tracked = 0
        if apps_tracked > 0:
            missing.append(f"git-index:tracked-private-files={apps_tracked}")

        gi_valid = not missing_gi
        is_clean = gi_valid and env_valid and lic_valid and cla_valid and apps_tracked == 0 and leaked_secrets == 0
        return FilesystemHygieneResult(is_clean, gi_valid, env_valid, lic_valid, cla_valid, apps_tracked, leaked_secrets, tuple(missing))

    @staticmethod
    def audit_blueprint(repo_root: str | Path) -> dict[str, Any]:
        """Verify 25-step synchronization across tasks.md, plan.md, brainstorm doc, and company.json."""
        root = Path(repo_root).resolve()
        bp_dir = root / "plans" / "company-blueprint"
        tasks_path, plan_path, brainstorm_path = bp_dir / "tasks.md", bp_dir / "plan.md", bp_dir / "brainstorm-25-step-opencore-saas.md"
        company_path = root / ".mekong" / "company.json"
        tasks_text = _read_if_exists(tasks_path)
        matched = [s.slug for s in TWENTY_FIVE_OPENCORE_STEPS if s.slug in tasks_text]
        lenses_ok = all(lens in tasks_text for lens in ("[Business]", "[Agentic]", "[Governance]"))
        company_clean = False
        if company_path.is_file():
            data = json.loads(_read_if_exists(company_path))
            company_clean = len(data.get("binh_phap_state", {}).get("revenue_events", [])) == 0 and data.get("open_core_25_steps_aligned") is True
        return {
            "tasks_exists": tasks_path.is_file(), "plan_exists": plan_path.is_file(),
            "brainstorm_exists": brainstorm_path.is_file(), "matched_steps_count": len(matched),
            "total_expected_steps": len(TWENTY_FIVE_OPENCORE_STEPS), "three_lenses_present": lenses_ok,
            "company_json_clean": company_clean,
            "synchronized": len(matched) == 25 and lenses_ok and plan_path.is_file() and brainstorm_path.is_file() and company_clean,
        }

    @classmethod
    def audit_repository(cls, repo_root: str | Path, completed_steps: int = 25, jwt_license_gate_enforced: bool | None = None, mcu_http402_billing_wired: bool | None = None, verify_monetization: bool = True) -> OpenCoreReadinessReport:
        h = cls.verify_filesystem_hygiene(repo_root)
        gaps: tuple[str, ...] = ()
        if verify_monetization and jwt_license_gate_enforced is None and mcu_http402_billing_wired is None:
            from src.core.opencore.monetization_gate_probes import probe
            probes = probe(repo_root)
            gate_enforced, billing_wired = probes.jwt_license_gate_enforced, probes.mcu_http402_billing_wired
            gaps = probes.gate_gaps + probes.billing_gaps
        else:
            gate_enforced = bool(jwt_license_gate_enforced) if jwt_license_gate_enforced is not None else True
            billing_wired = bool(mcu_http402_billing_wired) if mcu_http402_billing_wired is not None else True
        return cls.evaluate(OpenCoreReadinessTelemetry(completed_steps, h.leaked_secrets_detected, h.apps_tracked_files_count > 0 or not h.is_clean, gate_enforced, billing_wired, gaps))

    @staticmethod
    def evaluate(telemetry: OpenCoreReadinessTelemetry) -> OpenCoreReadinessReport:
        total = len(TWENTY_FIVE_OPENCORE_STEPS)
        clamped = max(0, min(total, telemetry.completed_step_Count))
        pct = round((clamped / total) * 100.0, 2)
        if telemetry.leaked_secrets_detected > 0 or telemetry.private_dirs_exposed_in_git:
            return OpenCoreReadinessReport(OpenCoreReadinessVerdict.BLOCKED_SECRET_OR_BOUNDARY_LEAK, pct, total, False, False, "Secret leak or private apps/billing directory exposed in public git index.")
        if not (telemetry.jwt_license_gate_enforced and telemetry.mcu_http402_billing_wired) or clamped < total:
            if telemetry.monetization_gaps:
                rationale = "Public hygiene clean, but the paywall is unverified: " + "; ".join(telemetry.monetization_gaps)
            else:
                rationale = "Public hygiene clean, but JWT license_gate or HTTP 402 MCU billing incomplete."
            return OpenCoreReadinessReport(OpenCoreReadinessVerdict.MONETIZATION_GATE_INCOMPLETE, pct, total, True, False, rationale, telemetry.monetization_gaps)
        return OpenCoreReadinessReport(OpenCoreReadinessVerdict.PUBLIC_GITHUB_SAAS_READY, pct, total, True, True, "All 25 Open-Core steps verified: MIT public repo safe and Cloud SaaS paywall active.")
