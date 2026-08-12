from scripts.command_fabric_release_gate import run_gate
from pathlib import Path

from src.command_fabric.target_matrix import (
    EXPECTED_NATIVE_INSTALL_HOST_COUNT,
    EXPECTED_PACKAGE_BUILD_CHECKS,
    EXPECTED_RELEASE_SECTION_COUNT,
)


def test_release_gate_validates_bundle_and_install_dry_run(tmp_path) -> None:
    payload = run_gate(tmp_path / "out", tmp_path / "home")

    assert payload["schema"] == "mekong.command_fabric.release_gate.v1"
    assert payload["bundle"]["command_count"] == 91
    assert payload["bundle"]["section_count"] == EXPECTED_RELEASE_SECTION_COUNT
    assert payload["package_build"]["check_count"] == EXPECTED_PACKAGE_BUILD_CHECKS
    assert payload["install"]["install_count"] == EXPECTED_NATIVE_INSTALL_HOST_COUNT
    assert payload["install"]["dry_run"] is True
    assert payload["readiness"]["ready"] is True
    assert payload["readiness"]["check_count"] == 23
    assert not (tmp_path / "home" / ".claude" / "commands" / "mekong").exists()


def test_release_gate_workflow_runs_all_command_fabric_tests() -> None:
    workflow = Path(".github/workflows/command-fabric-release-gate.yml").read_text(encoding="utf-8")

    expected_tests = [
        "tests/test_command_fabric_catalog.py",
        "tests/test_command_fabric_adapters.py",
        "tests/test_command_fabric_runtime.py",
        "tests/test_command_fabric_ide_extensions.py",
        "tests/test_command_fabric_shell_package.py",
        "tests/test_command_fabric_agent_cli_package.py",
        "tests/test_command_fabric_contracts.py",
        "tests/test_command_fabric_distribution.py",
        "tests/test_command_fabric_npm_package.py",
        "tests/test_command_fabric_mcp_package.py",
        "tests/test_command_fabric_workspace_templates.py",
        "tests/test_command_fabric_package_managers.py",
        "tests/test_command_fabric_visual_studio_package.py",
        "tests/test_command_fabric_eclipse_package.py",
        "tests/test_command_fabric_lightweight_editor_packages.py",
        "tests/test_command_fabric_vim_package.py",
        "tests/test_command_fabric_neovim_package.py",
        "tests/test_command_fabric_helix_package.py",
        "tests/test_command_fabric_zed_package.py",
        "tests/test_command_fabric_emacs_package.py",
        "tests/test_command_fabric_sublime_package.py",
        "tests/test_command_fabric_package_build.py",
        "tests/test_command_fabric_release_bundle.py",
        "tests/test_command_fabric_native_install.py",
        "tests/test_command_fabric_native_install_editors.py",
        "tests/test_command_fabric_release_gate.py",
        "tests/test_command_fabric_readiness.py",
    ]
    for test_path in expected_tests:
        assert test_path in workflow
