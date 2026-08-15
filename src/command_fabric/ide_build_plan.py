"""Build-plan artifacts for generated IDE packages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


BuildPlanHost = Literal["vscode", "cursor", "windsurf", "theia", "jetbrains"]


@dataclass(frozen=True)
class IdeBuildPlanArtifact:
    """One generated IDE build-plan artifact."""

    name: str
    path: str
    host: str


def build_package_script(host: BuildPlanHost) -> str:
    """Return a deterministic package build script for one IDE host."""
    if host in {"vscode", "cursor", "windsurf", "theia"}:
        return """#!/usr/bin/env bash
set -euo pipefail

npm install
npm run compile
npm run package
"""
    return """#!/usr/bin/env bash
set -euo pipefail

gradle buildPlugin
"""


def build_readme(host: BuildPlanHost) -> str:
    """Return package build instructions for one IDE host."""
    if host == "vscode":
        channel = "VS Code Marketplace via vsce"
    elif host == "cursor":
        channel = "Open VSX/Cursor compatible package channel"
    elif host == "windsurf":
        channel = "VS Code-compatible package channel for Windsurf"
    elif host == "theia":
        channel = "VS Code-compatible package channel for Theia"
    else:
        channel = "JetBrains Marketplace via Gradle IntelliJ Plugin"
    return f"""# Mekong {host} Package Build

Generated from the Mekong command fabric catalog.

## Build

```bash
./build-package.sh
```

## Channel

{channel}
"""


def materialize_ide_build_plan(root: Path, host: BuildPlanHost) -> list[IdeBuildPlanArtifact]:
    """Write build-plan artifacts into a generated IDE package root."""
    script_path = root / "build-package.sh"
    readme_path = root / "BUILD.md"
    script_path.write_text(build_package_script(host), encoding="utf-8")
    script_path.chmod(0o755)
    readme_path.write_text(build_readme(host), encoding="utf-8")
    return [
        IdeBuildPlanArtifact("build-script", script_path.as_posix(), host),
        IdeBuildPlanArtifact("build-readme", readme_path.as_posix(), host),
    ]


__all__ = [
    "BuildPlanHost",
    "IdeBuildPlanArtifact",
    "build_package_script",
    "build_readme",
    "materialize_ide_build_plan",
]
