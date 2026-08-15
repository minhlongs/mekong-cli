# Contributing to Mekong CLI

## Setup

```bash
git clone https://github.com/minhlongs/mekong-cli.git
cd mekong-cli
poetry install
```

## Commands

```bash
poetry run mekong --help
python3 -m pytest tests/ -q
python3 -m ruff check src/ tests/
python3 -m mypy src/
```

## Standards

- **Python**: type hints, docstrings, files under 200 lines
- **Tests**: pytest for all new modules in `tests/`
- **Commits**: conventional format (feat/fix/docs/refactor/test/chore)
- **No secrets** — use `.env`, never commit credentials

## Structure

```
src/           Python PEV engine + agents
tests/         Python test suite
engine/        Billing, license, payments
```

PRs must pass CI: tests, ruff, and mypy.