# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Python and container package-manager templates for Mekong CLI."""

from __future__ import annotations


def bun_package_json(command_count: int) -> str:
    return f"""{{
  "name": "mekong-cli",
  "version": "0.0.0",
  "description": "Mekong command fabric CLI with {command_count} command definitions",
  "type": "module",
  "license": "BSL-1.1",
  "bin": {{
    "mekong": "bin/mekong.js"
  }},
  "files": [
    "bin",
    "src",
    "pyproject.toml",
    "README.md"
  ],
  "engines": {{
    "bun": ">=1.0.0"
  }},
  "os": [
    "darwin",
    "linux",
    "win32"
  ]
}}
"""


def deno_config(command_count: int) -> str:
    return f"""{{
  "name": "mekong-cli",
  "version": "0.0.0",
  "license": "BSL-1.1",
  "description": "Mekong command fabric CLI with {command_count} command definitions",
  "tasks": {{
    "install": "deno install --global --allow-run --allow-read --name mekong ./mekong.ts"
  }}
}}
"""


def deno_bin() -> str:
    return """const packageRootUrl = new URL('..', import.meta.url)
const packageRoot = decodeURIComponent(packageRootUrl.pathname)

const command = new Deno.Command('python3', {
  args: ['-m', 'src.main', ...Deno.args],
  cwd: packageRoot,
  stdin: 'inherit',
  stdout: 'inherit',
  stderr: 'inherit',
})

const status = await command.spawn().status
Deno.exit(status.code)
"""


def npm_global_package_json(command_count: int) -> str:
    return f"""{{
  "name": "mekong-cli",
  "version": "0.0.0",
  "description": "Mekong command fabric CLI with {command_count} command definitions",
  "type": "module",
  "license": "BSL-1.1",
  "bin": {{
    "mekong": "bin/mekong.js"
  }},
  "files": [
    "bin",
    "src",
    "pyproject.toml",
    "README.md"
  ],
  "engines": {{
    "node": ">=18"
  }},
  "os": [
    "darwin",
    "linux",
    "win32"
  ]
}}
"""


def npm_global_bin() -> str:
    return """#!/usr/bin/env node
import { spawnSync } from 'node:child_process'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..')

const result = spawnSync('python3', ['-m', 'src.main', ...process.argv.slice(2)], {
  cwd: packageRoot,
  stdio: 'inherit',
})

process.exit(result.status ?? 1)
"""


def pypi_project_metadata(command_count: int) -> str:
    return f"""[project]
name = "mekong-cli"
version = "0.0.0"
description = "Mekong command fabric CLI with {command_count} command definitions"
readme = "README.md"
requires-python = ">=3.9,<3.13"
license = {{ text = "BSL-1.1" }}
authors = [{{ name = "Mekong", email = "support@mekongmind.com" }}]
dependencies = []

[project.scripts]
mekong = "src.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""


def dockerfile(command_count: int) -> str:
    return f"""FROM python:3.12-slim

LABEL org.opencontainers.image.title="Mekong CLI"
LABEL org.opencontainers.image.description="Mekong command fabric CLI with {command_count} command definitions"
LABEL org.opencontainers.image.source="https://github.com/longtho638-jpg/mekong-cli"

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir .

ENTRYPOINT ["mekong"]
CMD ["--help"]
"""


__all__ = [
    "bun_package_json",
    "deno_bin",
    "deno_config",
    "dockerfile",
    "npm_global_bin",
    "npm_global_package_json",
    "pypi_project_metadata",
]
