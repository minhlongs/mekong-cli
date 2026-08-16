# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Installer registry templates for Mekong CLI package-manager metadata."""

from __future__ import annotations


def aqua_registry(command_count: int) -> str:
    return f"""# Mekong CLI aqua registry metadata with {command_count} command definitions.
packages:
  - type: github_release
    repo_owner: longtho638-jpg
    repo_name: mekong-cli
    asset: mekong_{{{{.OS}}}}_{{{{.Arch}}}}.tar.gz
    description: Mekong command fabric CLI
    files:
      - name: mekong
        src: mekong
"""


def pkgx_package_yml(command_count: int) -> str:
    return f"""# Mekong CLI pkgx/tea package metadata with {command_count} command definitions.
distributable:
  url: https://github.com/longtho638-jpg/mekong-cli/archive/refs/tags/v{{{{version}}}}.tar.gz
  strip-components: 1

versions:
  github: longtho638-jpg/mekong-cli

dependencies:
  python.org: ">=3.9<3.13"

build:
  script: |
    python3 -m pip install --prefix "$PREFIX" .

provides:
  - bin/mekong
"""


__all__ = ["aqua_registry", "pkgx_package_yml"]
