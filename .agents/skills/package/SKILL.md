---
name: package
description: >-
  📦 Multi-Platform Packaging — generate Homebrew formula, Docker assets, and release manifests.
---

# /package — Multi-Platform Release Packaging

Builds deterministic distribution packages, Homebrew formulas, Docker multi-stage
assets, and release integrity manifests for Mekong CLI and Google Antigravity.

## Usage

```bash
# Verify release metadata and asset completeness
mekong package --verify
mekong package --verify --json

# Build all distribution artifacts into dist/
mekong package

# Build specific target (homebrew, docker, pypi, all)
mekong package --target homebrew --output-dir dist/
mekong package --target docker

# Output machine-readable JSON build manifest
mekong package --json
```

## Features

1. **Metadata & PEP Conformance**:
   - Parses `pyproject.toml` metadata, versions, licenses, and entry points.
   - Validates existence of `README.md` and `LICENSE`.
2. **Antigravity Asset Bundling**:
   - Automatically bundles `.agents/skills/`, `.agents/subagents/`, and `hooks.json` into package distributions.
3. **Homebrew Formula Generation**:
   - Synthesizes `Formula/mekong.rb` with virtualenv resources and automated smoke tests.
4. **Multi-Stage Docker & Compose**:
   - Produces minimal, hardened production Dockerfile with Gateway healthchecks and SSE/WS port exposure.

## Options

- `-o, --output-dir`: Output destination directory (default: `dist`).
- `-t, --target`: Target format (`all`, `homebrew`, `docker`, `pypi`).
- `--verify`: Verify metadata and assets without writing artifacts.
- `--json`: Output machine-readable JSON build manifest.
