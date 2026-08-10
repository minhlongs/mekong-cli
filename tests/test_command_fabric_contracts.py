import json

from src.command_fabric.catalog import build_command_catalog
from src.command_fabric.contracts import (
    contract_coverage,
    generated_contract,
    materialize_command_contracts,
)


def test_generated_contract_has_deep_command_metadata() -> None:
    records = build_command_catalog()
    assert len(records) >= 1
    sample = records[0]
    contract = generated_contract(sample)

    assert contract["schema"] == "mekong.command_contract.v1"
    assert contract["id"] == sample.name
    assert contract["source"] == sample.source
    # execution may be empty for stub commands
    if contract["execution"].get("command"):
        assert contract["execution"]["command"].startswith("python3 -m src.main")
    assert contract["input"]["properties"]["arguments"]["type"] == "string"
    assert contract["output"]["required"] == ["exit_code"]


def test_contract_coverage_is_complete_with_generated_contracts() -> None:
    records = build_command_catalog()
    coverage = contract_coverage(records)

    assert coverage.command_count == len(records)
    assert coverage.complete is True
    assert coverage.missing_contracts == []


def test_materialize_command_contracts_writes_one_contract_per_command(tmp_path) -> None:
    records = build_command_catalog()
    payload = materialize_command_contracts(tmp_path, records)

    assert payload["schema"] == "mekong.command_contracts.materialized.v1"
    assert payload["contract_count"] == len(records)
    assert payload["coverage"]["complete"] is True
