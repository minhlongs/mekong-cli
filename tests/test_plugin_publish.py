"""Tests for PluginPublisher — E4b marketplace publish flow.

TDD: these tests define the contract. They will all fail (ImportError)
until src/core/plugin_publisher.py is implemented in Phase 2.
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ---------------------------------------------------------------------------
# SDK mock mirrors (same pattern as test_hook_activation + test_hookpoint_routing)
# ---------------------------------------------------------------------------

from enum import Enum
from dataclasses import dataclass


class HookPoint(str, Enum):
    BEFORE_CLI_START = "before_cli_start"
    AFTER_CLI_START = "after_cli_start"
    BEFORE_COMMAND = "before_command"
    AFTER_COMMAND = "after_command"
    BEFORE_PLAN = "before_plan"
    AFTER_PLAN = "after_plan"
    BEFORE_EXECUTE = "before_execute"
    AFTER_EXECUTE = "after_execute"
    BEFORE_VERIFY = "before_verify"
    AFTER_VERIFY = "after_verify"
    ON_SHUTDOWN = "on_shutdown"


@dataclass
class HookContext:
    plugin_id: str
    command_name: str | None = None
    data: dict | None = None


@dataclass
class Hook:
    point: HookPoint
    handler: any
    priority: int = 50


class HookRegistry:
    def __init__(self) -> None:
        self._hooks: dict[str, list[Hook]] = {}

    def initialize(self, plugin_id: str) -> None:
        self._plugin_id = plugin_id

    def register(self, point, handler, priority=50) -> None:
        key = point.value if hasattr(point, "value") else str(point)
        self._hooks.setdefault(key, []).append(Hook(point=point, handler=handler, priority=priority))

    def get_hooks(self, point) -> list[Hook]:
        key = point.value if hasattr(point, "value") else str(point)
        return sorted(self._hooks.get(key, []), key=lambda h: h.priority)

    def execute(self, point, context) -> None:
        for hook in self.get_hooks(point):
            hook.handler(context)

    def clear(self) -> None:
        self._hooks = {}


import types as _types  # noqa: E402

_sdk_hooks_mod = _types.ModuleType("packages.mekong_plugin_sdk.hooks")
_sdk_hooks_mod.HookPoint = HookPoint
_sdk_hooks_mod.HookContext = HookContext
_sdk_hooks_mod.Hook = Hook
_sdk_hooks_mod.HookRegistry = HookRegistry

_sdk_pkg = _types.ModuleType("packages.mekong_plugin_sdk")
_sdk_pkg.hooks = _sdk_hooks_mod

# Provide plugin submodule so test_plugin_binding mock detection does not skip
_plugin_mod = _types.ModuleType("packages.mekong_plugin_sdk.plugin")
_plugin_mod.create_plugin = None  # placeholder
_sdk_pkg.plugin = _plugin_mod

sys.modules.setdefault("packages", _types.ModuleType("packages"))
sys.modules["packages.mekong_plugin_sdk"] = _sdk_pkg
sys.modules["packages.mekong_plugin_sdk.hooks"] = _sdk_hooks_mod

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_MANIFEST = {
    "id": "com.test.publisher",
    "name": "Test Publisher",
    "version": "1.0.0",
    "description": "Test plugin for publish flow",
    "author": "Test Author",
    "license": "MIT",
    "engines": {"mekong": "^6.0.0"},
    "permissions": [],
    "mcu_cost": 1,
    "dependencies": [],
    "hooks": [],
    "isolation": "none",
}


def _scaffold_plugin(tmp_path: Path, name: str = "test-plugin", extra_files: list | None = None) -> Path:
    """Create a minimal valid plugin directory structure."""
    plugin_dir = tmp_path / name
    plugin_dir.mkdir()

    # .plugin.json
    manifest = dict(VALID_MANIFEST)
    manifest["id"] = f"com.test.{name.replace('-', '')}"
    manifest["name"] = name
    (plugin_dir / ".plugin.json").write_text(json.dumps(manifest), encoding="utf-8")

    # src/__init__.py
    src = plugin_dir / "src"
    src.mkdir()
    (src / "__init__.py").write_text('def register(registry): pass\n', encoding="utf-8")

    # README.md
    (plugin_dir / "README.md").write_text(f"# {name}\n", encoding="utf-8")

    # extra files (for secret scan testing, etc.)
    if extra_files:
        for rel_path, content in extra_files:
            f = plugin_dir / rel_path
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(content, encoding="utf-8")

    return plugin_dir


# ---------------------------------------------------------------------------
# Tests — all fail with ImportError until Phase 2 implements the module
# ---------------------------------------------------------------------------


class TestPluginPublisherInit:

    def test_publisher_init_with_valid_plugin_dir(self, tmp_path: Path) -> None:
        """PluginPublisher initializes with a valid plugin directory."""
        plugin_dir = _scaffold_plugin(tmp_path)
        # No assertion — import fails before we get here
        from src.core.plugin_publisher import PluginPublisher
        pub = PluginPublisher(plugin_dir)
        assert pub.plugin_dir == plugin_dir

    def test_publisher_init_with_missing_plugin_json(self, tmp_path: Path) -> None:
        """PluginPublisher raises PublishError when .plugin.json is missing."""
        bad_dir = tmp_path / "no-manifest"
        bad_dir.mkdir()
        from src.core.plugin_publisher import PluginPublisher, PublishError
        with pytest.raises(PublishError, match="[.p]lugin.json"):
            PluginPublisher(bad_dir)


class TestPluginPublisherBundle:

    def test_bundle_contains_required_files(self, tmp_path: Path) -> None:
        """ZIP contains .plugin.json, src/, README.md."""
        from src.core.plugin_publisher import PluginPublisher
        plugin_dir = _scaffold_plugin(tmp_path)
        pub = PluginPublisher(plugin_dir)
        zip_path = pub.bundle(output_dir=tmp_path / "out")
        assert zip_path.exists()
        with zipfile.ZipFile(zip_path) as zf:
            names = set(zf.namelist())
        assert "test-plugin/.plugin.json" in names
        assert "test-plugin/src/__init__.py" in names
        assert "test-plugin/README.md" in names

    def test_bundle_excludes_hidden_dirs(self, tmp_path: Path) -> None:
        """ZIP excludes .git/ and __pycache__/."""
        from src.core.plugin_publisher import PluginPublisher
        plugin_dir = _scaffold_plugin(
            tmp_path,
            extra_files=[
                (".git/config", "[core]\n"),
                ("src/__pycache__/foo.pyc", "bytecode"),
            ],
        )
        pub = PluginPublisher(plugin_dir)
        zip_path = pub.bundle(output_dir=tmp_path / "out")
        with zipfile.ZipFile(zip_path) as zf:
            names = set(zf.namelist())
        assert not any(n.startswith(".git/") for n in names)
        assert not any("__pycache__" in n for n in names)

    def test_bundle_excludes_venv_and_node_modules(self, tmp_path: Path) -> None:
        """ZIP excludes .venv/ and node_modules/."""
        from src.core.plugin_publisher import PluginPublisher
        plugin_dir = _scaffold_plugin(
            tmp_path,
            extra_files=[
                (".venv/lib/python/site.py", "# venv"),
                ("node_modules/foo/index.js", "// npm"),
            ],
        )
        pub = PluginPublisher(plugin_dir)
        zip_path = pub.bundle(output_dir=tmp_path / "out")
        with zipfile.ZipFile(zip_path) as zf:
            names = set(zf.namelist())
        assert not any(n.startswith(".venv/") for n in names)
        assert not any(n.startswith("node_modules/") for n in names)

    def test_bundle_preserves_directory_structure(self, tmp_path: Path) -> None:
        """ZIP internal paths match source tree structure."""
        from src.core.plugin_publisher import PluginPublisher
        plugin_dir = _scaffold_plugin(
            tmp_path,
            extra_files=[
                ("src/utils/helper.py", "# helper"),
                ("tests/test_basic.py", "def test(): pass"),
            ],
        )
        pub = PluginPublisher(plugin_dir)
        zip_path = pub.bundle(output_dir=tmp_path / "out")
        with zipfile.ZipFile(zip_path) as zf:
            names = sorted(zf.namelist())
        assert "test-plugin/src/__init__.py" in names
        assert "test-plugin/src/utils/helper.py" in names
        assert "test-plugin/tests/test_basic.py" in names


class TestPluginPublisherSecretScan:

    def test_secret_scan_blocks_openai_key(self, tmp_path: Path) -> None:
        """Publish raises PublishError when sk- key found in source."""
        from src.core.plugin_publisher import PluginPublisher, PublishError
        plugin_dir = _scaffold_plugin(
            tmp_path,
            extra_files=[("src/client.py", 'api_key = "sk-abc123xyz789"\n')],
        )
        pub = PluginPublisher(plugin_dir)
        with pytest.raises(PublishError, match="[Ss]ecret"):
            pub.bundle(output_dir=tmp_path / "out")

    def test_secret_scan_blocks_api_key_var(self, tmp_path: Path) -> None:
        """Publish raises PublishError when api_key assignment found."""
        from src.core.plugin_publisher import PluginPublisher, PublishError
        plugin_dir = _scaffold_plugin(
            tmp_path,
            extra_files=[("src/config.py", 'api_key = "real-key-here"\n')],
        )
        pub = PluginPublisher(plugin_dir)
        with pytest.raises(PublishError, match="[Ss]ecret"):
            pub.bundle(output_dir=tmp_path / "out")

    def test_secret_scan_blocks_token_var(self, tmp_path: Path) -> None:
        """Publish raises PublishError when token assignment found."""
        from src.core.plugin_publisher import PluginPublisher, PublishError
        plugin_dir = _scaffold_plugin(
            tmp_path,
            extra_files=[("src/auth.py", 'token = "ghp_real_token_12345"\n')],
        )
        pub = PluginPublisher(plugin_dir)
        with pytest.raises(PublishError, match="[Ss]ecret"):
            pub.bundle(output_dir=tmp_path / "out")

    def test_secret_scan_allows_placeholder_keys(self, tmp_path: Path) -> None:
        """Publish succeeds when keys contain placeholder patterns."""
        from src.core.plugin_publisher import PluginPublisher
        plugin_dir = _scaffold_plugin(
            tmp_path,
            extra_files=[
                ("src/client.py", 'api_key = "sk-YOUR_KEY_HERE"\n'),
                ("src/auth.py", 'token = "YOUR_TOKEN_HERE"\n'),
            ],
        )
        pub = PluginPublisher(plugin_dir)
        zip_path = pub.bundle(output_dir=tmp_path / "out")
        assert zip_path.exists()


class TestPluginPublisherVersionBump:

    def test_version_override_sets_manifest_version(self, tmp_path: Path) -> None:
        """--version X.Y.Z updates the manifest version inside the ZIP."""
        from src.core.plugin_publisher import PluginPublisher
        plugin_dir = _scaffold_plugin(tmp_path)
        pub = PluginPublisher(plugin_dir)
        zip_path = pub.bundle(output_dir=tmp_path / "out", version="2.0.0")
        with zipfile.ZipFile(zip_path) as zf:
            manifest_raw = zf.read("test-plugin/.plugin.json").decode()
        manifest = json.loads(manifest_raw)
        assert manifest["version"] == "2.0.0"

    def test_auto_patch_bumps_patch(self, tmp_path: Path) -> None:
        """Auto version bumps patch: 1.2.3 -> 1.2.4."""
        from src.core.plugin_publisher import PluginPublisher
        plugin_dir = _scaffold_plugin(tmp_path)
        # Override manifest version first
        manifest_path = plugin_dir / ".plugin.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["version"] = "1.2.3"
        manifest_path.write_text(json.dumps(manifest))
        pub = PluginPublisher(plugin_dir)
        zip_path = pub.bundle(output_dir=tmp_path / "out", version="auto")
        with zipfile.ZipFile(zip_path) as zf:
            manifest_raw = zf.read("test-plugin/.plugin.json").decode()
        manifest = json.loads(manifest_raw)
        assert manifest["version"] == "1.2.4"

    def test_version_override_requires_semver(self, tmp_path: Path) -> None:
        """Invalid semver version raises PublishError."""
        from src.core.plugin_publisher import PluginPublisher, PublishError
        plugin_dir = _scaffold_plugin(tmp_path)
        pub = PluginPublisher(plugin_dir)
        with pytest.raises(PublishError, match="[Vv]ersion"):
            pub.bundle(output_dir=tmp_path / "out", version="not-semver")


class TestPluginPublisherPublishFlow:

    def test_publish_creates_zip_in_output_dir(self, tmp_path: Path) -> None:
        """ZIP file is created at expected path after bundle."""
        from src.core.plugin_publisher import PluginPublisher
        plugin_dir = _scaffold_plugin(tmp_path)
        pub = PluginPublisher(plugin_dir)
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        zip_path = pub.bundle(output_dir=out_dir)
        assert zip_path.is_file()
        assert zip_path.suffix == ".zip"

    def test_publish_failure_no_partial_state(self, tmp_path: Path) -> None:
        """Failed publish leaves no ZIP behind."""
        from src.core.plugin_publisher import PluginPublisher, PublishError
        plugin_dir = _scaffold_plugin(tmp_path)
        # Inject a real secret to trigger failure
        (plugin_dir / "src" / "client.py").write_text(
            'api_key = "sk-real-key-12345"\n'
        )
        pub = PluginPublisher(plugin_dir)
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        with pytest.raises(PublishError):
            pub.bundle(output_dir=out_dir)
        # No ZIP should exist
        assert not any(out_dir.iterdir()), "Partial ZIP should not be created"

    def test_publish_with_none_router_skips_marketplace(self, tmp_path: Path) -> None:
        """Publish does not crash when marketplace config is absent."""
        from src.core.plugin_publisher import PluginPublisher
        plugin_dir = _scaffold_plugin(tmp_path)
        pub = PluginPublisher(plugin_dir)
        zip_path = pub.bundle(output_dir=tmp_path / "out")
        assert zip_path.exists()  # local publish succeeds without marketplace
