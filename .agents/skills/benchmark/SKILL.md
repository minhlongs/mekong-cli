---
name: benchmark
description: >-
  ⚡ Autonomous Benchmark & Chaos Suite — stress-test PEV, checkpoints, subagents, and fault resilience.
---

# /benchmark — Autonomous Benchmark & Chaos Resilience Suite

Runs deterministic performance benchmarks and simulated chaos fault injections
across PEV planning, atomic checkpoints, subagents, and memory systems.

## Usage

```bash
# Run all benchmark suites with default settings
mekong benchmark

# Run specific suite (pev, checkpoints, subagents, chaos)
mekong benchmark --suite pev --iterations 5
mekong benchmark --suite checkpoints --iterations 3

# Inject simulated chaos faults (low, medium, high)
mekong benchmark --suite chaos --chaos-level high

# Machine-readable JSON output for headless CI/CD & MCP tools
mekong benchmark --json --suite all
```

## Suites

1. **PEV (`--suite pev`)**: Measures plan decomposition latency, task sequencing, and verification DAG generation.
2. **Checkpoints (`--suite checkpoints`)**: Benchmarks atomic snapshot creation and state rollback speeds.
3. **Subagents (`--suite subagents`)**: Measures agent registry inspection and context budget limit compliance.
4. **Chaos (`--suite chaos`)**: Simulates SQLite snapshot corruption, tool execution timeouts, and malformed JSON payloads to verify autonomous self-healing.

## Options

- `-s, --suite`: Benchmark suite to run (`pev`, `checkpoints`, `subagents`, `chaos`, `all`). Default: `all`.
- `-n, --iterations`: Number of benchmark iterations per test. Default: `5`.
- `-c, --chaos-level`: Chaos injection intensity (`none`, `low`, `medium`, `high`). Default: `none`.
- `--json`: Format output as JSON for headless pipelines.
