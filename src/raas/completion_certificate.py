# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Completion Certificate — ROIaaS Onboarding Lifecycle Closure."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.raas.completion_certificate_display import CompletionCertificateDisplayMixin


@dataclass
class CompletionCertificate(CompletionCertificateDisplayMixin):
    """ROIaaS Onboarding Completion Certificate."""

    certificate_id: str
    version: str = "1.0.0"
    issued_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    project_id: str = ""
    project_name: str = "Mekong CLI"
    project_version: str = "0.2.0"

    license_key_hash: str = ""
    license_tier: str = "free"
    license_expires_at: Optional[str] = None

    total_billed_usage_units: int = 0
    usage_period_start: Optional[str] = None
    usage_period_end: Optional[str] = None

    gateway_issuer: str = ""
    gateway_version: str = ""
    gateway_attestation_hash: str = ""

    phases_completed: Dict[str, bool] = field(default_factory=dict)
    all_phases_operational: bool = False

    validation_timestamp: str = ""
    validation_errors: List[str] = field(default_factory=list)

    signature: str = ""
    signature_algorithm: str = "SHA3-256"

    phases_hash: str = ""
    payment_provider: str = ""
    payment_webhook_verified: bool = False
    analytics_snapshot: Optional[Dict[str, Any]] = None
    kv_storage_key: Optional[str] = None
    kv_rate_limit_remaining: int = 0
    verification_url: str = ""
    jwt_issuer: str = ""
    mk_api_key_validated: bool = False

    def __post_init__(self) -> None:
        if not self.certificate_id:
            self.certificate_id = self._generate_certificate_id()
        if not self.signature:
            self.signature = self._generate_signature()

    def _generate_certificate_id(self) -> str:
        payload = f"{self.project_id}:{self.issued_at}:{self.project_name}"
        return f"CERT-{hashlib.sha256(payload.encode()).hexdigest()[:12].upper()}"

    def _generate_signature(self) -> str:
        payload = (
            f"{self.project_id}:{self.license_key_hash}:"
            f"{self.total_billed_usage_units}:{self.gateway_attestation_hash}:{self.validation_timestamp}"
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def verify_signature(self) -> bool:
        return self.signature == self._generate_signature()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def export(self, path: str) -> bool:
        try:
            output_path = Path(path).expanduser()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(self.to_json())
            os.chmod(output_path, 0o600)
            return True
        except Exception:
            return False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompletionCertificate":
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "CompletionCertificate":
        return cls.from_dict(json.loads(json_str))


def generate_certificate(
    validation_result: Any,
    phases_status: Optional[Dict[str, bool]] = None,
) -> CompletionCertificate:
    from src.raas.final_phase_validator import Phase6ValidationResult

    if not isinstance(validation_result, Phase6ValidationResult):
        raise ValueError("Expected Phase6ValidationResult")

    if phases_status is None:
        phases_status = {
            "Phase 1: License Gate": True,
            "Phase 2: License UI": True,
            "Phase 3: Payment Webhook": True,
            "Phase 4: Usage Metering": True,
            "Phase 5: Analytics Dashboard": True,
            "Phase 6: Terminal Validation": validation_result.all_passed,
        }

    all_operational = all(phases_status.values()) and validation_result.all_passed
    return CompletionCertificate(
        certificate_id="",
        project_id=validation_result.project_id,
        license_key_hash=validation_result.license_key_hash,
        total_billed_usage_units=validation_result.total_billed_usage,
        gateway_issuer=validation_result.gateway_issuer or "Unknown",
        gateway_version="2.0.0",
        gateway_attestation_hash=validation_result.attestation or "",
        phases_completed=phases_status,
        all_phases_operational=all_operational,
        validation_timestamp=validation_result.validation_timestamp,
        validation_errors=validation_result.errors,
    )


def load_certificate(path: str) -> Optional[CompletionCertificate]:
    try:
        with open(path, "r") as f:
            return CompletionCertificate.from_dict(json.load(f))
    except Exception:
        return None


def get_certificate_path() -> str:
    return os.path.expanduser("~/.mekong/raas/completion-certificate.json")


def save_certificate(cert: CompletionCertificate, path: Optional[str] = None) -> bool:
    return cert.export(path or get_certificate_path())


__all__ = [
    "CompletionCertificate", "generate_certificate", "load_certificate",
    "get_certificate_path", "save_certificate",
]
