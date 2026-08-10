import json


from src.command_fabric.artifacts import materialize_command_fabric
from src.command_fabric.adapters import SUPPORTED_ADAPTERS
from src.command_fabric.catalog import build_command_catalog
from src.command_fabric.runtime import (
    command_fabric_manifest,
    invoke_command_fabric,
    records_for_scope,
)


def test_command_fabric_materializes_adapter_artifacts(tmp_path) -> None:
    payload = materialize_command_fabric(
        output_dir=tmp_path,
        scope="project",
        adapters=["mcp", "vscode"],
    )

    assert payload["schema"] == "mekong.command_fabric.artifacts.v1"
    assert payload["scope"] == "project"
    assert payload["artifact_count"] == 5
    assert (tmp_path / "canonical.json").exists()
    assert (tmp_path / "mcp.json").exists()
    assert (tmp_path / "vscode.json").exists()
    assert (tmp_path / "adapters.json").exists()
    assert (tmp_path / "command-packs.json").exists()

    mcp_payload = json.loads(
        (tmp_path / "mcp.json").read_text(encoding="utf-8")
    )
    assert mcp_payload["schema"] == "mekong.command_fabric.adapter.mcp.v1"
    assert mcp_payload["tool_count"] == len(build_command_catalog())

    bundle = json.loads(
        (tmp_path / "adapters.json").read_text(encoding="utf-8")
    )
    assert bundle["schema"] == "mekong.command_fabric.adapter_bundle.v1"
    assert bundle["adapter_count"] == 2
    assert set(bundle["adapters"]) == {"mcp", "vscode"}


def test_command_fabric_cli_materializes_artifacts(tmp_path) -> None:
    payload = materialize_command_fabric(
        output_dir=tmp_path,
        scope="project",
        adapters=["shell"],
    )

    assert payload["schema"] == "mekong.command_fabric.artifacts.v1"
    assert payload["artifact_count"] == 4
    assert (tmp_path / "canonical.json").exists()
    assert (tmp_path / "shell.json").exists()
    assert (tmp_path / "adapters.json").exists()
    assert (tmp_path / "command-packs.json").exists()


def test_command_fabric_materializes_deploy_ready_adapter_bundle(tmp_path) -> None:
    payload = materialize_command_fabric(output_dir=tmp_path, scope="project")

    assert payload["artifact_count"] == len(SUPPORTED_ADAPTERS) + 2
    bundle = json.loads(
        (tmp_path / "adapters.json").read_text(encoding="utf-8")
    )
    assert bundle["schema"] == "mekong.command_fabric.adapter_bundle.v1"
    assert bundle["adapter_count"] == len(SUPPORTED_ADAPTERS) - 1
    assert set(bundle["adapters"]) == set(SUPPORTED_ADAPTERS) - {"canonical"}


def test_command_fabric_runtime_lists_project_mcp_tools() -> None:
    payload = command_fabric_manifest(adapter="mcp", scope="project")

    assert payload["schema"] == "mekong.command_fabric.adapter.mcp.v1"
    assert payload["tool_count"] == len(records_for_scope("project"))
    assert any(
        tool["name"] == "mekong_cook_auto_parallel" for tool in payload["tools"]
    )


def test_command_fabric_runtime_catalog_only_command_does_not_recurse() -> None:
    result = invoke_command_fabric("cook-auto-parallel", scope="project")

    assert result.exit_code == 0
    assert result.mode == "catalog-only"
    assert "cook-auto-parallel" in result.stdout


def test_command_fabric_runtime_can_invoke_native_command() -> None:
    result = invoke_command_fabric("tasks", args="--help", scope="project")

    assert result.exit_code == 0
    assert result.mode == "executed"


def test_command_fabric_manifest_returns_valid_mcp_schema() -> None:
    payload = command_fabric_manifest(adapter="mcp", scope="project")

    assert payload["schema"] == "mekong.command_fabric.adapter.mcp.v1"
    assert payload["tool_count"] >= 1
    assert len(payload["tools"]) == payload["tool_count"]
