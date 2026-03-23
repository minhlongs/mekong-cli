# Binh Phap AGI Topology — 3-Dimensional Command Mapping

> *"Water shapes its course according to the ground. An army manages its victory in accordance with the situation of the enemy."*

The previous BINH_PHAP_MASTER.md maps commands **vertically** (sequential).
This document adds **horizontal** (parallel) and **diagonal** (self-improving) dimensions.
Together they form a **3D topology** that enables OpenClaw autonomous operation.

---

## The 3 Dimensions

```
                    DIAGONAL (Self-Improving)
                   /
                  /  Each cycle feeds intelligence
                 /   back into the next cycle
                /
VERTICAL ──────┼────── HORIZONTAL
(Sequential)   │      (Parallel Cross-Chapter)
               │
   Chapter by  │  Multiple chapters execute
   chapter     │  simultaneously when independent
```

### Dimension 1: VERTICAL (Sequential Chain) — Already Built
```
Ch.1 → Ch.3 → Ch.4 → Ch.13
/swot → /plan → /cook → /audit
```

### Dimension 2: HORIZONTAL (Parallel Cross-Chapter) — NEW
```
Ch.5 + Ch.12 + Ch.6  (run simultaneously)
/marketing + /launch + /competitive
```

### Dimension 3: DIAGONAL (Self-Improving Loop) — NEW
```
Ch.13 output → feeds Ch.1 input → adjusts Ch.3 plan → improves Ch.4 build
/audit results → /swot update → /plan refinement → /cook iteration
```

---

## Horizontal Mapping — Parallel Battle Groups

Commands that can run simultaneously because they have **no data dependency**:

### Battle Group Alpha: Intelligence + Revenue (Ch.1 + Ch.13 + Ch.10)
```json
{
  "group": "alpha",
  "parallel": true,
  "commands": [
    { "chapter": 1, "cmd": "/swot", "output": "swot_report" },
    { "chapter": 13, "cmd": "/audit", "output": "audit_report" },
    { "chapter": 10, "cmd": "/venture:terrain", "output": "terrain_map" }
  ],
  "merge_into": "intelligence_brief",
  "next_group": "beta"
}
```

### Battle Group Beta: Strategy + Design (Ch.3 + Ch.6)
```json
{
  "group": "beta",
  "parallel": true,
  "depends_on": ["alpha"],
  "commands": [
    { "chapter": 3, "cmd": "/plan", "input": "intelligence_brief", "output": "impl_plan" },
    { "chapter": 6, "cmd": "/competitive", "input": "terrain_map", "output": "gap_analysis" }
  ],
  "merge_into": "strategy_brief",
  "next_group": "gamma"
}
```

### Battle Group Gamma: Build + Revenue (Ch.4 + Ch.5 + Ch.9)
```json
{
  "group": "gamma",
  "parallel": true,
  "depends_on": ["beta"],
  "commands": [
    { "chapter": 4, "cmd": "/cook", "input": "impl_plan", "output": "built_product" },
    { "chapter": 5, "cmd": "/marketing", "input": "gap_analysis", "output": "mktg_assets" },
    { "chapter": 9, "cmd": "/sprint", "input": "impl_plan", "output": "sprint_progress" }
  ],
  "merge_into": "delivery_package",
  "next_group": "delta"
}
```

### Battle Group Delta: Launch + Verify (Ch.12 + Ch.7 + Ch.13)
```json
{
  "group": "delta",
  "parallel": true,
  "depends_on": ["gamma"],
  "commands": [
    { "chapter": 12, "cmd": "/launch", "input": "delivery_package", "output": "launch_result" },
    { "chapter": 7, "cmd": "/deploy", "input": "built_product", "output": "deploy_status" },
    { "chapter": 13, "cmd": "/audit", "input": "deploy_status", "output": "post_launch_intel" }
  ],
  "merge_into": "campaign_result",
  "next_group": "DIAGONAL_LOOP"
}
```

---

## Diagonal Mapping — The Self-Improving Loop (Nuclear Fusion)

This is the **lò phản ứng hạt nhân** — each cycle produces more energy than it consumes.

