"""Tests for plugin install command — E2b install enhancement."""
from __future__ import annotations
import json
import shutil
import subprocess
import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.plugin_runtime import PluginRuntime

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TMPDIRS: list[Path] = [] # track so cleanup doesn't race tests


def _make_plugin_dir(tmpdir: Path, plugin_id: str) -> Path:
    pdir = tmpdir / f"plugin-{plugin_id.rsplit('.', 1)[-1]}"
    pdir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "id": plugin_id,
        "name": "Test",
        "version": "0.1.0",
        "description": "test",
        "license": "MIT",
        "engines": {"mekong": "^6.0.0"},
        "permissions": [],
        "mcu_cost": 1,
        "dependencies": [],
        "hooks": [],
        "entry_point": None,
        "isolation": "none",
    }
    (pdir / ".plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
    src = pdir / "src"
    src.mkdir()
    (src / "__init__.py").write_text("def register(registry): pass\n", encoding="utf-8")
    return pdir


def _cleanup():
    for d in _TMPDIRS:
        shutil.rmtree(d, ignore_errors=True)
    _TMPDIRS.clear()


# ---------------------------------------------------------------------------
# TDD: tests for install command
# ---------------------------------------------------------------------------

class TestInstallLocalPath:
    def test_install_local_dir_success(self):
        tmp = Path(tempfile.mkdtemp())
        _TMPDIRS.append(tmp)
        plugin_dir = _make_plugin_dir(tmp, "com.ex.install")
        runtime = PluginRuntime(plugin_dirs=[tmp / "plugins"])

        result = runtime.install(plugin_dir, name="test-install")
        assert result["status"] == "installed"
        assert result["plugin_id"] == "com.ex.install"
        assert (tmp / "plugins" / "test-install" / ".plugin.json").exists()

    def test_install_preserves_name(self):
        tmp = Path(tempfile.mkdtemp())
        _TMPDIRS.append(tmp)
        plugin_dir = _make_plugin_dir(tmp, "com.ex.name")
        runtime = PluginRuntime(plugin_dirs=[tmp / "plugins"])

        result = runtime.install(plugin_dir, name="my-custom-name")
        assert result["install_name"] == "my-custom-name"
        assert (tmp / "plugins" / "my-custom-name").is_dir()

    def test_install_nonexistent_dir_returns_error(self):
        tmp = Path(tempfile.mkdtemp())
        _TMPDIRS.append(tmp)
        runtime = PluginRuntime(plugin_dirs=[tmp / "plugins"])

        result = runtime.install(tmp / "does-not-exist")
        assert result["status"] == "error"
        assert len(result["error_message"]) > 0

    def test_install_dir_without_manifest_returns_error(self):
        tmp = Path(tempfile.mkdtemp())
        _TMPDIRS.append(tmp)
        bad = tmp / "bad-plugin"
        bad.mkdir()
        runtime = PluginRuntime(plugin_dirs=[tmp / "plugins"])

        result = runtime.install(bad)
        assert result["status"] == "error"
        assert ".plugin.json" in result["error_message"].lower()

    def test_install_overwrite_blocks_without_force(self):
        tmp = Path(tempfile.mkdtemp())
        _TMPDIRS.append(tmp)
        plugin_dir = _make_plugin_dir(tmp, "com.ex.block")
        runtime = PluginRuntime(plugin_dirs=[tmp / "plugins"])
        (tmp / "plugins" / "block").mkdir(parents=True) # pre-existing

        result = runtime.install(plugin_dir, name="block", force=False)
        assert result["status"] == "error"
        assert "already exists" in result["error_message"].lower()

    def test_install_overwrite_with_force(self):
        tmp = Path(tempfile.mkdtemp())
        _TMPDIRS.append(tmp)
        plugin_dir = _make_plugin_dir(tmp, "com.ex.force")
        runtime = PluginRuntime(plugin_dirs=[tmp / "plugins"])
        (tmp / "plugins" / "force").mkdir(parents=True)

        result = runtime.install(plugin_dir, name="force", force=True)
        assert result["status"] == "installed"
        assert (tmp / "plugins" / "force" / ".plugin.json").exists()

    def test_install_validates_manifest_after_copy(self):
        tmp = Path(tempfile.mkdtemp())
        _TMPDIRS.append(tmp)
        # write a BAD manifest (no id field)
        bad_plugin = tmp / "bad-id-plugin"
        bad_plugin.mkdir()
        (bad_plugin / ".plugin.json").write_text('{"name":"x"}', encoding="utf-8")
        runtime = PluginRuntime(plugin_dirs=[tmp / "plugins"])

        result = runtime.install(bad_plugin)
        assert result["status"] == "error"
        assert ".plugin.json" in result["error_message"].lower()


class TestInstallSourceDetection:
    def test_detect_local_path(self):
        tmp = Path(tempfile.mkdtemp())
        _TMPDIRS.append(tmp)
        local = _make_plugin_dir(tmp, "com.ex.local")
        runtime = PluginRuntime(plugin_dirs=[tmp / "plugins"])

        result = runtime.install(local)
        assert result["status"] == "installed"
        assert result["source_type"] == "local"

    def test_detect_git_url(self):
        """Git URLs should be detected and return 'git' source_type."""
        runtime = PluginRuntime(plugin_dirs=[])
        result = runtime.install(
            "https://github.com/example/plugin-repo.git",
        )
        assert result["source_type"] == "git"
        # Should not raise — returns info dict
        assert "status" in result

    def test_detect_zip_url(self):
        """ZIP URLs should be detected and return 'zip' source_type."""
        runtime = PluginRuntime(plugin_dirs=[])
        result = runtime.install(
            "https://github.com/example/plugin/archive/refs/heads/main.zip",
        )
        assert result["source_type"] == "zip"
        assert "status" in result

    def test_detect_pypi_package(self):
        """PyPI package names detected via 'mekong-plugin-' prefix."""
        runtime = PluginRuntime(plugin_dirs=[])
        result = runtime.install("mekong-plugin-example")
        assert result["source_type"] == "pypi"
        # Will fail to find (not real pkg), but should return status
        assert "status" in result


class TestInstallGitSource:
    def test_git_clone_installed(self):
        """Simulate git clone using a local bare-git proxy."""
        tmp = Path(tempfile.mkdtemp())
        _TMPDIRS.append(tmp)
        remote = tmp / "remote.git"
        remote.mkdir()
        subprocess.run(["git", "init", "--bare", str(remote)], check=True)

        work = tmp / "work"
        work.mkdir()
        # commit a plugin into the bare repo
        checkout = work / "checkout"
        checkout.mkdir()
        subprocess.run(["git", "clone", str(remote), str(checkout)], check=True)
        # Write plugin directly at checkout root so clone produces tmp/src/.plugin.json
        (checkout / ".plugin.json").write_text(
            json.dumps({
                "id": "com.ex.git",
                "name": "Git Plugin",
                "version": "0.1.0",
                "description": "git test",
                "license": "MIT",
                "engines": {"mekong": "^6.0.0"},
                "permissions": [],
                "mcu_cost": 1,
                "dependencies": [],
                "hooks": [],
                "isolation": "none",
            }),
            encoding="utf-8",
        )
        src_dir = checkout / "src"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text(
            "def register(registry): pass\n", encoding="utf-8"
        )
        subprocess.run(["git", "add", "."], cwd=checkout, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=checkout, check=True)
        subprocess.run(["git", "push", "origin", "master"], cwd=checkout, check=True)

        runtime = PluginRuntime(plugin_dirs=[tmp / "plugins"])

        result = runtime.install(f"git+{remote}")
        assert result["status"] == "installed"
        assert result["source_type"] == "git"
        assert (tmp / "plugins" / "git-plugin" / ".plugin.json").exists()


class TestInstallGitCredentials:
    """Git URL with HTTP credentials — ensure no leakage in error msgs."""

    def test_credentials_not_in_error(self):
        runtime = PluginRuntime(plugin_dirs=[])
        bad_url = "https://user:secret@github.com/example/private.git"
        result = runtime.install(bad_url)
        error_msg = result.get("error_message", "")
        assert "secret" not in error_msg
        assert "user:pass" not in error_msg
