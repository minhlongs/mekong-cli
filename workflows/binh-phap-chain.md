---
name: binh-phap-chain
description: "Auto-execute 13 Binh Phap chapters in sequence with status tracking"
trigger: "/binh-phap chain"
owner: COO
agents: [founder, ceo, cfo, cto, cmo, cso, coo, chro]
---

# Binh Phap Auto-Chain

Executes 13 chapters in Binh Phap order. Each chapter spawns an agent.

## Chain Order

| # | Chapter | Layer | Agent | Command |
|---|---------|-------|-------|---------|
| 1 | Strategy Assessment | L2 CEO | CEO | /swot |
| 2 | Operations Runway | L3 COO | COO | /audit |
| 3 | Win-Without-Fighting | L5 CSO | CSO | /market |
| 4 | Position Moat | L4 CTO | CTO | /audit-tech |
| 5 | Momentum Growth | L5 CMO | CMO | /campaign |
| 6 | Anti-Dilution | L1 Founder | Founder | /cap-table |
| 7 | Speed Sprint | L5 CSO | CSO | /competitive |
| 8 | Pivot Workshop | L2 CEO | CEO | /brainstorm |
| 9 | OKR Movement | L3 COO | COO | /okr |
| 10 | Market Entry | L4 CTO | CTO | /deploy |
| 11 | Crisis Situations | L1 Founder | Founder | /risk |
| 12 | Disruption Attack | L5 CSO | CSO | /launch |
| 13 | Competitive Intel | L5 CMO | CMO | /intel |

## Error Recovery
- Chapter fail → auto-retry 1x
- Retry fail → skip chapter, log reason
- 3 consecutive fails → pause chain, notify Founder

## Status
Check: `/binh-phap chain --status`
State file: `.mekong/binh-phap-state.json`
