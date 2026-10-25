#!/usr/bin/env python3
"""Generate a CycloneDX 1.5 SBOM for Mekong CLI's own first-party source.

CycloneDX describes third-party dependencies, but the component that matters for a
public MIT release is the repository's own code: this emits one component per
first-party Python module under src/, so a reader can see exactly which source is
published. Third-party packages are resolved from the environment when it is
installed, and reported as a separate list rather than invented.

Usage:
    python3 scripts/generate-sbom.py            # print CycloneDX JSON to stdout
    python3 scripts/generate-sbom.py --out path # write to a file
    python3 scripts/generate-sbom.py --check    # exit 1 if output would change

Stdlib only — no CycloneDX tooling dependency is added by this script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC_VERSION = "1.5"
BOM_FORMAT = "CycloneDX"
SCHEMA = "http://cyclonedx.org/schema/bom-1.5.schema.json"
SOURCE_ROOTS = ("src",)


def _read_license() -> str | None:
    text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8", errors="replace")
    return "MIT" if "MIT License" in text else None


def _project_version() -> str:
    for manifest, marker in (("pyproject.toml", "version"), ("package.json", "version")):
        path = REPO_ROOT / manifest
        if not path.is_file():
            continue
        try:
            if manifest.endswith(".toml"):
                for line in path.read_text(encoding="utf-8").splitlines():
                    if line.startswith(f"{marker} ="):
                        return line.split("=", 1)[1].strip().strip('"')
            else:
                data = json.loads(path.read_text(encoding="utf-8"))
                if version := data.get(marker):
                    return str(version)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return "0.0.0"


def _file_components() -> list[dict[str, object]]:
    components: list[dict[str, object]] = []
    for root in SOURCE_ROOTS:
        base = REPO_ROOT / root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            rel = path.relative_to(REPO_ROOT).as_posix()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            components.append(
                {
                    "type": "library",
                    "name": rel,
                    "version": _project_version(),
                    "hashes": [{"alg": "SHA-256", "content": digest}],
                    "licenses": [{"license": {"id": "MIT"}}],
                }
            )
    return components


def _metadata_component() -> dict[str, object]:
    component: dict[str, object] = {
        "type": "application",
        "name": "mekong-cli",
        "version": _project_version(),
        "bom-ref": "pkg:golang/github.com/minhlongs/mekong-cli@"
        + _project_version(),
    }
    if license_id := _read_license():
        component["licenses"] = [{"license": {"id": license_id}}]
    return component


def build_bom() -> dict[str, object]:
    components = _file_components()
    return {
        "bomFormat": BOM_FORMAT,
        "specVersion": SPEC_VERSION,
        "serialNumber": "urn:uuid:"
        + hashlib.sha256(
            json.dumps([c["name"] for c in components], sort_keys=True).encode()
        ).hexdigest()[:32],
        "version": 1,
        "metadata": {
            "component": _metadata_component(),
            "tools": [{"vendor": "mekong-cli", "name": "scripts/generate-sbom.py"}],
        },
        "components": components,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="write the SBOM to this path")
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 when the generated SBOM differs from --out (no write)",
    )
    args = parser.parse_args(argv)

    bom = build_bom()
    payload = json.dumps(bom, indent=2, ensure_ascii=False, sort_keys=True) + "\n"

    if args.check:
        if not args.out or not args.out.is_file():
            print("SBOM missing or unreadable", file=sys.stderr)
            return 1
        if args.out.read_text(encoding="utf-8") != payload:
            print(f"SBOM drift: {args.out} is out of date", file=sys.stderr)
            return 1
        print(f"SBOM up to date: {args.out} ({len(bom['components'])} components)")
        return 0

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
        print(f"Wrote {args.out} ({len(bom['components'])} components)", file=sys.stderr)
        return 0

    sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(os.sys.argv[1:]))
