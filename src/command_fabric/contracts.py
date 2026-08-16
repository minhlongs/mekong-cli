# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Generate machine-readable command contracts from command fabric records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.command_fabric.catalog import CommandRecord, build_command_catalog


@dataclass(frozen=True)
class CommandContractCoverage:
    """Command contract coverage summary."""

    command_count: int
    existing_contract_count: int
    generated_contract_count: int
    missing_contracts: list[str]

    @property
    def complete(self) -> bool:
        return self.command_count == self.existing_contract_count + self.generated_contract_count


def generated_contract(record: CommandRecord) -> dict[str, object]:
    """Return a deterministic contract for one command fabric record."""
    return {
        "schema": "mekong.command_contract.v1",
        "id": record.name,
        "version": "1.0.0",
        "source": record.source,
        "generated": record.contract is None,
        "source_contract": record.contract,
        "layer": record.layer or "unassigned",
        "display": {
            "name": record.name,
            "description": record.description,
        },
        "execution": {
            "command": record.execution,
            "argument_hint": record.argument_hint,
            "allowed_tools": record.allowed_tools,
            "portability_targets": record.portability_targets,
            "requires_approval": False,
        },
        "input": {
            "type": "object",
            "properties": {
                "arguments": {
                    "type": "string",
                    "description": record.argument_hint or "Arguments to pass to the command",
                }
            },
            "required": [],
        },
        "output": {
            "type": "object",
            "properties": {
                "stdout": {"type": "string"},
                "stderr": {"type": "string"},
                "exit_code": {"type": "integer"},
            },
            "required": ["exit_code"],
        },
        "validation": {
            "must_not_recurse": record.execution.strip() == f"mekong {record.name}",
            "max_exit_code": 0,
        },
    }


def contract_coverage(records: list[CommandRecord] | None = None) -> CommandContractCoverage:
    """Return coverage for existing and generated command contracts."""
    command_records = records if records is not None else build_command_catalog()
    existing = [record for record in command_records if record.contract]
    generated = [record for record in command_records if not record.contract]
    return CommandContractCoverage(
        command_count=len(command_records),
        existing_contract_count=len(existing),
        generated_contract_count=len(generated),
        missing_contracts=[],
    )


def materialize_command_contracts(
    output_dir: Path,
    records: list[CommandRecord] | None = None,
) -> dict[str, object]:
    """Write one generated command contract per catalog record."""
    command_records = records if records is not None else build_command_catalog()
    contracts_dir = output_dir / "contracts" / "commands"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    for record in command_records:
        path = contracts_dir / f"{record.name}.json"
        path.write_text(json.dumps(generated_contract(record), indent=2) + "\n", encoding="utf-8")

    coverage = contract_coverage(command_records)
    return {
        "schema": "mekong.command_contracts.materialized.v1",
        "output_dir": output_dir.as_posix(),
        "contract_count": len(command_records),
        "coverage": coverage.__dict__ | {"complete": coverage.complete},
    }


__all__ = [
    "CommandContractCoverage",
    "contract_coverage",
    "generated_contract",
    "materialize_command_contracts",
]
