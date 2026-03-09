# Phase 6: CLI License Activation Implementation

**Status:** Ready to implement
**Priority:** P0
**Effort:** 4h

## Overview

Implement `mekong auth activate` command để activate license key với RaaS Gateway, secure storage, và dashboard sync.

## Existing Infrastructure (90% Complete)

| Component | File | Status |
|-----------|------|--------|
| Secure Storage | `src/auth/secure_storage.py` | ✅ macOS Keychain, Windows Vault, Linux AES |
| RaaS Auth Client | `src/core/raas_auth.py` | ✅ JWT/mk_ validation, session cache 5min |
| Gateway Client | `src/core/gateway_client.py` | ✅ Circuit breaker, multi-gateway failover |
| Rate Limit Client | `src/core/rate_limit_client.py` | ✅ 429 handling, exponential backoff |
| Auth CLI Commands | `src/cli/raas_auth_commands.py` | ✅ login/logout/status/validate |

## Gap Analysis

1. ❌ Không có `activate` command riêng biệt
2. ❌ Không có offline validation cache với TTL
3. ❌ Không có explicit dashboard sync handshake
4. ❌ License validation chưa enforce trước khi execute commands

## Implementation Plan

### Phase 1: Activate Command (1h)

**File:** `src/cli/raas_auth_commands.py` (modify)

Add new `activate` subcommand:
```python
@app.command("activate")
def activate(
    key: str = typer.Option(..., "--key", "-k", help="License key (mk_...)"),
    no_persist: bool = typer.Option(False, "--no-persist", help="Session only"),
) -> None:
    """Activate license key against RaaS Gateway."""
```

**Flow:**
1. Accept `--key=mk_...` parameter
2. Call `RaaSAuthClient.activate(key)` method
3. Store in secure storage (keychain/vault/encrypted file)
4. Display activation success with dashboard link

### Phase 2: RaaS Auth Client activate() Method (1h)

**File:** `src/core/raas_auth.py` (modify)

Add `activate()` method:
```python
def activate(self, license_key: str, persist: bool = True) -> ActivateResult:
    """
    Activate license key against RaaS Gateway.

    POST /v1/license/activate with:
    - Authorization: Bearer mk_...
    - X-Cert-ID: device_id
    - X-Cert-Sig: device_signature
    """
```

**API Request:**
```http
POST https://raas.agencyos.network/v1/license/activate
Authorization: Bearer mk_abc123...
X-Cert-ID: {device_id}
X-Cert-Sig: {signature}

Response:
{
  "tenant_id": "tenant_123",
  "tier": "pro",
  "agency_id": "agency_456",
  "plan_tier": "pro",
  "rate_limit": 100,
  "features": ["feature1", "feature2"],
  "expires_at": "2026-12-31T23:59:59Z"
}
```

### Phase 3: License Validation Middleware (1h)

**File:** `src/core/gateway_client.py` (modify)

Add license validation check trước khi execute commands:

```python
def ensure_valid_license(self) -> ValidateResult:
    """Ensure license is valid before command execution."""
    session = self.auth.get_session()
    if not session.authenticated:
        return ValidateResult(valid=False, error="Not authenticated")

    if not session.is_valid():
        # Try refresh
        refresh_result = self.auth.refresh_session()
        if not refresh_result.success:
            return ValidateResult(valid=False, error="Session expired")

    return ValidateResult(valid=True)
```

**Integration:** Hook vào `GatewayClient.request()` để check license trước mỗi API call.

### Phase 4: Dashboard Sync (1h)

**File:** `src/core/activation_sync.py` (create)

Sync activation event to AgencyOS dashboard:

```python
def sync_activation(tenant_id: str, agency_id: str, tier: str) -> None:
    """Sync activation metadata to dashboard."""
    # POST /v1/dashboard/sync
    # {
    #   "event": "license_activated",
    #   "tenant_id": "...",
    #   "agency_id": "...",
    #   "tier": "...",
    #   "timestamp": "ISO8601"
    # }
```

## Files to Modify

| File | Changes |
|------|---------|
| `src/cli/raas_auth_commands.py` | Add `activate` command |
| `src/core/raas_auth.py` | Add `activate()` method, `ActivateResult` dataclass |
| `src/core/gateway_client.py` | Add `ensure_valid_license()` method |
| `src/core/activation_sync.py` | NEW: Dashboard sync webhook bridge |
| `src/main.py` | Ensure auth app is registered |

## API Endpoints Required

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/license/activate` | POST | Activate license with device cert |
| `/v1/license/validate` | POST | Validate license key |
| `/v1/dashboard/sync` | POST | Sync activation event to dashboard |

## Storage Format

### Secure Storage (Platform Native)
```
macOS Keychain:
  Service: mekong-cli
  Account: {username}
  Label: raas_license_key
  Value: mk_abc123...
```

### Session Cache (`~/.mekong/session.json`)
```json
{
  "tenant_id": "tenant_abc123",
  "tier": "pro",
  "agency_id": "agency_456",
  "plan_tier": "pro",
  "license_key": "mk_...last4",
  "features": ["feature1"],
  "expires_at": "2026-12-31T23:59:59Z",
  "cached_at": "2026-03-09T14:37:00Z",
  "ttl_seconds": 300
}
```

## Success Criteria

1. ✅ `mekong auth activate -k mk_...` works
2. ✅ License stored securely trong platform keychain/vault
3. ✅ Validation succeeds với RaaS Gateway
4. ✅ Dashboard hiển thị activation status sau sync
5. ✅ Subsequent CLI commands include client ID trong usage reporting

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gateway downtime | High | Circuit breaker + offline cache |
| Secure storage fails | Medium | Fallback to encrypted file |
| Dashboard sync fails | Low | Async retry queue |

## Testing

```bash
# Test activate command
mekong auth activate -k mk_test_key_123

# Test status
mekong auth status

# Test license validation
mekong cook "test goal"

# Test offline mode
# 1. Activate license
# 2. Disable network
# 3. Run command - should work with cached session
```
