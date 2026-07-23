# Phase 03 — Pricing + Checkout
Goal: Ship monetization surface for SaaS tiers.

## Scope
- VN-priced tiers in `src/api/vn_pricing_routes.py`
- Polar checkout + VietQR checkout unification
- Trial / freemium gating in CLI

## Deliverables
1. Pricing table: Free / $29 / $99 / Enterprise
2. Checkout routes returning valid Polar/VietQR URLs
3. MCU billing + quota enforcement wired to tiers

## Definition of Done
- `mekong plan list` respects freemium limits
- Checkout returns live redirect URL (test env)
- `billing` CLI shows current plan + MCU usage

## Dependencies
- Phase 01 (VN pricing + currency support)

## Risks
- Polar sandbox vs live account mismatch
- Token/cost leakage in free tier
