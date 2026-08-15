# Unit Economics Model

Comprehensive financial modeling for Mekong CLI SaaS business.

## Overview

The unit economics model calculates key SaaS metrics:

- **LTV** (Lifetime Value) - Total revenue per customer over lifetime
- **CAC** (Customer Acquisition Cost) - Cost to acquire one customer
- **LTV:CAC Ratio** - Health indicator (target ≥3:1)
- **Gross Margin** - Revenue minus direct costs
- **Payback Period** - Months to recover CAC
- **Contribution Margin** - Revenue minus variable costs

## Quick Start

```bash
# Show unit economics report
python3 -m src.cli.unit_economics_commands show

# Run sensitivity analysis
python3 -m src.cli.unit_economics_commands sensitivity cac 400 512 600

# Project MRR for 100 Starter, 50 Growth, 10 Pro customers
python3 -m src.cli.unit_economics_commands project 100 50 10

# Export to JSON
python3 -m src.cli.unit_economics_commands export reports/unit-economics.json

# Validate against targets
python3 -m src.cli.unit_economics_commands validate
```

## Model Components

### Cost Structure

| Component | Default Value | Description |
|-----------|---------------|-------------|
| LLM Input Cost | $1.25/Mtok | Blended rate across Claude/Gemini/GPT |
| LLM Output Cost | $12.50/Mtok | Blended output token cost |
| MCU Overhead | $0.002/MCU | Infrastructure + ops per MCU |
| Infra/Customer/Mo | $0.50 | Cloudflare + DB overhead |
| Payment Processing | 2.9% + $0.30 | Polar/Stripe fees |
| Support Rate | $50/hr | Support engineer cost |

### Pricing Tiers

| Tier | Price | MCU Included | Target Segment |
|------|-------|--------------|----------------|
| Starter | $49/mo | 200 | Solo founders |
| Growth | $149/mo | 1,000 | Small agencies |
| Pro | $499/mo | 5,000 | Growing SaaS |

Average usage is modeled at 65-85% of included MCU.

### Customer Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| CAC | $512 | Customer acquisition cost |
| Monthly Churn | 5% | Monthly cancellation rate |
| Net Revenue Retention | 115% | Expansion/contraction net |

## Calculations

### Gross Margin

```
Gross Margin % = (Revenue - Cost of Revenue) / Revenue × 100

Cost of Revenue includes:
- LLM costs (MCU usage × cost per MCU)
- Payment processing fees
- Infrastructure per customer
- Support costs (tickets × time × rate)
```

### Lifetime Value (LTV)

```
LTV = MRR × Gross Margin % × Avg Lifetime Months × (1 + NDR)

Avg Lifetime Months = 1 / Monthly Churn Rate
```

### Payback Period

```
Payback (months) = CAC / (MRR × Gross Margin %)
```

### LTV:CAC Ratio

```
Ratio = LTV / CAC
Healthy threshold: ≥3:1
```

## Interpreting Results

| Metric | Healthy Range | Mekong Target |
|--------|---------------|---------------|
| LTV:CAC | 3-5x | 10x |
| Gross Margin | 70-90% | 85% |
| Payback | 6-18 months | 3 months |
| Monthly Churn | 1-3% | 5% |

### Tier-Specific Insights

- **Starter**: Lower revenue but faster sales cycle. Payback critical.
- **Growth**: Sweet spot - good revenue, reasonable churn.
- **Pro**: Highest LTV but longer sales cycle and higher support costs.

## Scenario Analysis

### Optimistic Scenario
- Lower churn (3%)
- Higher expansion (20%)
- Lower CAC ($400)

### Pessimistic Scenario
- Higher churn (8%)
- Lower expansion (5%)
- Higher CAC ($700)

Use the `sensitivity` command to model these scenarios.

## Integration with Company Config

The model reads defaults from `.mekong/company-openclaw.json`:

```json
{
  "revenue_model": {
    "unit_economics": {
      "cac_target": 512,
      "ltv_target": 5107,
      "ltv_cac_ratio": 10,
      "payback_months": 3,
      "gross_margin": 0.85
    }
  }
}
```

## Extending the Model

### Adding Custom Cost Components

```python
from src.core.unit_economics import CostStructure

custom_costs = CostStructure(
    # ... existing fields
    custom_overhead=0.05,  # Add custom field
)
```

### Creating Custom Scenarios

```python
from src.core.unit_economics import BusinessModel, load_default_mekong_model

model = load_default_mekong_model()

# Modify parameters
model.cost_structure.mcu_overhead_usd = 0.003  # Higher MCU cost
model.customer_metrics.monthly_churn_rate = 0.08  # Higher churn
model.calculate()

# Access blended metrics
print(f"New LTV: ${model.blended_ltv:.2f}")
```

## Export Formats

### JSON Report Structure

```json
{
  "cost_structure": {
    "llm_input_cost_per_mtok": 1.25,
    "mcu_overhead_usd": 0.002,
    ...
  },
  "customer_metrics": {
    "cac": 512.0,
    "monthly_churn_rate": 0.05,
    ...
  },
  "tiers": [
    {
      "tier": "Starter",
      "price_monthly": 49.0,
      "effective_monthly_revenue": 49.0,
      "gross_margin_pct": 78.5,
      "ltv_usd": 987.50,
      "ltv_cac_ratio": 1.93,
      ...
    }
  ],
  "blended_metrics": {
    "arpu": 127.45,
    "gross_margin_pct": 82.1,
    "ltv": 2456.78
  }
}
```

## Validation Rules

The `validate` command checks against SaaS health benchmarks:

| Check | Threshold | Status |
|-------|-----------|--------|
| LTV:CAC ≥ 3 | PASS if ≥3.0 | Core unit economics |
| Gross Margin ≥ 70% | PASS if ≥70% | Unit profitability |
| Payback ≤ 12mo | PASS if ≤12 | Cash efficiency |
| Churn ≤ 5% | PASS if ≤5% | Retention health |

## Monthly Reporting

Generate monthly unit economics report:

```bash
python3 -m src.cli.unit_economics_commands show > reports/unit-economics-$(date +%Y-%m).txt
python3 -m src.cli.unit_economics_commands export data/unit-economics/$(date +%Y-%m).json
```

## References

- [SaaS Metrics 2.0 - David Skok](http://www.forentrepreneurs.com/saas-metrics-2/)
- [Unit Economics for Startups - Andreessen Horowitz](https://a16z.com/2017/02/18/unit-economics/)
- [The Startup Finance Model - Allen](https://www.aljenait.com/startup-finance-model/)
