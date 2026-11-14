"""Declarative Goose-compatible YAML recipe loader & MCP manifest SHA-256 allowlist verifier."""
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import yaml

from src.opc.accounting_draft import DRAFT_STATUS_PENDING_TVAN
from src.opc.state_graph import STAGE_SEQUENCE, GraphStage
from src.opc.verifier import MIN_EXTRACTION_CONFIDENCE

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent
DEFAULT_ALLOWLIST_PATH: Final[Path] = _REPO_ROOT / "config" / "mcp_manifest_allowlist.json"
DEFAULT_PILOT_A_RECIPE_PATH: Final[Path] = _REPO_ROOT / ".goose" / "recipes" / "pilot-a-zalo-lead-to-quote.yaml"
_EXPECTED_STAGE_NAMES: Final[tuple[str, ...]] = tuple(st.value for st in STAGE_SEQUENCE)


class RecipeValidationError(ValueError):
    """Raised when a declarative .goose/recipes/*.yaml recipe fails schema validation."""


class ManifestAllowlistError(PermissionError):
    """Raised when an MCP server or OPC pack manifest is unlisted or fails SHA-256 check."""


@dataclass(frozen=True)
class DeclarativeRecipe:
    """Validated Goose-compatible declarative workflow recipe."""

    version: str
    title: str
    description: str
    instructions: str
    min_confidence: float
    low_confidence_action: str
    accounting_draft_status: str
    stages: tuple[str, ...]
    required_capabilities: tuple[str, ...]
    price_sheet_schema: dict[str, Any]
    recipe_path: str = ""


def load_declarative_recipe(recipe_path: str | Path) -> DeclarativeRecipe:
    """Load and strictly validate a declarative YAML recipe using yaml.safe_load."""
    path = Path(recipe_path).resolve()
    if not path.is_file():
        raise RecipeValidationError(f"Recipe file not found: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise RecipeValidationError(f"Invalid YAML syntax in '{path.name}': {exc}") from exc
    if not isinstance(raw, dict):
        raise RecipeValidationError(f"Recipe '{path.name}' must parse to a YAML mapping.")
    return validate_recipe_dict(raw, recipe_path=str(path))


def validate_recipe_dict(raw: dict[str, Any], recipe_path: str = "") -> DeclarativeRecipe:
    """Validate declarative recipe fields and compliance invariants."""
    version = str(raw.get("version", "")).strip()
    title = str(raw.get("title", "")).strip()
    if not version or not title:
        raise RecipeValidationError("Recipe requires non-empty 'version' and 'title'.")

    try:
        min_conf = float(raw["min_confidence"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RecipeValidationError("Recipe requires numeric 'min_confidence'.") from exc
    if min_conf < MIN_EXTRACTION_CONFIDENCE or min_conf > 1.0:
        raise RecipeValidationError(f"Recipe min_confidence ({min_conf}) must be in [{MIN_EXTRACTION_CONFIDENCE}, 1.0].")

    low_act = str(raw.get("low_confidence_action", "")).strip()
    if low_act != GraphStage.HANDOFF_ZALO_OA_MANAGER.value:
        raise RecipeValidationError(f"low_confidence_action must be '{GraphStage.HANDOFF_ZALO_OA_MANAGER.value}', got '{low_act}'.")

    draft_status = str(raw.get("accounting_draft_status", "")).strip()
    if draft_status != DRAFT_STATUS_PENDING_TVAN:
        raise RecipeValidationError(f"accounting_draft_status must be '{DRAFT_STATUS_PENDING_TVAN}', got '{draft_status}'.")

    raw_stages = raw.get("stages")
    if not isinstance(raw_stages, list) or tuple(str(s) for s in raw_stages) != _EXPECTED_STAGE_NAMES:
        raise RecipeValidationError(f"Recipe stages must match exact 5-stage sequence {_EXPECTED_STAGE_NAMES}.")

    raw_caps = raw.get("required_capabilities")
    if not isinstance(raw_caps, list) or not raw_caps or not all(isinstance(c, str) and c.strip() for c in raw_caps):
        raise RecipeValidationError("Recipe must declare non-empty string 'required_capabilities'.")

    schema = raw.get("price_sheet_schema")
    if not isinstance(schema, dict) or schema.get("type") != "object" or "services" not in schema.get("properties", {}):
        raise RecipeValidationError("Recipe requires flat 'price_sheet_schema' object defining 'services'.")

    return DeclarativeRecipe(
        version=version,
        title=title,
        description=str(raw.get("description", "")).strip(),
        instructions=str(raw.get("instructions", "")).strip(),
        min_confidence=min_conf,
        low_confidence_action=low_act,
        accounting_draft_status=draft_status,
        stages=tuple(str(s) for s in raw_stages),
        required_capabilities=tuple(c.strip() for c in raw_caps),
        price_sheet_schema=schema,
        recipe_path=recipe_path,
    )


def compute_canonical_manifest_sha256(manifest_path: str | Path) -> tuple[str, str]:
    """Parse JSON manifest and return (manifest_id, canonical_sha256_hex)."""
    path = Path(manifest_path).resolve()
    if not path.is_file():
        raise ManifestAllowlistError(f"Manifest file not found: {path}")
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestAllowlistError(f"Malformed JSON manifest '{path.name}': {exc}") from exc
    if not isinstance(parsed, dict):
        raise ManifestAllowlistError(f"Manifest '{path.name}' must be a JSON object.")
    manifest_id = str(parsed.get("pack_id") or parsed.get("server_id") or parsed.get("name") or "").strip()
    if not manifest_id:
        raise ManifestAllowlistError(f"Manifest '{path.name}' missing 'pack_id'/'server_id' identifier.")
    canonical = json.dumps(parsed, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return manifest_id, hashlib.sha256(canonical).hexdigest()


def verify_mcp_manifest_sha256(
    manifest_path: str | Path, allowlist_path: str | Path = DEFAULT_ALLOWLIST_PATH,
) -> dict[str, str]:
    """Verify canonical SHA-256 digest of MCP/pack manifest against allowlist (fail-closed)."""
    allow_file = Path(allowlist_path).resolve()
    if not allow_file.is_file():
        raise ManifestAllowlistError(f"Allowlist file not found: {allow_file}")
    try:
        allow_data = json.loads(allow_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestAllowlistError(f"Malformed allowlist JSON '{allow_file.name}': {exc}") from exc
    entries = allow_data.get("manifests") if isinstance(allow_data, dict) else None
    if not isinstance(entries, dict):
        raise ManifestAllowlistError("Allowlist JSON missing 'manifests' mapping.")

    manifest_id, actual_sha256 = compute_canonical_manifest_sha256(manifest_path)
    entry = entries.get(manifest_id)
    if not isinstance(entry, dict):
        raise ManifestAllowlistError(f"Unlisted MCP/pack manifest '{manifest_id}' rejected (fail-closed).")
    expected_sha256 = str(entry.get("sha256", "")).strip().lower()
    if len(expected_sha256) != 64 or not hmac.compare_digest(expected_sha256, actual_sha256):
        raise ManifestAllowlistError(
            f"SHA-256 mismatch for manifest '{manifest_id}': expected {expected_sha256}, got {actual_sha256}."
        )
    return {"manifest_id": manifest_id, "sha256": actual_sha256, "status": "verified"}
