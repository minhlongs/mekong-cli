import json


from src.command_fabric.package_build import verify_package_builds
from src.command_fabric.release_bundle import materialize_release_bundle
from src.command_fabric.target_matrix import EXPECTED_PACKAGE_BUILD_CHECKS, PACKAGE_BUILD_TARGETS


def test_package_build_verifier_checks_generated_ide_scaffolds(tmp_path) -> None:
    materialize_release_bundle(tmp_path, scope="project")
    payload = verify_package_builds(tmp_path)

    assert payload["schema"] == "mekong.command_fabric.package_build.v1"
    assert payload["check_count"] == EXPECTED_PACKAGE_BUILD_CHECKS
    hosts = {check["host"] for check in payload["checks"]}
    assert hosts == set(PACKAGE_BUILD_TARGETS)


def test_package_build_cli_verifies_bundle(tmp_path) -> None:
    materialize_release_bundle(tmp_path, scope="project")
    result = CliRunner().invoke(
        build_app(),
        ["command-fabric", "package-build-check", "--bundle", str(tmp_path)],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["check_count"] == EXPECTED_PACKAGE_BUILD_CHECKS
