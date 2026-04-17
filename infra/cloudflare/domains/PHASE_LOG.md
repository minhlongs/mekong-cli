# Phase Log — CF Domain Consolidation B4

**Phase:** B4 (Phases 3-5 finish)
**Executed:** 2026-04-17
**Upstream:** plans/260326-2036-domain-consolidation/ (Phases 1-2 done 2026-03-26)
**Status:** PARTIAL — config + scripts shipped; 2 action items need CF dashboard access

---

## What This Phase Does

| Task | Status | Notes |
|------|--------|-------|
| Enumerate production domains | DONE | 8 active + 2 gaps documented |
| Document redirect map | DONE | 4 active 301s verified live |
| Security headers config | DONE | YAML spec written; HSTS missing (action item) |
| Deploy script | DONE | `deploy.sh` — manual-apply, no auto-deploy |
| Smoke test script | DONE | `verify.sh` — curl-based, runs in <30s |
| Run verify.sh | DONE | 16 PASS / 1 FAIL / 1 GAP (see results below) |

---

## Smoke Test Results (2026-04-17 09:59:57)

### Canonical Domains (HTTP 200)
| Domain | Status |
|--------|--------|
| agencyos.network | PASS 200 |
| agencyos.network/docs | PASS 200 |
| agencyos.network/dashboard | PASS 200 |
| api.agencyos.network | PASS 200 |
| sophia.agencyos.network | PASS 200 |
| cashclaw.cc | PASS 200 |
| wellnexus.vn | PASS 200 |
| ide.mekongmind.com | PASS 200 |

### Redirect Domains (HTTP 301)
| Domain | Redirects To | Status |
|--------|-------------|--------|
| app.agencyos.network | agencyos.network/dashboard/ | PASS 301 |
| dashboard.agencyos.network | agencyos.network/dashboard/ | PASS 301 |
| docs.agencyos.network | agencyos.network/docs/ | PASS 301 |
| landing.agencyos.network | agencyos.network/ | PASS 301 |

### Gaps / Failures
| Domain | Result | Action Required |
|--------|--------|----------------|
| mekongmind.com | TIMEOUT (HTTP 000) | CF Pages project not identified. CF IPs confirmed (104.21.8.197), TLS valid (exp 2026-07-11). Run: `wrangler pages project list \| grep mekong` |
| strict-transport-security on agencyos.network | MISSING | Enable in CF Dashboard > SSL/TLS > Edge Certificates > HSTS, OR add Transform Rule |

---

## Action Items (CF Dashboard Access Required)

### Action 1: Enable HSTS on agencyos.network — PRIORITY HIGH
```
CF Dashboard > agencyos.network zone > SSL/TLS > Edge Certificates
  > HTTP Strict Transport Security (HSTS)
  > Enable: max-age=31536000, includeSubDomains, preload
```
Prerequisite: confirm ALL agencyos.network subdomains serve HTTPS (sophia.* does — verified).

### Action 2: Identify mekongmind.com CF Pages project — PRIORITY MEDIUM
```bash
export CLOUDFLARE_API_TOKEN=<token>
wrangler pages project list | grep -i mekong
```
Likely candidate: `mekongmind-flagsite` (shipped 2026-04-16, commit 5ec45a6, 18 files).
If confirmed, add custom domain `mekongmind.com` in CF Pages > project > Custom domains.

### Action 3: Verify Always Use HTTPS on cashclaw.cc + wellnexus.vn — PRIORITY HIGH
```
CF Dashboard > each zone > SSL/TLS > Edge Certificates > Always Use HTTPS = ON
```

### Action 4: CORS update on mekong-engine — PRIORITY HIGH (Phase 5 carry-over)
Update Workers code: allow `https://agencyos.network`, remove old subdomain origins.
Ref: plans/260326-2036-domain-consolidation/plan.md Phase 5.3.

### Action 5: sophia.agencyos.network redirect — HOLD
Currently HTTP 200 (Sophia Worker live). Do NOT redirect until product decision.
Ref: redirects.yaml > pending > agencyos-sophia-to-root.

---

## What Is Still Pending (vs Phase Plan)

| Phase Plan Item | B4 Status | Reason |
|----------------|-----------|--------|
| `wrangler login + account verify` | SKIPPED | No CF token in scope; scripts use env var ref |
| `Apply DNS changes` | NOT APPLIED | Config-only phase per task spec (YAGNI) |
| `Apply redirects via CF API` | NOT APPLIED | Redirects already live from prior work; config documented |
| `Apply security headers via CF Transform` | NOT APPLIED | YAML spec written; CF dashboard action required |
| `Rollback runbook` | DONE | See docs/domain-plan.md |

Per task spec: "Phase 3-5 = config + manual-apply scripts + verification checklist. DO NOT wrangler deploy anything."

---

## Files Created (This Phase)

| File | Purpose |
|------|---------|
| `infra/cloudflare/domains/production-domains.yaml` | Authoritative domain list + status |
| `infra/cloudflare/domains/redirects.yaml` | 301 redirect map (active + pending) |
| `infra/cloudflare/domains/security-headers.yaml` | HSTS/CSP/X-Frame spec |
| `infra/cloudflare/domains/deploy.sh` | Manual deploy helper per project |
| `infra/cloudflare/domains/verify.sh` | curl-based smoke test suite |
| `infra/cloudflare/domains/README.md` | Architecture overview |
| `infra/cloudflare/domains/PHASE_LOG.md` | This file |
| `docs/domain-plan.md` | Runbook: apply order + rollback |

---

## Rollback Procedure

If any DNS/redirect change breaks production:

1. **Identify affected zone** — check CF analytics or verify.sh output
2. **Restore DNS** — CF Dashboard > zone > DNS > revert to snapshot in production-domains.yaml
3. **Remove redirect rule** — CF Dashboard > Rules > Redirect Rules > disable/delete the rule
4. **Verify** — run `./verify.sh --domain <affected-domain>`
5. **Root cause** — check CF Transform Rule ordering conflicts

DNS TTL note: CF Proxy records use 300s TTL automatically. Non-proxied records at original TTL.
Safe window for rollback: <5 min for proxied records.
