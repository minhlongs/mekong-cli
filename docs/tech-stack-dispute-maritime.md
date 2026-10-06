# Tech Stack — Dispute Resolution & Maritime Law Suite (Phases 159 - 162)

## 1. Architectural Philosophy
- **Zero External Dependencies**: 100% Python Standard Library (`math`, `dataclasses`, `enum`, `datetime`, `typing`, `json`, `re`).
- **High Determinism**: Zero network calls, zero floating point variance through exact roundings, 100% reproducible test executions.
- **Unified Standard Interfaces**: Direct integration into Typer CLI (`mekong dispute` & `mekong maritime`), in-process FastMCP server, and stdio JSON-RPC MCP server.

## 2. Technology Composition
- **Runtime Core**: Python 3.9+ (`src/core/dispute_engine.py` & `src/core/maritime_engine.py`).
- **CLI Framework**: Typer & Rich for interactive terminal formatting and clean `--json` pipes (`src/cli/commands/dispute_command.py` & `src/cli/commands/maritime_command.py`).
- **MCP Integration**: Dual FastMCP & Stdio JSON-RPC tools for LLM agent integration.
- **Testing Engine**: pytest with pytest-timeout gate (< 60s target).
- **Statutory Frameworks**:
  - Law on Commercial Arbitration 2010 & VIAC Arbitration Rules 2024.
  - Law on Civil Judgment Enforcement 2008/2014 & Decree 62/2015/ND-CP.
  - Civil Procedure Code 2015 & Resolution 326/2016/UBTVQH14 (Court Fees).
  - Vietnam Maritime Code 2015, Hague-Visby Rules & York-Antwerp Rules 2016.
