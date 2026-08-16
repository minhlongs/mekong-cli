# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""4-layer priority resolution for templates, commands, and configs."""
from __future__ import annotations

import os
from pathlib import Path


class PriorityStack:
    """Resolve one file per key across four ordered layers."""

    def __init__(self, project_root: str | None = None) -> None:
        root = Path(project_root) if project_root else Path(os.getcwd())
        self._layers: list[tuple[str, Path]] = [
            ("overrides", root / ".mekong" / "overrides"),
            ("presets", Path.home() / ".mekong" / "presets"),
            ("extensions", root / "src" / "extensions"),
            ("core", root / "src" / "presets" / "core"),
        ]

    def resolve(self, key: str, suffix: str = "") -> Path | None:
        if ".." in key or key.startswith("/"):
            return None
        safe_suffix = suffix.lstrip("/")
        if safe_suffix and (".." in safe_suffix or safe_suffix.startswith("/")):
            return None
        for _layer_name, layer_dir in self._layers:
            candidate = (layer_dir / f"{key}{safe_suffix}").resolve()
            try:
                layer_dir_resolved = layer_dir.resolve()
            except OSError:
                continue
            try:
                if not str(candidate).startswith(str(layer_dir_resolved)):
                    continue
            except (OSError, ValueError):
                continue
            if candidate.is_file():
                return candidate
        return None

    def resolve_text(self, key: str, suffix: str = "", default: str = "") -> str:
        """Resolve a text file across layers; return ``default`` if not found."""
        path = self.resolve(key, suffix)
        return default if path is None else path.read_text(encoding="utf-8")

    def all_layers(self) -> list[dict]:
        return [
            {"name": n, "path": str(p), "exists": p.is_dir()}
            for n, p in self._layers
        ]