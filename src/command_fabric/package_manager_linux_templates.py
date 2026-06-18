"""Linux portable package templates for Mekong CLI."""

from __future__ import annotations


def snapcraft_yaml(command_count: int) -> str:
    return f"""name: mekong-cli
base: core24
version: "0.0.0"
summary: Mekong command fabric CLI
description: |
  Mekong command fabric CLI with {command_count} command definitions.
grade: stable
confinement: strict

apps:
  mekong:
    command: bin/mekong
    plugs:
      - home
      - network

parts:
  mekong:
    plugin: python
    source: .
"""


def flatpak_manifest(command_count: int) -> str:
    return f"""app-id: io.mekongmind.MekongCLI
runtime: org.freedesktop.Platform
runtime-version: "24.08"
sdk: org.freedesktop.Sdk
command: mekong
finish-args:
  - --share=network
  - --filesystem=home
modules:
  - name: mekong-cli
    buildsystem: simple
    build-commands:
      - python3 -m pip install --prefix=/app .
    sources:
      - type: dir
        path: .
# Mekong command fabric CLI with {command_count} command definitions.
"""


def appimage_apprun() -> str:
    return """#!/usr/bin/env bash
set -euo pipefail

APPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="${APPDIR}/usr/bin:${PATH}"
exec "${APPDIR}/usr/bin/mekong" "$@"
"""


def appimage_desktop(command_count: int) -> str:
    return f"""[Desktop Entry]
Type=Application
Name=Mekong CLI
Exec=mekong
Icon=mekong-cli
Categories=Development;Utility;
Terminal=true
Comment=Mekong command fabric CLI with {command_count} command definitions
"""


def appimage_readme(command_count: int) -> str:
    return f"""# Mekong CLI AppImage AppDir

AppDir scaffold for Mekong CLI with {command_count} command definitions.

Build with:

```bash
appimagetool MekongCLI.AppDir
```
"""


__all__ = ["appimage_apprun", "appimage_desktop", "appimage_readme", "flatpak_manifest", "snapcraft_yaml"]
