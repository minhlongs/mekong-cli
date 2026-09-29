---
name: consensus
description: >-
  🗳️ Multi-Agent Consensus Protocol & Swarm Debate — quorum voting, structured debates, and audit ballots.
---

# /consensus — Multi-Agent Consensus Protocol & Swarm Debate

Coordinates multi-agent voting (majority, supermajority, unanimous, and weighted roles),
structured thesis-antithesis-synthesis debates between domain agents (e.g. CTO vs SRE),
and cryptographic SHA-256 ballot ledger persistence in SQLite (`.mekong/consensus.db`).

## Usage

```bash
# Execute a quorum vote with default agents (CEO, CTO, CFO, PM, SRE)
mekong consensus vote "Migrate mission state storage from SQLite to PostgreSQL"

# Vote with custom quorum (majority, supermajority, unanimous, weighted)
mekong consensus vote "Promote release candidate v6.1.0 to production" --quorum supermajority

# Specify participating agents
mekong consensus vote "Allocate 30% of quarterly budget to growth campaigns" --agents ceo,cfo,cmo --quorum weighted

# Output machine-readable JSON ballot
mekong consensus vote "Deprecate legacy endpoints" --json

# Conduct a structured debate between technical roles
mekong consensus debate "Should we break the monolith into independent microservices?" --proponent cto --opponent sre

# View recent consensus ballots and debate history
mekong consensus history
mekong consensus history --json
```

## Features

1. **Quorum Rules**:
   - `majority`: > 50% affirmative votes.
   - `supermajority`: ≥ 66.6% affirmative votes.
   - `unanimous`: 100% affirmative votes (zero negative votes).
   - `weighted`: Authority-weighted threshold (CEO=3, CTO=2, CFO=2, PM=1, SRE=1).
2. **Multi-Round Structured Debate**:
   - Thesis / Antithesis / Synthesis exchange between domain roles.
   - Computes consensus score (0–100) and actionable architectural synthesis.
3. **Cryptographic Ledger**:
   - Every ballot calculates a SHA-256 hash across canonical vote JSON and persists to `.mekong/consensus.db`.
4. **Gateway Event Streaming**:
   - Emits real-time SSE and WebSocket events (`consensus_proposal_created`, `consensus_vote_cast`, `consensus_resolved`).

## Options

- `-a, --agents`: Comma-separated list of participating agent roles.
- `-q, --quorum`: Quorum mode (`majority`, `supermajority`, `unanimous`, `weighted`).
- `-p, --proponent`: Proponent agent role for debates (default: `cto`).
- `-o, --opponent`: Opponent agent role for debates (default: `sre`).
- `-m, --moderator`: Moderator agent role (default: `ceo`).
- `-r, --rounds`: Number of debate rounds (default: `2`).
- `--json`: Output machine-readable JSON telemetry.
