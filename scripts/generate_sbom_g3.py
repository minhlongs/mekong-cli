#!/usr/bin/env python3
"""Reproducible CycloneDX 1.5 JSON SBOM & G3 license-compatibility generator for Mekong CLI.

Inventories Python dependencies, JS/Next.js lockfile dependencies, and Docker base images.
Never emits credentials, tokens, or private registry auth strings.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.metadata as ilm
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib
from typing import Any
from urllib.parse import quote

TOOL_NAME = "mekong-sbom-g3-generator"
TOOL_VERSION = "1.1.0"

_PERMISSIVE_LICENSES = frozenset({
    "MIT", "APACHE-2.0", "APACHE 2.0", "APACHE SOFTWARE LICENSE", "BSD-2-CLAUSE",
    "BSD-3-CLAUSE", "BSD", "BSD LICENSE", "ISC", "PSF-2.0", "PYTHON SOFTWARE FOUNDATION LICENSE",
    "0BSD", "CC0-1.0", "UNLICENSE", "ZLIB", "BLUEOAK-1.0.0", "WTPL",
})
_RESTRICTED_TOKENS = (
    "GPL", "AGPL", "LGPL", "MPL", "SSPL", "BSL", "FSL", "ELASTIC", "SUSTAINABLE USE",
    "COMMONS CLAUSE", "PROPRIETARY", "NON-COMMERCIAL", "N8N", "DIFY",
)
_REQ_LINE_RE = re.compile(r"^\s*([A-Za-z0-9_.\-]+)(?:\[[^\]]+\])?\s*(?:==|>=|<=|~=|!=|>|<)?\s*([^\s;#]+)?")
_DOCKER_FROM_RE = re.compile(r"^\s*FROM\s+(?:--platform=\S+\s+)?([^\s]+)", re.IGNORECASE)
_URL_CRED_RE = re.compile(r"(?:[a-zA-Z][a-zA-Z0-9+.-]*://|@)")


def _sanitize_version(raw: str | None) -> str:
    val = (raw or "").strip()
    if not val or _URL_CRED_RE.search(val):
        return "unspecified"
    return val


def _deterministic_timestamp(repo_root: Path) -> str:
    sde = (os.environ.get("SOURCE_DATE_EPOCH") or "").strip()
    if sde.isdigit():
        return datetime.fromtimestamp(int(sde), tz=timezone.utc).isoformat()
    try:
        out = subprocess.check_output(
            ["git", "show", "-s", "--format=%cI", "HEAD"],
            cwd=str(repo_root),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if out:
            return out
    except Exception:
        pass
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_head_sha(repo_root: Path) -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(repo_root), text=True, stderr=subprocess.DEVNULL)
        return out.strip()
    except Exception:
        return "UNKNOWN"


def _classify_license(raw_license: str | None) -> tuple[str, str]:
    clean = (raw_license or "").strip()
    if not clean or clean.upper() in ("UNKNOWN", "NONE", "N/A"):
        return "UNKNOWN", "LICENSE_REVIEW_REQUIRED"
    upper = clean.upper()
    if any(tok in upper for tok in _RESTRICTED_TOKENS):
        return clean, "LICENSE_REVIEW_REQUIRED"
    parts = [p.strip().strip("()") for p in re.split(r"\b(?:OR|AND)\b|,|/", upper) if p.strip()]
    if parts and all(p in _PERMISSIVE_LICENSES for p in parts):
        return clean, "PERMISSIVE_VERIFIED"
    if upper in _PERMISSIVE_LICENSES:
        return clean, "PERMISSIVE_VERIFIED"
    return clean, "LICENSE_REVIEW_REQUIRED"


def _extract_python_license(dist: ilm.Distribution) -> str:
    meta = dist.metadata
    expr = (meta.get("License-Expression") or "").strip()
    if expr:
        return expr
    classifiers = [c for c in meta.get_all("Classifier") or [] if c.startswith("License ::")]
    if classifiers:
        mapped: list[str] = []
        for cls in classifiers:
            leaf = cls.split("::")[-1].strip()
            if "MIT" in leaf:
                mapped.append("MIT")
            elif "Apache" in leaf:
                mapped.append("Apache-2.0")
            elif "BSD" in leaf:
                mapped.append("BSD-3-Clause")
            elif "ISC" in leaf:
                mapped.append("ISC")
            elif "Mozilla Public License 2.0" in leaf:
                mapped.append("MPL-2.0")
            elif "Python Software Foundation" in leaf:
                mapped.append("PSF-2.0")
            else:
                mapped.append(leaf)
        return " OR ".join(dict.fromkeys(mapped))
    lic = (meta.get("License") or "").strip()
    if lic and len(lic) <= 80 and "\n" not in lic:
        return lic
    return "UNKNOWN"


def _collect_python_components(repo_root: Path) -> tuple[list[dict[str, Any]], dict[str, str]]:
    lockfiles: dict[str, str] = {}
    locked_pkgs: dict[str, tuple[str, str]] = {}  # norm_name -> (version, scope)
    declared_direct: dict[str, str] = {}

    for rel in ("poetry.lock", "packages/mekongd/poetry.lock"):
        p = repo_root / rel
        if not p.exists():
            continue
        lockfiles[rel] = _sha256_file(p)
        data = tomllib.loads(p.read_text(encoding="utf-8"))
        for pkg in data.get("package") or []:
            name = str(pkg.get("name") or "").strip().lower().replace("_", "-")
            version = _sanitize_version(str(pkg.get("version") or ""))
            if name:
                locked_pkgs[name] = (version, "locked_transitive")

    for rel in ("requirements.txt", "requirements.seed.txt", "packages/alphaear/requirements.txt", "pyproject.toml"):
        p = repo_root / rel
        if not p.exists():
            continue
        lockfiles[rel] = _sha256_file(p)
        if rel.endswith(".txt"):
            for line in p.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or stripped.startswith("-"):
                    continue
                if " @ " in stripped:
                    pkg_part = stripped.split(" @ ", 1)[0].split("[", 1)[0].strip().lower().replace("_", "-")
                    if pkg_part:
                        declared_direct[pkg_part] = "unspecified"
                    continue
                m = _REQ_LINE_RE.match(stripped)
                if m:
                    declared_direct[m.group(1).lower().replace("_", "-")] = _sanitize_version(m.group(2))
        elif rel == "pyproject.toml":
            pyproj = tomllib.loads(p.read_text(encoding="utf-8"))
            deps = (pyproj.get("project") or {}).get("dependencies") or []
            for spec in deps:
                m = _REQ_LINE_RE.match(str(spec))
                if m:
                    declared_direct.setdefault(m.group(1).lower().replace("_", "-"), _sanitize_version(m.group(2)))

    installed: dict[str, ilm.Distribution] = {}
    for dist in ilm.distributions():
        name = (dist.metadata.get("Name") or "").strip()
        if name:
            installed[name.lower().replace("_", "-")] = dist

    all_names = sorted(set(locked_pkgs.keys()) | set(declared_direct.keys()))
    components: list[dict[str, Any]] = []
    for norm in all_names:
        if norm in locked_pkgs:
            version, scope = locked_pkgs[norm]
            if norm in declared_direct:
                scope = "direct"
        else:
            version = declared_direct[norm]
            scope = "direct"
        dist = installed.get(norm)
        raw_lic = _extract_python_license(dist) if dist is not None else "UNKNOWN"
        lic_expr, status = _classify_license(raw_lic)
        components.append({
            "type": "library",
            "name": norm,
            "version": version,
            "purl": f"pkg:pypi/{quote(norm, safe='')}@{quote(version, safe='')}",
            "licenses": [{"expression": lic_expr}] if lic_expr != "UNKNOWN" else [],
            "properties": [
                {"name": "mekong:ecosystem", "value": "python"},
                {"name": "mekong:scope", "value": scope},
                {"name": "mekong:license_status", "value": status},
            ],
        })
    return components, lockfiles


def _collect_npm_components(repo_root: Path) -> tuple[list[dict[str, Any]], dict[str, str]]:
    lockfiles: dict[str, str] = {}
    components: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for rel in ("package-lock.json", "apps/dashboard/package-lock.json"):
        p = repo_root / rel
        if not p.exists():
            continue
        lockfiles[rel] = _sha256_file(p)
        data = json.loads(p.read_text(encoding="utf-8"))
        packages = data.get("packages") or {}
        for pkg_path, info in sorted(packages.items()):
            if not pkg_path or not isinstance(info, dict):
                continue
            name = info.get("name") or pkg_path.split("node_modules/")[-1]
            version = str(info.get("version") or "unspecified").strip()
            if not name or (name, version) in seen:
                continue
            seen.add((name, version))
            raw_lic = info.get("license")
            if isinstance(raw_lic, list):
                raw_lic = " OR ".join(str(x) for x in raw_lic)
            lic_expr, status = _classify_license(str(raw_lic) if raw_lic else None)
            purl_name = quote(name, safe="@/")
            components.append({
                "type": "library",
                "name": name,
                "version": version,
                "purl": f"pkg:npm/{purl_name}@{quote(version, safe='')}",
                "licenses": [{"expression": lic_expr}] if lic_expr != "UNKNOWN" else [],
                "properties": [
                    {"name": "mekong:ecosystem", "value": "npm"},
                    {"name": "mekong:lockfile", "value": rel},
                    {"name": "mekong:license_status", "value": status},
                ],
            })
    return components, lockfiles


def _collect_docker_images(repo_root: Path) -> tuple[list[dict[str, Any]], dict[str, str]]:
    files: dict[str, str] = {}
    components: list[dict[str, Any]] = []
    seen: set[str] = set()
    for rel in ("Dockerfile", "Dockerfile.dashboard", "Dockerfile.seed", "apps/dashboard/Dockerfile", "packages/agent-core/Dockerfile"):
        p = repo_root / rel
        if not p.exists():
            continue
        files[rel] = _sha256_file(p)
        for line in p.read_text(encoding="utf-8").splitlines():
            m = _DOCKER_FROM_RE.match(line)
            if not m:
                continue
            ref = m.group(1).strip()
            if ref.lower() in ("scratch", "builder", "base", "deps", "runner"):
                continue
            if ref in seen:
                continue
            seen.add(ref)
            name, _, tag = ref.partition(":")
            version = tag or "latest"
            components.append({
                "type": "container",
                "name": name,
                "version": version,
                "purl": f"pkg:oci/{quote(name.split('/')[-1], safe='')}?tag={quote(version, safe='')}",
                "licenses": [],
                "properties": [
                    {"name": "mekong:ecosystem", "value": "docker"},
                    {"name": "mekong:source_file", "value": rel},
                    {"name": "mekong:license_status", "value": "LICENSE_REVIEW_REQUIRED"},
                ],
            })
    return components, files


def generate_sbom_report(repo_root: Path, *, advisory_scan_executed: bool = False) -> dict[str, Any]:
    """Build deterministic CycloneDX 1.5 JSON SBOM plus G3 exception register and verdict."""
    py_comps, py_locks = _collect_python_components(repo_root)
    npm_comps, npm_locks = _collect_npm_components(repo_root)
    docker_comps, docker_files = _collect_docker_images(repo_root)
    all_components = py_comps + npm_comps + docker_comps
    all_inputs = {**py_locks, **npm_locks, **docker_files}

    review_required = [
        {
            "name": c["name"],
            "version": c["version"],
            "purl": c["purl"],
            "licenses": [x.get("expression", "UNKNOWN") for x in c.get("licenses", [])] or ["UNKNOWN"],
            "ecosystem": next((p["value"] for p in c["properties"] if p["name"] == "mekong:ecosystem"), "unknown"),
        }
        for c in all_components
        if any(p["name"] == "mekong:license_status" and p["value"] == "LICENSE_REVIEW_REQUIRED" for p in c["properties"])
    ]
    g3_verdict = "PASS" if (not review_required and advisory_scan_executed) else "HOLD"
    commit_sha = _git_head_sha(repo_root)
    timestamp = _deterministic_timestamp(repo_root)

    bom: dict[str, Any] = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": timestamp,
            "tools": [{"vendor": "MekongMind", "name": TOOL_NAME, "version": TOOL_VERSION}],
            "component": {
                "type": "application",
                "name": "mekong-cli",
                "version": commit_sha[:12],
                "licenses": [{"expression": "MIT"}],
            },
            "properties": [
                {"name": "mekong:commit_sha", "value": commit_sha},
                {"name": "mekong:g3_verdict", "value": g3_verdict},
                {"name": "mekong:advisory_scan_executed", "value": str(advisory_scan_executed).lower()},
                {"name": "mekong:total_components", "value": str(len(all_components))},
                {"name": "mekong:license_review_required_count", "value": str(len(review_required))},
            ],
        },
        "components": all_components,
        "g3_assessment": {
            "verdict": g3_verdict,
            "input_manifest_sha256": all_inputs,
            "counts": {
                "python": len(py_comps),
                "npm": len(npm_comps),
                "docker": len(docker_comps),
                "total": len(all_components),
                "license_review_required": len(review_required),
            },
            "advisory_scan": {
                "executed": advisory_scan_executed,
                "note": "Offline deterministic SBOM generation; run pip-audit and npm audit in CI/online runner before lifting HOLD.",
            },
            "exception_register": review_required,
        },
    }
    return bom


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    repo_root = Path(__file__).resolve().parent.parent
    out_path = Path(args[0]) if args else repo_root / "sbom-g3-cyclonedx.json"
    bom = generate_sbom_report(repo_root, advisory_scan_executed=False)
    serialized = json.dumps(bom, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(serialized, encoding="utf-8")
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    print(json.dumps({
        "output": str(out_path),
        "sha256": digest,
        "commit_sha": bom["metadata"]["properties"][0]["value"],
        "g3_verdict": bom["g3_assessment"]["verdict"],
        "counts": bom["g3_assessment"]["counts"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
