# Code Review: Multi-Tenant Architecture

**Date:** 2026-04-10
**Reviewer:** code-reviewer agent
**Verdict:** COMMENT (no critical blockers, 2 high-priority items)

---

## Scope

| File | Lines | Status |
|------|-------|--------|
| `src/api/tenant_config_loader.py` | 34 | PASS |
| `src/raas/revenue_router.py` | 262 | FAIL (>200) |
| `landing/build.py` | 110 | PASS |
| `landing/template.html` | 73 | PASS |
| `landing/static/style.css` | 150 | PASS |
| `tenants/_schema.json` | 31 | PASS |
| `tenants/dev-agency.json` | 20 | PASS |
| `tenants/trading-desk.json` | 21 | PASS |
| `tenants/content-studio.json` | 21 | PASS |

---

## Overall Assessment

Clean, well-structured multi-tenant architecture. Tenant configs as static JSON + LRU cache is KISS-compliant. Jinja2 template rendering and API endpoints are well-separated. Two high-priority issues: XSS via unescaped Jinja2 output and `revenue_router.py` exceeding 200-line limit.

---

## Critical Issues

None.

---

## High Priority

### H1. XSS — Jinja2 autoescape disabled (landing/build.py)

**File:** `landing/build.py` line 34
**Impact:** All tenant JSON values (name, tagline, description, use_cases) render unescaped into HTML. If any tenant JSON contains `<script>` or HTML entities, they execute in the browser.

```python
# CURRENT (autoescape=False by default)
env = Environment(loader=FileSystemLoader(str(ROOT)))

# FIX
env = Environment(loader=FileSystemLoader(str(ROOT)), autoescape=True)
```

**Mitigating factors:** Tenant JSONs are developer-controlled static files, not user input. Risk is low but defense-in-depth matters. The hub page (`build_hub_page`) uses f-strings with tenant data directly in HTML — also unescaped.

### H2. revenue_router.py exceeds 200-line limit (262 lines)

**File:** `src/raas/revenue_router.py`
**Impact:** Violates project file size rule. New tenant endpoints (`/v1/tenants`, `/v1/tenants/{slug}`, `/v1/departments`) could be extracted.

**Suggested split:**
- Keep `revenue_router.py` with onboard + webhook + pricing (lines 1-191)
- Extract `tenant_router.py` with `/v1/tenants`, `/v1/tenants/{slug}`, `/v1/departments` (lines 193-263)

---

## Medium Priority

### M1. LRU cache never invalidates (tenant_config_loader.py)

`load_all_tenants()` uses `@lru_cache(maxsize=1)` — cached forever for the process lifetime. If tenant JSON files change while the server runs, stale configs served until restart. Acceptable for static deploys but risky for long-running dev/staging servers.

**Fix options:**
- Add a `clear_cache()` function: `load_all_tenants.cache_clear()`
- Use TTL-based cache instead

### M2. Duplicate pricing tier definitions (DRY violation)

`PRICING_TIERS` defined in two places:
- `src/raas/revenue_router.py` lines 42-46
- `landing/build.py` lines 12-16

If pricing changes, both must be updated manually.

**Fix:** Extract to shared config or have `build.py` import from `revenue_router.py`.

### M3. hub page bypasses template (landing/build.py)

`build_hub_page()` (line 75) uses raw f-strings with tenant data to build HTML. This bypasses Jinja2 entirely — no escaping, no template reuse. Tenant names/taglines containing quotes or `<>` will break HTML structure.

**Fix:** Create a `hub_template.html` Jinja2 template.

### M4. `description` not in schema required fields

`_schema.json` line 4: `required` list does not include `description`. But `template.html` line 7 uses `{{ tenant.description }}` — would render empty/undefined for tenants without it. All 3 checked tenant JSONs do include it, but schema doesn't enforce.

### M5. Webhook HMAC: Polar may use different signature format

Line 120-131 in `revenue_router.py`: The webhook reads `webhook-signature` header and does plain `hmac.new(...).hexdigest()` comparison. Polar.sh actual webhook signatures may use a different format (e.g., `v1=<hex>` prefix, or base64). If the format doesn't match, all webhooks silently fail with 401.

**Action:** Verify against Polar.sh webhook docs for exact signature format.

---

## Low Priority

### L1. `onboard_tenant` ignores `req.name`, uses `req.email` as name

Line 99: `store.create_tenant(name=req.email)` — the `OnboardRequest.name` field is declared but never used. Either remove `name` from the request model or pass it through.

### L2. No JSON schema validation at load time

`tenant_config_loader.py` loads JSONs without validating against `_schema.json`. Invalid tenant configs silently load and may cause KeyError at render time.

### L3. `_redirects` file assumes CF Pages deployment

`build.py` line 69-70 generates a `_redirects` file specific to Cloudflare Pages. Fine for current infra but couples build output to hosting platform.

---

## Edge Cases Found by Scout

1. **Missing `branding` key in tenant JSON** — `list_tenants()` endpoint (line 248) accesses `t["branding"]["accent_color"]` and `t["branding"]["icon"]` without safety checks. Schema requires `branding`, but if a malformed JSON slips through, server crashes with 500.
2. **`featured_departments` empty array** — `/v1/departments?tenant=X` with empty `featured_departments` returns 0 departments. Not a bug, but UX concern.
3. **Slug collision** — `tenant_config_loader.py` uses `cfg["slug"]` as dict key. If two JSON files have the same slug, last-sorted file wins silently.
4. **Path traversal** — Not an issue. Loader uses `TENANTS_DIR.glob("*.json")` which stays within the tenants directory. No user input reaches file path construction.

---

## Positive Observations

- Clean separation: loader, router, builder, template, CSS each in own file
- Schema with regex pattern for slug (`^[a-z0-9-]+$`) prevents bad slugs
- `_schema.json` files skipped via `startswith("_")` — clean convention
- Proper 404 for missing tenant in `/v1/tenants/{slug}`
- HMAC signature verification on webhook (timing-safe via `compare_digest`)
- CSS uses custom properties for theming — per-tenant `--accent` override is elegant
- All tenant JSONs checked are consistent in structure

---

## Recommended Actions

1. **Enable Jinja2 autoescape** in `build.py` (H1) — 1-line fix
2. **Split revenue_router.py** — extract tenant endpoints to `tenant_router.py` (H2)
3. **Fix hub_page XSS** — convert to Jinja2 template (M3)
4. **Extract shared PRICING_TIERS** to avoid DRY violation (M2)
5. **Verify Polar webhook signature format** against docs (M5)
6. **Add `description` to schema required fields** (M4)

---

## Metrics

| Metric | Value |
|--------|-------|
| Files reviewed | 9 |
| Total LOC | 660 |
| File size violations | 1 (`revenue_router.py`: 262 lines) |
| Security issues | 1 high (XSS/autoescape), 1 medium (webhook sig format) |
| DRY violations | 1 (pricing tiers duplicated) |
| Missing error handling | 1 (branding key access in list_tenants) |
