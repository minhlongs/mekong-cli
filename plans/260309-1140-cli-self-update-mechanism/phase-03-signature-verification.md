---
title: "Phase 3: Signature Verification System"
description: "Implement Ed25519/GPG signature validation for update security"
status: pending
priority: P1
effort: 2h
branch: master
tags: [phase-6, security, signatures]
created: 2026-03-09
---

# Phase 3: Signature Verification System

## Overview

Implement cryptographic signature verification for CLI updates to prevent supply chain attacks. Validate downloaded artifacts against AgencyOS public key.

## Requirements

1. Support Ed25519 signatures (preferred) or GPG
2. Store public key in CLI (embedded or fetched securely)
3. Verify signature before install
4. Block update if signature fails
5. Clear error messages for users

## Context Links

- Existing stub: `/Users/macbookprom1/mekong-cli/src/cli/auto_updater.py` (GPG class)
- Gateway auth: `/Users/macbookprom1/mekong-cli/src/core/raas_auth.py`
- Certificate store: `/Users/macbookprom1/mekong-cli/src/core/certificate_store.py`

## Key Insights

From reading `src/cli/auto_updater.py`:
- `GPGSignatureVerifier` class exists but has truncated key
- Uses `python-gnupg` library
- Signature downloaded from `.sig` URL

From reading `src/core/certificate_store.py` (referenced in raas_auth.py):
- Device certificate system exists
- Could extend for code signing

## Architecture

### Option A: Ed25519 (Recommended)

```
┌─────────────────────────────────────────────────────────┐
│  Release Process (CI/CD)                                │
├─────────────────────────────────────────────────────────┤
│  1. Build mekong-cli.tar.gz                            │
│  2. Sign with private key:                              │
│     python -m nacl.signing.SignKey                     │
│  3. Upload .sig to GitHub Releases                     │
│  4. Public key embedded in CLI                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Update Verification (CLI)                              │
├─────────────────────────────────────────────────────────┤
│  1. Download mekong-cli.tar.gz                         │
│  2. Download mekong-cli.tar.gz.sig                     │
│  3. Load embedded public key                           │
│  4. Verify: sign_key.verify(signature, data)           │
│  5. Install only if valid                              │
└─────────────────────────────────────────────────────────┘
```

### Option B: GPG (Fallback)

- Use existing `GPGSignatureVerifier` class
- Requires GPG installed on system
- More complex but widely supported

## Implementation Steps

1. **Choose signature algorithm** (Ed25519 recommended)
2. **Generate keypair** for AgencyOS
3. **Embed public key** in CLI source
4. **Create signing script** for CI/CD
5. **Update `SandboxedUpdater.verify()`** to validate

## Related Code Files

**To Create:**
- `src/core/signature_verifier.py` — Ed25519 verification
- `scripts/sign-release.py` — CI/CD signing script
- `src/core/agencyos_public_key.py` — Embedded public key

**To Modify:**
- `src/cli/auto_updater.py` — Integrate new verifier
- `.github/workflows/release.yml` — Add signing step

## Todo List

- [ ] Install PyNaCl for Ed25519 support
- [ ] Generate AgencyOS signing keypair
- [ ] Create `signature_verifier.py` with `Ed25519Verifier` class
- [ ] Embed public key in `agencyos_public_key.py`
- [ ] Create `sign-release.py` script
- [ ] Update `SandboxedUpdater.verify()` to use new verifier
- [ ] Add tests for signature verification
- [ ] Document key management in docs/

## Success Criteria

- [ ] `Ed25519Verifier.verify()` validates signatures
- [ ] Invalid signature blocks update with clear error
- [ ] Valid signature allows install
- [ ] CI/CD signing script works
- [ ] Public key can't be extracted (obfuscated)

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Private key leaked | Critical | Rotate keys, revoke old releases |
| Public key extracted | Medium | Obfuscate, add fake data |
| GPG not installed | Low | Ed25519 is pure Python |
| Verification slow | Low | Signatures are small (~64 bytes) |

## Security Considerations

- **Private key**: Store in secure CI/CD secrets (GitHub Secrets)
- **Public key**: Embed in CLI, consider obfuscation
- **Signature download**: HTTPS only, from GitHub Releases
- **Timing attacks**: Constant-time comparison

## Next Steps

After Phase 3 complete:
- Phase 4: Usage metering integration
