import json

from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.command_fabric.catalog import build_command_catalog
from src.command_fabric.mcp_package import materialize_mcp_package, package_json


def test_mcp_package_metadata_exposes_bin() -> None:
    payload = package_json()

    assert payload["name"] == "@mekongcli/command-fabric-mcp"
    assert payload["bin"]["mekong-command-fabric-mcp"] == "./dist/server.js"


def test_mcp_package_materializes_stdio_server(tmp_path) -> None:
    payload = materialize_mcp_package(tmp_path, build_command_catalog())

    assert payload["schema"] == "mekong.command_fabric.mcp_package.v1"
    assert payload["command_count"] == 91
    assert (tmp_path / "src" / "server.ts").exists()
    assert (tmp_path / "data" / "mcp.json").exists()
    server = (tmp_path / "src" / "server.ts").read_text(encoding="utf-8")
    assert "tools/list" in server
    assert "tools/call" in server


def test_command_fabric_cli_materializes_mcp_package(tmp_path) -> None:
    result = CliRunner().invoke(
        build_app(),
        ["command-fabric", "mcp-package", "--scope", "project", "--out", str(tmp_path)],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["artifact_count"] == 6
    assert (tmp_path / "package.json").exists()
