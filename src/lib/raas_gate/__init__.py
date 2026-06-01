"""
RaaS Gate package — public API re-exports.

Usage:
from src.lib.raas_gate import RaasLicenseGate, get_license_gate, require_license, check_license
from src.lib.raas_gate import LicenseService, LicenseTier, PREMIUM_FEATURES
"""

from .license_gate_core import RaasLicenseGate
from .license_compat import LicenseService, LicenseTier, PREMIUM_FEATURES, _ValidationResult # noqa: F401
from .async_helper import _run_async_safe # noqa: F401

# Re-export dependencies so existing patch() targets remain valid
import requests # noqa: F401
from src.lib.license_generator import validate_license # noqa: F401
from src.lib.usage_meter import record_usage # noqa: F401
from src.lib.jwt_license_generator import validate_jwt_license # noqa: F401


def get_cached_quota(key_id):
    """Lazy wrapper - defers import until first call."""
    from src.raas.quota_cache import get_cached_quota as _f
    return _f(key_id)


from src.core.license_monitor import record_failure as record_license_failure # noqa: F401
from src.lib.quota_error_messages import ( # noqa: F401
    format_grace_period_expired,
    format_license_expired,
    format_license_revoked,
)

from typing import Optional

_license_gate: Optional[RaasLicenseGate] = None


def get_license_gate(enable_remote: bool = True) -> RaasLicenseGate:
    """Get or create global RaasLicenseGate singleton."""
    global _license_gate
    if _license_gate is None:
        _license_gate = RaasLicenseGate(enable_remote=enable_remote)
    return _license_gate


def require_license(command: str) -> None:
    """Require valid license for command or raise SystemExit(1)."""
    gate = get_license_gate()
    allowed, error = gate.check(command)
    if not allowed:
        from rich.console import Console
        Console().print(f"[bold red]License Error:[/bold red] {error}")
        raise SystemExit(1)


def check_license(command: str) -> bool:
    """Check if license allows command. Returns bool."""
    gate = get_license_gate()
    allowed, _ = gate.check(command)
    return allowed


__all__ = [
    "RaasLicenseGate",
    "get_license_gate",
    "require_license",
    "check_license",
    "LicenseService",
    "LicenseTier",
    "PREMIUM_FEATURES",
]
