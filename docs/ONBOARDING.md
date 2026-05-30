# 🚀 Developer Onboarding Guide
**Mekong CLI / AgencyOS — Developer & Agent Onboarding**

Welcome to the team! This onboarding guide will help you understand the codebase, get your local sandbox running, and understand key system conventions.

---

## 1. Sandbox Setup Checklist

Follow these steps to configure your local sandbox environment and run baseline verification tests:

- [ ] **Prepare Python 3.11 Virtual Environment**:
  Initialize the `.venv` and activate it:
  ```bash
  make venv
  source .venv/bin/activate
  ```
- [ ] **Install and Build Node.js Workspace Packages**:
  Install all workspace dependencies using `pnpm` and compile the TS/JS modules:
  ```bash
  pnpm install
  pnpm run build
  ```
- [ ] **Execute Quick Validation Suite**:
  Run the seed verification tests to confirm basic functionality:
  ```bash
  .venv/bin/pytest tests/seed/ -v --tb=short
  ```
  Ensure all seed tests pass cleanly (showing a green status).

---

## 2. Core Conventions

When writing code, introducing routing layers, or creating new CLI commands, developers must adhere to the following principles:

*   **DRY (Don't Repeat Yourself)**: Shared helper utilities (such as LLM integrations, environment variable parsing, or file path helpers) must reside in `src/core/` or dedicated utility packages. Do not duplicate helper modules.
*   **KISS (Keep It Simple, Stupid)**: Avoid over-engineering orchestrator loops or CLI routing interfaces. Clear Typer scripts and clean async FastAPI routers are preferred.
*   **Preserve Documentation**: Do not remove existing docstrings, header blocks, or strategic comments unless explicitly instructed.
*   **Vietnamese vs. English Rules**: 
    - **Developer Surface (Source Code)**: All source code (variable names, classes, function signatures), test suites, developer guides, and inline comments must remain strictly in English.
    - **User Surface (Logs/UI)**: Strategic user-facing panels, strategic logs, Binh Pháp strategical logs, and CLI output dashboards can display Vietnamese or bilingual (Vietnamese/English) summaries to the user.

---

## 3. Contribution Workflow

When implementing changes:
1.  **Branch Creation**: Create a branch off `main` for your feature.
2.  **Define Spec**: If introducing a new command, add its markdown spec under `.claude/commands/` first.
3.  **Implementation**: Write clean python modules in `src/commands/` or routing hooks.
4.  **Tests**: Write corresponding pytest modules inside `tests/core/` and verify they pass.
5.  **Quality Gates**: Run contract generation and schema checks:
    ```bash
    make regenerate
    ```
6.  **Pull Request**: Submit your code for integration review.
