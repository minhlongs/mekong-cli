---
name: governance
description: >-
  ZenOS Commons constitutional governance: draft amendment proposals, cast weighted ballots, verify tier-bound quorums, and tally outcomes.
---

# /governance — Autonomous Constitutional Governance & Voting Engine

The `mekong governance` engine provides decentralized decision-making, proposal lifecycle management, and cryptographic ballot verification for sovereign AI operators and the ZenOS Commons. It coordinates tier-bound quorum satisfaction (`soft` at 50%, `operational` at 66.7%, `foundational` at 75%) and stores immutable voting audit trails with SQLite WAL persistence.

## Usage

```bash
// turbo
mekong governance [COMMAND] [OPTIONS]
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| *(none / overview)* | Display governance engine status, tier specifications, and recent active proposals. |
| `status` | Display operational health, active voting sessions, and quorum thresholds. |
| `propose` | Draft and submit a new constitutional amendment proposal. |
| `vote` | Cast a weighted cryptographic ballot on an active governance proposal. |
| `tally` | Tally ballots, compute quorum satisfaction, and finalize proposal outcome. |
| `list` | List constitutional governance proposals with optional status and tier filtering. |

## Options & Flags

- `title`: Proposal title (argument for `propose`).
- `description`: Rationale or context (argument for `propose`).
- `text`: Exact proposed amendment text (argument for `propose`).
- `--from, -f`: Proposer or voter member ID (default `founder`).
- `--tier, -t`: Governance tier (`soft` | `operational` | `foundational`).
- `--co-sponsor`: Repeatable co-sponsor member IDs.
- `--choice, -c`: Vote option (`yes` | `no` | `abstain` | `recuse`).
- `--weight`: Voting weight or reputation multiplier (default 1.0).
- `--status, -s`: Filter proposals by status (`voting`, `passed`, `rejected`, `enacted`, `all`).
- `--json, -j`: Output machine-readable JSON for autonomous subagents and CI/CD pipelines.

## Native MCP Tools

The engine exposes 4 dual FastMCP and JSON-RPC 2.0 tools:

1. `mekong_governance_propose(title, description, text, proposer, tier, co_sponsors)`: Submit a new proposal.
2. `mekong_governance_vote(proposal_id, voter, choice, weight)`: Cast a weighted ballot.
3. `mekong_governance_tally(proposal_id)`: Compute quorum and finalize verdict.
4. `mekong_governance_list(status, tier, limit)`: Query proposals catalog.
