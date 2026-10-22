"""Computed evidence that the SaaS monetization gates are actually enforced.

These probes replace caller-asserted booleans with checks a reviewer can run.
Every probe reads source text or constructs throwaway objects in a temp
directory, so none of them reads or writes production billing state.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[3]

# A route that calls license_gate for every request, not one gated behind an opt-out.
_GATE_CONSUMER = "src/api/gateway_mission_routes.py"
# The layer that actually decides whether a caller's tier may run a command.
_TIER_AUTHORIZER = "src/core/command_authorizer.py"
# The canonical tier enum every other tier mapping must be derived from.
_TIER_MODULE = "src/seed/config/tiers_models.py"
_402_SITES = (
    "src/api/auth_routes.py",
    "src/api/gateway_webhook_mcu_routes.py",
    "src/raas/missions_service.py",
    "src/raas/marketplace_router_install.py",
    "src/raas/missions_api_router.py",
)


@dataclass(frozen=True)
class MonetizationProbe:
    jwt_license_gate_enforced: bool
    mcu_http402_billing_wired: bool
    gate_evidence: tuple[str, ...]
    billing_evidence: tuple[str, ...]
    gate_gaps: tuple[str, ...]
    billing_gaps: tuple[str, ...]


def _read(rel: str, root: Path | None = None) -> str:
    path = (root or REPO_ROOT) / rel
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _tier_names() -> set[str]:
    """Canonical tier names, lowercased, from the enum that owns them."""
    match = re.search(r"class TierKey\([^)]*\):(.*?)(?=\nclass |\Z)", _read(_TIER_MODULE), re.DOTALL)
    if not match:
        return set()
    return {name.lower() for name in re.findall(r"^\s{4}([A-Z][A-Z0-9_]*)\s*=", match.group(1), re.MULTILINE)}


# A gate skip is acceptable only when it is confined to a test or CI run.
_BYPASS_GUARDS = ("PYTEST_CURRENT_TEST", "CI")


def _mapped_tier_names(source: str) -> list[set[str]]:
    """Tier names used as keys of each inline tier-to-int mapping in source.

    Parsed rather than pattern-matched, so a mapping written across several
    lines is seen just as a single-line one is.
    """
    found: list[set[str]] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return found
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict) or not node.keys:
            continue
        keys = {k.value.lower() for k in node.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)}
        if (keys & _tier_names()) and any(isinstance(v, ast.Constant) for v in node.values):
            found.append(keys)
    return found


def _probe_license_gate(root: Path | None = None) -> tuple[bool, tuple[str, ...], tuple[str, ...]]:
    evidence: list[str] = []
    gaps: list[str] = []
    consumer = _read(_GATE_CONSUMER, root)
    if "license_gate" not in consumer:
        gaps.append(f"{_GATE_CONSUMER}: license_gate is not called by any route")
    elif "LICENSE_GATE_ENFORCE" in consumer and not all(g in consumer for g in _BYPASS_GUARDS):
        evidence.append(f"{_GATE_CONSUMER}: calls license_gate")
        gaps.append(f"{_GATE_CONSUMER}: gate is conditional on LICENSE_GATE_ENFORCE without a test-only guard, so it can be turned off at runtime")
    else:
        evidence.append(f"{_GATE_CONSUMER}: calls license_gate, with any skip confined to test/CI runs")

    # The tier decision lives in the command authorizer, not in the entitlement
    # reporter, which only reads usage counts for display.
    authorizer = _read(_TIER_AUTHORIZER, root)
    tier_names = _tier_names()
    if "INSUFFICIENT_TIER" not in authorizer:
        gaps.append(f"{_TIER_AUTHORIZER}: never denies a command for insufficient tier")
    else:
        evidence.append(f"{_TIER_AUTHORIZER}: denies commands with INSUFFICIENT_TIER")

    # A hardcoded tier mapping that omits a paying tier makes that tier
    # authorize as free, because the lookup defaults unknown tiers to level 0.
    for mapped in _mapped_tier_names(authorizer):
        unmapped = sorted(tier_names - mapped)
        if unmapped:
            gaps.append(
                f"{_TIER_AUTHORIZER}: tier map omits {', '.join(unmapped)}, "
                "so those tiers authorize at the free level"
            )
        else:
            evidence.append(f"{_TIER_AUTHORIZER}: tier map covers every canonical tier")
    return not gaps, tuple(evidence), tuple(gaps)


def _probe_billing(root: Path | None = None) -> tuple[bool, tuple[str, ...], tuple[str, ...]]:
    evidence: list[str] = []
    gaps: list[str] = []
    emitters = [rel for rel in _402_SITES if "402" in _read(rel, root)]
    if not emitters:
        gaps.append("no route emits HTTP 402")
    else:
        evidence.append("HTTP 402 emitted in: " + ", ".join(emitters))
    if len(emitters) < len(_402_SITES):
        missing = sorted(set(_402_SITES) - set(emitters))
        gaps.append("expected emitters without a 402 status: " + ", ".join(missing))
    return not gaps, tuple(evidence), tuple(gaps)


def probe(repo_root: str | Path | None = None) -> MonetizationProbe:
    """Compute both monetization flags from repository evidence."""
    root = Path(repo_root).resolve() if repo_root is not None else REPO_ROOT
    gate_ok, gate_evidence, gate_gaps = _probe_license_gate(root)
    billing_ok, billing_evidence, billing_gaps = _probe_billing(root)
    return MonetizationProbe(gate_ok, billing_ok, gate_evidence, billing_evidence, gate_gaps, billing_gaps)


def expected_verdict() -> str:
    """The verdict a correct audit must report for this repository.

    Both flags used to be caller-supplied defaults, so every audit read READY and the
    value carried no information. Tests assert this computed value instead of a literal.
    """
    probes = probe()
    if probes.jwt_license_gate_enforced and probes.mcu_http402_billing_wired:
        return "PUBLIC_GITHUB_SAAS_READY"
    return "MONETIZATION_GATE_INCOMPLETE"

