---
phase: 4
title: "License Enforcement Runtime"
status: completed
priority: P1
effort: "2w"
dependencies: [1]
---

# Phase 4: License Enforcement Runtime

## Overview
Runtime license check that gates features by tier.

## Requirements
- License validation at startup
- Feature flag system per tier (BASIC/PRO/ENTERPRISE)
- Offline grace period (7 days)

## Implementation Steps
1. Build license validator in engine/license/
2. Add feature flags to gateway
3. Wire tier gating to MCU billing

## Success Criteria
- [ ] Invalid license blocks premium features
- [ ] BASIC tier cannot access PRO features
- [ ] Grace period works offline

## Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| License bypass via patch | Medium | High | Sign license + verify at runtime |
