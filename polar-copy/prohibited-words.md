# Polar Prohibited Words — Zero Tolerance List

> Reference: https://polar.sh/docs/merchant-of-record/acceptable-use
> Incidents: WellNexus (2026-03-23), mekongmind (2026-04-12)

## Banned Words (auto-reject triggers)

| Word | Category | Safe Replacement |
|------|----------|-----------------|
| AI | Technology | automation, workflow engine, operations platform |
| A.I. | Technology | automation |
| artificial intelligence | Technology | workflow automation |
| machine learning | Technology | optimization engine |
| smart assistant | Technology | workflow assistant |
| wellness | Health | (none — avoid health verticals) |
| health | Health | (none — avoid health verticals) |
| healthcare | Health | (none) |
| medical | Health | (none) |
| therapy / therapeutic | Health | (none) |
| clinical | Health | (none) |
| patient | Health | user, subscriber |
| prescription | Health | (none) |
| diagnosis / treatment | Health | (none) |
| BAA | Compliance | (none) |
| HIPAA | Compliance | (none) |
| trading | Finance | (none — Polar bans trading) |
| crypto / cryptocurrency | Finance | (none) |
| token | Finance | credit, unit |
| investment | Finance | subscription |
| gambling | Finance | (none) |

## Safe Words for Mekong CLI Copy

- business operations platform
- workflow automation
- command-line productivity tool
- developer tooling SaaS
- autonomous workflow agents
- operations orchestrator
- company automation platform
- business management platform
- solo founder tooling
- task orchestration engine
- operations credits

## Pre-Submit Checklist

```bash
# Run before every Polar dashboard update or README change
grep -ciE "\b(AI|A\.I\.|wellness|health|medical|therapy|therapeutic|clinical|patient|BAA|HIPAA|diagnosis|treatment|trading|crypto|token|investment|gambling)\b" README.md
# Expected: 0 (user-visible prose only; URLs and code blocks exempt)
```

## Check Script (doc-only, not wired to pre-commit)

See `polar-copy/check-prohibited.sh` for standalone scan script.
