"""Declarative Pack Manifest loader, validator, and registry (opc-pack/v1)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from src.opc.models import PackManifest

SUPPORTED_SCHEMA_VERSIONS = {"opc-pack/v1"}
SUPPORTED_RUNTIMES = {"mekong-runtime>=6.0", "mekong-runtime==6.0.0"}
ENTRYPOINT_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_\.]*:[a-zA-Z_][a-zA-Z0-9_]*$")


class ManifestValidationError(ValueError):
    """Raised when a pack manifest fails declarative validation."""


def _check_string(data: dict[str, Any], key: str, errs: list[str]) -> str:
    val = data.get(key)
    if not isinstance(val, str) or not val.strip():
        errs.append(f"Field '{key}' must be a non-empty string.")
        return ""
    return val.strip()


def validate_pack_manifest_dict(raw: dict[str, Any], pack_dir: str = "") -> PackManifest:
    """Validate a raw manifest dict without executing any Python code."""
    errors: list[str] = []

    pack_id = _check_string(raw, "pack_id", errors)
    version = _check_string(raw, "version", errors)
    schema_ver = _check_string(raw, "schema_version", errors)
    owner = _check_string(raw, "owner", errors)
    lic = _check_string(raw, "license", errors)
    compat_rt = _check_string(raw, "compatible_runtime", errors)
    wf_id = _check_string(raw, "workflow_id", errors)
    entrypoint = _check_string(raw, "entrypoint", errors)

    if schema_ver and schema_ver not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(f"Unsupported schema_version: '{schema_ver}'. Supported: {SUPPORTED_SCHEMA_VERSIONS}")

    if compat_rt and not any(compat_rt.startswith(sup.split(">=")[0]) for sup in SUPPORTED_RUNTIMES):
        errors.append(f"Incompatible runtime: '{compat_rt}'. Supported: {SUPPORTED_RUNTIMES}")

    if entrypoint and not ENTRYPOINT_RE.match(entrypoint):
        errors.append(f"Invalid entrypoint format '{entrypoint}'. Expected 'module.path:AttributeName'.")

    input_schema = raw.get("input_schema")
    if not isinstance(input_schema, dict) or not input_schema:
        errors.append("Field 'input_schema' must be a non-empty JSON schema dict.")

    output_schema = raw.get("output_schema")
    if not isinstance(output_schema, dict) or not output_schema:
        errors.append("Field 'output_schema' must be a non-empty JSON schema dict.")

    connectors = tuple(raw.get("connectors", []))
    capabilities = tuple(raw.get("capabilities", []))
    permissions = tuple(raw.get("permissions", []))

    if not capabilities:
        errors.append("Pack must declare at least one capability in 'capabilities'.")

    approval_req = raw.get("approval_required")
    if not isinstance(approval_req, bool):
        errors.append("Field 'approval_required' must be a boolean.")

    cost_policy = raw.get("cost_policy")
    if not isinstance(cost_policy, dict):
        errors.append("Field 'cost_policy' must be a dict.")

    languages = tuple(raw.get("languages", ["en"]))
    jurisdiction = raw.get("jurisdiction", "global")
    cred_refs = tuple(raw.get("credential_refs", []))
    ext_effects = tuple(raw.get("external_effects", []))

    if errors:
        raise ManifestValidationError(f"Invalid pack manifest: {'; '.join(errors)}")

    return PackManifest(
        pack_id=pack_id,
        version=version,
        schema_version=schema_ver,
        owner=owner,
        license=lic,
        compatible_runtime=compat_rt,
        workflow_id=wf_id,
        entrypoint=entrypoint,
        input_schema=input_schema or {},
        output_schema=output_schema or {},
        connectors=connectors,
        credential_refs=cred_refs,
        capabilities=capabilities,
        permissions=permissions,
        external_effects=ext_effects,
        approval_required=bool(approval_req),
        cost_policy=cost_policy or {},
        languages=languages,
        jurisdiction=jurisdiction,
        pack_dir=pack_dir,
    )


def load_pack_manifest(manifest_path: str | Path) -> PackManifest:
    """Read and validate a pack manifest file purely as JSON."""
    path = Path(manifest_path).resolve()
    if not path.is_file():
        raise ManifestValidationError(f"Manifest file not found: {path}")

    try:
        raw_text = path.read_text(encoding="utf-8")
        data = json.loads(raw_text)
    except Exception as exc:
        raise ManifestValidationError(f"Failed to parse manifest JSON from {path.name}: {exc}") from exc

    if not isinstance(data, dict):
        raise ManifestValidationError(f"Manifest must be a JSON object, got {type(data).__name__}")

    return validate_pack_manifest_dict(data, pack_dir=str(path.parent))


class PackRegistry:
    """Registry managing discovered packs with duplicate ID rejection."""

    def __init__(self) -> None:
        self._packs: dict[str, PackManifest] = {}

    def register(self, manifest: PackManifest) -> None:
        """Register a validated pack manifest, rejecting duplicates."""
        if manifest.pack_id in self._packs:
            existing = self._packs[manifest.pack_id]
            raise ManifestValidationError(
                f"Duplicate pack_id '{manifest.pack_id}' already registered from {existing.pack_dir}"
            )
        self._packs[manifest.pack_id] = manifest

    def get(self, pack_id: str) -> PackManifest | None:
        return self._packs.get(pack_id)

    def list_packs(self) -> list[PackManifest]:
        return list(self._packs.values())

    def discover_from_dir(self, directory: str | Path) -> int:
        """Scan a directory for pack.json manifests and register them."""
        base = Path(directory).resolve()
        count = 0
        if not base.is_dir():
            return 0
        for manifest_file in base.rglob("pack.json"):
            manifest = load_pack_manifest(manifest_file)
            self.register(manifest)
            count += 1
        return count
