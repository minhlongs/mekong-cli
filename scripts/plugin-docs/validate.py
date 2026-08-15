#!/usr/bin/env python3
"""Plugin documentation linter and validator.

This script validates generated plugin documentation for correctness,
completeness, and formatting.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path



class ValidationError(Exception):
    """Raised when validation fails."""

    def __init__(self, message: str, file: Path | None = None, line: int | None = None) -> None:
        super().__init__(message)
        self.file = file
        self.line = line


class PluginDocsValidator:
    """Validate plugin documentation."""

    REQUIRED_FILES = ['index.md', 'commands.md', 'api.md', 'config.md', 'plugin.json']
    REQUIRED_MANIFEST_FIELDS = ['id', 'name', 'version', 'description']
    REQUIRED_COMMAND_FIELDS = ['name', 'description']

    def __init__(self, docs_dir: Path) -> None:
        """Initialize validator.

        Args:
            docs_dir: Base directory containing plugin documentation
        """
        self.docs_dir = docs_dir
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate(self, plugin_dir: Path) -> None:
        """Validate a single plugin's documentation.

        Args:
            plugin_dir: Path to plugin documentation directory

        Raises:
            ValidationError: If validation fails
        """
        plugin_id = plugin_dir.name

        # Check required files exist
        for file in self.REQUIRED_FILES:
            file_path = plugin_dir / file
            if not file_path.exists():
                self.errors.append(f"[{plugin_id}] Missing required file: {file}")

        # Validate plugin.json
        plugin_json = plugin_dir / 'plugin.json'
        if plugin_json.exists():
            self._validate_plugin_json(plugin_json, plugin_id)

        # Validate Markdown files
        for md_file in plugin_dir.glob('*.md'):
            self._validate_markdown(md_file, plugin_id)

        # Report
        if self.errors:
            raise ValidationError(
                f"Validation failed for {plugin_id}:\n" + "\n".join(f"  - {e}" for e in self.errors)
            )

    def _validate_plugin_json(self, file_path: Path, plugin_id: str) -> None:
        """Validate plugin.json manifest.

        Args:
            file_path: Path to plugin.json
            plugin_id: Plugin identifier
        """
        try:
            with open(file_path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"[{plugin_id}] Invalid JSON in plugin.json: {e}")
            return

        # Check required fields
        for field in self.REQUIRED_MANIFEST_FIELDS:
            if field not in data:
                self.warnings.append(f"[{plugin_id}] Missing field in plugin.json: {field}")

        # Validate commands if present
        commands = data.get('commands', [])
        for i, cmd in enumerate(commands):
            for field in self.REQUIRED_COMMAND_FIELDS:
                if field not in cmd:
                    self.warnings.append(
                        f"[{plugin_id}] Command {i} missing required field: {field}"
                    )

            # Check for command name pattern
            cmd_name = cmd.get('name', '')
            if cmd_name and not re.match(r'^[a-z][a-z0-9-]*$', cmd_name):
                self.warnings.append(
                    f"[{plugin_id}] Invalid command name: {cmd_name} (must be kebab-case)"
                )

    def _validate_markdown(self, file_path: Path, plugin_id: str) -> None:
        """Basic Markdown validation.

        Args:
            file_path: Path to Markdown file
            plugin_id: Plugin identifier
        """
        content = file_path.read_text()
        rel_path = file_path.relative_to(self.docs_dir)

        # Check for common issues

        # Empty file
        if not content.strip():
            self.warnings.append(f"[{plugin_id}] Empty file: {rel_path}")

        # Code blocks not closed
        code_block_count = content.count('```')
        if code_block_count % 2 != 0:
            self.errors.append(
                f"[{plugin_id}] Unclosed code block in {rel_path}"
            )

        # Broken internal links
        link_pattern = r'\[[^\]]*\]\(([^)]+)\)'
        for match in re.finditer(link_pattern, content):
            link = match.group(1)
            if link.startswith(('.', '#', 'plugins/')):
                # Resolve relative link
                if link.startswith('plugins/'):
                    # Already absolute from docs root
                    continue
                target = file_path.parent / link
                if not target.exists() and '#' not in link:
                    self.warnings.append(
                        f"[{plugin_id}] Broken link in {rel_path}: {link}"
                    )

        # Check headings hierarchy
        lines = content.splitlines()
        heading_levels = []
        for i, line in enumerate(lines, 1):
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                if heading_levels and level > heading_levels[-1] + 1:
                    self.warnings.append(
                        f"[{plugin_id}] Skipped heading level in {rel_path}:{i}"
                    )
                heading_levels.append(level)

    def validate_all(self) -> None:
        """Validate all plugin documentation."""
        if not self.docs_dir.exists():
            print(f"Docs directory does not exist: {self.docs_dir}")
            return

        plugin_dirs = [d for d in self.docs_dir.iterdir() if d.is_dir() and (d / 'plugin.json').exists()]

        if not plugin_dirs:
            print(f"No plugin documentation found in {self.docs_dir}")
            return

        print(f"Validating {len(plugin_dirs)} plugin(s)...")

        for plugin_dir in plugin_dirs:
            try:
                self.validate(plugin_dir)
                print(f"✓ {plugin_dir.name}")
            except ValidationError as e:
                print(f"✗ {plugin_dir.name}")
                print(e)
                # Reset errors for next plugin
                self.errors = []

        # Summary
        if self.warnings:
            print(f"\n{len(self.warnings)} warning(s):")
            for w in self.warnings[:10]:  # Show first 10
                print(f"  {w}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Validate plugin documentation'
    )
    parser.add_argument(
        'docs_dir',
        type=Path,
        nargs='?',
        default=Path('docs/plugins'),
        help='Documentation directory (default: docs/plugins)'
    )

    args = parser.parse_args()

    validator = PluginDocsValidator(args.docs_dir)
    validator.validate_all()


if __name__ == '__main__':
    main()
