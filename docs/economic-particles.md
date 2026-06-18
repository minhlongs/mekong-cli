# Economic Particles

> The atomic financial unit of ZenOS — replacing tenants with composable economic identity

**Last Updated**: 2026-06-18  
**Related**: [`docs/zenos-migration-guide.md`](./zenos-migration-guide.md), [`docs/founder-genome.md`](./founder-genome.md)

---

## What Are Economic Particles?

Economic Particles are **immutable, append-only financial event records** that track every economic transaction within the ZenOS ecosystem. Unlike traditional double-entry bookkeeping, particles are:

- **Atomic**: One particle = one economic event (no bundling)
- **Immutable**: Once written, never modified (audit trail integrity)
- **Composable**: Particles aggregate into balances, statements, reports
- **Contextual**: Rich metadata links particles to missions, constitutions, behavior

### The Particle Model

```
┌─────────────────────────────────────────────────────────┐
│                    ECONOMIC PARTICLE                     │
├─────────────────────────────────────────────────────────┤
│ id: UUIDv7                                               │
│ tenant_id: Optional[str]        ← Legacy RaaS reference │
│ key_id: str                     ← Primary identifier     │
│ particle_type: Enum             ← What happened         │
│ amount: Decimal                 ← Signed (±)            │
│ currency: ISO code              │
│ balance_after: Decimal          ← Snapshot for queries  │
│ metadata: JSONB                 → {rate_card, usage...} │
│ source: Enum                    → api|manual|webhook... │
│ reference_id: Optional[str]     → External reference   │
│ created_at: DateTime (UTC)      │
│ updated_at: DateTime (UTC)      │
│ tenant_reference_id: Optional   → Multi-tenancy link   │
└─────────────────────────────────────────────────────────┘
```

---

## Particle Types

| Type | Direction | Use Case | Example |
|------|-----------|----------|---------|
| `usage` | Debit (-) | Consuming credits/API calls | `-0.5 MCU` for command execution |
| `credit` | Credit (+) | Adding funds to balance | `+$49.00` subscription payment |
| `adjustment` | Signed | Manual balance corrections | `+10.0` admin credit |
| `payment` | Credit (+) | External payment received | `+$149.00` from Stripe |
| `refund` | Credit (+) | Refund to customer | `+$29.00` refund issued |
| `fee` | Debit (-) | Platform fees deducted | `-$4.90` processing fee |
| `subscription` | Debit (-) | Recurring subscription charge | `-$49.00` monthly |

### Usage Particle Example

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "tenant_id": null,
  "key_id": "opc_001_abc123def456",
  "particle_type": "usage",
  "amount": "-2.500",
  "currency": "USD",
  "balance_after": "197.500",
  "metadata": {
    "command": "marketing:create-campaign",
    "mcu_cost": 2.5,
    "duration_ms": 4250,
    "agent": "marketing-campaign-agent"
  },
  "source": "api",
  "reference_id": null,
  "created_at": "2025-06-18T15:30:00Z",
  "updated_at": "2025-06-18T15:30:00Z"
}
```

### Credit Particle Example

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "tenant_id": null,
  "key_id": "opc_001_abc123def456",
  "particle_type": "credit",
  "amount": "49.000",
  "currency": "USD",
  "balance_after": "200.000",
  "metadata": {
    "payment_method": "stripe",
    "payment_intent_id": "pi_123456789",
    "subscription_tier": "starter",
    "invoice_id": "inv_abc123"
  },
  "source": "webhook",
  "reference_id": "pi_123456789",
  "created_at": "2025-06-18T16:00:00Z",
  "updated_at": "2025-06-18T16:00:00Z"
}
```

---

## Balance Calculation

### Real-Time Balance

```python
from decimal import Decimal
from src.models.particle import ParticleRepository

async def get_balance(key_id: str) -> Decimal:
    """Calculate current balance by summing all particles."""
    repo = ParticleRepository()
    balance = await repo.get_balance(key_id)
    return balance  # e.g., Decimal('197.50')
```

Balance = Σ(amount) for all particles with given `key_id`

### Balance with Snapshot

For performance, use the denormalized `balance_after` from the most recent particle:

```python
balance, last_particle = await repo.get_balance_with_snapshot(key_id)
# Uses last_particle.balance_after (faster, no aggregation)
```

**Trade-off**: Snapshot is faster but may be stale if async writes are in flight. Use aggregation for critical financial calculations.

### Multi-Currency Balances

