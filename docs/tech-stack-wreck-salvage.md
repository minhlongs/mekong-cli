# Tech Stack Specification: Maritime Wreck Removal, LLMC, Salvage & Penalties (Phases 199-202)

## 1. Architectural Philosophy
Strict alignment with the Mekong CLI autonomous runtime standards:
- **Zero External Dependencies**: Pure Python standard library only (`dataclasses`, `datetime`, `enum`, `math`, `typing`, `json`, `hashlib`, `re`).
- **Deterministic AST Invariant**: Validated via Python `ast.parse` unit test ensuring no third-party package runtime imports in the domain engine.
- **Fail-Closed Statutory Validation**: Strict boundary checks against Vietnam Maritime Code 2015, Decree 58/2017/NĐ-CP, Decree 162/2016/NĐ-CP & Decree 123/2021/NĐ-CP, LLMC 1976/1996, and LOF 2024 / SCOPIC guidelines.

## 2. Technology Choices & Justifications

| Layer | Technology | Version / Spec | Justification |
| :--- | :--- | :--- | :--- |
| **Language Runtime** | Python | 3.9+ / 3.11 System Python | Cross-platform compatibility, standard system runtime on Darwin / Linux |
| **Domain Logic** | Standard Library Dataclasses & Enums | Pure Python stdlib | Zero runtime overhead, serialized determinism, immutable state transitions |
| **CLI Framework** | Typer + Rich | CLI layer | Existing Mekong CLI standard (`app_setup.build_app()`), Rich ANSI console tables & JSON output |
| **MCP Integration** | FastMCP / JSON-RPC | In-process Server | High-performance tool interface for external AI orchestrators and Claude Desktop |
| **Test Engine** | Pytest | System pytest runner | Deterministic test assertions, AST static inspection, Typer `CliRunner` verification |

## 3. Module Boundaries & Interfaces
- **Engine Layer**: `src/core/maritime_wreck_llmc_salvage_engine.py`
  - `MaritimeWreckRemovalEngine`: 30-day notice, 60-day salvage start, auction waterfall, 300 GT WRC compulsory insurance.
  - `MaritimeLLMCEngine`: IMO 2012 SDR brackets for Personal Injury (Art. 302) and Property (Art. 303), Art. 304 pro-rata rollover, limitation fund constitution, willful intent exception gate.
  - `MaritimeSalvageSCOPICEngine`: Art. 13 "No Cure - No Pay" 10-criteria ceiling, SCOPIC 2024 tariff + 25% bonus, Sub-clause 6 discount clawback.
  - `MaritimeSanctionEngine`: Decree 162/2016 & 123/2021 penalty brackets (pilotage, draft, speed, pollution, accident reporting), certificate suspension, port departure block flag.
- **CLI Commands**: `src/cli/commands/maritime_wreck_llmc_salvage_command.py`
  - Groups: `wreck` (alias `trucvot`), `llmc` (alias `gioihanbt`), `salvage` (alias `cuuho`), `maritimepen` (alias `xuphatbien`).
- **MCP Server Tools**: `scripts/mcp_server.py`
  - Handlers: `handle_wreck_removal_audit`, `handle_llmc_calculate`, `handle_salvage_scopic_evaluate`, `handle_maritime_penalty_assess`.
