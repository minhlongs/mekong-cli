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

- **Python**: type hints, docstrings, files strictly under 200 lines
- **Tests**: pytest for all new modules in `tests/`
- **Commits**: conventional format (feat/fix/docs/refactor/test/chore)
- **No secrets** — use `.env` (see `.env.example`), never commit credentials

## Open-Core Architecture Boundary (`src/` MIT vs `apps/`/`billing/` Commercial)

- **Public MIT Open-Source (`src/`, `tests/`, `docs/`)**: Core autonomous runtime, CLI commands, BYOK local adapters, and deterministic verification engines are licensed under the MIT License.
- **Commercial / Private Boundary (`apps/`, `app/`, `billing/`)**: Client-specific deployments, hosted multi-tenant SaaS billing planes, and enterprise operational vaults are strictly isolated from the public Git index via `.gitignore`.
- **`src/core/` Stdlib & Provider Neutrality**: Core modules must remain provider-neutral and respect `tests/test_core_boundary.py`.

## Contributor License Agreement (CLA)

By submitting a pull request or contribution to this repository, you agree to the **Contributor License Agreement (CLA)**:
1. You certify that your contribution is your original work and that you have the right to grant this license.
2. You grant MekongMind and project maintainers a perpetual, worldwide, non-exclusive, royalty-free, irrevocable license to use, reproduce, modify, sublicense, and distribute your contribution under both the public **MIT License** and commercial SaaS/Enterprise distributions.

## Trademark Policy

The **Trademark Policy** governs the use of the **Mekong CLI**, **MekongMind**, and **Sophia AI Factory** names, logos, and brand assets:
- The MIT License grants rights to use, modify, and distribute the source code, but **does not** grant any rights to use project trademarks or trade dress for commercial SaaS reselling or confusingly similar forks without prior written permission.

PRs must pass CI: tests, ruff, mypy, and Open-Core readiness hygiene checks.
