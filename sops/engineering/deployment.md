# SOP: Engineering Deployment
**Layer:** Engineering | **Version:** 1.0.0 | **Owner:** ENG (Engineer)

## Intent
Safe, observable, reversible deployments.

## Pre-Deploy
1. All tests pass
2. Code review approved
3. Monitoring dashboards loaded and alerting active
4. Rollback plan documented

## Deploy Steps
1. Tag release: `git tag v<semver> && git push origin v<semver>`
2. Deploy to staging, verify health checks
3. Deploy to production (staged: 10% → 50% → 100%)
4. Monitor for 30 minutes post-deploy

## Post-Deploy
- Confirm all health metrics green
- Update deployment log: `deployments/YYYY-MM-DD.md`
- If issue: rollback immediately, then investigate

## Rollback Trigger
- Error rate > 5% within 10 minutes
- Response time > 2x baseline
- Any security-related alert

## Escalation
Rollback triggered: notify CEO within 15 minutes.
