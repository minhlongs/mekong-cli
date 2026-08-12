# SSO Implementation Plan
**Status:** Stub-only. No SAML runtime.  
**Priority:** P2 — not blocking ship.  
**Date:** 2026-07-31

---



## Current Stub State

`sso_providers.py` exposes:
- `SAMLProvider` dataclass holding config fields (`entity_id`, `sso_url`, `x509_cert`, `attribute_mapping`)
- In-memory `_registry` dict with CRUD helpers (`register/get/list/create/update/delete`)
- `configure_from_env()` reading `MEKONG_SSO_*` env vars
- `build_saml_auth_request()` and `verify_saml_response()` — both raise `SSOProviderError("not implemented yet")`

`__init__.py` exposes:
- `SSOProviderConfig` dataclass mirroring the same fields
- `EnterpriseConfig` grouping `sso_providers` dict + SLA/support fields
- `register_provider()`, `get_provider()`, `get_enterprise_config()`

**Observations:**
- Two parallel registries exist (`sso_providers._registry` dict vs `_providers` dict in `__init__`). They are not wired together — `configure_from_env()` in each file populates its own independently.
- No route/endpoint code present yet; SSO is config-only today.



## python3-saml Integration Path

Add `python3-saml` (Okta's `pysaml2`-adjacent library) as a production dependency.  
Replace `raise SSOProviderError(...)` stubs with:

1. **`build_auth_request()`** — OneLogin-style `OneLogin_Saml2_Auth` init with `SP` config from env, call `login()` to produce AuthnRequest + RelayState redirect URL.  
2. **`verify_response()`** — Parse POSTed SAMLResponse, extract attributes, apply `attribute_mapping`, return normalized user dict (`email`, `name`, `role`).  
3. **Metadata endpoint** — Serve IdP-initiated SP metadata XML at `/enterprise/sso/metadata/{provider_id}`.



## Enterprise Tier Integration

- SSO providers register under `EnterpriseConfig.sso_providers` keyed by `provider_id`.
- After SAML assertion: create/link local account, map `role` attribute to internal tier permissions.
- Auth middleware gate: if `EnterpriseConfig` has any enabled provider, expose `/login/sso/{provider_id}` route; otherwise SSO is invisible (opt-in per tenant).
- Configure via `MEKONG_SSO_*` env vars (already plumbed) or admin API calling `create_sso_provider()`.



## Effort Estimate

| Phase | Scope | Effort |
|-------|-------|--------|
| 1 — Dedup registries | Merge `sso_providers._registry` into `__init__._providers` (single source of truth) | 2-3 hrs |
| 2 — python3-saml wiring | Replace stubs, SP metadata endpoint, SAMLResponse POST handler | 4-6 hrs |
| 3 — Enterprise route + middleware | `/login/sso/{id}`, `/sso/acs`, account linking, role mapping | 3-4 hrs |
| 4 — Tests | Mock SAML round-trip, registry CRUD, env configure | 3-4 hrs |
| **Total** | | **~2-3 days** |



## Unresolved Questions

- Which IdP(s) target first (Okta, Azure AD, Google Workspace)? Affects attribute mapping defaults.
- Should SSO config be tenant-scoped (per-org stored in D1) or deployment-scoped (env-only)?
- python3-saml vs pysaml2 — python3-saml is lighter but less actively maintained; worth confirming compatibility with Python 3.11+.
