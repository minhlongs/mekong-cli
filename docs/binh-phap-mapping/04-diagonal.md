# Phần 4: Diagonal Dispatch — Nuclear Fusion Feedback Loop

> Status: DRAFT

## 1. Brainstorm Contract (reuse P1)
Outcome: Diagonal loop documented with MRR tracking, cycle learning, and auto_dispatch spec.
Constraints: (1) Loop stops at target_mrr (2) Max 3 consecutive failures (3) Lessons persist across cycles
Non-goals: (1) No automatic budget spending (2) No auto-pivot without human approval
Acceptance: Loop state machine + lesson schema + MRR event format

## 2. Current State (topology.py)
DIAGONAL_LOOP = ["audit", "swot", "plan", "cook", "growth:experiment", "launch"]
CycleLesson: {cycle, mrr, customers, channels_tested, lessons[], adaptations[]}

Pain:
- Loop is static list, no adaptive ordering
- channels_tested field exists but never populated
- No link between adaptations -> next cycle
- No stop condition for "diminishing returns"

## 3. Proposed Architecture

### 3.1 Loop State Machine
```
START -> execute_loop -> record_lesson -> check_continue
    |
    +-- continue -> next_cycle
    |
    +-- pause (target reached) -> STOP
    |
    +-- stop (3x failure) -> ESCALATE
```

### 3.2 MRR Event Schema (.mekong/revenue_events/)
{
  "tx_id": "tx_001",
  "amount": 1000.0,
  "customer_id": "cust_abc",
  "product_id": "prod_xyz",
  "timestamp": "2026-07-25T...",
  "source_command": "launch",
  "chapter": 12
}

### 3.3 Cycle Learning Schema
{
  "cycle": 5,
  "mrr": 2500.0,
  "customers": 25,
  "channels_tested": 3,          # NEW: populate from growth:experiment
  "lessons": ["email open rate low", "CTA weak"],
  "adaptations": ["rewrite CTA", "A/B test subject line"],
  "diminishing_returns": false,  # NEW
  "next_cycle_focus": [5, 11]   # NEW: chapters to emphasize next
}

## 4. Trade-off
| A: Fixed loop | B: Adaptive loop (REC) | C: AI-generated loop |
|--------------|------------------------|----------------------|
| Predictable | Learns from history | Most adaptive |
| No optimization | Medium complexity | Black box |
| **REC** | | |

## 5. Recommendation
Approach B (Adaptive loop):
1. Record lessons + adaptations after each cycle
2. Compute diminishing_returns flag (delta_mrr < 5% threshold)
3. next_cycle_focus = recommend chapters based on weakest MRR signals
4. Stop loop if: target_mrr reached OR 3x failure OR diminishing_returns x 3

## 6. Handoff to P5
Infrastructure: Jidoka self-healing + PEV orchestrator integration + ZuneF auth.
