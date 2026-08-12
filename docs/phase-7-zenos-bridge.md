# Phase 7: ZenOS Bridge

> Particle-Aware Plugin Execution and Economic Accounting

**Last Updated**: 2026-06-21  
**Status**: Completed  
**Related**: [Zenos Migration Guide](zenos-migration-guide.md), [Economic Particles](economic-particles.md), [Constitutional AI](constitutional-ai.md)

---

## Overview

Phase 7 integrates the plugin system with ZenOS — the constitutional operating system for one-person companies. This bridge enables particle-aware execution, economic accounting, and constitutional governance for all plugin operations.

### Objectives

- Convert plugin invocations to economic particles
- Apply constitutional AI review to plugin actions
- Track plugin economics per particle
- Enable particle-based access control
- Support particle lifecycle (birth → active → dissolve)

---

## ZenOS Architecture

### What is ZenOS?

ZenOS is the operating system for one-person companies, built on:

1. **Economic Particles** — Immutable financial events
2. **Constitutional AI** — 9-principle ethical review
3. **Founder Genome** — Encrypted psychological profile
4. **Behavior Graph** — Knowledge graph of entity relationships
5. **Treasury** — Multi-currency fund management

### Plugin Integration Points

```
┌────────────────────────────────────────────────┐
│              Plugin executes command           │
└────────────────┬───────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────┐
│           ZenOS Bridge (Phase 7)               │
│  • Create particle                             │
│  • Constitutional review                      │
│  • Deduct MCU credits                         │
│  • Record to immutable ledger                 │
└────────────────┬───────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────┐
│         Economic Particle Created              │
│  { id, type, mission, constitution,           │
│    founder, treasury, trust_score, ... }      │
└────────────────────────────────────────────────┘
```

---

## Particle Creation

### Every Plugin Invocation Creates a Particle

When a plugin command executes:

```python
# Before Phase 7
result = await plugin.execute("annual", {"year": 2025})

# After Phase 7
particle = await zenos_bridge.execute(
    plugin_id="mekong-core-founder",
    command="annual",
    payload={"year": 2025},
    user_id="opc_001_abc123"
)
# Returns particle with economic record
```

### Particle Schema

```python
class EconomicParticle(BaseModel):
    id: UUID
    type: ParticleType  # "opc" | "cooperative" | "micro_enterprise"
    mission: str
    constitution: Constitution
    founder: FounderGenome
    behavior_graph: BehaviorGraphRef
    treasury: Treasury
    trust_score: int  # 0-100
    
    # This execution
    command: str
    plugin: str
    mcu_cost: int
    timestamp: datetime
    result: dict
```

---

## Constitutional AI Review

### 9-Principle Evaluation

Every plugin action is scored against:

1. **Human Dignity First** — Humans > AI > Capital
2. **AI as Assistant** — AI serves, doesn't command
3. **Transparency** — All decisions explainable
4. **Freedom to Exit** — No lock-in
5. **Anti-Extraction** — Fair value exchange
6. **Micro-Enterprise First** — Solo founders primary
7. **Mission Alignment** — Revenue serves mission
8. **Polycentric Governance** — Multiple jurisdictions
9. **Right to Repair** — Owners control infrastructure

### Review Process

```python
async def constitutional_review(particle: Particle, action: dict) -> ReviewResult:
    scores = {}
    
    for principle in PRINCIPLES:
        score = await evaluate_principle(principle, particle, action)
        scores[principle.id] = score
    
    overall = sum(scores.values()) / len(scores)
    
    if overall < 0.7:
        return ReviewResult(
            approved=False,
            score=overall,
            warnings=[f"Low score on {p}" for p, s in scores.items() if s < 0.5]
        )
    
    return ReviewResult(approved=True, score=overall)
```

Configuration per particle:

```json
{
  "constitution": {
    "principle_weights": {
      "human_dignity_first": 1.2,
      "anti_extraction": 1.0,
      "mission_alignment": 0.8
    },
    "thresholds": {
      "min_overall": 0.7,
      "min_per_principle": 0.4
    }
  }
}
```

---

## Economic Accounting

### MCU Deduction per Particle

```python
class AccountingService:
    async def deduct_for_particle(self, particle: Particle):
        # Get particle's treasury
        treasury = await self.get_treasury(particle.id)
        
        # Check balance
        if treasury.balance < particle.mcu_cost:
            raise InsufficientFundsError()
        
        # Deduct
        deduction = EconomicParticle(
            type="mcu_deduction",
            amount=-particle.mcu_cost,
            currency="MCU",
            description=f"Plugin: {particle.plugin}.{particle.command}",
            reference_id=particle.id
        )
        
        await treasury.add_particle(deduction)
        await self.record_immutable(particle)
```

### Treasury Management

Each particle has a treasury:

```python
class Treasury:
    id: UUID
    balance: dict  # {"MCU": 1000, "USD": 49.00, "VND": 1199000}
    allocation_rules: list[AllocationRule]
    transaction_history: list[ParticleRef]
```

Allocation rules automate fund distribution:

```json
{
  "rules": [
    {
      "source": "income",
      "targets": [
        {"treasury": "operational", "percentage": 0.6},
        {"treasury": "investment", "percentage": 0.3},
        {"treasury": "reserve", "percentage": 0.1}
      ]
    }
  ]
}
```

---

## Trust Score Calculation

Plugin executions affect particle trust score:

```python
def calculate_trust_score(particle: Particle) -> int:
    factors = {
        "success_rate": particle.success_rate * 30,
        "constitutional_compliance": particle.avg_constitutional_score * 25,
        "timely_payment": particle.payment_punctuality * 20,
        "community_contribution": particle.community_contrib * 15,
        "transparency": particle.transparency_score * 10
    }
    
    return sum(factors.values())
```

