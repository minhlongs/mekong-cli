# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for root CLI command-surface manifest (src/core/command_surface.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.core.command_surface import (
    DEFAULT_COMMAND_SURFACE_PATH,
    CommandSurfaceManifest,
    current_root_commands,
    validate_command_surface,
)


class TestCommandSurfaceManifest:
    """Validate loading and schema checking of CommandSurfaceManifest."""

    def test_default_manifest_loads_and_has_commands(self):
        manifest = CommandSurfaceManifest.load()
        assert manifest.schema == "mekong.command_surface.v1"
        assert manifest.path == DEFAULT_COMMAND_SURFACE_PATH
        assert len(manifest.commands) == 57
        assert isinstance(manifest.command_set, set)
        assert len(manifest.command_set) == 57
        assert "cfo" in manifest.command_set
        assert "run" in manifest.command_set

    def test_load_custom_manifest(self, tmp_path: Path):
        data = {
            "schema": "mekong.command_surface.v1",
            "version": "1.0-test",
            "description": "Test manifest",
            "commands": ["cmd1", "cmd2"],
        }
        custom_path = tmp_path / "custom.json"
        custom_path.write_text(json.dumps(data), encoding="utf-8")

        manifest = CommandSurfaceManifest.load(custom_path)
        assert manifest.version == "1.0-test"
        assert manifest.command_set == {"cmd1", "cmd2"}
        assert manifest.path == custom_path

    def test_unsupported_schema_raises_value_error(self, tmp_path: Path):
        data = {
            "schema": "unknown.schema.v99",
            "version": "1.0",
            "description": "Bad schema",
            "commands": [],
        }
        bad_path = tmp_path / "bad.json"
        bad_path.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(ValueError, match="Unsupported command-surface schema: unknown.schema.v99"):
            CommandSurfaceManifest.load(bad_path)


class TestValidateCommandSurface:
    """Validate live command surface against manifest."""

    def test_default_command_surface_matches_root_cli(self):
        validation = validate_command_surface()
        assert validation.valid is True
        assert validation.manifest_count == 57
        assert validation.current_count == 57
        assert validation.missing_from_manifest == []
        assert validation.stale_in_manifest == []

    def test_command_surface_reports_missing_command(self, tmp_path: Path):
        current = sorted(current_root_commands())
        data = {
            "schema": "mekong.command_surface.v1",
            "version": "test",
            "description": "test",
            "commands": current[:-1],
        }
        path = tmp_path / "command-surface.json"
        path.write_text(json.dumps(data), encoding="utf-8")

        manifest = CommandSurfaceManifest.load(path)
        validation = validate_command_surface(manifest)

        assert validation.valid is False
        assert validation.missing_from_manifest == [current[-1]]
        assert validation.stale_in_manifest == []

    def test_command_surface_reports_stale_command(self, tmp_path: Path):
        current = sorted(current_root_commands())
        data = {
            "schema": "mekong.command_surface.v1",
            "version": "test",
            "description": "test",
            "commands": current + ["phantom_command_xyz"],
        }
        path = tmp_path / "command-surface.json"
        path.write_text(json.dumps(data), encoding="utf-8")

        manifest = CommandSurfaceManifest.load(path)
        validation = validate_command_surface(manifest)

        assert validation.valid is False
        assert validation.missing_from_manifest == []
        assert validation.stale_in_manifest == ["phantom_command_xyz"]
