---
title: "Certificate-Based Authentication Implementation"
description: "Implement device certificate auth for mekong-cli → RaaS Gateway"
status: pending
priority: P1
effort: 8h
branch: master
tags: [security, authentication, raas, certificate]
created: 2026-03-08
---

# Certificate-Based Authentication Plan

## Overview

Implement certificate-based device authentication for mekong-cli to replace/augment current Bearer token auth with RaaS Gateway.

## Architecture

```
mekong-cli ──[X-Cert-ID + X-Cert-Sig]──▶ RaaS Gateway
                                            │
                                            ▼
                                     Device Registry (KV)
                                            │
                                            ▼
                                     Certificate Validation
```

## Phases

| Phase | Description | Effort | Status |
|-------|-------------|--------|--------|
| 1 | Device Certificate Generation (CLI) | 2h | pending |
| 2 | Gateway Certificate Validation | 2h | pending |
| 3 | API Request Integration | 2h | pending |
| 4 | Security & Compliance | 2h | pending |

## Files to Create

- `src/core/device_certificate.py` - Certificate generation + signing
- `src/core/certificate_store.py` - Secure storage + retrieval
- `src/core/http_client.py` - HTTP client with certificate headers
- `src/core/certificate_rotator.py` - Auto-rotation logic
- `src/core/revocation_checker.py` - Revocation status checks
- `apps/raas-gateway/src/certificate-validator.js` - Certificate validation
- `apps/raas-gateway/src/device-registry.js` - Device tracking
- `docs/CERTIFICATE_AUTH.md` - Documentation

## Files to Modify

- `src/core/raas_auth.py` - Add certificate auth flow
- `src/auth/secure_storage.py` - Add certificate storage
- `src/lib/raas_gate.py` - Use certificate headers
- `apps/raas-gateway/index.js` - Add certificate endpoints
- `apps/raas-gateway/src/edge-auth-handler.js` - Support cert headers

## Dependencies

- `cryptography` library for ECDSA P-256
- Cloudflare KV for device registry
- Platform secure storage (Keychain/Windows Vault)

## Risks

| Risk | Mitigation |
|------|------------|
| Private key extraction | Use platform secure storage only |
| Certificate theft | Device fingerprint binding |
| Multi-device abuse | Per-tenant device limits |

## Success Criteria

- [ ] Certificate generated on `mekong init`
- [ ] Certificate stored securely
- [ ] All gateway requests include cert headers
- [ ] Gateway validates certificate signatures
- [ ] Certificate rotation works automatically
- [ ] Revocation checking functional

## Open Questions

1. ECDSA vs RSA key algorithm?
2. Default certificate expiry duration?
3. Device limits per tenant tier?
4. Offline mode support duration?
