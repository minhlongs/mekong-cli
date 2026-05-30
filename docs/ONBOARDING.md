# 🚀 Developer Onboarding Guide
**Mekong CLI / AgencyOS — Developer & Agent Onboarding**

Welcome to the team! This onboarding guide will help you understand the codebase, get your local environment running, and make your first contribution.

---

## 1. Quick Sandbox Setup

Start by configuring your system and running baseline tests to make sure your local workspace is functional.

1.  **Prepare Python 3.11 virtualenv**:
    ```bash
    make venv
    source .venv/bin/activate
    ```
2.  **Install Node dependencies & build**:
    ```bash
    pnpm install
    pnpm run build
    ```
3.  **Run Quick Validation Suite**:
    ```bash
    .venv/bin/pytest tests/seed/ -v --tb=short
    ```
    All 69 tests must return green.

---

## 2. Codebase Conventions

When writing code or adding command routing layers, adhere to the following principles:

*   **DRY (Don't Repeat Yourself)**: Shared utilities (such as LLM calls or path utilities) live in `src/core/`. Do not duplicate helper modules.
*   **KISS (Keep It Simple, Stupid)**: Avoid over-engineering command flows. Simple Typer scripts and clean async FastAPI routes are preferred.
*   **Preserve Documentation**: Do not remove existing docstrings or file headers unless explicitly requested.
*   **Vietnamese vs. English Rules**: System messages, CLI help summaries, and Binh Pháp strategic logs visible to the user may display Vietnamese. However, all source code comments, function names, classes, test frameworks, and developer guides must remain in English.

---

## 3. Contribution Workflow

Follow this sequence for implementing changes:

1.  **Branch Creation**: Create a branch off `main` for your feature.
2.  **Define Spec**: If introducing a new CLI command, add its markdown spec under `.claude/commands/` first.
3.  **Implementation**: Write clean python modules in `src/commands/` or routing hooks.
4.  **Tests**: Write corresponding pytest modules inside `tests/core/` and verify they pass.
5.  **Quality Gates**: Run contract generation and schema checks:
    ```bash
    make regenerate
    ```
6.  **Pull Request**: Submit your code for integration review.
