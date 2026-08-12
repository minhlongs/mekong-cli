# Plan
**Company:** Mekong CLI  
**Product:** saas  
**Status:** planned  
**Created:** 2026-08-09

---

## Phases

- **Research** ([[phase-01](phase-01-research.md)](phase-01-research.md))
- **Implement** ([[phase-02](phase-02-implement.md)](phase-02-implement.md))
- **Test** ([[phase-03](phase-03-test.md)](phase-03-test.md))
- **Review** ([[phase-04](phase-04-review.md)](phase-04-review.md))
- **Deploy** ([[phase-05](phase-05-deploy.md)](phase-05-deploy.md))

## Dependencies

- phase-01 -> phase-02
- phase-02 -> phase-03
- phase-03 -> phase-04
- phase-04 -> phase-05

## Acceptance Criteria

1. **User authentication & authorization (SSO, RBAC)** — implemented, tested, reviewed
2. **Subscription billing & invoicing (Stripe / NOWPayments / PayOS)** — implemented, tested, reviewed
3. **REST / GraphQL API layer with rate limiting** — implemented, tested, reviewed
4. **Usage analytics & quota enforcement** — implemented, tested, reviewed
5. **Admin dashboard & team management** — implemented, tested, reviewed
6. **Email notification pipeline** — implemented, tested, reviewed
7. **Audit log & compliance reporting** — implemented, tested, reviewed
