"""Tests for reproducible CycloneDX 1.5 G3 SBOM generator and fail-closed license classification."""
from __future__ import annotations

import json
from pathlib import Path
import re

from scripts.generate_sbom_g3 import _classify_license, generate_sbom_report


def test_license_classification_never_assumes_permissive_for_restricted_or_unknown() -> None:
    assert _classify_license("MIT") == ("MIT", "PERMISSIVE_VERIFIED")
    assert _classify_license("Apache-2.0") == ("Apache-2.0", "PERMISSIVE_VERIFIED")
    assert _classify_license("MIT OR Apache-2.0") == ("MIT OR Apache-2.0", "PERMISSIVE_VERIFIED")

    for restricted in ("", None, "UNKNOWN", "MPL-2.0", "GPL-3.0-only", "AGPL-3.0", "LGPL-2.1", "FSL-1.1-MIT", "BSL-1.1", "SSPL-1.0", "Sustainable Use License (n8n)", "Dify Open Source License"):
        _, status = _classify_license(restricted)
        assert status == "LICENSE_REVIEW_REQUIRED", f"Expected LICENSE_REVIEW_REQUIRED for {restricted!r}"


def test_generate_sbom_report_covers_python_npm_docker_and_emits_zero_secrets() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    bom = generate_sbom_report(repo_root, advisory_scan_executed=False)
    bom_repeat = generate_sbom_report(repo_root, advisory_scan_executed=False)
    assert bom == bom_repeat  # Byte-deterministic on the same commit

    assert bom["bomFormat"] == "CycloneDX"
    assert bom["specVersion"] == "1.5"
    counts = bom["g3_assessment"]["counts"]
    assert counts["python"] > 0
    assert counts["npm"] > 0
    assert counts["docker"] > 0
    assert counts["total"] == counts["python"] + counts["npm"] + counts["docker"]
    assert bom["g3_assessment"]["verdict"] == "HOLD"

    # Every component has a valid purl and never leaks URL credentials
    for comp in bom["components"]:
        assert comp["purl"].startswith("pkg:")
        assert comp["name"] and comp["version"]
        assert "://" not in comp["version"]

    # Zero credentials or tokens emitted
    serialized = json.dumps(bom)
    for forbidden in (r"ghp_[A-Za-z0-9]{20,}", r"sk-[A-Za-z0-9]{20,}", r"AKIA[0-9A-Z]{16}", r"BEGIN [A-Z ]*PRIVATE KEY"):
        assert re.search(forbidden, serialized) is None