Particles support multiple currencies (USD, VND, EUR):

```python
# Get balance per currency
usd_balance = await repo.get_balance(key_id, currency="USD")
vnd_balance = await repo.get_balance(key_id, currency="VND")
```

Aggregation queries filter by `currency` column.

---

## Particle Repository API

### Creating Particles

```python
from decimal import Decimal
from src.models.particle import (
    EconomicParticle,
    PARTICLE_TYPE_USAGE,
    PARTICLE_TYPE_CREDIT,
    CURRENCY_USD,
    SOURCE_API
)

particle = EconomicParticle(
    key_id="opc_001_abc123",
    particle_type=PARTICLE_TYPE_USAGE,
    amount=Decimal("-2.5"),
    currency=CURRENCY_USD,
    balance_after=Decimal("197.5"),  # Set by caller or calculated
    metadata={
        "command": "engineering:deploy",
        "agent": "deployment-agent",
        "project": "my-app"
    },
    source=SOURCE_API
)

particle_id = await repo.create_particle(particle)
```

### Querying Particles

```python
# List by key_id with filters
particles = await repo.list_particles_by_key(
    key_id="opc_001_abc123",
    particle_type=PARTICLE_TYPE_USAGE,
    start_date=datetime(2025, 6, 1),
    end_date=datetime(2025, 6, 30),
    limit=100,
    offset=0
)

# Count particles
count = await repo.count_particles(
    key_id="opc_001_abc123",
    particle_type=PARTICLE_TYPE_USAGE
)

# Aggregate by type
aggregations = await repo.aggregate_by_type(
    key_id="opc_001_abc123",
    particle_types=[PARTICLE_TYPE_USAGE, PARTICLE_TYPE_CREDIT]
)
# Returns: [
#   ParticleAggregation(type='usage', total_amount=Decimal('-125.50'), count=50),
#   ParticleAggregation(type='credit', total_amount=Decimal('200.00'), count=3)
# ]
```

---

## Treasury System

Every particle has an associated **Treasury** that manages fund allocation across categories:

### Treasury Structure

```json
{
  "version": "1.0",
  "currency_balances": {
    "USD": 197.50,
    "VND": 15000000,
    "USDT": 0.0
  },
  "allocation_rules": {
    "operating_reserve_percent": 0.30,
    "tax_reserve_percent": 0.25,
    "reinvestment_percent": 0.30,
    "founder_draw_percent": 0.15
  },
  "transactions": [
    {
      "id": "alloc_001",
      "type": "reserve_allocation",
      "amount": 59.25,
      "currency": "USD",
      "category": "operating_reserve",
      "timestamp": "2025-06-18T20:00:00Z"
    }
  ],
  "metadata": {
    "created_at": "2025-06-18T15:45:00Z",
    "currency_support": ["VND", "USD", "EUR"],
    "self_custody_enabled": false,
    "last_rebalance": "2025-06-18T20:00:00Z"
  }
}
```

### Allocation Rules

Treasury automatically allocates incoming credits:

| Category | Default % | Purpose |
|----------|-----------|---------|
| Operating Reserve | 30% | Day-to-day expenses |
| Tax Reserve | 25% | Tax withholding (configurable by jurisdiction) |
| Reinvestment | 30% | Business growth, R&D, marketing |
| Founder Draw | 15% | Personal income (withdrawable) |

### Treasury Rebalancing

```python
from src.raas.treasury_service import TreasuryService

treasury_service = TreasuryService()

# Rebalance based on allocation rules
await treasury_service.rebalance(key_id)

# Manual allocation
await treasury_service.allocate(
    key_id="opc_001_abc123",
    category="reinvestment",
    amount=Decimal("50.00"),
    currency="USD",
    reason="Marketing campaign expansion"
)

# Withdraw from founder draw
await treasury_service.withdraw(
    key_id="opc_001_abc123",
    amount=Decimal("100.00"),
    currency="VND",
    destination_bank="...via ZenPay"
)
```

---

## Multi-Currency Support

### Supported Currencies

| Currency | Code | Precision | Notes |
|----------|------|-----------|-------|
| US Dollar | USD | 2 decimals | Primary international |
| Vietnamese Dong | VND | 0 decimals | No subunit (whole numbers) |
| Euro | EUR | 2 decimals | EU operations |
| USDT (Tether) | USDT | 6 decimals | Crypto option (self-custody) |

### Currency Conversion

When using multiple currencies, balance queries return per-currency:

