#!/usr/bin/env python3
"""Build all plugin documentation."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from generate import generate_all


def find_plugins(docs_dir: Path) -> List[Path]:
    """Find all plugin documentation directories."""
    if not docs_dir.exists():
        return []
    return [d for d in docs_dir.iterdir() if d.is_dir() and (d / 'plugin.json').exists()]


def build_index(plugins: List[dict], output_path: Path) -> None:
    """Build plugin index page."""
    content = "# Mekong CLI Plugins\n\n"
    content += "> Auto-generated plugin registry\n\n"
    content += "| Plugin | Version | Description | Category |\n"
    content += "|--------|---------|-------------|----------|\n"

    for plugin in sorted(plugins, key=lambda p: p.get('id', '')):
        plugin_id = plugin.get('id', 'unknown')
        name = plugin.get('name', plugin_id)
        version = plugin.get('version', 'N/A')
        description = plugin.get('description', 'No description')[:60]
        if len(plugin.get('description', '')) > 60:
            description += '...'
        category = plugin.get('category', 'uncategorized')

        content += f"| [{name}]({plugin_id}/) | {version} | {description} | {category} |\n"

    output_path.write_text(content)
    print(f"✓ Generated index at {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description='Build plugin documentation')
    parser.add_argument(
        '--plugins-dir',
        type=Path,
        default=Path('docs/plugins'),
        help='Plugins documentation directory (default: docs/plugins)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('docs/plugins'),
        help='Output directory (default: docs/plugins)'
    )
    parser.add_argument(
        '--templates',
        type=Path,
        default=Path(__file__).parent / 'templates',
        help='Templates directory'
    )
    parser.add_argument(
        '--serve',
        action='store_true',
        help='Start MkDocs server after build'
    )

    args = parser.parse_args()

    # Generate docs for all plugins from source packages
    print("Generating plugin documentation...")
    generate_all(args.plugins_dir.parent.parent / 'packages', args.output, args.templates)

    # Build index from generated docs
    plugins = []
    for plugin_dir in args.output.iterdir():
        if plugin_dir.is_dir() and (plugin_dir / 'plugin.json').exists():
            try:
                with open(plugin_dir / 'plugin.json') as f:
                    plugins.append(json.load(f))
            except Exception:
                pass

    if plugins:
        build_index(plugins, args.output / 'index.md')

    print(f"\n✓ Built {len(plugins)} plugin documentation pages")

    # Optionally start MkDocs
    if args.serve:
        print("\nStarting MkDocs server...")
        subprocess.run(['mkdocs', 'serve', '-f', 'docs/mkdocs.yml'], cwd=Path.cwd())


if __name__ == '__main__':
    main()
