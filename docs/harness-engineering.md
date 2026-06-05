# Mekong Harness Engineering

> CEO Solo Agentic Harness Engineering Platform

Mekong treats the harness as the operating system around agents: guides
before action, sensors after action, and a steering loop that decides the next
move. This follows the Fowler/Thoughtworks harness model and the Hermes-style
closed learning loop, then uses Binh Phap as the company operating doctrine.

## Core DNA

The official feature surface is declared in [`dna/core-dna.json`](../dna/core-dna.json).
The manifest is public, but it is also the runtime contract:

- `feedforward`: `HARNESS.md`, SOPs, registry, and Core DNA manifest.
- `feedback`: tests, evals, observability, and CI workflows.
- `steering`: PEV, Binh Phap topology, and event reactions.
- `contribution gate`: unknown new features require PR evidence before use.

This keeps the code open while making new capability adoption reviewable by
the owner and community. It does not claim forks are technically impossible;
it makes the official Mekong runtime reject unreviewed feature surfaces.

Runtime enforcement lives in:

- `src/core/core_dna.py`: manifest loading and feature-gate decisions.
- `src/core/core_dna.py`: SHA-256 attestation over immutable Core DNA roots.
- `src/core/command_authorizer.py`: blocks undeclared local commands before
  license/gateway checks.
- `src/harness/core/control_loop.py`: projects Core DNA into guides, sensors,
  steering controls, and Hermes learning capabilities.
- `dna/binh-phap-operating-system.json`: maps 13 Binh Phap chapters into the
  CEO, revenue, product, engineering, and ops layers.
- `dna/hermes-learning-loop.json`: declares persistent memory, scoped memory,
  procedural memory, MCP gateway, and skill-surface requirements.
- `dna/command-surface.json`: declares the reviewed root CLI command surface;
  command additions must update this manifest through PR.
- `src/binh_phap/operating_system.py`: validates chapter coverage, agent
  registry references, and SOP paths.
- `src/harness/learning_loop.py`: validates the Hermes-style closed learning
  loop against local runtime files.
- `src/core/command_surface.py`: validates current Typer root commands against
  the reviewed command-surface manifest.
- `src/harness/evals/solo_ceo.py`: deterministic EVAL-07/EVAL-08 runner for
  Core DNA, Binh Phap doctrine, attestation, Hermes loop, and command-surface guarantees.
- `.github/workflows/core-dna-gate.yml`: requires manifest updates when PRs
  touch command/feature surfaces, then runs `harness-eval --json`.

## Source Anchors

- Martin Fowler / Thoughtworks:
  <https://martinfowler.com/articles/harness-engineering.html>. Harness =
  model plus surrounding controls, feedforward + feedback, steering loop,
  keep quality left.
- Hermes Agent docs: <https://hermes-agent.nousresearch.com/docs/>. Closed
  learning loop, skills, persistent memory, MCP, safe tool gateways, portable
  execution.
- Binh Phap: terrain-aware execution, intelligence before action, momentum
  through orchestrated battle groups.

## Runtime Check

```bash
python3 -m src.main binh-phap dna
python3 -m src.main binh-phap dna --attest
python3 -m src.main binh-phap dna --feature cook-auto-parallel
python3 -m src.main binh-phap dna --feature private-local-updater
python3 -m src.main binh-phap doctrine
python3 -m src.main harness-eval --json
```

See [HARNESS.md](../HARNESS.md) for the runtime contract.
See [agents/registry.yaml](../agents/registry.yaml) for agent definitions.
See [sops/](../sops/) for Standard Operating Procedures.
See [evals/](../evals/) for the eval suite.
See [observability/](../observability/) for traces and dashboards.
