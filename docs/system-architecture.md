# System Architecture — Mekong Dispute Resolution & Maritime Law Suite

## 1. High-Level Architecture

The Mekong Dispute Resolution & Maritime Law Suite extends Mekong CLI v6.0 with four dedicated legal and maritime calculation engines compliant with Vietnamese statutes and international maritime conventions.

```
+-------------------------------------------------------------------------------+
|                                 CLIENT SURFACES                                |
|  +-------------------------------+   +--------------------------------------+  |
|  | CLI Terminal (Typer + Rich)   |   | MCP Server (JSON-RPC + FastMCP)      |  |
|  | mekong dispute <command>      |   | claude_ai / cursor / windsurf tools  |  |
|  +---------------+---------------+   +------------------+-------------------+  |
+------------------|--------------------------------------|---------------------+
                   |                                      |
+------------------v--------------------------------------v---------------------+
|                             ROUTING & ADAPTER LAYER                           |
|  - src/cli/commands/dispute_command.py (CLI Options & Formatting)             |
|  - scripts/mcp_server.py (JSON-RPC Tools: handle_dispute_*)                   |
+------------------+--------------------------------------+---------------------+
                   |                                      |
+------------------v--------------------------------------v---------------------+
|                            CORE ENGINE DOMAIN LAYER                           |
|             (100% Python Standard Library - Zero External Dependencies)        |
|                                                                               |
|  +--------------------------------+   +------------------------------------+  |
|  | src/core/dispute_engine.py     |   | src/core/maritime_law_engine.py    |  |
|  |                                |   |                                    |  |
|  | - CommercialArbitrationEngine  |   | - MaritimeLawEngine                |  |
|  |   * VIAC 2024 Fee Scale        |   |   * Carrier Liability (Hague-Visby)|  |
|  |   * Clause Validity & Risks    |   |   * General Average (York-Antwerp) |  |
|  |   * 2-Year Limitation Period   |   |   * Salvage Rewards (No Cure No Pay|  |
|  |                                |   |   * Maritime Liens Priority Ranking|  |
|  | - CivilEnforcementEngine       |   +------------------------------------+  |
|  |   * 5-Year Statute Check       |                                           |
|  |   * 3% Fee & 200M Cap          |                                           |
|  |   * Article 47 Priority Queue  |                                           |
|  |                                |                                           |
|  | - CourtLitigationEngine        |                                           |
|  |   * District vs Provincial     |                                           |
|  |   * Resolution 326 Fee Scale   |                                           |
|  |   * 50% Court Fee Advance      |                                           |
|  +--------------------------------+                                           |
+-------------------------------------------------------------------------------+
```

## 2. Key Modules & Boundaries

1. **`src/core/dispute_engine.py`**:
   - Zero-dependency Python standard library implementation.
   - Enforces statutory rules for arbitration, judgment enforcement, and court litigation.

2. **`src/core/maritime_law_engine.py`**:
   - Zero-dependency Python standard library implementation.
   - Enforces Vietnam Maritime Code 2015, Hague-Visby SDR limits, and York-Antwerp 2016 General Average zero-sum balance.

3. **`src/cli/commands/dispute_command.py`**:
   - Rich terminal interface with tables, panels, and machine-readable `--json` flags.
   - Aliased under both `dispute` and `tranhchap`.

4. **`scripts/mcp_server.py`**:
   - Dual-protocol (FastMCP + JSON-RPC) tool definitions for agentic workflows.
