# ZenOS Commons Governance

> Version: 0.1.0 | Status: Draft | Last revised: 2026-07-04

## Charter

The ZenOS Commons governs the mekong-cli ecosystem: protocol upgrades, treasury allocation, dispute resolution, and constitutional amendments. It exists to prevent capture - by founders, large contributors, or external actors - while enabling evolution.

## Members

- **Founder**: 1 vote (veto power on foundational issues only)
- **Contributor**: Weighted by contribution (commits^0.5, capped at 10x)
- **Holder**: Token-weighted (future, post-launch)

Anti-concentration: No single member may control >25% of voting power.

## Tripartite Separation

1. **Legislation** — Proposal submission + voting
2. **Execution** — Guardian AI Cell executes approved proposals
3. **Adjudication** — Dispute resolution via Guardian mediation → Community vote

## Proposal Types

| Type | Threshold | Cooling Period | Examples |
|------|-----------|----------------|----------|
| Soft | Simple majority | 3 days | Guidelines, best practices |
| Operational | 2/3 supermajority | 7 days | Rules, parameter changes |
| Foundational | 3/4 supermajority | 14 days | Charter amendments |

## Anti-Capture Mechanisms

| Mechanism | Prevents |
|-----------|----------|
| Term limits (Guardian: max 2 terms) | Entrenched leadership |
| Right to fork (any member can fork with data) | Protocol capture |
| Transparent treasury on SQLite ledger | Embezzlement |
| Sunset clause (charter expires 5 years) | Zombie Commons |
| Contribution-weighted voting | Investor capture |

## Voting

- Base: 1 vote per member
- Quorum: 3 (soft), 5 (operational), 7 (foundational)
- Voting period: 7 days for all types
- Pass: meets threshold AND quorum

## Implementation

Proposals: `node scripts/zenos-proposal.cjs`
State: `.mekong/commons/proposals.json`
Commands: `/govern proposal`, `/govern vote`, `/govern status`
