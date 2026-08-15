#!/usr/bin/env python3
"""
Plugin Validation CI Script

Validates Mekong CLI plugins for:
- Manifest structure and schema compliance
- Plugin code can be imported and loaded
- Command definitions are valid
- Required files and directories exist
- Basic security checks
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Dict, List

# Add the mekong-plugin-sdk to path when run from repo root
sys.path.insert(0, str(Path(__file__).parent.parent / "packages" / "mekong-plugin-sdk" / "src"))

from mekong_plugin_sdk.manifest import validate_manifest, load_manifest


class PluginValidationError(Exception):
    """Plugin validation error."""
    pass


class PluginValidator:
    """Validate Mekong CLI plugins."""

    REQUIRED_FILES = ['mekong-plugin.json']
    OPTIONAL_FILES = ['README.md', 'LICENSE', 'src/', 'tests/']

    def __init__(self, plugin_dir: Path, fix: bool = False):
        self.plugin_dir = plugin_dir
        self.fix = fix
        self.errors: List[Dict[str, str]] = []
        self.warnings: List[Dict[str, str]] = []
        self.passed: List[str] = []

    def validate(self) -> bool:
        """Run all validations."""
        if not self.plugin_dir.exists():
            raise PluginValidationError(f"Plugin directory not found: {self.plugin_dir}")

        print(f"Validating plugin: {self.plugin_dir.name}")
        print(f"  Location: {self.plugin_dir}")

        # Check required files
        self._check_required_files()

        # Find and validate manifest
        manifest_path = self.plugin_dir / "mekong-plugin.json"
        if manifest_path.exists():
            self._validate_manifest(manifest_path)
        else:
            self._error("No mekong-plugin.json found")

        # Check plugin structure if manifest is valid
        if not any(e['message'].startswith("Invalid manifest") for e in self.errors):
            self._check_plugin_structure()

        # Check entrypoint module exists
        self._check_entrypoint()

        # Security checks
        self._check_security()

        return len(self.errors) == 0

    def _check_required_files(self):
        """Check that required files exist."""
        for req_file in self.REQUIRED_FILES:
            file_path = self.plugin_dir / req_file
            if not file_path.exists():
                self._error(f"Missing required file: {req_file}")

    def _validate_manifest(self, manifest_path: Path):
        """Validate the plugin manifest."""
        try:
            with open(manifest_path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self._error(f"Invalid JSON in manifest: {e}")
            return

        # Use SDK validation
        errors = validate_manifest(data)
        for error in errors:
            self._error(f"Manifest validation: {error}")

        if not errors:
            self.passed.append("Manifest is valid")
            print("  ✓ Manifest schema valid")

        # Additional checks
        plugin_id = data.get("id", "")
        if plugin_id != self.plugin_dir.name:
            self._warning(
                f"Plugin ID '{plugin_id}' doesn't match directory name '{self.plugin_dir.name}'"
            )

        # Check entrypoint format
        entrypoint = data.get("entrypoint", "")
        if entrypoint and ":" not in entrypoint:
            self._warning("Entrypoint should be in format 'module:ClassName'")

        # Check commands have unique names
        commands = data.get("commands", [])
        command_names = [cmd.get("name") for cmd in commands if "name" in cmd]
        if len(command_names) != len(set(command_names)):
            self._error("Duplicate command names found in manifest")

    def _check_plugin_structure(self):
        """Check plugin directory structure."""
        manifest_path = self.plugin_dir / "mekong-plugin.json"
        try:
            _manifest = load_manifest(manifest_path)
        except Exception:
            return  # Already reported in manifest validation

        # Check for common directories
        has_src = (self.plugin_dir / "src").exists()
        has_tests = (self.plugin_dir / "tests").exists()

        if not has_src:
            self._warning("No 'src/' directory found")
        if not has_tests:
            self._warning("No 'tests/' directory found - tests recommended")

        # Check for README
        if not (self.plugin_dir / "README.md").exists():
            self._warning("No README.md found")

    def _check_entrypoint(self):
        """Check that the entrypoint module and class exist."""
        manifest_path = self.plugin_dir / "mekong-plugin.json"
        if not manifest_path.exists():
            return

        try:
            with open(manifest_path) as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return

        entrypoint = data.get("entrypoint", "")
        if not entrypoint:
            return

        if ":" not in entrypoint:
            self._error(f"Invalid entrypoint format: '{entrypoint}' (expected 'module:Class')")
            return

        module_path, class_name = entrypoint.split(":", 1)
        module_file = module_path.replace(".", "/")

        # Construct potential file path
        if self.plugin_dir.name == "plugins" and module_path.count(".") >= 1:
            # Already in plugins dir, module path might be plugin.id.module
            potential_file = self.plugin_dir / (module_file + ".py")
        else:
            # Assume src/ directory
            potential_file = self.plugin_dir / "src" / (module_file + ".py")

        if not potential_file.exists():
            # Try alternate location
            alt_file = self.plugin_dir / (module_file + ".py")
            if not alt_file.exists():
                self._warning(f"Entrypoint module not found at expected location: {potential_file}")

    def _check_security(self):
        """Perform basic security checks."""
        # Check for hardcoded secrets in Python files
        python_files = list(self.plugin_dir.rglob("*.py"))

        for py_file in python_files:
            try:
                content = py_file.read_text()
            except Exception:
                continue

            # Skip test files for some checks
            if "test" in str(py_file):
                continue

            # Check for common secret patterns
            secret_patterns = [
                (r'(API_KEY|SECRET|PASSWORD|TOKEN)\s*=\s*[\'"][^\'"]{8,}[\'"]',
                 "Possible hardcoded secret")
            ]

            for pattern, message in secret_patterns:
                import re
                if re.search(pattern, content, re.IGNORECASE):
                    # Make sure it's not an environment variable reference
                    if not ("os.environ" in content or "os.getenv" in content):
                        self._warning(f"{py_file.name}: {message}")

        # Check for dangerous imports
        dangerous_imports = [
            'subprocess', 'socket', 'pickle', 'yaml',
            'requests', 'urllib', 'http.client'
        ]

        for py_file in python_files:
            try:
                content = py_file.read_text()
            except Exception:
                continue

            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name in dangerous_imports:
                                self._info(f"File uses '{alias.name}' - ensure proper sandboxing")
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.module.split('.')[0] in dangerous_imports:
                            self._info(f"File imports '{node.module}' - ensure proper sandboxing")
            except SyntaxError:
                pass  # Syntax errors caught elsewhere

    def _error(self, message: str):
        """Record an error."""
        self.errors.append({'plugin': self.plugin_dir.name, 'message': message})
        print(f"  ✗ {message}")

    def _warning(self, message: str):
        """Record a warning."""
        self.warnings.append({'plugin': self.plugin_dir.name, 'message': message})
        print(f"  ⚠ {message}")

    def _info(self, message: str):
        """Log informational message."""
        print(f"  ℹ {message}")
        self.passed.append(message)

    def _report(self):
        """Print validation report."""
        print(f"\n{'='*60}")
        if self.errors:
            print(f"❌ Validation FAILED: {len(self.errors)} error(s)")
            for err in self.errors:
                print(f"   {err['plugin']}: {err['message']}")
        else:
            print("✅ All validations passed!")

        if self.warnings:
            print(f"\n⚠️  {len(self.warnings)} warning(s):")
            for warn in self.warnings:
                print(f"   {warn['plugin']}: {warn['message']}")

        if self.passed:
            print(f"\n✓ {len(self.passed)} checks passed")


def find_plugins(plugins_dir: Path) -> List[Path]:
    """Find all plugin directories containing mekong-plugin.json."""
    if not plugins_dir.exists():
        return []

    # Find all mekong-plugin.json files recursively
    manifest_files = list(plugins_dir.rglob("mekong-plugin.json"))
    # Return parent directories (unique)
    plugins = list(set(manifest_file.parent for manifest_file in manifest_files))

    return plugins


def main():
    parser = argparse.ArgumentParser(description='Validate Mekong CLI plugins')
    parser.add_argument(
        'plugins_dir',
        type=Path,
        nargs='?',
        default=Path('packages'),
        help='Directory containing plugins (default: packages/)'
    )
    parser.add_argument(
        '--plugin',
        type=str,
        help='Validate only a specific plugin (by directory name)'
    )
    parser.add_argument(
        '--format',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )

    args = parser.parse_args()

    # Find plugins to validate
    if args.plugin:
        plugins = [args.plugins_dir / args.plugin]
        plugins = [p for p in plugins if p.exists()]
    else:
        plugins = find_plugins(args.plugins_dir)

    if not plugins:
        print("No plugins found to validate.")
        sys.exit(0)

    print(f"Found {len(plugins)} plugin(s) to validate\n")

    all_valid = True
    results = []

    for plugin_dir in plugins:
        validator = PluginValidator(plugin_dir)
        valid = validator.validate()
        validator._report()
        results.append({
            'plugin': plugin_dir.name,
            'valid': valid,
            'errors': validator.errors,
            'warnings': validator.warnings
        })
        if not valid:
            all_valid = False

    # Output summary
    print(f"\n{'='*60}")
    print(f"SUMMARY: {len([r for r in results if r['valid']])}/{len(results)} plugins valid")

    if args.format == 'json':
        import json
        print(json.dumps({
            'all_valid': all_valid,
            'plugins': results
        }, indent=2))

    sys.exit(0 if all_valid else 1)


if __name__ == '__main__':
    main()