Trust score affects:
- Credit limits
- Priority execution
- Marketplace visibility
- Investor matching

---

## Behavior Graph Integration

### Knowledge Graph of Relationships

Every particle interaction updates the behavior graph:

```python
# When plugin A talks to plugin B
await behavior_graph.record_interaction(
    source=particle_a.id,
    target=particle_b.id,
    relationship="invoked",
    properties={
        "command": "annual",
        "duration_ms": 45,
        "result": "success"
    }
)

# Graph queries enable:
# - Recommendation engine (plugins you might need)
# - Anomaly detection (unusual invocation patterns)
# - Impact analysis (what breaks if plugin X fails)
```

---

## Migration from Tenants

### Tenant → Particle Migration

Existing tenant accounts are automatically migrated:

```bash
# Run migration script
python3 scripts/migrate-tenants-to-particles.py

# For each tenant:
# 1. Create particle with tenant data
# 2. Attach default constitution
# 3. Initialize treasury with balance
# 4. Set trust_score based on tenant history
# 5. Migrate all records as particles
```

Backwards compatible: tenant IDs still work, internally mapped to particle IDs.

---

## Configuration

### Enable ZenOS Bridge

```json
// ~/.mekong/settings.json
{
  "zenos": {
    "enabled": true,
    "bridge_mode": "strict",  // "strict" | "permissive" | "audit-only"
    "particle_auto_create": true,
    "default_constitution": "zenos-default"
  }
}
```

### Bridge Modes

| Mode | Behavior |
|------|----------|
| `strict` | All executions require particle; reject without |
| `permissive` | Create particle if missing, log warning |
| `audit-only` | Don't enforce, just record for audit |

---

## API Changes

### New Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /v1/particles` | Create new particle |
| `GET /v1/particles/{id}` | Get particle details |
| `POST /v1/particles/{id}/constitution/review` | Review against constitution |
| `GET /v1/particles/{id}/treasury` | Get treasury balance |
| `POST /v1/particles/{id}/treasury/allocate` | Allocate funds |
| `GET /v1/behavior-graph/query` | Query behavior graph |

### Updated Execute Endpoint

```http
POST /v1/execute

# Now requires particle context
{
  "particle_id": "opc_001_abc123",  // NEW
  "plugin": "mekong-core-founder",
  "command": "annual",
  "payload": {"year": 2025}
}

# Response includes particle
{
  "particle_id": "part_xyz789",
  "result": {...},
  "constitutional_score": 0.87,
  "mcu_deducted": 2,
  "treasury_balance": {"MCU": 998, "USD": 49.00}
}
```

---

## Monitoring

### ZenOS Metrics

```
# Particle creation rate
zenos_particles_created_total{type="opc"}

# Constitutional review scores
zenos_constitutional_score_bucket{principle="human_dignity"}

# Treasury operations
zenos_treasury_transactions_total{type="income|expense|transfer"}

# Trust score distribution
zenos_trust_score_bucket
```

### Grafana Dashboard

`grafana/zenos-bridge.json` includes:
- Particle creation timeline
- Constitutional compliance heatmap
- Treasury balance trends
- Trust score distribution
- Plugin execution by particle type

---

## Testing

### Unit Tests

```bash
# Test particle creation
pytest tests/zenos/test_particle_creation.py

# Test constitutional review
pytest tests/zenos/test_constitutional_review.py

# Test treasury operations
pytest tests/zenos/test_treasury.py

# Test migration
pytest tests/zenos/test_migration_tenant_to_particle.py
```

### Integration Tests

```bash
# Full bridge integration
pytest tests/zenos/test_zenos_bridge_integration.py

# With real D1 database
pytest tests/zenos/test_d1_integration.py --integration
```

---

## Rollback

If ZenOS Bridge causes issues:

```bash
# Disable bridge
jq '.zenos.enabled = false' ~/.mekong/settings.json > tmp && mv tmp ~/.mekong/settings.json

# Restart gateway
mekong platform restart gateway

# System falls back to legacy execution (no particles)
# Existing particles remain intact
```

To re-enable:
```bash
jq '.zenos.enabled = true' ~/.mekong/settings.json > tmp && mv tmp ~/.mekong/settings.json
mekong platform restart gateway
```

---

## Troubleshooting

### Particle Not Created

```bash
# Check bridge mode
mekong admin config get zenos.enabled

# Check logs
mekong admin logs --component zenos-bridge --level error --tail 50

# Verify D1 database connection
mekong admin health check-d1
```

### Constitutional Review Blocking

```bash
# Temporarily set permissive mode
jq '.zenos.bridge_mode = "permissive"' ~/.mekong/settings.json > tmp && mv tmp ~/.mekong/settings.json

# Review blocked actions
mekong admin zenos review-failures --last 24h

# Adjust constitution if needed
mekong admin constitution update <particle_id> --threshold 0.6
```

---

## Next Steps

Phase 7 completes the core platform evolution. Post-Phase 7 work:

1. **Plugin Marketplace** — enable third-party plugin publishing
2. **Advanced Analytics** — particle-based business intelligence
3. **Multi-Particle Operations** — cross-particle transactions
4. **ZenOS Mobile** — iOS/Android client

See also:
- [Zenos Migration Guide](zenos-migration-guide.md)
- [Economic Particles](economic-particles.md)
- [Constitutional AI](constitutional-ai.md)
- [Founder Genome](founder-genome.md)