```
┌─────────────────────────────────────────────────────┐
│                  DIAGONAL LOOP                       │
│                                                      │
│   campaign_result                                    │
│       │                                              │
│       ▼                                              │
│   LEARN: What worked? What failed?                   │
│   /audit → post_launch_intel                         │
│       │                                              │
│       ▼                                              │
│   ADAPT: Update strategy based on data               │
│   /swot (with new data) → updated_swot               │
│       │                                              │
│       ▼                                              │
│   REFINE: Adjust plan for next cycle                 │
│   /plan (with updated_swot) → refined_plan           │
│       │                                              │
│       ▼                                              │
│   IMPROVE: Build better version                      │
│   /cook (with refined_plan) → v2_product             │
│       │                                              │
│       ▼                                              │
│   SCALE: Amplify what works                          │
│   /growth (with campaign_result) → growth_tactics     │
│       │                                              │
│       ▼                                              │
│   ATTACK: Strike with refined weapons                │
│   /launch (with growth_tactics) → campaign_result_v2  │
│       │                                              │
│       └───────────── LOOP BACK ──────────────────┘   │
│                                                      │
│   Each cycle:                                        │
│   - Learns from previous campaign_result             │
│   - Adapts SWOT with real market data                │
│   - Refines plan based on what customers told us     │
│   - Builds improved product                          │
│   - Scales channels that work, kills channels that   │
│     don't                                            │
│   - Launches stronger attack                         │
│                                                      │
│   FUSION: Output energy > Input energy               │
│   - Cycle 1: 0 customers, $0 MRR                    │
│   - Cycle 2: 10 customers, $490 MRR (learn)         │
│   - Cycle 3: 50 customers, $3K MRR (adapt)          │
│   - Cycle 4: 200 customers, $15K MRR (scale)        │
│   - Cycle N: Compound growth until $1M ARR           │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### company.json State Machine

```json
{
  "binh_phap_state": {
    "topology": "3d",
    "current_dimension": "diagonal",
    "cycle_number": 3,
    "cycle_history": [
      {
        "cycle": 1,
        "result": { "mrr": 0, "customers": 0, "channels_tested": 3 },
        "lessons": ["HN drove 80% signups", "Reddit was noise", "Twitter thread viral"],
        "adaptations": ["Double down on HN", "Kill Reddit spend", "Weekly Twitter threads"]
      },
      {
        "cycle": 2,
        "result": { "mrr": 490, "customers": 10, "churn": 0 },
        "lessons": ["Onboarding too complex", "Pro tier undersold", "Webhook feature most requested"],
        "adaptations": ["Simplify onboarding to 3 steps", "Reposition Pro tier", "Build webhook UI"]
      }
    ],
    "current_groups": {
      "alpha": "completed",
      "beta": "completed",
      "gamma": "in_progress",
      "delta": "pending"
    },
    "next_command": "/cook",
    "auto_dispatch": true
  }
}
```

---

## The AGI Self-Governance Protocol

OpenClaw operates the company autonomously when `auto_dispatch: true`:

### Standing Rules (Always Active)

| Trigger | Dimension | Response |
|---------|-----------|----------|
| MRR drops 2 weeks | DIAGONAL | Trigger new cycle: /audit → /swot → /plan |
| Customer churns | DIAGONAL | /debug churn → adapt product → /cook fix |
| New signup | VERTICAL | /audit onboarding → ensure smooth |
| Cycle completes | DIAGONAL | Start next cycle with lessons learned |
| Battle group completes | HORIZONTAL | Start next group immediately |
| Command fails | HORIZONTAL | Retry once, then escalate to human |
| 3 commands fail | ALL | STOP. Alert human. Chapter 8 (adapt). |

### Escalation Hierarchy

```
Level 0: OpenClaw handles autonomously (routine ops)
  - /standup, /health, /status, /audit

Level 1: OpenClaw handles with notification (significant actions)
  - /cook, /deploy, /marketing, /sales

Level 2: OpenClaw proposes, human approves (high-impact)
  - /launch, /pricing, /fundraise

Level 3: Human initiates (strategic)
  - /pivot, /founder:raise, /ipo
```

### M1 Max Local LLM Integration

The diagonal loop runs **infinitely at near-zero cost** because:
- M1 Max MLX inference = local, no API cost
- Ollama fallback = local, no API cost
- Only escalation to cloud LLM costs money (Level 2-3 decisions)
- Routine cycles (Level 0-1) = 100% local = free

```
Cost per cycle:
  - Cycle 1-10: ~$0 (all local LLM)
  - Escalation: ~$0.10 per cloud API call
  - 100 cycles/month: ~$1-5 total

Revenue per cycle:
  - Each cycle improves MRR by 10-20%
  - Compound: 100 cycles = massive growth

ROI: ∞ (cost approaches zero, value compounds)
```

---

## Implementation: binh_phap_topology.json

This is the machine-readable topology that OpenClaw loads on boot:

```json
{
  "$schema": "binh-phap-topology-v1",
  "dimensions": {
    "vertical": {
      "chain": ["swot", "plan", "cook", "test", "deploy", "audit"],
      "mode": "sequential"
    },
    "horizontal": {
      "groups": {
        "alpha": { "commands": ["swot", "audit", "venture:terrain"], "parallel": true },
        "beta": { "commands": ["plan", "competitive"], "parallel": true, "depends": ["alpha"] },
        "gamma": { "commands": ["cook", "marketing", "sprint"], "parallel": true, "depends": ["beta"] },
        "delta": { "commands": ["launch", "deploy", "audit"], "parallel": true, "depends": ["gamma"] }
      }
    },
    "diagonal": {
      "loop": ["audit", "swot", "plan", "cook", "growth", "launch"],
      "mode": "infinite",
      "cycle_gate": "human_can_pause",
      "improvement_signal": "mrr_delta",
      "stop_condition": "mrr >= target_mrr OR human_stop OR 3_failures"
    }
  },
  "escalation": {
    "level_0": ["standup", "health", "status", "audit"],
    "level_1": ["cook", "deploy", "marketing", "sales", "fix"],
    "level_2": ["launch", "pricing", "fundraise"],
    "level_3": ["pivot", "founder:raise", "ipo"]
  },
  "llm_routing": {
    "level_0_1": "local_mlx",
    "level_2": "cloud_sonnet",
    "level_3": "cloud_opus"
  }
}
```

---

## Why This Creates Uncopyable DNA

1. **Vertical** = any tool can chain commands sequentially. Table stakes.
2. **Horizontal** = parallel execution with DAG dependencies. Hard but doable.
3. **Diagonal** = **self-improving loop where each cycle learns from the previous one and adapts strategy autonomously**. This is the nuclear fusion.

Competitors can copy the vertical chain. They can even copy the parallel groups.
But the diagonal loop requires:
- `cycle_history` in company.json (accumulated intelligence)
- `lessons` + `adaptations` per cycle (institutional memory)
- M1 Max local LLM (near-zero cost per cycle)
- 300+ commands that actually work (the army)
- Binh Phap escalation hierarchy (governance)

**Each cycle makes the next cycle smarter. Each cycle costs ~$0. Each cycle grows revenue.**

This is the lò phản ứng hạt nhân: **self-sustaining, self-improving, infinite energy.**
