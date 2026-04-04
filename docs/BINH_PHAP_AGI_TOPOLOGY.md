# Binh Pháp AGI Topology — Battle Group Architecture

## 3D Execution Model

```
Horizontal (→): Command DAGs execute in parallel groups
Vertical (↓):   Results feed metrics and learning
Diagonal (↗):   Metrics improve commands (self-improving loop)
```

## Battle Groups (α → η)

```json
{
  "horizontal": {
    "groups": {
      "alpha": {
        "name": "Intelligence & Assessment",
        "commands": ["swot", "risk:assess", "venture:terrain", "intel:blind-spot"],
        "parallel": true,
        "depends": [],
        "chapter": "始計 — Initial Calculations"
      },
      "beta": {
        "name": "Strategy & Planning",
        "commands": ["plan", "pm:roadmap", "pm:competitor", "venture:thesis"],
        "parallel": true,
        "depends": ["alpha"],
        "chapter": "謀攻 — Attack by Stratagem"
      },
      "gamma": {
        "name": "Execution & Build",
        "commands": ["eng:sprint-execute", "marketing:campaign-run", "sales:pipeline-build"],
        "parallel": true,
        "depends": ["beta"],
        "chapter": "作戰 — Waging War"
      },
      "delta": {
        "name": "Delivery & Audit",
        "commands": ["ship", "sec:full-audit", "qa:regression", "compliance:sox-cycle"],
        "parallel": true,
        "depends": ["gamma"],
        "chapter": "軍形 — Disposition of Forces"
      },
      "epsilon": {
        "name": "Infrastructure & Observability",
        "commands": ["obs:dashboard", "infra:topology", "gateway:route", "sre:morning-check"],
        "parallel": true,
        "depends": ["delta"],
        "chapter": "地形 — Terrain"
      },
      "zeta": {
        "name": "Market Intelligence & Positioning",
        "commands": ["cdp:profile", "terrain:segment", "revops:pipeline", "growth:channel-optimize"],
        "parallel": true,
        "depends": ["epsilon"],
        "chapter": "九地 — Nine Terrains"
      },
      "eta": {
        "name": "Momentum & Scale",
        "commands": ["momentum:velocity", "momentum:compound", "pm:feature-flag", "ml:deploy"],
        "parallel": true,
        "depends": ["zeta"],
        "chapter": "兵勢 — Momentum"
      }
    }
  },
  "vertical": {
    "metrics_flow": [
      "execution_time → optimize_dag_parallelism",
      "error_rate → retrain_prompts",
      "human_override_rate → escalation_calibration",
      "credit_cost → budget_allocation"
    ]
  },
  "diagonal": {
    "self_improvement": [
      "metrics → factory-intelligence → command_tuning",
      "audit_findings → sec:policy → auto_remediation",
      "customer_health → cdp:journey → product_priorities"
    ]
  }
}
```

## Escalation Hierarchy

```json
{
  "level_0": ["health", "status", "daily", "sre:morning-check", "cto-dashboard", "obs:*", "worker:health"],
  "level_1": ["worker:*", "dev:*", "eng:*", "qa:*", "data:daily-pipeline", "ml:eval", "writer:*", "kb:*"],
  "level_2": ["ship", "release:*", "finance:*", "sec:incident", "compliance:*", "ml:deploy", "ir:narrative", "board:manage", "treasury:*"],
  "level_3": ["ipo:*", "governance:*", "corpdev:integrate", "venture:thesis", "terrain:retreat", "sec:incident-response"]
}
```

## Chapter Mapping (Complete 13-Chapter Art of War)

| # | Chinese | English | Domain | Commands |
|---|---------|---------|--------|----------|
| 1 | 始計 | Initial Calculations | Strategy/Planning | 52 |
| 2 | 作戰 | Waging War | Business/Revenue | 71+ |
| 3 | 謀攻 | Attack by Stratagem | DevRel/KB/Product | 12+ |
| 4 | 軍形 | Disposition of Forces | Data Platform | 8+ |
| 5 | 兵勢 | Momentum | Scaling/Growth | 5 |
| 6 | 虛實 | Void and Substance | Context/Intel | 5 |
| 7 | 軍爭 | Military Contention | PM/RevOps | 15+ |
| 8 | 九變 | Nine Variations | Intl/ESG/Workflow/Incident | 16+ |
| 9 | 行軍 | Army on the March | Security/QA/IAM/IT | 33+ |
| 10 | 地形 | Terrain | Infra/Obs/Gateway | 13+ |
| 11 | 九地 | Nine Terrains | Market Positioning | 5 |
| 12 | 火攻 | Fire Attack | AI/ML Ops | 11+ |
| 13 | 用間 | Use of Intelligence | Governance/IR/CDP | 14+ |
