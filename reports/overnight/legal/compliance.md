# Compliance Report — March 2026
**Generated:** 2026-03-12 | **Entity:** Mekong CLI / OpenClaw | **License:** MIT

---

## Executive Summary

Mekong CLI v5.0 is an MIT-licensed open source project. Compliance posture is clean:
no PII stored, no user data processed beyond API keys, GDPR considerations addressed
via architecture (stateless Workers, user-controlled data). CLA template prepared for
future contributors.

---

## License Compliance

### Project License: MIT

```
MIT License — Copyright (c) 2026 Mekong CLI Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

**Status:** COMPLIANT

### Third-Party Dependency Audit

| Package           | License      | Compliant | Notes                         |
|-------------------|--------------|-----------|-------------------------------|
| typer             | MIT          | YES       | CLI framework                 |
| rich              | MIT          | YES       | Terminal formatting           |
| fastapi           | MIT          | YES       | API gateway                   |
| httpx             | BSD-3        | YES       | Compatible with MIT           |
| pytest            | MIT          | YES       | Test framework                |
| anthropic (SDK)   | MIT          | YES       | Official Anthropic SDK        |
| openai            | Apache 2.0   | YES       | Compatible with MIT           |
| pydantic          | MIT          | YES       | Data validation               |
| click             | BSD-3        | YES       | Typer dependency              |

**Note:** Apache 2.0 dependencies are compatible with MIT distribution.
GPL-licensed packages must be avoided — run `pip-licenses` before adding new deps.

### License Compatibility Matrix

| Dependency License | Compatible with MIT? | Action Required |
|--------------------|---------------------|-----------------|
| MIT                | YES                  | None            |
| BSD-2/BSD-3        | YES                  | None            |
| Apache 2.0         | YES                  | None            |
| LGPL               | YES (dynamic link)   | Keep separate   |
| GPL                | NO                   | DO NOT USE      |
| AGPL               | NO                   | DO NOT USE      |

---

## GDPR Compliance

### Data Inventory

| Data Type          | Stored? | Where    | Basis           | Retention |
|--------------------|---------|----------|-----------------|-----------|
| User API keys      | NO      | Env vars | N/A             | N/A       |
| LLM prompts        | NO      | Transit  | N/A             | N/A       |
| MCU credit balance | YES     | CF D1    | Contract        | Per sub   |
| Email (Polar.sh)   | NO      | Polar.sh | Polar holds     | Polar's   |
| Payment data       | NO      | Polar.sh | Polar holds     | Polar's   |
| IP addresses       | NO      | CF logs  | CF holds 7 days | CF's      |
| Usage analytics    | NO      | N/A      | N/A             | N/A       |

**PII stored by Mekong:** NONE

### GDPR Principles Assessment

| Principle             | Status      | Notes                                   |
|-----------------------|-------------|-----------------------------------------|
| Lawfulness            | COMPLIANT   | Contract basis for MCU billing          |
| Purpose limitation    | COMPLIANT   | MCU balance only, no secondary use      |
| Data minimisation     | COMPLIANT   | Only credit balance stored              |
| Accuracy              | COMPLIANT   | Real-time ledger updates                |
| Storage limitation    | COMPLIANT   | Deleted on subscription termination     |
| Security              | COMPLIANT   | Cloudflare D1 encrypted at rest        |
| Accountability        | COMPLIANT   | This report serves as evidence          |

### Data Subject Rights (DSR) Procedures

- **Right of access:** Customer can query `/v1/account/balance` — shows all MCU data
- **Right to erasure:** DELETE `/v1/account` removes D1 ledger row — automated
- **Right to portability:** Credit history exportable as JSON via API
- **Right to object:** N/A (no marketing processing)

### GDPR for agencyos.network (EU Visitors)

- [ ] Cookie consent banner — PENDING (no cookies currently set)
- [x] Privacy policy — PENDING (draft in legal/contract-review.md)
- [x] No third-party trackers on landing page
- [x] Cloudflare CDN (EU data processing agreement in place with CF)
- [ ] Data Processing Agreement (DPA) template — for enterprise customers

---

## CLA (Contributor License Agreement) Template

For future contributors when community grows beyond 10 external PRs:

```markdown
## Contributor License Agreement (CLA)

By submitting a pull request to the Mekong CLI repository, you agree:

1. GRANT OF COPYRIGHT LICENSE
   You grant the project maintainers a perpetual, worldwide, non-exclusive,
   royalty-free license to reproduce, prepare derivative works of, publicly
   display, publicly perform, sublicense, and distribute your contributions.

2. GRANT OF PATENT LICENSE
   You grant a perpetual patent license for any patent claims licensable by
   you that are necessarily infringed by your contribution.

3. REPRESENTATIONS
   - You are legally entitled to grant the above licenses.
   - Your contribution is your original creation.
   - You have disclosed any third-party licenses affecting your contribution.

4. INBOUND = OUTBOUND
   Contributions are accepted under the same MIT license as the project.

Signed: _____________________ GitHub: _____________ Date: ___________
```

**CLA enforcement:** Use `cla-assistant.io` (free, GitHub-integrated) when first
external contributor submits PR. Until then, informal — GitHub DCO sign-off acceptable.

---

## Open Source Compliance Checklist

- [x] LICENSE file present in repo root
- [x] MIT license text complete and correct
- [x] Copyright year updated (2026)
- [x] Third-party licenses documented
- [ ] NOTICE file (needed if Apache 2.0 deps require attribution) — LOW PRIORITY
- [ ] `pip-licenses` scan in CI pipeline — PENDING
- [x] No GPL/AGPL dependencies
- [ ] CLA bot configured — PENDING (activate at 10+ external contributors)

---

## Export Control (EAR / OFAC)

Mekong CLI is general-purpose developer tooling. No encryption technology beyond
standard HTTPS/TLS (exempt from EAR). No export restrictions anticipated.

OFAC screening: Polar.sh (merchant of record) handles sanctions screening for payments.
No direct sales operations to screen.

---

## Vietnamese Law Considerations (ĐIỀU 55 — Vietnamese-First)

- **Cybersecurity Law 2018:** No user data stored in Vietnam, no compliance trigger.
- **Decree 13/2023:** Personal data protection — COMPLIANT (no PII processed).
- **IP Law:** MIT license valid under Vietnamese IP framework.
- **E-commerce:** Polar.sh handles e-commerce obligations as merchant of record.

---

## Action Items

| Item                             | Priority | Owner    | Due        |
|----------------------------------|----------|----------|------------|
| Add `pip-licenses` to CI         | Medium   | Founder  | Apr 2026   |
| Draft privacy policy             | High     | Founder  | Apr 2026   |
| Cookie consent (if analytics)    | Low      | Founder  | When added |
| CLA bot setup                    | Low      | Founder  | 10th PR    |
| NOTICE file for Apache 2.0 deps  | Low      | Founder  | May 2026   |

---

*Next compliance review: 2026-06-01 or upon first enterprise customer.*
