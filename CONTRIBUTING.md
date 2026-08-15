# Contributing to Mekong CLI

## Setup

```bash
git clone https://github.com/longtho638-jpg/mekong-cli.git
cd mekong-cli
pnpm install

# TypeScript packages
cd packages/mekong-cli-core && pnpm test    # 1,263 TS tests
cd packages/openclaw-engine && pnpm test     # Engine tests

# Python (requires Python 3.11+)
pip install -r requirements.txt
python3 -m pytest tests/ -q
```

## Adding a Command

1. Create `.claude/commands/your-command.md` with frontmatter
2. Create `factory/contracts/commands/your-command.json` with typed I/O schema
3. Update `dna/command-surface.json` when the root CLI surface changes
4. Update `dna/core-dna.json` when the command is an official free command or advanced feature
5. Run: `python3 factory/self_test.py` (must pass)
6. Run: `python3 -m src.main harness-eval --json` (must pass)
7. Submit PR for owner/community review

## Adding a Skill

1. Create `.claude/skills/your-skill/SKILL.md`
2. Update `dna/core-dna.json` if the skill exposes a new official runtime feature
3. Run factory self-test
4. Run `python3 -m src.main harness-eval --json`
5. Submit PR for owner/community review

## Core DNA Governance

Mekong is open source, but the official runtime feature surface is locked by
public manifests in `dna/`.

- `dna/core-dna.json`: source anchors, immutable harness roots, free commands, advanced features.
- `dna/command-surface.json`: reviewed root CLI command surface.
- `dna/binh-phap-operating-system.json`: solo-company operating doctrine.
- `dna/hermes-learning-loop.json`: Hermes-style memory, skills, MCP, and learning-loop contract.

New commands, features, doctrine changes, and harness roots must go through a
pull request. Local-only bypasses are not accepted for official Mekong runtime.
The PR must pass `python3 -m src.main harness-eval --json`, and CODEOWNERS must
review changes touching `dna/`, core harness code, or GitHub workflows.

## Code Standards

- **Python**: type hints, docstrings, < 200 lines per file
- **TypeScript**: strict mode, no `any` types
- **Tests**: `pytest` for Python, `vitest` for TypeScript. No mocks for core logic.
- **Commits**: conventional format (`feat/fix/docs/refactor/test/chore`)
- **File naming**: kebab-case with descriptive names
- **No secrets** in code -- use `.env`

## CI Checks

All of these must pass before merge:

| Check | What it does |
|-------|-------------|
| Test Suite | `vitest run` (1,263 TS tests) + `pytest` (4,450 Python tests) |
| Factory Integrity | Validates 388 JSON contracts against schema |
| Security Hardening | Scans for secrets, validates attestation |
| Ruff Lint | Python linter (pre-commit hook) |

## PR Process

1. Fork and create a feature branch
2. Make changes following code standards above
3. Ensure all CI checks pass locally
4. Submit PR with conventional commit title
5. Address review feedback

## Architecture

```
.claude/commands/   206 command definitions (.md)
.claude/skills/     248 skill definitions (SKILL.md)
factory/contracts/  388 typed JSON contracts
packages/           npm packages (openclaw-engine, cli-core)
src/                Python PEV engine + agents
```
