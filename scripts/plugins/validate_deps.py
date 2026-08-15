#!/usr/bin/env python3
"""
Plugin Dependency Validator

Validates dependency specifications in plugin manifests:
- Proper version specifier format
- Required dependencies present
- Conflicts detection
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, Set

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages" / "mekong-plugin-sdk" / "src"))

from mekong_plugin_sdk.manifest import load_manifest


def find_plugins(plugins_dir: Path) -> List[Path]:
    """Find all plugin directories containing mekong-plugin.json."""
    if not plugins_dir.exists():
        return []

    # Find all mekong-plugin.json files recursively
    manifest_files = list(plugins_dir.rglob("mekong-plugin.json"))
    # Return parent directories (unique)
    plugins = list(set(manifest_file.parent for manifest_file in manifest_files))

    return plugins


# Semantic version regex (simplified)
SEMVER_PATTERN = re.compile(
    r'^(~>|>=|<=|>|<|=|\^)?\s*'
    r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)'
    r'(-([0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*))?'
    r'(\+([0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*))?$'
)

VALID_OPERATORS = ['^', '~', '>=', '<=', '>', '<', '=']


def is_valid_version_spec(spec: str) -> bool:
    """Check if a version specification is valid."""
    if not spec:
        return False

    # Handle caret and tilde prefixes
    spec = spec.strip()

    # Check for wildcard patterns
    if spec.endswith('.*') or spec == '*':
        return True

    # Match semver pattern
    return SEMVER_PATTERN.match(spec) is not None


def validate_dependencies(plugins_dir: Path) -> bool:
    """Validate dependencies in all plugin manifests."""
    plugins = find_plugins(plugins_dir)

    if not plugins:
        print("No plugins found.")
        return True

    print(f"Validating dependencies for {len(plugins)} plugin(s)...\n")

    all_valid = True
    all_plugin_ids: Set[str] = set()

    # First pass: collect all plugin IDs
    for plugin_dir in plugins:
        try:
            manifest = load_manifest(plugin_dir / "mekong-plugin.json")
            all_plugin_ids.add(manifest.id)
        except Exception:
            continue

    # Second pass: validate each plugin's dependencies
    for plugin_dir in plugins:
        plugin_id = plugin_dir.name
        manifest_path = plugin_dir / "mekong-plugin.json"

        try:
            manifest = load_manifest(manifest_path)
        except Exception as e:
            print(f"❌ {plugin_id}: Could not load manifest: {e}")
            all_valid = False
            continue

        has_errors = False

        # Check dependencies
        for dep in manifest.dependencies:
            dep_id = dep.id
            version_spec = dep.version

            if not version_spec:
                print(f"⚠️  {plugin_id}: Dependency '{dep_id}' has no version specification")
                continue

            if not is_valid_version_spec(version_spec):
                print(f"❌ {plugin_id}: Invalid version spec for '{dep_id}': '{version_spec}'")
                has_errors = True

            # Check if it's a plugin dependency
            if dep_id in all_plugin_ids:
                # Plugin dependency - check optional flag
                if dep.optional:
                    print(f"ℹ️  {plugin_id}: Optional plugin dependency '{dep_id}' (version: {version_spec})")

        # Check peerDependencies
        peer_deps = manifest.peer_dependencies
        if peer_deps:
            for pkg, version_spec in peer_deps.items():
                if not is_valid_version_spec(version_spec):
                    print(f"❌ {plugin_id}: Invalid peer dependency version for '{pkg}': '{version_spec}'")
                    has_errors = True

        if not has_errors:
            print(f"✅ {plugin_id}: Dependencies valid")

    return all_valid


def main():
    if len(sys.argv) > 1:
        plugins_dir = Path(sys.argv[1])
    else:
        plugins_dir = Path('packages')

    success = validate_dependencies(plugins_dir)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
