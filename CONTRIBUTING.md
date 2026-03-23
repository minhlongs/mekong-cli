# Contributing to Mekong CLI

## Setup

```bash
git clone https://github.com/longtho638-jpg/mekong-cli.git
cd mekong-cli
pnpm install

# TypeScript packages
cd packages/mekong-cli-core && pnpm test    # 1,263 tests
cd packages/openclaw-engine && pnpm test     # Engine tests

# Python (requires Python 3.11+)
pip install -r requirements.txt
python3 -m pytest tests/ -q
```

## Adding a Command

1. Create `.claude/commands/your-command.md` with frontmatter
2. Create `factory/contracts/commands/your-command.json` with typed I/O schema
3. Run: `python3 factory/self_test.py` (must pass)
4. Submit PR

## Adding a Skill

1. Create `.claude/skills/your-skill/SKILL.md`
2. Run factory self-test
3. Submit PR

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
| Test Suite | `vitest run` on all packages (1,263 tests) |
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
