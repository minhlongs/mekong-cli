---
description: "ZenOS Commons governance — proposals, voting, charter"
argument-hint: "[proposal|vote|charter|status] [args]"
---

# /govern — ZenOS Commons Governance

## Usage

### Proposals
```
/govern proposal submit "Title" "Description" --type soft|operational|foundational
/govern proposal list [--status pending|active|passed]
/govern proposal status <id>
```

### Voting
```
/govern vote <proposal-id> yes|no|abstain
```

### Charter
```
/govern charter          # View ZenOS Commons charter
```

### Status
```
/govern status           # Show governance state
```

## Proposal Types

| Type | Threshold | Cooling | Examples |
|------|-----------|---------|----------|
| Soft | >50% | 3 days | Guidelines, best practices |
| Operational | >66% | 7 days | Rules, parameter changes |
| Foundational | >75% | 14 days | Charter amendments |

## Implementation
- proposal: `node scripts/zenos-proposal.cjs submit <title> <desc> --type <type>`
- vote: `node scripts/zenos-proposal.cjs vote <id> <choice>`
- list: `node scripts/zenos-proposal.cjs list [--status <filter>]`
- charter: `cat docs/zenos-commons.md`
