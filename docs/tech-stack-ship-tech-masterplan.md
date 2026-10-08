# Tech Stack: Ship Technical, Registration, Dredging & Seaport Masterplan Suite (Phases 195-198)

## Architecture Overview
- **Core Engine**: Pure Python 3.10+ standard library (`dataclasses`, `datetime`, `enum`, `math`, `typing`, `json`, `hashlib`, `re`). Zero external runtime dependencies.
- **CLI Sub-Apps**: Typer command modules registered with rich tables, JSON output mode (`--json`), and bilingual help text.
  - Sub-app 1: `shipclass` (alias `dangkiem`) - Ship Classification & HSSC Survey Cycles.
  - Sub-app 2: `shipreg` (alias `dangky`) - Ship Registration, Bareboat Charters & Mortgages.
  - Sub-app 3: `dredging` (alias `naovet`) - Channel Maintenance Dredging & Dynamic UKC Squat.
  - Sub-app 4: `masterplan` (alias `quyhoach`) - Decision 1579/QĐ-TTg Seaport Capacity & Berth Utilization.
- **Model Context Protocol (MCP)**: FastMCP & JSON-RPC tools registered in `scripts/mcp_server.py`.
- **Test Automation**: pytest suite validating AST zero-dependency compliance, mathematical invariants, CLI command execution, and FastMCP handlers.

## Layer Contracts
1. `src/core/ship_tech_masterplan_engine.py`: Encapsulates all domain logic, statutory formulas, certificate windows, and state transitions.
2. `src/cli/commands/ship_tech_masterplan_command.py`: Handles CLI argument parsing, console output rendering, error propagation.
3. `src/cli/app_setup.py`: Wires command groups into root CLI application.
4. `scripts/mcp_server.py`: Exposes programmatic tools to external agents.
5. `tests/test_ship_tech_masterplan_suite.py`: Automated regression suite.
