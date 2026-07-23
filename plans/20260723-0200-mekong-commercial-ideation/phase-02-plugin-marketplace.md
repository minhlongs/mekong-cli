# Phase 02 — Plugin Marketplace
Goal: Activate third-party vendor plugin ecosystem.

## Scope
- Vendor onboarding CLI (`mekong vendor onboard`)
- Plugin registry public API
- Vendor dashboard (basic web UI or CLI)

## Deliverables
1. `src/cli/commands/vendor_marketplace.py` (done — scaffold ready)
2. Marketplace API endpoints: list / onboard / delist
3. Plugin validation + sandboxing policy

## Definition of Done
- `mekong marketplace list` shows ≥ 3 sample plugins
- Vendor can onboard, publish, delist plugin
- Plugin install/uninstall round-trip tested

## Dependencies
- Phase 01 (Vietnamese docs for vendor onboarding)

## Risks
- Malicious plugin surface area
- Versioning + compatibility across CLI versions
