# Implementation Plan: Phases 199-202 Maritime Wreck, LLMC, Salvage & Penalties Suite

- **Engine Module**: `src/core/maritime_wreck_llmc_salvage_engine.py` (pure standard library only, 0 external deps).
- **CLI Commands**: `src/cli/commands/maritime_wreck_llmc_salvage_command.py` (`wreck`/`trucvot`, `llmc`/`gioihanbt`, `salvage`/`cuuho`, `maritimepen`/`xuphatbien`).
- **App Setup**: Register 4 new Typer app groups in `src/cli/app_setup.py`.
- **FastMCP Handlers**: Wire tools in `scripts/mcp_server.py`.
- **Comprehensive Test Suite**: `tests/test_maritime_wreck_llmc_salvage_suite.py` covering AST invariants, engine calculations, Typer CliRunner commands, and FastMCP tool invocations.
