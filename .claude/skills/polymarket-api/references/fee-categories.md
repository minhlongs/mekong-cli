# Polymarket Fee Categories (March 30, 2026 Expansion)

## Maker Fees
All categories: **0%** with rebates

| Category | Maker Rebate |
|----------|-------------|
| Sports | 50% |
| Politics | 40% |
| Crypto | 30% |
| Finance | 30% |
| Science | 20% |
| Entertainment | 20% |
| Other | 20% |

## Taker Fees (Dynamic by Probability)

Taker fee increases as probability moves away from 50%.

| Probability Range | Base Taker Fee |
|------------------|---------------|
| 40-60% | 0.15% |
| 30-40% or 60-70% | 0.30% |
| 20-30% or 70-80% | 0.60% |
| 10-20% or 80-90% | 1.00% |
| 5-10% or 90-95% | 1.40% |
| <5% or >95% | 1.80% |

## Category Multiplier

Final taker fee = Base Taker Fee * Category Multiplier

| Category | Multiplier |
|----------|-----------|
| Sports | 1.0x |
| Politics | 1.2x |
| Crypto | 1.5x |
| Finance | 1.3x |
| Other | 1.0x |

## Impact on CashClaw

For market-making at 55% probability in Crypto:
- Maker: 0% (with 30% rebate on fills)
- Taker: 0.15% * 1.5 = 0.225%
- Effective spread needed: > 0.225% to profit on taker fills

For market-making at 90% probability in Politics:
- Taker: 1.00% * 1.2 = 1.20%
- Effective spread needed: > 1.20% — much wider, less liquid
