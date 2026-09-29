---
name: founder
description: >-
  Founder genome assessment: TIPI-10 Big Five personality traits, Schwartz values, risk tolerance dimensions, cognitive bias extraction, and team archetype analysis.
---

# /founder — Founder Genome Assessment & Psychometric Profiling Engine

The `mekong founder` engine provides a comprehensive psychometric assessment and profiling system for solo agency operators and founding teams. It integrates the TIPI-10 Big Five instrument, Schwartz Core Values Inventory, 5-dimensional risk profiling, 10-factor cognitive bias detection, and synthetic archetype classification with SQLite WAL persistence.

## Usage

```bash
// turbo
mekong founder [COMMAND] [OPTIONS]
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| *(none / overview)* | Display founder psychometric distributions, active archetypes, and recent assessments. |
| `assess` | Assess a founder genome and store results with psychometric score normalization. |
| `review <founder_id>` | Load and display a complete founder genome profile and risk breakdown. |
| `list` | List all assessed founders in the registry with optional risk level filtering. |
| `analyze <founder_id>` | Synthesize psychometric strengths, potential blindspots, and team pairing recommendations. |

## Options & Flags

- `--name, -n`: Founder identifier or handle.
- `--mission, -m`: Stated purpose or company mission.
- `--tipi`: JSON string mapping TIPI-10 question IDs (`tipi_01` to `tipi_10`) to Likert ratings (1-7).
- `--values`: JSON array of Schwartz value IDs (e.g. `["self_direction", "achievement"]`).
- `--fears`: JSON array of fear trigger objects with predicted behaviors and mitigations.
- `--risk`: JSON dict of risk ratings across dimensions (`financial`, `operational`, `reputational`, `compliance`, `technical`).
- `--biases`: JSON dict of cognitive bias presence indicators (`bias_confirmation`, `bias_overconfidence`, etc.).
- `--risk, -r` (on `list`): Filter by risk level (`conservative`, `moderate`, `aggressive`, `all`).
- `--limit, -l`: Maximum number of results to display (default 50).
- `--json, -j`: Output machine-readable JSON for automated agent pipelines and CI/CD.

## Native MCP Tools

The engine exposes 3 dual FastMCP and JSON-RPC 2.0 tools:

1. `mekong_founder_assess(name, mission, tipi_responses, values, fears, risk_ratings, bias_responses, particle_id)`: Perform and persist founder assessment.
2. `mekong_founder_review(founder_id)`: Retrieve detailed founder genome profile.
3. `mekong_founder_list(risk_level, limit)`: Query assessed founder catalog.
