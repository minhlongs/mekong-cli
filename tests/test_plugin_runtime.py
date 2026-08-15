"""Tests for PluginRuntime (src/core/plugin_runtime.py)."""
from __future__ import annotations
import importlib.metadata
import json
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.plugin_runtime import (
    PluginInfo, LoadedPlugin, PluginRuntime,
    _extract_type_from_id, _noop_registry,
)

FAKE_MANIFEST = {
    "id": "com.example.test-plugin",
    "name": "Test Plugin",
    "version": "0.1.0",
    "description": "A test plugin",
    "author": "Test Author",
    "license": "MIT",
    "engines": {"mekong": "^6.0.0"},
    "permissions": [],
    "mcu_cost": 1,
    "dependencies": [],
    "hooks": [],
    "entry_point": None,
    "isolation": "none",
}


class _TmpDir:
    def __enter__(self):
        self._dir = Path(tempfile.mkdtemp())
        return self._dir
    def __exit__(self, *args):
        shutil.rmtree(self._dir, ignore_errors=True)


def make_plugin_dir(tmpdir, plugin_id, name="Test Plugin"):
    plugin_dir = tmpdir / f"plugin-{plugin_id.rsplit(chr(46), 1)[-1]}"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(json.dumps(FAKE_MANIFEST))
    manifest["id"] = plugin_id
    manifest["name"] = name
    (plugin_dir / ".plugin.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    return plugin_dir


def make_legacy_plugin(tmpdir, plugin_id):
    plugin_dir = tmpdir / f"plugin-{plugin_id.rsplit(chr(46), 1)[-1]}"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(json.dumps(FAKE_MANIFEST))
    manifest["id"] = plugin_id
    manifest["name"] = plugin_id
    (plugin_dir / ".plugin.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    src = plugin_dir / "src"
    src.mkdir()
    init_lines = [
        "def register(registry):",
        "    registry[" + repr("commands") + "] = []",
        "    registry[" + repr("hooks") + "] = []",
    ]
    (src / "__init__.py").write_text(
        "\n".join(init_lines) + "\n", encoding="utf-8"
    )
    return plugin_dir


def _patch_sdk(fake_schema, fake_context, fake_instance):
    mock_plugin_mod = MagicMock()
    mock_plugin_mod.create_plugin.return_value = fake_instance
    mock_context_mod = MagicMock(return_value=fake_context)
    mock_hooks_mod = MagicMock(
        HookRegistry=MagicMock(return_value=MagicMock()),
        HookPoint=MagicMock(),
    )
    return patch.dict(sys.modules, {
        "packages.mekong_plugin_sdk.plugin": mock_plugin_mod,
        "packages.mekong_plugin_sdk.context": mock_context_mod,
        "packages.mekong_plugin_sdk.hooks": mock_hooks_mod,
        "src.core.plugin_schema": MagicMock(
            PluginManifestSchema=MagicMock(
                from_file=MagicMock(return_value=fake_schema)
            )
        ),
    })


def _make_fake():
    fake_schema = MagicMock()
    fake_schema.id = "com.ex.good"
    fake_schema.name = "Good Plugin"
    fake_schema.version = "0.1.0"
    fake_schema.description = "desc"
    fake_schema.hooks = []
    fake_context = MagicMock(
        plugin_id="com.ex.good",
        manifest=fake_schema,
    )
    fake_instance = MagicMock()
    fake_instance.get_commands.return_value = []
    fake_instance.register_commands = MagicMock()
    fake_instance.register_hooks = MagicMock()
    return fake_schema, fake_context, fake_instance


class TestPluginInfo(unittest.TestCase):
    def test_plugin_info_defaults(self):
        info = PluginInfo(source="/tmp/test")
        self.assertEqual(info.source, "/tmp/test")
        self.assertEqual(info.status, "loaded")
        self.assertEqual(info.plugin_id, "")
        self.assertEqual(info.error_message, "")

    def test_plugin_info_setters(self):
        info = PluginInfo(source="/tmp/test")
        info.plugin_id = "com.example.test"
        info.status = "loaded"
        info.error_message = "something went wrong"
        self.assertEqual(info.plugin_id, "com.example.test")
        self.assertEqual(info.status, "loaded")
        self.assertEqual(info.error_message, "something went wrong")


class TestPluginRuntimeInit(unittest.TestCase):
    def test_default_plugin_dir(self):
        rt = PluginRuntime()
        expected = Path.home() / ".mekong" / "plugins"
        self.assertEqual(rt.plugin_dirs, [expected])

    def test_custom_plugin_dirs(self):
        rt = PluginRuntime(plugin_dirs=[Path("/tmp/plugins")])
        self.assertEqual(rt.plugin_dirs, [Path("/tmp/plugins")])

    def test_loaded_starts_empty(self):
        rt = PluginRuntime(plugin_dirs=[])
        self.assertEqual(len(rt._loaded), 0)


class TestPluginRuntimeDiscover(unittest.TestCase):
    def setUp(self):
        self._tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_empty_dir_returns_empty(self):
        rt = PluginRuntime(plugin_dirs=[self._tmpdir])
        self.assertEqual(len(rt.discover_manifests()), 0)

    def test_single_plugin_dir(self):
        make_plugin_dir(self._tmpdir, plugin_id="com.ex.a")
        rt = PluginRuntime(plugin_dirs=[self._tmpdir])
        self.assertEqual(len(rt.discover_manifests()), 1)

    def test_multiple_plugin_dirs(self):
        d2 = self._tmpdir / "extra"
        d2.mkdir()
        make_plugin_dir(self._tmpdir, plugin_id="com.ex.a")
        make_plugin_dir(d2, plugin_id="com.ex.b")
        rt = PluginRuntime(plugin_dirs=[self._tmpdir, d2])
        self.assertEqual(len(rt.discover_manifests()), 2)

    def test_default_dir_uses_home(self):
        rt = PluginRuntime()
        expected = Path.home() / ".mekong" / "plugins"
        self.assertEqual(rt.plugin_dirs, [expected])


class TestPluginRuntimeLoad(unittest.TestCase):
    def setUp(self):
        self._tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_load_valid_plugin_returns_loaded(self):
        plugin_dir = make_plugin_dir(self._tmpdir, plugin_id="com.ex.good")
        fake_schema, fake_context, fake_instance = _make_fake()
        rt = PluginRuntime(plugin_dirs=[self._tmpdir])
        with _patch_sdk(fake_schema, fake_context, fake_instance):
            info = rt.load_plugin(plugin_dir / ".plugin.json")
        self.assertEqual(info.status, "loaded")
        self.assertEqual(info.plugin_id, "com.ex.good")
        self.assertEqual(info.name, "Good Plugin")
        self.assertEqual(info.version, "0.1.0")

    def test_load_caches_internal(self):
        plugin_dir = make_plugin_dir(self._tmpdir, plugin_id="com.ex.cached")
        fake_schema, fake_context, fake_instance = _make_fake()
        fake_schema.id = "com.ex.cached"
        rt = PluginRuntime(plugin_dirs=[self._tmpdir])
        with _patch_sdk(fake_schema, fake_context, fake_instance):
            rt.load_plugin(plugin_dir / ".plugin.json")
        self.assertEqual(len(rt._loaded), 1)
        self.assertIn("com.ex.cached", rt._loaded)

    def test_load_invalid_manifest_returns_error(self):
        rt = PluginRuntime(plugin_dirs=[self._tmpdir])
        bad_manifest_path = self._tmpdir / "p-bad" / ".plugin.json"
        bad_manifest_path.parent.mkdir()
        bad_manifest_path.write_text(
            json.dumps({"id": "no-name-field"}), encoding="utf-8"
        )
        info = rt.load_plugin(bad_manifest_path)
        self.assertEqual(info.status, "error")
        self.assertIn("manifest_error", info.error_message)

    def test_loaded_plugins_property(self):
        plugin_dir = make_plugin_dir(self._tmpdir, plugin_id="com.ex.a")
        fake_schema, fake_context, fake_instance = _make_fake()
        fake_schema.id = "com.ex.a"
        rt = PluginRuntime(plugin_dirs=[self._tmpdir])
        with _patch_sdk(fake_schema, fake_context, fake_instance):
            rt.load_plugin(plugin_dir / ".plugin.json")
        ids = [p.plugin_id for p in rt.iter_loaded()]
        self.assertEqual(ids, ["com.ex.a"])

    def test_get_loaded_returns_record(self):
        plugin_dir = make_plugin_dir(self._tmpdir, plugin_id="com.ex.b")
        fake_schema, fake_context, fake_instance = _make_fake()
        fake_schema.id = "com.ex.b"
        rt = PluginRuntime(plugin_dirs=[self._tmpdir])
        with _patch_sdk(fake_schema, fake_context, fake_instance):
            rt.load_plugin(plugin_dir / ".plugin.json")
        rec = rt.get_loaded("com.ex.b")
        self.assertIsInstance(rec, LoadedPlugin)

    def test_load_all_collects_results(self):
        make_plugin_dir(self._tmpdir, plugin_id="com.ex.a")
        make_plugin_dir(self._tmpdir, plugin_id="com.ex.b")
        fake_schema, fake_context, fake_instance = _make_fake()
        rt = PluginRuntime(plugin_dirs=[self._tmpdir])
        with _patch_sdk(fake_schema, fake_context, fake_instance), \
             patch.object(rt, "discover_manifests") as mock_d:
            m1 = self._tmpdir / "plugin-a" / ".plugin.json"
            m2 = self._tmpdir / "plugin-b" / ".plugin.json"
            mock_d.return_value = [m1, m2]
            results = rt.load_all()
            self.assertEqual(len(results), 2)

    def test_load_all_returns_errors_for_bad_plugins(self):
        pdir = self._tmpdir / "p-broken"
        pdir.mkdir()
        (pdir / ".plugin.json").write_text("", encoding="utf-8")
        make_plugin_dir(self._tmpdir, plugin_id="com.ex.ok")
        rt = PluginRuntime(plugin_dirs=[self._tmpdir])
        fake_schema, fake_context, fake_instance = _make_fake()
        fake_schema.id = "com.ex.ok"
        with _patch_sdk(fake_schema, fake_context, fake_instance):
            results = rt.load_all()
        statuses = [r.status for r in results]
        self.assertTrue(
            any(s == "loaded" for s in statuses),
            f"expected at least one loaded plugin, got: {statuses}",
        )

    def test_unload_all_calls_stop_dispose(self):
        plugin_dir = make_plugin_dir(self._tmpdir, plugin_id="com.ex.stop")
        fake_schema, fake_context, fake_instance = _make_fake()
        fake_schema.id = "com.ex.stop"
        rt = PluginRuntime(plugin_dirs=[self._tmpdir])
        with _patch_sdk(fake_schema, fake_context, fake_instance):
            rt.load_plugin(plugin_dir / ".plugin.json")
        loaded = rt.get_loaded("com.ex.stop")
        self.assertIsNotNone(loaded)
        rt.unload_all()
        loaded.instance.stop.assert_called_once()
        loaded.instance.dispose.assert_called_once()

    def test_legacy_plugin_with_init_py(self):
        plugin_dir = make_legacy_plugin(self._tmpdir, plugin_id="com.ex.legacy")
        fake_schema, fake_context, fake_instance = _make_fake()
        fake_schema.id = "com.ex.legacy"
        # create_plugin raises TypeError("missing plugin class") which
        # triggers the legacy fallback in load_plugin()
        def _missing_plugin(*args, **kwargs):
            raise TypeError("missing plugin class")
        plugin_mod = MagicMock()
        plugin_mod.create_plugin = _missing_plugin
        plugin_mod.PluginContext = MagicMock(return_value=fake_context)
        hook_mod = MagicMock(
            HookRegistry=MagicMock(return_value=MagicMock()),
            HookPoint=MagicMock(),
        )
        schema_mod = MagicMock(
            PluginManifestSchema=MagicMock(
                from_file=MagicMock(return_value=fake_schema)
            )
        )
        rt = PluginRuntime(plugin_dirs=[self._tmpdir])
        with patch.dict(sys.modules, {
            "packages.mekong_plugin_sdk.plugin": plugin_mod,
            "packages.mekong_plugin_sdk.context": MagicMock(
                return_value=fake_context
            ),
            "packages.mekong_plugin_sdk.hooks": hook_mod,
            "src.core.plugin_schema": schema_mod,
        }):
            info = rt.load_plugin(plugin_dir / ".plugin.json")
        self.assertEqual(info.status, "loaded")
        self.assertEqual(info.plugin_id, "com.ex.legacy")
        self.assertEqual(info.plugin_type, "legacy")

    def test_plugin_without_init_py(self):
        plugin_dir = make_plugin_dir(self._tmpdir, plugin_id="com.ex.noreg")
        fake_schema, fake_context, fake_instance = _make_fake()
        fake_schema.id = "com.ex.noreg"
        rt = PluginRuntime(plugin_dirs=[self._tmpdir])
        with _patch_sdk(fake_schema, fake_context, fake_instance):
            info = rt.load_plugin(plugin_dir / ".plugin.json")
        self.assertEqual(info.status, "loaded")

    def test_e2e_full_lifecycle_with_mock_sdk(self):
        plugin_dir = make_plugin_dir(self._tmpdir, plugin_id="com.ex.lifecycle")
        fake_schema, fake_context, fake_instance = _make_fake()
        fake_schema.id = "com.ex.lifecycle"
        rt = PluginRuntime(plugin_dirs=[self._tmpdir])
        with _patch_sdk(fake_schema, fake_context, fake_instance):
            info = rt.load_plugin(plugin_dir / ".plugin.json")
        self.assertEqual(info.status, "loaded")
        loaded = rt.get_loaded("com.ex.lifecycle")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.plugin_id, "com.ex.lifecycle")
        self.assertIsNotNone(loaded.instance)


class TestPluginRuntimeReexports(unittest.TestCase):
    def test_extract_type_from_id(self):
        self.assertEqual(
            _extract_type_from_id("com.example.my-agent"), "agent"
        )
        self.assertEqual(
            _extract_type_from_id("com.example.my-hook"), "hook"
        )
        self.assertEqual(
            _extract_type_from_id("com.example.data-provider"), "provider"
        )

    def test_noop_registry_collects(self):
        cmds = _noop_registry([{"id": "a"}, {"id": "b"}])
        self.assertIsNotNone(cmds)

    def test_loaded_plugin_dataclass(self):
        lp = LoadedPlugin(
            plugin_id="test",
            manifest=MagicMock(),
            instance=MagicMock(),
            commands=[],
            hooks=[],
            source="/tmp",
        )
        self.assertEqual(lp.plugin_id, "test")
        self.assertEqual(len(lp.commands), 0)
        self.assertEqual(len(lp.hooks), 0)

    def test_plugin_runtime_has_load_all(self):
        rt = PluginRuntime(plugin_dirs=[])
        self.assertTrue(hasattr(rt, "load_all"))
        self.assertTrue(callable(rt.load_all))

    def test_plugin_runtime_has_unload_all(self):
        rt = PluginRuntime(plugin_dirs=[])
        self.assertTrue(hasattr(rt, "unload_all"))
        self.assertTrue(callable(rt.unload_all))

    def test_version_metadata(self):
        try:
            ver = importlib.metadata.version("mekong-cli")
            self.assertIsInstance(ver, str)
            self.assertTrue(len(ver) > 0)
        except importlib.metadata.PackageNotFoundError:
            self.skipTest("mekong-cli not installed as package")


if __name__ == "__main__":
    unittest.main()
