#!/usr/bin/env python3
"""
Plugin Load Test

Tests that all plugins can be discovered and loaded.
This is a smoke test to ensure plugins are properly structured and importable.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages" / "mekong-plugin-sdk" / "src"))


def find_plugin_directories(plugins_root: Path) -> List[Path]:
    """Find all plugin directories."""
    if not plugins_root.exists():
        return []

    # Find all mekong-plugin.json files recursively
    manifest_files = list(plugins_root.rglob("mekong-plugin.json"))
    # Return parent directories (unique)
    plugins = list(set(manifest_file.parent for manifest_file in manifest_files))

    return plugins


async def run_load_tests(plugins_root: Path) -> bool:
    """Run load tests for all plugins."""
    plugins = find_plugin_directories(plugins_root)

    if not plugins:
        print("No plugins found to test.")
        return True

    print(f"Testing load capability for {len(plugins)} plugin(s)...\n")

    all_passed = True

    for plugin_dir in plugins:
        try:
            from mekong_plugin_sdk.manifest import load_manifest
            manifest = load_manifest(plugin_dir / "mekong-plugin.json")
            plugin_id = manifest.id
            entrypoint = manifest.entrypoint
        except Exception as e:
            print(f"  ✗ Failed to load manifest for {plugin_dir.name}: {e}")
            all_passed = False
            continue

        if ":" not in entrypoint:
            print(f"  ✗ Invalid entrypoint format: {entrypoint}")
            all_passed = False
            continue

        module_name, class_name = entrypoint.split(":", 1)

        # Add plugin directory to Python path temporarily so module can be imported
        # The entrypoint module is expected to be directly in the plugin_dir or in a
        # package structure under plugin_dir.
        sys.path.insert(0, str(plugin_dir))

        try:
            import importlib
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, class_name)

            # Check it inherits from MekongPlugin
            from mekong_plugin_sdk import MekongPlugin
            if not issubclass(plugin_class, MekongPlugin):
                print(f"  ✗ Class {class_name} does not inherit from MekongPlugin")
                all_passed = False
                continue

            # Try to instantiate (without context - just basic smoke test)
            _plugin = plugin_class()

            print(f"  ✓ {plugin_id} loaded successfully")

        except ImportError as e:
            print(f"  ✗ Import error: {e}")
            all_passed = False
        except Exception as e:
            print(f"  ✗ Load error: {e}")
            all_passed = False
        finally:
            # Clean up sys.path
            path_str = str(plugin_dir)
            if path_str in sys.path:
                sys.path.remove(path_str)

    print(f"\n{'='*60}")
    if all_passed:
        print("✅ All plugins passed load tests")
    else:
        print("❌ Some plugins failed load tests")

    return all_passed


def main():
    if len(sys.argv) > 1:
        plugins_root = Path(sys.argv[1])
    else:
        plugins_root = Path('packages')

    success = asyncio.run(run_load_tests(plugins_root))
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
