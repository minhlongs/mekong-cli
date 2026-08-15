#!/usr/bin/env python3
"""Plugin documentation generator.

This module provides the core functionality for generating documentation
from plugin manifests and source code.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import jinja2


class PluginDocsGenerator:
    """Generate documentation from plugin manifests and code."""

    def __init__(self, templates_dir: Path, output_dir: Path) -> None:
        """Initialize the generator.

        Args:
            templates_dir: Directory containing Jinja2 templates
            output_dir: Base directory for generated documentation
        """
        self.templates_dir = templates_dir
        self.output_dir = output_dir
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def load_plugin_manifest(self, manifest_path: Path) -> dict[str, Any]:
        """Load and validate plugin manifest.

        Args:
            manifest_path: Path to plugin.json

        Returns:
            Parsed manifest dictionary

        Raises:
            ValueError: If manifest is invalid
        """
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
            return manifest
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {manifest_path}: {e}") from e
        except FileNotFoundError as e:
            raise ValueError(f"Manifest not found: {manifest_path}") from e

    def extract_api_docs(self, plugin_path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
        """Extract API documentation from Python source code.

        Args:
            plugin_path: Path to plugin directory
            manifest: Plugin manifest dictionary

        Returns:
            Dictionary containing extracted API documentation
        """
        api_docs = {
            "classes": [],
            "functions": [],
            "modules": [],
        }

        entrypoint = manifest.get("entrypoint", "")
        if not entrypoint:
            return api_docs

        # Resolve entrypoint path
        entrypoint_path = plugin_path / entrypoint
        if not entrypoint_path.exists():
            return api_docs

        # Simple extraction: look for docstrings in the main module
        try:
            # Use ast to parse without executing
            import ast

            with open(entrypoint_path) as f:
                source = f.read()

            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    docstring = ast.get_docstring(node) or ""
                    methods = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            methods.append({
                                "name": item.name,
                                "docstring": ast.get_docstring(item) or "",
                                "args": [arg.arg for arg in item.args.args],
                            })
                    api_docs["classes"].append({
                        "name": node.name,
                        "docstring": docstring,
                        "methods": methods,
                    })
                elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                    # Top-level function
                    docstring = ast.get_docstring(node) or ""
                    api_docs["functions"].append({
                        "name": node.name,
                        "docstring": docstring,
                        "args": [arg.arg for arg in node.args.args],
                    })

        except Exception:
            # Silently fail - API docs are nice-to-have
            pass

        return api_docs

    def generate_index(self, plugin: dict[str, Any], api_docs: dict[str, Any]) -> str:
        """Generate main plugin reference page.

        Args:
            plugin: Plugin manifest dictionary
            api_docs: Extracted API documentation

        Returns:
            Rendered Markdown content
        """
        template = self.env.get_template('index.md')
        return template.render(
            plugin=plugin,
            api=api_docs,
            now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

    def generate_api_ref(self, plugin: dict[str, Any], api_docs: dict[str, Any]) -> str:
        """Generate API reference page.

        Args:
            plugin: Plugin manifest dictionary
            api_docs: Extracted API documentation

        Returns:
            Rendered Markdown content
        """
        template = self.env.get_template('api.md')
        return template.render(
            plugin=plugin,
            api=api_docs,
            now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

    def generate_commands(self, plugin: dict[str, Any]) -> str:
        """Generate commands reference page.

        Args:
            plugin: Plugin manifest dictionary

        Returns:
            Rendered Markdown content
        """
        commands = plugin.get('commands', [])
        template = self.env.get_template('commands.md')
        return template.render(
            plugin=plugin,
            commands=commands,
            now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

    def generate_config(self, plugin: dict[str, Any]) -> str:
        """Generate configuration reference page.

        Args:
            plugin: Plugin manifest dictionary

        Returns:
            Rendered Markdown content
        """
        config = plugin.get('config', {})
        template = self.env.get_template('config.md')
        return template.render(
            plugin=plugin,
            config=config,
            now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

    def copy_assets(self, plugin_path: Path, plugin_output: Path) -> None:
        """Copy asset files from plugin to output.

        Args:
            plugin_path: Source plugin directory
            plugin_output: Output directory for this plugin
        """
        assets_src = plugin_path / 'docs' / 'assets'
        if assets_src.exists():
            import shutil
            shutil.copytree(assets_src, plugin_output / 'assets', dirs_exist_ok=True)

    def copy_examples(self, plugin_path: Path, plugin_output: Path) -> None:
        """Copy example files from plugin to output.

        Args:
            plugin_path: Source plugin directory
            plugin_output: Output directory for this plugin
        """
        examples_src = plugin_path / 'examples'
        if examples_src.exists():
            import shutil
            shutil.copytree(examples_src, plugin_output / 'examples', dirs_exist_ok=True)

    def generate_plugin_json(self, plugin: dict[str, Any], plugin_output: Path) -> None:
        """Generate plugin.json for the documentation site.

        Args:
            plugin: Plugin manifest dictionary
            plugin_output: Output directory for this plugin
        """
        # Create a documentation-friendly version of the manifest
        doc_manifest = {
            "id": plugin.get("id"),
            "name": plugin.get("name"),
            "version": plugin.get("version"),
            "description": plugin.get("description"),
            "author": plugin.get("author"),
            "license": plugin.get("license"),
            "homepage": plugin.get("homepage"),
            "repository": plugin.get("repository"),
            "keywords": plugin.get("keywords", []),
            "category": plugin.get("category"),
            "mcuCost": plugin.get("mcuCost", 0),
            "permissions": plugin.get("permissions", {}),
            "commands": plugin.get("commands", []),
            "generated_at": datetime.now().isoformat(),
        }

        output_file = plugin_output / 'plugin.json'
        with open(output_file, 'w') as f:
            json.dump(doc_manifest, f, indent=2)

    def generate(self, plugin_path: Path) -> None:
        """Generate all documentation for a plugin.

        Args:
            plugin_path: Path to plugin directory containing plugin.json

        Raises:
            ValueError: If plugin manifest is invalid or missing
        """
        manifest_path = plugin_path / 'plugin.json'
        if not manifest_path.exists():
            raise ValueError(f'No plugin.json in {plugin_path}')

        # Load manifest
        plugin = self.load_plugin_manifest(manifest_path)
        plugin_id = plugin.get('id') or plugin_path.name
        plugin['source_dir'] = str(plugin_path)

        # Create output directory
        plugin_output = self.output_dir / plugin_id
        plugin_output.mkdir(parents=True, exist_ok=True)

        # Extract API docs from source
        api_docs = self.extract_api_docs(plugin_path, plugin)

        # Generate files
        try:
            index_content = self.generate_index(plugin, api_docs)
            (plugin_output / 'index.md').write_text(index_content)

            api_content = self.generate_api_ref(plugin, api_docs)
            (plugin_output / 'api.md').write_text(api_content)

            commands_content = self.generate_commands(plugin)
            (plugin_output / 'commands.md').write_text(commands_content)

            config_content = self.generate_config(plugin)
            (plugin_output / 'config.md').write_text(config_content)

            # Generate plugin.json for the site
            self.generate_plugin_json(plugin, plugin_output)

            # Copy assets and examples
            self.copy_assets(plugin_path, plugin_output)
            self.copy_examples(plugin_path, plugin_output)

            print(f'✓ Generated docs for {plugin_id} at {plugin_output}')

        except Exception as e:
            print(f'✗ Failed to generate docs for {plugin_id}: {e}')
            raise


def find_plugins(plugins_dir: Path) -> list[Path]:
    """Find all plugin directories with plugin.json.

    Args:
        plugins_dir: Directory to scan for plugins

    Returns:
        List of plugin directory paths
    """
    if not plugins_dir.exists():
        return []

    plugins = []
    for item in plugins_dir.iterdir():
        if item.is_dir() and (item / 'plugin.json').exists():
            plugins.append(item)

    return plugins


def generate_all(plugins_dir: Path, output_dir: Path, templates_dir: Path) -> None:
    """Generate documentation for all plugins.

    Args:
        plugins_dir: Directory containing plugin packages
        output_dir: Base output directory for generated docs
        templates_dir: Directory containing Jinja2 templates
    """
    generator = PluginDocsGenerator(templates_dir, output_dir)

    plugins = find_plugins(plugins_dir)
    if not plugins:
        print(f'No plugins found in {plugins_dir}')
        return

    print(f'Found {len(plugins)} plugin(s)')

    for plugin_path in plugins:
        try:
            generator.generate(plugin_path)
        except Exception as e:
            print(f'Error generating docs for {plugin_path.name}: {e}')


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate plugin documentation from plugin manifests'
    )
    parser.add_argument(
        'plugin_path',
        type=Path,
        nargs='?',
        help='Path to plugin directory (default: all plugins in packages/)'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        default=Path('docs/plugins'),
        help='Output directory (default: docs/plugins)'
    )
    parser.add_argument(
        '-t', '--templates',
        type=Path,
        default=Path(__file__).parent / 'templates',
        help='Templates directory (default: scripts/plugin-docs/templates)'
    )
    parser.add_argument(
        '--plugins-dir',
        type=Path,
        default=Path('packages'),
        help='Plugins directory (default: packages)'
    )

    args = parser.parse_args()

    try:
        if args.plugin_path:
            # Generate for single plugin
            generator = PluginDocsGenerator(args.templates, args.output)
            generator.generate(args.plugin_path)
        else:
            # Generate for all plugins
            generate_all(args.plugins_dir, args.output, args.templates)

    except ValueError as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'Unexpected error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
