""".plugin.json schema and validator for Mekong CLI plugins.

Defines the canonical manifest format that plugins MUST provide at their
root directory. Uses pydantic v2 for validation.

Minimal contract:
    {
      "id":          "com.example.my-plugin",   # required, reverse-domain
      "name":        "My Plugin",                # required, human-readable
      "version":     "1.2.3",                   # required, semver
      "description": "...",                      # optional
      "author":      "...",                       # optional
      "license":     "MIT",                      # optional, default MIT
      "engines":     {"mekong": "^6.0.0"},       # optional
      "permissions": ["file:read"],              # optional
      "mcu_cost":    1,                          # optional, default 1
      "dependencies": ["requests>=2"],           # optional
      "hooks": [...],                            # optional
      "entry_point": "module.fn",                # optional
      "isolation":   "none",                     # optional, one of [none|restricted|sandboxed]
    }
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# Regex for semver: MAJOR.MINOR.PATCH with optional prerelease/metadata
_SEMVER_RE = re.compile(
    r"^\d+\.\d+\.\d+"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)

# Reverse-domain style: com.example.thing or io.github.user.project
_REVERSE_DOMAIN_RE = re.compile(r"^[a-z0-9]+([.\-][a-z0-9]+)*\.[a-z0-9]+$")


class HookManifest(BaseModel):
    """Single hook declaration in .plugin.json."""

    point: str = Field(..., description="Hook point, e.g. BEFORE_COMMAND")
    handler: str = Field(..., description="module.function to call")
    priority: int = Field(50, ge=0, le=1000)


class PluginManifestSchema(BaseModel):
    """Validated .plugin.json manifest.

    Instantiate from a dict (parsed JSON) or from a file path via
    ``PluginManifestSchema.from_file(path)``.
    """

    id: str = Field(..., description="Reverse-domain plugin identifier")
    name: str = Field(..., description="Human-readable plugin name")
    version: str = Field(..., description="Semver version string")
    description: Optional[str] = Field("", description="One-line description")
    author: Optional[str] = Field("", description="Plugin author")
    license: str = Field("MIT", description="SPDX license identifier")
    engines: Dict[str, str] = Field(
        default_factory=lambda: {"mekong": "^6.0.0"},
        description="Engine version constraints",
    )
    permissions: List[str] = Field(
        default_factory=list, description="Declared permission flags"
    )
    mcu_cost: int = Field(1, ge=0, description="Credits per invocation")
    dependencies: List[str] = Field(
        default_factory=list, description="Pip dependency specifiers"
    )
    hooks: List[HookManifest] = Field(
        default_factory=list, description="Lifecycle hooks"
    )
    entry_point: Optional[str] = Field(
        None, description="module.function - alternate to register()"
    )
    isolation: str = Field(
        "none",
        pattern="^(none|restricted|sandboxed)$",
        description="Isolation level for this plugin",
    )

    # ---- validators ------------------------------------------------- #

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not _REVERSE_DOMAIN_RE.match(value):
            raise ValueError(
                f"Invalid plugin id '{value}': must be reverse-domain "
                "(e.g. com.example.my-plugin)"
            )
        return value

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        if not _SEMVER_RE.match(value):
            raise ValueError(
                f"Invalid semver '{value}': "
                "expected MAJOR.MINOR.PATCH[-prerelease][+build]"
            )
        return value

    @field_validator("engines")
    @classmethod
    def validate_engines(cls, value: Dict[str, str]) -> Dict[str, str]:
        if "mekong" not in value:
            raise ValueError("engines.mekong constraint is required")
        return value

    # ---- loaders ---------------------------------------------------- #

    @classmethod
    def from_file(cls, path: Path | str) -> "PluginManifestSchema":
        """Read and validate a .plugin.json from disk.

        Args:
            path: Path to .plugin.json or to the plugin root directory.

        Returns:
            Validated PluginManifestSchema.

        Raises:
            FileNotFoundError: .plugin.json not found.
            ValueError: JSON missing or invalid.
        """
        p = Path(path)
        if p.is_dir():
            candidate = p / ".plugin.json"
        else:
            candidate = p
        if not candidate.exists():
            raise FileNotFoundError(
                f".plugin.json not found at: {candidate}"
            )
        try:
            raw: Dict[str, Any] = __import__("json").loads(
                candidate.read_text(encoding="utf-8")
            )
        except Exception as exc:
            raise ValueError(f"Failed to parse .plugin.json: {exc}") from exc
        return cls.model_validate(raw)

    # ---- converters ------------------------------------------------ #

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to plain dict (alias for model_dump)."""
        return self.model_dump()

    def to_json(self, *, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(indent=indent).encode("utf-8").decode("utf-8")
