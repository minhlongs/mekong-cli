# Domain Consolidation Runbook

**Scope:** Mekong-ecosystem CF domain cutover, redirects, security headers
**Platform:** Cloudflare Pages + Workers only (Vercel BANNED 2026-03-27)
**Config source:** `infra/cloudflare/domains/`

---

## Apply Order (Safe Sequence)

Run changes in this order to minimize blast radius. Each step is independently
reversible before proceeding to the next.

```
Step 1: Always Use HTTPS (per zone)       — zero-risk, just toggles
Step 2: HSTS (agencyos.network first)     — 5 min TTL risk window
Step 3: Verify redirects still live       — ./verify.sh --fast
Step 4: Security headers (X-Frame, nosniff) — additive, no breakage
Step 5: CSP Report-Only (24h monitoring)  — non-enforcing, safe
Step 6: CSP Enforce (after B1 IDE stable) — coordinate with Phase B1
Step 7: CORS update in mekong-engine      — test API before/after
Step 8: mekongmind.com CF Pages link      — identify project, add custom domain
```

---

## Step-by-Step Instructions

### Step 1: Always Use HTTPS
```
CF Dashboard > [zone] > SSL/TLS > Edge Certificates
  > Always Use HTTPS: ON
Apply to: agencyos.network, cashclaw.cc, wellnexus.vn
Verify: curl -sI http://agencyos.network | grep -i location
Expected: Location: https://agencyos.network/
```

### Step 2: HSTS on agencyos.network
```
CF Dashboard > agencyos.network > SSL/TLS > Edge Certificates
  > HTTP Strict Transport Security (HSTS)
  > max-age: 31536000 (1 year)
  > includeSubDomains: ON  (verify all subdomains are HTTPS first)
  > preload: ON
Verify: curl -sI https://agencyos.network | grep -i strict
Expected: strict-transport-security: max-age=31536000; includeSubDomains; preload
```

Prerequisite check before enabling includeSubDomains:
```bash
for sub in app. dashboard. docs. landing. api. sophia.; do
  echo -n "${sub}agencyos.network: "
  curl -sw "%{http_code}" -o /dev/null --max-time 5 "https://${sub}agencyos.network"
  echo ""
done
# All must return 200 or 301 (not error)
```

### Step 3: Verify redirects
```bash
bash infra/cloudflare/domains/verify.sh --fast
# Must exit 0 before proceeding
```

### Step 4: Security headers via CF Transform Rules
```
CF Dashboard > [zone] > Rules > Transform Rules > Modify Response Header
Add rule: "Mekong Security Headers"
  When: Always
  Set headers:
    X-Frame-Options: DENY
    X-Content-Type-Options: nosniff
    Referrer-Policy: strict-origin-when-cross-origin
    Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
Apply to: agencyos.network, cashclaw.cc, wellnexus.vn (one rule per zone)
```

### Step 5: CSP Report-Only (24h before enforcing)
```
Add header: Content-Security-Policy-Report-Only
Value: (from infra/cloudflare/domains/security-headers.yaml > csp.zones[zone].policy)
report-uri: https://api.agencyos.network/csp-report
Monitor: CF Dashboard > Analytics > Security > CSP violations for 24h
```

### Step 6: CSP Enforce
```
ONLY after: Phase B1 (IDE UI) confirmed stable + 24h Report-Only monitoring clean
Change header name: Content-Security-Policy-Report-Only → Content-Security-Policy
Remove report-uri directive after stable
```

### Step 7: CORS update in mekong-engine
```bash
# In mekong-engine Workers code (api.agencyos.network):
# Remove: app.agencyos.network, dashboard.agencyos.network, docs.agencyos.network
# Keep:   agencyos.network, sophia.agencyos.network (if needed)
# Test:
curl -sI -X OPTIONS https://api.agencyos.network \
  -H "Origin: https://agencyos.network" \
  -H "Access-Control-Request-Method: POST" | grep -i "access-control"
# Expected: Access-Control-Allow-Origin: https://agencyos.network
```

### Step 8: mekongmind.com
```bash
export CLOUDFLARE_API_TOKEN=<token>
wrangler pages project list | grep -i mekong
# Identify project (likely mekongmind-flagsite)
# CF Dashboard > Pages > [project] > Custom domains > Add: mekongmind.com
# Verify:
curl -sw "%{http_code}" -o /dev/null --max-time 10 "https://mekongmind.com"
# Expected: 200
```

---

## Rollback Procedure

### If a redirect breaks a live domain

```bash
# 1. Identify which redirect rule is causing issues
CF Dashboard > [zone] > Rules > Redirect Rules
# 2. Disable the specific rule (do NOT delete — keep for reference)
# 3. Verify recovery:
bash infra/cloudflare/domains/verify.sh --domain [affected-domain]
# 4. Root cause before re-enabling
```

### If HSTS causes issues (subdomains not HTTPS)

```
CF Dashboard > agencyos.network > SSL/TLS > Edge Certificates > HSTS
  > Disable includeSubDomains (change to OFF)
  > Max-age: 0 (this sends HSTS header with max-age=0, instructing browsers to clear)
WARNING: Browsers that already cached HSTS will honor it for the original max-age period.
Recovery window: up to 1 year for cached clients.
Prevention: ALWAYS verify all subdomains serve HTTPS before enabling includeSubDomains.
```

### DNS snapshot restore

All current DNS state is documented in `infra/cloudflare/domains/production-domains.yaml`.
To restore a record:
```
CF Dashboard > [zone] > DNS > Add record matching yaml spec
```

---

## Verification Commands

```bash
# Full smoke test
bash infra/cloudflare/domains/verify.sh

# Fast (skip gap domains)
bash infra/cloudflare/domains/verify.sh --fast

# Single domain
bash infra/cloudflare/domains/verify.sh --domain agencyos.network

# Security headers only
bash infra/cloudflare/domains/verify.sh --security

# Manual HSTS check
curl -sI https://agencyos.network | grep -i strict-transport

# Manual redirect check
curl -sI https://app.agencyos.network | grep -i location

# CORS preflight check
curl -sI -X OPTIONS https://api.agencyos.network \
  -H "Origin: https://agencyos.network" \
  -H "Access-Control-Request-Method: POST"
```

---

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Merge Astro sites (agencyos-site monolith) | DONE 2026-03-26 |
| 2 | NOWPayments checkout integration | DONE 2026-03-26 |
| 3 | CF Pages deploy scripts | DONE 2026-04-17 (deploy.sh) |
| 4 | 301 Redirects config | DONE 2026-04-17 (redirects.yaml + 4 live) |
| 5 | Verification checklist | DONE 2026-04-17 (verify.sh, 16/17 pass) |
| 6 | Cleanup old CF projects | SCHEDULED 2026-04-30 (after 2-week monitoring) |

Remaining blockers before Phase 6:
- HSTS enabled (Action Item 1)
- mekongmind.com resolved (Action Item 2)
- CORS updated in mekong-engine (Action Item 4)

---

## Contacts / Resources

- CF Account: longtho638-jpg / cashback.mentoring@gmail.com
- CF API token scope: Pages:Edit + Zone:Read (NOT account admin)
- Config files: `infra/cloudflare/domains/`
- Phase log: `infra/cloudflare/domains/PHASE_LOG.md`
- Upstream plan: `plans/260326-2036-domain-consolidation/plan.md`
