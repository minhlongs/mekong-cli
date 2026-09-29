---
name: particle
description: >-
  ZenOS particle lifecycle management, behavior graph, and AI cells.
---

# /particle — ZenOS Autonomous Particle Lifecycle, AI Cell Runtime & Behavior Graph Engine

Serving as the atomic agency, peer-to-peer trust topology, and constitutional cell execution runtime for sovereign AI operators, `mekong particle` manages particle identities, trust graphs, collusion diagnostics, and autonomous AI cell invocations.

## Architecture

```
mekong particle
        │
        ├── init [NAME]       ── Scaffolds ZenOS particle directory & registers identity in .mekong/particle.db
        ├── list              ── Lists registered particles with trust ratings & status
        ├── status [ID]       ── Network connections, trust scores, recent behaviors & collusion check
        ├── connect [A] [B]   ── Establishes bidirectional trust edge between two particles
        ├── cell run [ROLE]   ── Executes autonomous AI cell (strategist, compliance, executor, evaluator)
        └── graph             ── Low-level behavior graph, collusion analysis & audit ledger
```

## Usage

```bash
// turbo
mekong particle [OPTIONS]
```

### Options & Subcommands

| Command | Arguments / Flags | Description |
|---------|-------------------|-------------|
| `mekong particle` | `[--json]` | Overview dashboard with active particles, connections, and AI cell metrics. |
| `mekong particle init` | `<name> [--mission TEXT] [--template skel] [--dry-run] [--json]` | Scaffold and register a new ZenOS particle with constitutional mission. |
| `mekong particle list` | `[--status active\|dormant\|revoked\|all] [--limit N] [--json]` | List registered ZenOS particles with trust scores and missions. |
| `mekong particle status` | `<particle_id_or_name> [--json]` | Inspect particle network status, trust connections, and collusion risk. |
| `mekong particle connect` | `<particle_a> <particle_b> [--json]` | Establish bidirectional trust relationship between two particles. |
| `mekong particle cell run`| `<role> --prompt TEXT [--particle DIR] [--auto-compliance]` | Execute autonomous AI cell in constitutional sandbox. |

## MCP Tools Integration

The Particle engine provides 4 native MCP tools for programmatic multi-agent coordination:

1. **`mekong_particle_init(name: str, mission: str = "", template: str = "skel")`**:
   Create and register a new ZenOS particle with constitutional mission statement.

2. **`mekong_particle_status(particle_id: str = "default")`**:
   Retrieve network status, active connections, trust ratings, and collusion diagnostics.

3. **`mekong_particle_connect(particle_a: str, particle_b: str, trust_score: float = 50.0)`**:
   Establish a verified bidirectional trust edge between two sovereign particles.

4. **`mekong_particle_cell_run(role: str, prompt: str, particle_id: str = "default", auto_compliance: bool = False)`**:
   Execute an autonomous AI cell role within particle constitutional context.

Both FastMCP and pure-Python stdio JSON-RPC 2.0 engines support 100% parity.
