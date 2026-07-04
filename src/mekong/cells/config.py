"""YAML-based AI Cell configuration loader and particle directory resolver.

Provides ``load_cell_config()`` for validating a single cell YAML file,
``resolve_particle_config()`` for locating a particle directory by name or
path, and ``find_cell_configs()`` to enumerate all cell configurations inside
a particle directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from src.mekong.cells.types import (
    CellBoundaries,
    CellConfig,
    CellPrivileges,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS = frozenset({"role", "model"})


def _validate_config(data: dict[str, Any], source: str) -> None:
    """Raise ``ValueError`` if required fields are missing from *data*."""
    missing = _REQUIRED_FIELDS - set(data.keys())
    if missing:
        raise ValueError(
            f"Cell config {source} is missing required field(s): "
            f"{', '.join(sorted(missing))}"
        )


def _build_privileges(data: dict[str, Any]) -> CellPrivileges:
    """Build a ``CellPrivileges`` from the YAML ``privileges`` block."""
    p = data.get("privileges", {})
    return CellPrivileges(
        max_budget=float(p.get("max_budget", 0.0)),
        requires_approval=bool(p.get("requires_approval", False)),
    )


def _build_boundaries(data: dict[str, Any]) -> CellBoundaries:
    """Build a ``CellBoundaries`` from the YAML ``boundaries`` block."""
    b = data.get("boundaries", {})
    return CellBoundaries(
        read=list(b.get("read", [])),
        write=list(b.get("write", [])),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_cell_config(path: str | Path) -> CellConfig:
    """Load and validate an AI Cell YAML configuration file.

    Parses the YAML at *path*, validates that required fields (``role``,
    ``model``) are present, and returns a ``CellConfig`` instance.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the YAML is malformed or required fields are missing.

    Examples
    --------
    >>> config = load_cell_config("particles/my-cell/cells/strategist.yaml")
    >>> config.role
    'strategist'
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Cell config not found: {path}")

    try:
        with open(path, encoding="utf-8") as fh:
            raw: dict[str, Any] = yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError(f"Cell config {path} must be a YAML mapping, got {type(raw).__name__}")

    _validate_config(raw, str(path))

    return CellConfig(
        role=str(raw["role"]),
        model=str(raw["model"]),
        capabilities=[str(c) for c in raw.get("capabilities", [])],
        privileges=_build_privileges(raw),
        boundaries=_build_boundaries(raw),
        metadata={k: v for k, v in raw.items()
                  if k not in _REQUIRED_FIELDS
                  and k not in ("capabilities", "privileges", "boundaries")},
    )


def resolve_particle_config(particle_id: str) -> Path:
    """Resolve a particle name to its directory path.

    Checks, in order:
    1. If *particle_id* is an existing directory, return it as-is.
    2. Otherwise, check if ``./{particle_id}/`` exists in the current working
       directory.
    3. Fall back to ``.mekong/particles/{particle_id}/``.

    Raises ``FileNotFoundError`` if none of the locations exist.

    Parameters
    ----------
    particle_id:
        Particle name, path, or identifier.

    Returns
    -------
    Path
        Resolved absolute path to the particle directory.
    """
    cwd = Path.cwd()
    candidates = [
        Path(particle_id).resolve(),
        cwd / particle_id,
        cwd / ".mekong" / "particles" / particle_id,
    ]

    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()

    raise FileNotFoundError(
        f"Particle not found: {particle_id}. "
        f"Checked: {', '.join(str(p) for p in candidates)}"
    )


def find_cell_configs(particle_dir: Path) -> list[dict[str, Any]]:
    """Enumerate all AI Cell YAML configs in a particle directory.

    Scans ``{particle_dir}/cells/*.yaml`` (and ``.yml``), loads each file,
    and returns a list of raw dictionaries with an additional ``_path`` key
    holding the absolute file path.

    Parameters
    ----------
    particle_dir:
        Path to the particle directory (must contain a ``cells/``
        subdirectory).

    Returns
    -------
    list[dict]
        List of parsed YAML configs, each with a ``_path`` key.
    """
    cells_dir = Path(particle_dir) / "cells"
    if not cells_dir.is_dir():
        return []

    results: list[dict[str, Any]] = []
    for yaml_path in sorted(cells_dir.glob("*.yaml")) + sorted(cells_dir.glob("*.yml")):
        try:
            with open(yaml_path, encoding="utf-8") as fh:
                data: dict[str, Any] = yaml.safe_load(fh) or {}
            if isinstance(data, dict):
                data["_path"] = str(yaml_path.resolve())
                results.append(data)
        except (yaml.YAMLError, OSError):
            continue

    return results