```python
balances = await repo.get_multi_currency_balance(key_id)
# Returns:
# {
#   "USD": Decimal('197.50'),
#   "VND": Decimal('15000000'),
#   "USDT": Decimal('0.000000')
# }
```

### Conversion Rate Management

```python
from src.zenpay.conversion import ConversionService

converter = ConversionService()

# Get current rate (from Wise/Stripe)
rate = await converter.get_rate("USD", "VND")
# Returns: Decimal('24750.50')

# Convert with fee calculation
converted = await converter.convert(
    from_currency="USD",
    to_currency="VND",
    amount=Decimal("100.00"),
    key_id="opc_001_abc123"
)
# Returns: 2,475,000 VND (minus 0.5% fee = 2,462,625)
```

---

## Particle Lifecycle

### Birth

Particles are created through:

1. **API Usage**: Command execution creates `usage` particles automatically
2. **Payments**: Webhook from Stripe/Polar creates `credit` particles
3. **Manual Admin**: `/admin credit-add` creates `credit` particles
4. **Subscription**: Recurring billing creates `subscription` particles

### Growth

As the particle accumulates particles, its `balance_after` updates with each new particle. The treasury rebalances periodically (daily or threshold-based).

### Maturity

After 6 months of consistent activity, particles can:

- Apply for **Trust Score** elevation (50 → 75 → 90)
- Access **self-custody** treasury options
- Create **sub-particles** for project-based accounting
- Participate in **protocol governance** (constitutional amendments)

### Merge & Split

Particles can combine (merge) or spawn children (split):

```bash
# Merge two particles (requires constitutional approval)
mekong particle merge --from particle_abc --into particle_xyz --reason "Consolidation"

# Split particle for new venture
mekong particle split --particle particle_abc --child-name "New Product Line"
```

### Death (Dissolution)

Voluntary dissolution requires:

1. Zero or negative balance confirmation
2. Treasury withdrawal/transfer to other particles
3. Constitutional amendment allowing dissolution
4. 30-day cooling period
5. Final audit report

```bash
mekong particle dissolve --particle particle_abc --reason "Business closure"
```

---

## Particle Types by Business Form

ZenOS supports different particle templates based on business structure:

### OPC (One-Person Company)

```bash
mekong particle create --type opc --name "My Solo Biz"
```

Characteristics:
- Single founder (1 key_id)
- Full control (100% voting)
- Simplified constitution (pre-built)
- Tax: Personal income tax rates

### Cooperative

```bash
mekong particle create --type cooperative --name "Dev Collective"
```

Characteristics:
- Multiple members (each gets key_id)
- Democratic voting (1 member = 1 vote)
- Indivisible reserves (cannot be bought out)
- Tax: Cooperative tax regime

### Micro-Enterprise

```bash
mekong particle create --type micro_enterprise --name "Family Shop"
```

Characteristics:
- Up to 9 employees
- Owner + employee key_ids
- Revenue-based thresholds
- Simplified compliance

### Creator

```bash
mekong particle create --type creator --name "Content Studio"
```

Characteristics:
- Platform integrations (YouTube, Patreon)
- Revenue share tracking
- Audience behavior graph enabled
- Creator-specific analytics

---

## Integrations

### With Constitutional AI

Every particle has a `constitution_id`. Constitutional review evaluates:

```python
# Check if particle action complies with constitution
review = constitution.review(
    action="particle:transfer",
    context={"particle_id": "abc123", "particle_type": "opc"},
    parameters={"amount": 1000, "to_particle": "xyz789"},
    metadata={"agent": "finance-agent"}
)
# Returns: {
#   "overall_score": 0.85,
#   "passed": true,
#   "principle_results": [...]
# }
```

If score < 0.7, the transfer may be blocked (in ENFORCE mode).

### With Behavior Graph

Particles create behavior nodes automatically:

```json
{
  "nodes": [
    {
      "id": "particle:opc_001_abc123",
      "type": "Particle",
      "properties": {
        "name": "Acme Corp",
        "type": "opc",
        "trust_score": 75,
        "created_at": "2025-06-01T..."
      }
    },
    {
      "id": "behavior:550e8400...",
      "type": "UsageConsumption",
      "properties": {
        "amount": -2.5,
        "command": "marketing:create",
        "timestamp": "2025-06-18T..."
      }
    }
  ],
  "edges": [
    {
      "source": "particle:opc_001_abc123",
      "target": "behavior:550e8400...",
      "type": "PERFORMED"
    }
  ]
}
```

