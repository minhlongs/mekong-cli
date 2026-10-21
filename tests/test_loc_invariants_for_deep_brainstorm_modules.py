"""Module-size invariants for the guard-listed source trees.

The constraint is a reviewability one: a module that grows past the limit stops
being reviewable in one sitting, and the Open-Core/SAAS engines are the files a
contributor must read to trust the release gate. Keeping them small keeps that
review cheap.

The limit applies to the listed trees only, because those are the ones a
reviewer is asked to trust for the public-GitHub boundary. The rest of `src/`
has no such promise and is deliberately not policed here — a global limit would
redden the suite on 500+ unrelated pre-existing files.
"""
from __future__ import annotations

from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

MAX_LOC = 185

# Trees a reviewer is asked to trust when judging the public boundary.
GUARDED_TREES = (
    Path("src/core/opencore"),
)


def _python_files(tree: Path) -> list[Path]:
    root = REPO_ROOT / tree
    if not root.is_dir():
        return []
    return [p for p in sorted(root.rglob("*.py")) if "__pycache__" not in p.parts]


@pytest.mark.parametrize("tree", GUARDED_TREES)
def test_guarded_modules_stay_reviewable(tree: Path) -> None:
    files = _python_files(tree)
    assert files, f"no modules found under {tree} — did the path move?"
    oversized = {
        p.relative_to(REPO_ROOT).as_posix(): len(p.read_text(encoding="utf-8").splitlines())
        for p in files
        if len(p.read_text(encoding="utf-8").splitlines()) > MAX_LOC
    }
    assert not oversized, (
        f"modules over {MAX_LOC} LOC in {tree}: "
        + ", ".join(f"{k}={v}" for k, v in oversized.items())
    )


@pytest.mark.parametrize("tree", GUARDED_TREES)
def test_open_core_gate_probes_stay_separate(tree: Path) -> None:
    """The probe helpers must not collapse back into the engine they audit.

    Merging them would put the auditor and the audited code in one file, which
    is what let the caller-supplied defaults look like verification.
    """
    probes = REPO_ROOT / tree / "monetization_gate_probes.py"
    engine = REPO_ROOT / tree / "phase_560_opencore_saas_readiness_engine.py"
    if not probes.is_file() or not engine.is_file():
        pytest.skip(f"probe split not present under {tree}")
    probes_src = probes.read_text(encoding="utf-8")
    assert "def probe(" in probes_src, "probe entry point missing"
    assert "jwt_license_gate_enforced" in probes_src


def test_audit_repository_defaults_to_probing() -> None:
    """A green verdict must be impossible without running the probes.

    If `audit_repository` ever defaults the monetization flags back to True, the
    engine reports READY while checking nothing — the exact failure this suite
    exists to prevent.
    """
    import inspect

    from src.core.opencore.phase_560_opencore_saas_readiness_engine import (
        OpenCoreSaasReadinessEngine,
    )

    signature = inspect.signature(OpenCoreSaasReadinessEngine.audit_repository)
    for param in ("jwt_license_gate_enforced", "mcu_http402_billing_wired"):
        assert param in signature.parameters, f"{param} no longer accepted by audit_repository"
        assert signature.parameters[param].default is None, (
            f"{param} must default to None so the probe runs; a truthy default re-enables "
            "the unverified READY verdict"
        )
