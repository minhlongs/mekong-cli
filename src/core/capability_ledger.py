# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Capability Ledger Loader & Validator for the 197 Mekong CLI Command Groups.

Provides deterministic access to ``src/registry/capability_ledger.json``,
mapping every advertised command on ``https://www.mekongmind.com/cli`` to its
contract schema, department, operating layer (L0–L5), SOP chain, and maturity tier.

Pure Python standard-library implementation adhering to ``tests/test_core_boundary.py``.
"""

from __future__ import annotations

import json
import pathlib
import typing

REQUIRED_LEDGER_FIELDS: tuple[str, ...] = (
    "claim_id",
    "name",
    "command",
    "aliases",
    "cluster",
    "department_id",
    "layer_id",
    "promise_summary",
    "display_source",
    "input_schema",
    "cli_entrypoint",
    "api_transport",
    "handler_path",
    "owner_agent",
    "sop_steps",
    "data_rw",
    "output_schema",
    "external_effects",
    "approval_policy",
    "acceptance_criteria",
    "test_evidence",
    "maturity_tier",
)

VALID_MATURITY_TIERS: frozenset[str] = frozenset({
    "REAL_VERIFIED",
    "PARTIAL_LOOKUP",
    "CATALOG_ONLY",
})


class CapabilityLedger:
    """In-memory index over the 197-command capability ledger."""

    def __init__(self, ledger_path: str | pathlib.Path | None = None) -> None:
        if ledger_path is None:
            self.ledger_path = (
                pathlib.Path(__file__).resolve().parents[1]
                / "registry"
                / "capability_ledger.json"
            )
        else:
            self.ledger_path = pathlib.Path(ledger_path)

        self._entries: list[dict[str, typing.Any]] = self._load()
        self._by_name: dict[str, dict[str, typing.Any]] = {}
        self._by_claim_id: dict[str, dict[str, typing.Any]] = {}
        self._alias_map: dict[str, str] = {}

        for entry in self._entries:
            name = entry["name"]
            self._by_name[name] = entry
            self._by_claim_id[entry["claim_id"]] = entry
            for alias in entry.get("aliases", []):
                self._alias_map[alias] = name

    def _load(self) -> list[dict[str, typing.Any]]:
        raw = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError("capability_ledger.json root must be a JSON array")
        return raw

    def list_all(
        self,
        cluster: str | None = None,
        department_id: str | None = None,
        layer_id: str | None = None,
        maturity_tier: str | None = None,
    ) -> list[dict[str, typing.Any]]:
        """Filter capability entries by cluster, department, layer, or maturity tier."""
        results = self._entries
        if cluster:
            results = [e for e in results if e.get("cluster") == cluster]
        if department_id:
            results = [e for e in results if e.get("department_id") == department_id]
        if layer_id:
            results = [e for e in results if e.get("layer_id") == layer_id]
        if maturity_tier:
            results = [e for e in results if e.get("maturity_tier") == maturity_tier]
        return results

    def resolve_command(self, identifier: str) -> dict[str, typing.Any] | None:
        """Resolve a command by canonical name, ``mekong <name>``, alias, or claim_id."""
        cleaned = identifier.strip()
        if cleaned.startswith("mekong "):
            cleaned = cleaned[len("mekong ") :].strip().split()[0]

        if cleaned in self._by_name:
            return self._by_name[cleaned]
        if cleaned in self._by_claim_id:
            return self._by_claim_id[cleaned]
        if cleaned in self._alias_map:
            canonical = self._alias_map[cleaned]
            return self._by_name.get(canonical)
        return None

    def get_summary_stats(self) -> dict[str, typing.Any]:
        """Compute summary counts across clusters, layers, departments, and maturity tiers."""
        by_cluster: dict[str, int] = {}
        by_layer: dict[str, int] = {}
        by_department: dict[str, int] = {}
        by_tier: dict[str, int] = {}

        for entry in self._entries:
            c = entry["cluster"]
            l_id = entry["layer_id"]
            d_id = entry["department_id"]
            tier = entry["maturity_tier"]
            by_cluster[c] = by_cluster.get(c, 0) + 1
            by_layer[l_id] = by_layer.get(l_id, 0) + 1
            by_department[d_id] = by_department.get(d_id, 0) + 1
            by_tier[tier] = by_tier.get(tier, 0) + 1

        return {
            "total_command_groups": len(self._entries),
            "total_aliases": len(self._alias_map),
            "by_cluster": by_cluster,
            "by_layer": by_layer,
            "by_department": by_department,
            "by_maturity_tier": by_tier,
        }

    def validate_integrity(self) -> dict[str, typing.Any]:
        """Verify all 197 entries contain the 16 required contract fields and valid tiers."""
        errors: list[str] = []
        seen_ids: set[str] = set()
        seen_names: set[str] = set()

        for idx, entry in enumerate(self._entries):
            missing = [f for f in REQUIRED_LEDGER_FIELDS if f not in entry]
            if missing:
                errors.append(f"Entry #{idx} ({entry.get('name', '?')}) missing fields: {missing}")

            cid = entry.get("claim_id", "")
            if cid in seen_ids:
                errors.append(f"Duplicate claim_id: {cid}")
            seen_ids.add(cid)

            name = entry.get("name", "")
            if name in seen_names:
                errors.append(f"Duplicate command name: {name}")
            seen_names.add(name)

            tier = entry.get("maturity_tier", "")
            if tier not in VALID_MATURITY_TIERS:
                errors.append(f"Invalid maturity_tier '{tier}' on {name}")

        return {
            "valid": len(errors) == 0 and len(self._entries) == 197,
            "total_entries": len(self._entries),
            "errors": errors,
        }