Query patterns:
```cypher
// Find particles with high usage
MATCH (p:Particle)-[:PERFORMED]->(b:UsageConsumption)
WHERE b.amount < -10
RETURN p.name, sum(b.amount) as total_usage
ORDER BY total_usage DESC
```

### With Founder Genome

Link particle to founder:

```python
# During particle creation
particle = EconomicParticle(
    key_id="opc_001_abc123",
    name="My Startup",
    founder_id="genome_001",  // Links to FounderGenome record
    type="opc"
)
```

The founder genome's traits influence:
- Default constitution variant selection
- Trust score calculation
- AI agent behavior tuning
- Recommendation engine (co-founder matching, investor fit)

---

## Best Practices

### 1. Use key_id Consistently

The `key_id` is the primary identity for particles. Always use:

```python
# Good
particle.key_id = "opc_001_abc123"

# Avoid (legacy only)
particle.tenant_id = "tenant_abc123"
```

### 2. Never Modify Particles

Particles are append-only. To correct errors, create adjustment particles:

```python
# Wrong: modifying existing particle
particle.amount = Decimal("0.0")  # ❌ DON'T

# Right: create adjustment
adjustment = EconomicParticle(
    key_id=particle.key_id,
    particle_type=PARTICLE_TYPE_ADJUSTMENT,
    amount=Decimal("2.5"),  // Reverses the error
    metadata={"corrects": particle.id, "reason": "Billing error fix"}
)
await repo.create_particle(adjustment)
```

### 3. Set balance_after for Performance

When creating multiple particles in a batch, calculate `balance_after` upfront:

```python
current_balance = await repo.get_balance(key_id)
new_particle.balance_after = current_balance + new_particle.amount
```

This avoids re-aggregation on read.

### 4. Use Metadata for Audit Trail

Always include actionable metadata:

```python
metadata = {
    "agent": "marketing-campaign-agent",
    "command": "marketing:create-campaign",
    "duration_ms": 4250,
    "mcu_used": 2.5,
    "session_id": "sess_abc123",
    "user_id": "user_456"  // If different from key_id owner
}
```

### 5. Handle Currency Precision

```python
# Wrong: float imprecision
amount = 0.1  # Float can't represent exactly

# Right: use Decimal
from decimal import Decimal
amount = Decimal("0.10")
```

VND uses 0 decimal places (whole numbers):
```python
vnd_amount = Decimal("25000")  # 25,000 VND, not 25000.00
```

---

## Migration from Tenants

See [`docs/zenos-migration-guide.md`](./zenos-migration-guide.md) for complete migration instructions.

Key mappings:

| Tenant Field | Particle Equivalent |
|--------------|---------------------|
| `tenants.id` | `particles.id` (1:1 copy) |
| `tenants.name` | `particles.name` |
| `tenants.created_at` | `particles.created_at` |
| `tenants.is_active` | `particles.status` ("active" / "suspended") |
| (none) | `particles.type` = "opc" (default) |
| (none) | `particle_constitutions` (new, default ZenOS) |
| (none) | `behavior_graphs` (new, empty) |
| (none) | `treasuries` (new, with allocation rules) |

---

## Troubleshooting

### Balance Mismatch

If `balance_after` doesn't match aggregated balance:

```bash
# Recalculate from particles
python3 -m src.main raas balance-recalculate --key-id opc_001_abc123

# This updates all particles' balance_after fields
```

### Missing Currency Support

Add currency to `VALID_CURRENCIES` in `src/models/particle.py`:

```python
VALID_CURRENCIES = {CURRENCY_USD, CURRENCY_VND, CURRENCY_EUR, "JPY"}
```

### Performance: Slow Balance Queries

Add database index:
```sql
CREATE INDEX idx_economic_particles_key_currency
ON economic_particles(key_id, currency, created_at);
```

---

## References

- **Migration Guide**: [`docs/zenos-migration-guide.md`](./zenos-migration-guide.md)
- **Constitutional AI**: [`docs/constitutional-ai.md`](./constitutional-ai.md)
- **Founder Genome**: [`docs/founder-genome.md`](./founder-genome.md)
- **Database Schema**: `src/db/migrations/012_economic_particle_schema.sql`
- **ORM Models**: `src/models/particle.py`
- **Migration Script**: `scripts/migrate-tenants-to-particles.py`

---

**Next**: Learn about [`docs/constitutional-ai.md`](./constitutional-ai.md) to understand how particles are governed.
