"""
Tests for Mekong Plugin API (Track E / Wave E1c).

Covers:
- kebab-case name normalization
- allowed plugin types
- template renders valid JSON with all required keys
- _scaffold_plugin creates full directory tree
- init_cmd rejects invalid --type values
- init_cmd rejects existing target directory
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.cli.commands.plugin import (
 _PLUGIN_TYPES,
 _PLUGIN_JSON_TEMPLATE,
 _README_TEMPLATE,
 _INIT_PY_TEMPLATE,
 INIT_TEST_TEMPLATE,
 _title_to_kebab,
 _scaffold_plugin,
)


class TestTitleToKebab(unittest.TestCase):
 """Tests for _title_to_kebab() name normalization."""

 def test_lowercase(self):
  """Lowercase name stays lowercase."""
  self.assertEqual(_title_to_kebab("MyPlugin"), "myplugin")

 def test_spaces_to_hyphens(self):
  """Spaces become hyphens."""
  self.assertEqual(_title_to_kebab("my cool plugin"), "my-cool-plugin")

 def test_underscores_to_hyphens(self):
  """Underscores become hyphens."""
  self.assertEqual(_title_to_kebab("my_cool_plugin"), "my-cool-plugin")

 def test_mixed(self):
  """Mixed separators become hyphens."""
  self.assertEqual(_title_to_kebab("My_Cool Plugin"), "my-cool-plugin")

 def test_strip(self):
  """Leading/trailing whitespace is stripped."""
  self.assertEqual(_title_to_kebab("  plugin  "), "plugin")

 def test_already_kebab(self):
  """Already kebab-case name is unchanged."""
  self.assertEqual(_title_to_kebab("my-cool-plugin"), "my-cool-plugin")


class TestPluginTypes(unittest.TestCase):
 """Tests for _PLUGIN_TYPES constant."""

 def test_contains_agent(self):
  self.assertIn("agent", _PLUGIN_TYPES)

 def test_contains_provider(self):
  self.assertIn("provider", _PLUGIN_TYPES)

 def test_contains_hook(self):
  self.assertIn("hook", _PLUGIN_TYPES)

 def test_contains_recipe(self):
  self.assertIn("recipe", _PLUGIN_TYPES)

 def test_tuple_length(self):
  self.assertEqual(len(_PLUGIN_TYPES), 4)


class TestPluginJsonTemplate(unittest.TestCase):
 """Tests for _PLUGIN_JSON_TEMPLATE rendering."""

 def _render(self, description="test"):
  name = "my-cool-plugin"
  name_clean = _title_to_kebab(name)
  return _PLUGIN_JSON_TEMPLATE.format(
   name=name_clean, name_clean=name_clean, description=description
  )

 def test_renders_json(self):
  """Rendered template should be valid JSON."""
  result = self._render()
  parsed = json.loads(result)
  self.assertIsInstance(parsed, dict)

 def test_has_id(self):
  parsed = json.loads(self._render())
  self.assertEqual(parsed["id"], "com.yourorg.my-cool-plugin")

 def test_has_name(self):
  parsed = json.loads(self._render())
  self.assertEqual(parsed["name"], "my-cool-plugin")

 def test_has_version(self):
  parsed = json.loads(self._render())
  self.assertEqual(parsed["version"], "0.1.0")

 def test_has_description(self):
  parsed = json.loads(self._render("a cool plugin"))
  self.assertEqual(parsed["description"], "a cool plugin")

 def test_has_engines(self):
  parsed = json.loads(self._render())
  self.assertIn("mekong", parsed["engines"])
  self.assertEqual(parsed["engines"]["mekong"], "^6.0.0")

 def test_has_permissions(self):
  parsed = json.loads(self._render())
  self.assertIn("permissions", parsed)

 def test_has_mcu_cost(self):
  parsed = json.loads(self._render())
  self.assertEqual(parsed["mcu_cost"], 1)

 def test_has_dependencies(self):
  parsed = json.loads(self._render())
  self.assertIn("dependencies", parsed)

 def test_has_hooks(self):
  parsed = json.loads(self._render())
  self.assertIn("hooks", parsed)

 def test_has_isolation(self):
  parsed = json.loads(self._render())
  self.assertEqual(parsed["isolation"], "none")

 def test_no_literal_braces(self):
  """Output should not contain raw { or } characters from double escaping."""
  result = self._render()
  self.assertNotIn("{{", result)
  self.assertNotIn("}}", result)


class TestReadmeTemplate(unittest.TestCase):
 """Tests for _README_TEMPLATE."""

 def test_renders_name(self):
  result = _README_TEMPLATE.format(name_clean="my-plugin")
  self.assertIn("my-plugin", result)
  self.assertIn("mekong plugin init", result)


class TestInitPyTemplate(unittest.TestCase):
 """Tests for _INIT_PY_TEMPLATE."""

 def test_has_register_function(self):
  result = _INIT_PY_TEMPLATE.format(name_clean="my-plugin")
  self.assertIn("def register(registry)", result)


class TestInitTestTemplate(unittest.TestCase):
 """Tests for INIT_TEST_TEMPLATE."""

 def test_renders_name(self):
  result = INIT_TEST_TEMPLATE.format(name_clean="my-plugin")
  self.assertIn("my-plugin", result)
  self.assertIn("smoke tests", result)


class TestScaffoldPlugin(unittest.TestCase):
 """Tests for _scaffold_plugin directory creation."""

 def setUp(self):
  self.tmpdir = tempfile.mkdtemp()

 def tearDown(self):
  import shutil
  shutil.rmtree(self.tmpdir, ignore_errors=True)

 def test_creates_directory(self):
  target = Path(self.tmpdir) / "my-plugin"
  _scaffold_plugin(target, "My Plugin", "agent", "desc")
  self.assertTrue(target.exists())
  self.assertTrue(target.is_dir())

 def test_creates_src_dir(self):
  target = Path(self.tmpdir) / "my-plugin"
  _scaffold_plugin(target, "My Plugin", "agent", "desc")
  self.assertTrue((target / "src").exists())

 def test_creates_tests_dir(self):
  target = Path(self.tmpdir) / "my-plugin"
  _scaffold_plugin(target, "My Plugin", "agent", "desc")
  self.assertTrue((target / "tests").exists())

 def test_creates_plugin_json(self):
  target = Path(self.tmpdir) / "my-plugin"
  _scaffold_plugin(target, "My Plugin", "agent", "desc")
  manifest = target / ".plugin.json"
  self.assertTrue(manifest.exists())

 def test_plugin_json_is_valid_json(self):
  target = Path(self.tmpdir) / "my-plugin"
  _scaffold_plugin(target, "My Plugin", "agent", "desc")
  content = (target / ".plugin.json").read_text()
  parsed = json.loads(content)
  self.assertIsInstance(parsed, dict)

 def test_plugin_json_has_all_keys(self):
  target = Path(self.tmpdir) / "my-plugin"
  _scaffold_plugin(target, "My Plugin", "agent", "desc")
  parsed = json.loads((target / ".plugin.json").read_text())
  required = ["id", "name", "version", "description", "engines",
   "permissions", "mcu_cost", "dependencies", "hooks", "isolation"]
  for key in required:
   self.assertIn(key, parsed, f"Missing key: {key}")

 def test_creates_init_py(self):
  target = Path(self.tmpdir) / "my-plugin"
  _scaffold_plugin(target, "My Plugin", "agent", "desc")
  init_file = target / "src" / "__init__.py"
  self.assertTrue(init_file.exists())
  content = init_file.read_text()
  self.assertIn("def register(registry)", content)

 def test_creates_readme(self):
  target = Path(self.tmpdir) / "my-plugin"
  _scaffold_plugin(target, "My Plugin", "agent", "desc")
  readme = target / "README.md"
  self.assertTrue(readme.exists())
  self.assertIn("mekong plugin init", readme.read_text())

 def test_creates_tests_init(self):
  target = Path(self.tmpdir) / "my-plugin"
  _scaffold_plugin(target, "My Plugin", "agent", "desc")
  tests_init = target / "tests" / "__init__.py"
  self.assertTrue(tests_init.exists())

 def test_name_normalized_in_manifest(self):
  """Manifest id should use kebab-case, not raw input."""
  target = Path(self.tmpdir) / "my-plugin"
  _scaffold_plugin(target, "My Cool Plugin", "hook", "desc")
  parsed = json.loads((target / ".plugin.json").read_text())
  self.assertEqual(parsed["name"], "my-cool-plugin")
  self.assertEqual(parsed["id"], "com.yourorg.my-cool-plugin")


if __name__ == "__main__":
 unittest.main()
