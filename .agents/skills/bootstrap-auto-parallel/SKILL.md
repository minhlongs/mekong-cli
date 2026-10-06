---
name: bootstrap-auto-parallel
description: Autonomous Parallel Project Bootstrap Engine with multi-worker dependency DAG orchestration, workspace scaffolding, and atomic rollback.
---

# /bootstrap-auto-parallel — Autonomous Parallel Project Bootstrap Engine

The Autonomous Parallel Project Bootstrap Engine scaffolds end-to-end Mekong CLI and Google Antigravity workspaces concurrently using a dependency DAG (`ThreadPoolExecutor`), multi-worker task orchestration, domain template scaffolding, and atomic failure checkpointing with automatic rollback.

## CLI Invocation

```bash
// turbo
mekong bootstrap-auto-parallel [GOAL] [OPTIONS]
```

### Arguments

- `[GOAL]` *(string, optional)*: High-level goal or mission description for the project being scaffolded (e.g., `"Scaffold Enterprise VAS Platform"`).

### Options

| Option | Flag | Type | Default | Description |
|---|---|---|---|---|
| `--workers` | `-w` | `integer` | `4` | Number of concurrent worker threads (1–32) for DAG task execution. |
| `--profile` | `-p` | `string` | `standard` | Scaffolding verification profile: `smoke`, `standard`, or `full`. |
| `--template` | `-t` | `string` | `default` | Project domain template preset: `default`, `vas`, `fintech`, or `agent`. |
| `--target`, `--path` | | `path` | `.` | Target directory for the workspace root. |
| `--dry-run` | | `boolean` | `false` | Preview dependency DAG and target files without mutating disk. |
| `--json` | `-j` | `boolean` | `false` | Emit structured JSON execution telemetry for CI/CD and subagents. |
| `--force` | `-f` | `boolean` | `false` | Overwrite existing workspace files; default skips pre-existing files safely. |

---

## Profiles

The engine supports three validation profiles controlling scaffolding depth and verification intensity:

1. **`smoke`**:
   - Minimal latency verification pipeline.
   - Scaffolds essential project layout and governance files (`AGENTS.md`, `GEMINI.md`, `HARNESS.md`).
   - Runs fast AST and structure sanity checks.
   - Ideal for rapid testing, temporary sandbox environments, and CI healthchecks.

2. **`standard`** *(default)*:
   - Full enterprise-grade project scaffolding.
   - Scaffolds directories (`src/`, `tests/`, `.agents/skills/`, `.agents/subagents/`, `dna/`, `reports/`).
   - Configures baseline subagents, native Antigravity skills, lifecycle hooks, and MCP servers (`mcp_config.json`).
   - Populates chosen domain template files with full unit test coverage.
   - Verifies harness contracts and AST core boundaries.

3. **`full`**:
   - Comprehensive production-ready initialization.
   - Includes everything in `standard`, plus optional local git repository initialization (`git init`), pre-commit hooks, and extensive end-to-end verification.
   - Executes thorough integrity audits and generates execution telemetry reports.

---

## Template Presets

Select domain-specific architecture templates via `--template`:

1. **`default`**:
   - Generic standard Python application structure (`src/main.py`, `tests/test_main.py`).
   - Core governance files (`GEMINI.md`, `AGENTS.md`, `HARNESS.md`, `pyproject.toml`).
   - Baseline subagent definitions and MCP server configurations.

2. **`vas`** *(Vietnamese Accounting Standard)*:
   - VAS accounting and e-invoicing architecture conforming to Circular 78/2021/TT-BTC.
   - Scaffolds double-entry ledger (`VasLedger`), invoice validator (`validate_invoice`), and accounting unit tests.
   - Pre-configured for VAS compliance, tax calculation, and XML invoice exports.

3. **`fintech`**:
   - Vietnamese FinTech and digital banking platform foundation.
   - Scaffolds VietQR EMVCo payload generator (`generate_vietqr_payload`), transaction reconciliation engine (`reconcile_transaction`), and PCI-DSS card masking utilities (`mask_card`).
   - Pre-configured with banking integration hooks and cryptographic checks.

4. **`agent`**:
   - Multi-agent swarm and AGI autonomous loop platform.
   - Scaffolds agent swarm dispatcher (`AgentSwarm`), memory mesh knowledge graph (`MemoryMesh`), and autonomous loop supervisor (`AgiLoop`).
   - Pre-configured with subagent communication protocols and PEV pipeline integration.

---

## Workflow Examples

### 1. Standard Parallel Bootstrap with 4 Workers
```bash
mekong bootstrap-auto-parallel "Scaffold AI Agency OS" --workers 4
```

### 2. VAS Accounting Workspace Scaffolding
```bash
mekong bootstrap-auto-parallel "VAS Invoicing System" --template vas --profile standard --target ./viet-accounting
```

### 3. Dry-Run Inspection (Zero Disk Mutation)
```bash
mekong bootstrap-auto-parallel --template fintech --dry-run --json
```

### 4. High-Concurrency Full Production Scaffolding
```bash
mekong bootstrap-auto-parallel "Autonomous Agent Mesh" --workers 8 --template agent --profile full --force
```

---

## MCP Tool Reference

The engine is exposed via dual Model Context Protocol (MCP) tools across FastMCP and pure-Python stdio JSON-RPC:

### `mekong_bootstrap_auto_parallel`
Executes autonomous parallel bootstrap within an agentic tool session.
- **Arguments**:
  - `goal` *(string, optional)*: Goal statement or mission description.
  - `workers` *(integer, optional, default: 4)*: Concurrency level (1–32).
  - `profile` *(string, optional, default: "standard")*: `smoke` | `standard` | `full`.
  - `template` *(string, optional, default: "default")*: `default` | `vas` | `fintech` | `agent`.
  - `dry_run` *(boolean, optional, default: false)*: Simulate without disk writes.
  - `force` *(boolean, optional, default: false)*: Overwrite existing files.
- **Returns**: Structured dictionary with `ok`, `rolled_back`, `duration_ms`, `created_files`, and task timings.

### `mekong_bootstrap_status`
Queries the telemetry and execution state of the most recent bootstrap run.
- **Arguments**: None.
- **Returns**: Last execution metadata, status, error (if rolled back), and timing metrics.

---

## Atomic Rollback Guarantee

If any critical task in the topological DAG fails (e.g., permission denied, disk full, cyclic dependency), the engine halts dependent execution and atomically rolls back the workspace:
- Unlinks newly created files in reverse order (LIFO).
- Restores overwritten files from pre-execution snapshots.
- Prunes newly created empty directories.
- Zero corrupted or orphaned artifacts left behind.
