# Mekong CLI — Code Standards & Engineering Guidelines

## Core Principles

1. **Constitutional Alignment**: Adhere to `CLAUDE.md` and Binh Phap core engineering DNA.
2. **Quality Gates**: All code changes must pass linting (`ruff check`) and the full pytest suite.
3. **Typing & Clarity**: Strict type hints across all Python modules (`src/core`, `src/cli`, `src/agents`).
4. **Resilience & Fault Tolerance**: Defensive error handling, explicit fallbacks, and zero unhandled network or I/O exceptions.
5. **No Regressions**: Existing registered command groups and MCP tool endpoints must remain intact and verified.

## Python Style & Standards

- **Python Version**: Python 3.9+ compatible system Python.
- **Formatter & Linter**: Ruff for style checking and format enforcement.
- **Imports**: Grouped cleanly (standard library, third-party, local package imports).
- **Naming Conventions**:
  - Modules & packages: `snake_case.py`
  - Classes: `PascalCase`
  - Functions & variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
  - Test files: `test_*.py`

## Testing Standards

- Unit tests must be placed under `tests/` or `tests/unit/`.
- Use isolated mocks (`unittest.mock.patch`) for external services and DB operations.
- Maintain deterministic execution without live network dependencies in test fixtures.
- Pytest timeouts should be respected (target < 60s per test).
