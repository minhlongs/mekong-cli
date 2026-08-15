#!/usr/bin/env python3
"""Validate only changed plugin documentation for pre-commit hook.

This script is designed to be run in a pre-commit hook to quickly
validate only the plugin documentation that has been modified.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def get_changed_plugins(docs_dir: Path) -> list[Path]:
    """Get list of changed plugin documentation directories.

    Returns:
        List of plugin directory paths that have changed
    """
    try:
        # Get changed files from git
        result = subprocess.run(
            ['git', 'diff', '--name-only', '--cached'],
            capture_output=True,
            text=True,
            check=True
        )
        changed_files = result.stdout.strip().split('\n') if result.stdout.strip() else []

        # Find unique plugin directories
        plugin_dirs = set()
        for file_path in changed_files:
            path = Path(file_path)
            # Check if file is under docs/plugins/
            if 'docs/plugins/' in str(path):
                # Extract plugin ID (first directory after docs/plugins/)
                parts = path.parts
                if 'plugins' in parts:
                    idx = parts.index('plugins')
                    if idx + 1 < len(parts):
                        plugin_id = parts[idx + 1]
                        plugin_dir = docs_dir / plugin_id
                        if plugin_dir.exists():
                            plugin_dirs.add(plugin_dir)

        return list(plugin_dirs)

    except subprocess.CalledProcessError as e:
        print(f"Error getting changed files: {e}", file=sys.stderr)
        return []


def validate_plugin(plugin_dir: Path, validator_script: Path) -> bool:
    """Validate a single plugin using validate.py.

    Args:
        plugin_dir: Plugin documentation directory
        validator_script: Path to validate.py

    Returns:
        True if valid, False otherwise
    """
    import subprocess

    result = subprocess.run(
        [sys.executable, str(validator_script), str(plugin_dir)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"✗ {plugin_dir.name}")
        print(result.stdout)
        print(result.stderr)
        return False

    print(f"✓ {plugin_dir.name}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Validate changed plugin documentation (pre-commit hook)'
    )
    parser.add_argument(
        '--docs-dir',
        type=Path,
        default=Path('docs/plugins'),
        help='Documentation directory (default: docs/plugins)'
    )

    args = parser.parse_args()

    validator_script = Path(__file__).parent / 'validate.py'

    if not validator_script.exists():
        print(f"Validator not found: {validator_script}", file=sys.stderr)
        sys.exit(1)

    changed_plugins = get_changed_plugins(args.docs_dir)

    if not changed_plugins:
        print("No plugin documentation changes to validate.")
        sys.exit(0)

    print(f"Validating {len(changed_plugins)} changed plugin(s)...")

    all_valid = True
    for plugin_dir in changed_plugins:
        if not validate_plugin(plugin_dir, validator_script):
            all_valid = False

    if all_valid:
        print("\n✓ All changed plugins valid")
        sys.exit(0)
    else:
        print("\n✗ Some plugins failed validation")
        sys.exit(1)


if __name__ == '__main__':
    main()
