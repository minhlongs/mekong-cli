# Research Report: Certificate-Based Authentication for Mekong CLI

**Date:** 2026-03-08
**Author:** Planner Agent
**Work Context:** /Users/macbookprom1/mekong-cli

---

## 1. Executive Summary

This report analyzes the current authentication architecture and proposes a certificate-based authentication system for device identity verification and license compliance enforcement.

### Current State
- **Auth Method:** Bearer token (mk_ API keys + JWT)
- **Gateway:** Cloudflare Worker at `raas.agencyos.network`
- **Storage:** Secure storage (Keychain/Windows Vault/Linux encrypted)
- **Validation:** Edge-side JWT decoding + API key lookup

### Proposed State
- **Auth Method:** ECDSA P-256 signed device certificates + Bearer token
- **Certificate Binding:** Device fingerprint (CPU, disk, MAC, OS UUID)
- **Validation:** Gateway verifies certificate signature + checks revocation
- **Benefits:** Device-level tracking, revocation enforcement, offline validation

---

## 2. Current Architecture Analysis

### 2.1 Authentication Flow (Current)

```
┌─────────────────────────────────────────────────────────────────┐
│ CURRENT AUTH FLOW                                               │
└─────────────────────────────────────────────────────────────────┘

User sets RAAS_LICENSE_KEY env var
           │
           ▼
┌──────────────────┐
│ src/core/        │
│ raas_auth.py     │
│ RaaSAuthClient   │
└──────────────────┘
           │
           │ validate_credentials()
           ▼
┌──────────────────┐     POST /v1/auth/validate      ┌──────────────────┐
│ Python requests  │ ──────────────────────────────▶ │ RaaS Gateway     │
│ HTTP client      │     Headers:                    │ (Cloudflare)     │
│                  │     - Authorization: Bearer X   │                  │
└──────────────────┘                                  └──────────────────┘
                                                               │
                                                               │ Edge Auth:
                                                               │ - JWT decode
                                                               │ - API key lookup
                                                               │ - Tenant context
                                                               ▼
                                                      Returns: tenant_id, tier, features
```

### 2.2 Key Files Analyzed

| File | Purpose | Key Functions |
|------|---------|---------------|
| `src/core/raas_auth.py` | RaaS authentication client | `validate_credentials()`, `get_session()`, `login()`, `logout()` |
| `src/raas/completion_certificate.py` | Certificate generation | `CompletionCertificate`, `generate_certificate()`, SHA3-256 signatures |
| `src/raas/final_phase_validator.py` | Phase 6 validation | `validate_gateway_attestation()`, `validate_license_authentication()` |
| `src/auth/secure_storage.py` | Platform secure storage | `SecureStorage`, `store_license()`, `get_license()` |
| `src/lib/raas_gate.py` | License gate | `check()`, `validate_remote()`, quota enforcement |
| `apps/raas-gateway/index.js` | Gateway router | `/v1/auth/validate`, `/v1/usage`, rate limiting |
| `apps/raas-gateway/src/edge-auth-handler.js` | Edge auth | `authenticate()`, JWT decode, API key validation |

### 2.3 HTTP Request Pattern (Current)

```python
# src/core/raas_auth.py:495
response = requests.post(
    f"{self.gateway_url}{endpoint}",
    headers={"Authorization": f"Bearer {token}"},
    timeout=10,
)

# src/lib/raas_gate.py:715
response = requests.post(
    f"{self._remote_url}/v1/auth/validate",
    headers={"Authorization": f"Bearer {self._license_key}"},
    timeout=10,
)
```

**Issue:** Only Bearer token for auth - no device fingerprinting, no certificate binding.

---

## 3. Proposed Architecture

### 3.1 Certificate Auth Flow (New)

```
┌─────────────────────────────────────────────────────────────────┐
│ PROPOSED CERTIFICATE AUTH FLOW                                  │
└─────────────────────────────────────────────────────────────────┘

Phase 1: Device Registration (One-time)
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  mekong-cli  │────▶│  RaaS Gateway    │────▶│  Device KV      │
│              │     │                  │     │  Storage        │
│ 1. Generate  │     │ 2. Verify Bearer │     │                 │
│    device ID │     │    token         │     │ Store:          │
│ 2. Create    │     │ 3. Register cert │     │ - cert_id       │
│    ECDSA key │     │ 4. Return signed │     │ - device_fp     │
│ 3. Sign cert │     │    certificate   │     │ - tenant_id     │
│              │◀────│    + device_id   │     │ - public_key    │
└──────────────┘     └──────────────────┘     └─────────────────┘

Phase 2: Authenticated Requests (Every call)
┌──────────────┐     ┌──────────────────┐
│  mekong-cli  │────▶│  RaaS Gateway    │
│              │     │                  │
│ Headers:     │     │ Validate:        │
│ - X-Cert-ID  │     │ - Signature      │
│ - X-Cert-Sig │     │ - Revocation     │
│ - Bearer X   │     │ - Expiry         │
└──────────────┘     └──────────────────┘
```

### 3.2 Certificate Structure

```python
@dataclass
class DeviceCertificate:
    # Identity
    certificate_id: str          # CERT-{device_id}-{timestamp}
    device_id: str               # SHA3-256(machine_identifiers)
    device_fingerprint: dict     # Hardware identifiers hash
    tenant_id: str               # Associated tenant
    license_key_hash: str        # Linked license (SHA3-256)

    # Validity
    issued_at: datetime          # Issue time (UTC)
    expires_at: datetime         # Expiry (default: 30 days)
    revocation_status: str       # active | revoked | expired

    # Cryptography
    signature: str               # ECDSA P-256 signature
    public_key: str              # PEM-encoded public key
    signature_algorithm: str     # ECDSA-P256-SHA256
```

### 3.3 Device Fingerprint Generation

```python
def generate_device_fingerprint() -> dict:
    """Generate unique device fingerprint from hardware."""
    import platform
    import hashlib
    import uuid

    # Collect hardware identifiers
    identifiers = {
        "cpu_serial": get_cpu_serial(),      # Platform-specific
        "disk_serial": get_disk_serial(),    # Platform-specific
        "mac_address": get_mac_hash(),       # SHA3-256 of MAC
        "os_uuid": str(uuid.getnode()),      # OS-level UUID
        "platform": platform.platform(),
    }

    # Hash each field for privacy
    return {
        "cpu_hash": hashlib.sha3_256(identifiers["cpu_serial"].encode()).hexdigest()[:16],
        "disk_hash": hashlib.sha3_256(identifiers["disk_serial"].encode()).hexdigest()[:16],
        "mac_hash": hashlib.sha3_256(identifiers["mac_address"].encode()).hexdigest()[:16],
        "os_uuid": identifiers["os_uuid"],
    }

def generate_device_id(fingerprint: dict) -> str:
    """Generate unique device ID from fingerprint."""
    payload = f"{fingerprint['cpu_hash']}:{fingerprint['disk_hash']}:{fingerprint['mac_hash']}"
    return f"DEV-{hashlib.sha3_256(payload.encode()).hexdigest()[:16].upper()}"
```

---

## 4. Implementation Details

### 4.1 Phase 1: Device Certificate Generation (CLI)

#### File: `src/core/device_certificate.py` (NEW)

```python
"""
Device Certificate Generator — ECDSA P-256 signed certificates

Generates device-bound certificates for RaaS Gateway authentication.
"""

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend


@dataclass
class DeviceCertificate:
    certificate_id: str
    device_id: str
    device_fingerprint: Dict[str, str]
    tenant_id: str
    license_key_hash: str
    issued_at: str
    expires_at: str
    signature: str
    public_key_pem: str
    signature_algorithm: str = "ECDSA-P256-SHA256"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class DeviceCertificateGenerator:
    """Generate and sign device certificates."""

    CERTIFICATE_VALIDITY_DAYS = 30

    def __init__(self):
        self.backend = default_backend()
        self._key_pair: Optional[ec.EllipticCurvePrivateKey] = None

    def generate_device_fingerprint(self) -> Dict[str, str]:
        """Generate device fingerprint from hardware identifiers."""
        # Platform-specific implementation
        pass

    def generate_device_id(self, fingerprint: Dict[str, str]) -> str:
        """Generate unique device ID from fingerprint."""
        payload = ":".join([
            fingerprint.get("cpu_hash", ""),
            fingerprint.get("disk_hash", ""),
            fingerprint.get("mac_hash", ""),
        ])
        return f"DEV-{hashlib.sha3_256(payload.encode()).hexdigest()[:16].upper()}"

    def generate_key_pair(self) -> ec.EllipticCurvePrivateKey:
        """Generate ECDSA P-256 key pair."""
        self._key_pair = ec.generate_private_key(
            ec.SECP256R1(),  # NIST P-256 curve
            self.backend
        )
        return self._key_pair

    def generate_certificate(
        self,
        tenant_id: str,
        license_key: str,
    ) -> DeviceCertificate:
        """Generate signed device certificate."""
        # Generate fingerprint and device ID
        fingerprint = self.generate_device_fingerprint()
        device_id = self.generate_device_id(fingerprint)

        # Generate key pair
        key_pair = self.generate_key_pair()

        # Create certificate payload
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=self.CERTIFICATE_VALIDITY_DAYS)

        payload = {
            "device_id": device_id,
            "tenant_id": tenant_id,
            "license_key_hash": hashlib.sha3_256(license_key.encode()).hexdigest(),
            "issued_at": now.isoformat(),
            "expires_at": expires.isoformat(),
        }

        # Sign payload with private key
        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        signature = key_pair.sign(
            payload_bytes,
            ec.ECDSA(hashes.SHA256())
        )

        # Export public key
        public_key_pem = key_pair.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        # Generate certificate ID
        cert_id = f"CERT-{device_id}-{int(now.timestamp())}"

        return DeviceCertificate(
            certificate_id=cert_id,
            device_id=device_id,
            device_fingerprint=fingerprint,
            tenant_id=tenant_id,
            license_key_hash=payload["license_key_hash"],
            issued_at=payload["issued_at"],
            expires_at=payload["expires_at"],
            signature=signature.hex(),
            public_key_pem=public_key_pem,
        )

    def verify_certificate_signature(
        self,
        certificate: DeviceCertificate,
        payload: Dict[str, Any]
    ) -> bool:
        """Verify certificate signature using public key."""
        from cryptography.hazmat.primitives import serialization

        # Load public key
        public_key = serialization.load_pem_public_key(
            certificate.public_key_pem.encode(),
            backend=self.backend
        )

        # Verify signature
        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        signature_bytes = bytes.fromhex(certificate.signature)

        try:
            public_key.verify(
                signature_bytes,
                payload_bytes,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except Exception:
            return False
```

#### File: `src/core/certificate_store.py` (NEW)

```python
"""
Certificate Store — Secure storage for device certificates

Uses platform secure storage (Keychain/Windows Vault/Linux encrypted)
for private keys and certificate data.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from src.auth.secure_storage import get_secure_storage, SecureStorage
from src.core.device_certificate import DeviceCertificate


CERTIFICATE_FILE = "~/.mekong/device-certificate.json"
PRIVATE_KEY_FILE = "~/.mekong/device-private-key.pem"


class CertificateStore:
    """Secure storage for device certificates."""

    def __init__(self, secure_storage: Optional[SecureStorage] = None):
        self.secure_storage = secure_storage or get_secure_storage()
        self.cert_path = Path(CERTIFICATE_FILE).expanduser()
        self.key_path = Path(PRIVATE_KEY_FILE).expanduser()

    def store_certificate(
        self,
        certificate: DeviceCertificate,
        private_key_pem: str
    ) -> None:
        """Store certificate and private key securely."""
        # Ensure directory exists
        self.cert_path.parent.mkdir(parents=True, exist_ok=True)

        # Store certificate as JSON
        with open(self.cert_path, "w") as f:
            json.dump(certificate.to_dict(), f, indent=2)
        self.cert_path.chmod(0o600)

        # Store private key in secure storage
        self.secure_storage.store_credential(
            f"device_private_key:{certificate.device_id}",
            private_key_pem
        )

    def load_certificate(self) -> Optional[DeviceCertificate]:
        """Load certificate from disk."""
        if not self.cert_path.exists():
            return None

        try:
            with open(self.cert_path, "r") as f:
                data = json.load(f)
            return DeviceCertificate(**data)
        except Exception:
            return None

    def load_private_key(self, device_id: str) -> Optional[str]:
        """Load private key from secure storage."""
        return self.secure_storage.get_credential(
            f"device_private_key:{device_id}"
        )

    def delete_certificate(self) -> bool:
        """Delete certificate and private key."""
        deleted = False

        if self.cert_path.exists():
            self.cert_path.unlink()
            deleted = True

        # Clear secure storage (device_id unknown, try all)
        # Platform-specific cleanup

        return deleted

    def has_valid_certificate(self) -> bool:
        """Check if valid certificate exists."""
        cert = self.load_certificate()
        if not cert:
            return False

        # Check expiry
        from datetime import datetime, timezone
        expires = datetime.fromisoformat(cert.expires_at)
        return datetime.now(timezone.utc) < expires
```

### 4.2 Phase 2: Gateway Certificate Validation

#### File: `apps/raas-gateway/src/certificate-validator.js` (NEW)

```javascript
/**
 * Certificate Validator — ECDSA signature verification at edge
 * Validates device certificates for RaaS Gateway
 */

import { verifySignature } from './crypto-utils.js';

/**
 * Validate certificate from request headers
 * @param {Request} request
 * @param {object} env - Cloudflare environment bindings
 * @returns {Promise<{valid: boolean, tenantId: string, deviceId: string, error: string}>}
 */
export async function validateCertificate(request, env) {
  const certId = request.headers.get('X-Cert-ID');
  const certSig = request.headers.get('X-Cert-Sig');
  const authHeader = request.headers.get('Authorization');

  if (!certId || !certSig) {
    return { valid: false, error: 'Missing certificate headers' };
  }

  // Fetch certificate from KV storage
  let certData;
  try {
    certData = await env.CERT_KV.get(certId, 'json');
    if (!certData) {
      return { valid: false, error: 'Certificate not found' };
    }
  } catch (err) {
    return { valid: false, error: 'Certificate lookup failed' };
  }

  // Check expiry
  const expiresAt = new Date(certData.expires_at);
  if (expiresAt < new Date()) {
    return { valid: false, error: 'Certificate expired' };
  }

  // Check revocation
  try {
    const revoked = await env.REVOCATION_KV.get(certId);
    if (revoked === 'revoked') {
      return { valid: false, error: 'Certificate revoked' };
    }
  } catch (err) {
    console.error('Revocation check failed:', err);
  }

  // Extract payload for verification
  const payload = {
    device_id: certData.device_id,
    tenant_id: certData.tenant_id,
    license_key_hash: certData.license_key_hash,
    issued_at: certData.issued_at,
    expires_at: certData.expires_at,
  };

  // Verify signature using public key
  const isValid = await verifySignature(
    certData.public_key_pem,
    payload,
    certData.signature
  );

  if (!isValid) {
    return { valid: false, error: 'Signature verification failed' };
  }

  // Certificate valid — return tenant context
  return {
    valid: true,
    tenantId: certData.tenant_id,
    deviceId: certData.device_id,
    certId: certId,
  };
}

/**
 * Register new device certificate
 * @param {Request} request
 * @param {object} env
 * @returns {Promise<{success: boolean, certId: string, error: string}>}
 */
export async function registerCertificate(request, env) {
  try {
    const body = await request.json();
    const { certificate, device_fingerprint } = body;

    // Verify Bearer token first
    const authHeader = request.headers.get('Authorization');
    if (!authHeader?.startsWith('Bearer ')) {
      return { success: false, error: 'Missing Bearer token' };
    }

    // Validate license key from certificate matches Bearer token
    // (Implementation depends on existing auth handler)

    // Store certificate in KV
    await env.CERT_KV.put(
      certificate.certificate_id,
      JSON.stringify(certificate),
      { expirationTtl: 30 * 24 * 60 * 60 }  // 30 days
    );

    // Store device-to-cert mapping
    await env.CERT_KV.put(
      `device:${certificate.device_id}`,
      certificate.certificate_id
    );

    return {
      success: true,
      certId: certificate.certificate_id,
      deviceId: certificate.device_id,
    };
  } catch (err) {
    return { success: false, error: err.message };
  }
}
```

#### File: `apps/raas-gateway/src/crypto-utils.js` (NEW)

```javascript
/**
 * Crypto Utilities — ECDSA signature verification
 */

/**
 * Verify ECDSA P-256 signature
 * @param {string} publicKeyPem - PEM-encoded public key
 * @param {object} payload - Signed payload object
 * @param {string} signatureHex - Hex-encoded signature
 * @returns {Promise<boolean>}
 */
export async function verifySignature(publicKeyPem, payload, signatureHex) {
  try {
    // Import public key
    const publicKey = await crypto.subtle.importKey(
      'spki',
      pemToArrayBuffer(publicKeyPem),
      { name: 'ECDSA', namedCurve: 'P-256' },
      true,
      ['verify']
    );

    // Prepare data
    const payloadBytes = new TextEncoder().encode(
      JSON.stringify(payload, Object.keys(payload).sort())
    );
    const signature = hexToArrayBuffer(signatureHex);

    // Verify
    return await crypto.subtle.verify(
      { name: 'ECDSA', hash: 'SHA-256' },
      publicKey,
      signature,
      payloadBytes
    );
  } catch (err) {
    console.error('Signature verification failed:', err);
    return false;
  }
}

/**
 * Convert PEM to ArrayBuffer
 */
function pemToArrayBuffer(pem) {
  const base64 = pem
    .replace('-----BEGIN PUBLIC KEY-----', '')
    .replace('-----END PUBLIC KEY-----', '')
    .replace(/\s/g, '');
  return Uint8Array.from(atob(base64), c => c.charCodeAt(0)).buffer;
}

/**
 * Convert hex to ArrayBuffer
 */
function hexToArrayBuffer(hex) {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i / 2] = parseInt(hex.substr(i, 2), 16);
  }
  return bytes.buffer;
}
```

### 4.3 Phase 3: API Request Integration

#### File: `src/core/http_client.py` (NEW)

```python
"""
HTTP Client — RaaS Gateway client with certificate authentication

Automatically includes certificate headers in all requests.
"""

import requests
from typing import Optional, Dict, Any
from src.core.certificate_store import CertificateStore
from src.core.device_certificate import DeviceCertificate, DeviceCertificateGenerator


class RaaSHttpClient:
    """HTTP client with certificate authentication."""

    def __init__(self, gateway_url: str):
        self.gateway_url = gateway_url
        self.cert_store = CertificateStore()
        self.cert_generator = DeviceCertificateGenerator()
        self._certificate: Optional[DeviceCertificate] = None

    def _get_certificate(self) -> Optional[DeviceCertificate]:
        """Get or load certificate."""
        if self._certificate is None:
            self._certificate = self.cert_store.load_certificate()
        return self._certificate

    def _build_headers(
        self,
        include_cert: bool = True,
        bearer_token: Optional[str] = None
    ) -> Dict[str, str]:
        """Build request headers with certificate auth."""
        headers = {"Content-Type": "application/json"}

        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"

        if include_cert:
            cert = self._get_certificate()
            if cert:
                headers["X-Cert-ID"] = cert.certificate_id
                headers["X-Cert-Sig"] = cert.signature

        return headers

    def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        bearer_token: Optional[str] = None,
        timeout: int = 10,
    ) -> requests.Response:
        """POST request with certificate auth."""
        url = f"{self.gateway_url}{endpoint}"
        headers = self._build_headers(bearer_token=bearer_token)

        return requests.post(
            url,
            headers=headers,
            json=json_data,
            timeout=timeout,
        )

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        bearer_token: Optional[str] = None,
        timeout: int = 10,
    ) -> requests.Response:
        """GET request with certificate auth."""
        url = f"{self.gateway_url}{endpoint}"
        headers = self._build_headers(bearer_token=bearer_token)

        return requests.get(
            url,
            headers=headers,
            params=params,
            timeout=timeout,
        )

    def register_certificate(self, bearer_token: str) -> Dict[str, Any]:
        """Register new device certificate with gateway."""
        cert = self.cert_generator.generate_certificate(
            tenant_id="pending",  # Will be set by gateway
            license_key=bearer_token,
        )

        response = self.post(
            "/v1/cert/register",
            json_data={"certificate": cert.to_dict()},
            bearer_token=bearer_token,
        )

        if response.status_code == 200:
            # Store certificate on success
            private_key = self.cert_generator.export_private_key()
            self.cert_store.store_certificate(cert, private_key)
            return response.json()
        else:
            raise Exception(f"Certificate registration failed: {response.status_code}")
```

---

## 5. Security Considerations

### 5.1 Key Storage

| Platform | Storage Mechanism | Security Level |
|----------|------------------|----------------|
| macOS | Keychain (security CLI) | Hardware-backed (Secure Enclave) |
| Windows | Credential Vault | TPM-backed |
| Linux | AES-256-GCM encrypted file | Machine-key derived |

### 5.2 Certificate Lifecycle

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Generate   │────▶│   Valid     │────▶│   Expired   │
│  (Day 0)    │     │  (Day 1-29) │     │  (Day 30+)  │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                          │ Any time
                          ▼
                    ┌─────────────┐
                    │   Revoked   │
                    │  (Admin)    │
                    └─────────────┘
```

### 5.3 Revocation Flow

```python
# Gateway: Check revocation on every request
async def check_revocation(cert_id: str, env) -> bool:
    return await env.REVOCATION_KV.get(cert_id) == "revoked"

# Admin API: Revoke certificate
POST /v1/cert/revoke
Headers: Authorization: Bearer <admin_token>
Body: { "cert_id": "CERT-..." }
```

### 5.4 Device Limits by Tier

| Tier | Max Devices | Certificate Validity |
|------|-------------|---------------------|
| Free | 1 | 30 days |
| Pro | 3 | 90 days |
| Enterprise | Unlimited | 365 days |

---

## 6. API Endpoints Summary

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/v1/cert/register` | POST | Bearer token | Register new device certificate |
| `/v1/cert/validate` | POST | X-Cert-ID + X-Cert-Sig | Validate certificate (internal) |
| `/v1/cert/rotate` | POST | X-Cert-ID + X-Cert-Sig | Rotate expiring certificate |
| `/v1/cert/revoke` | POST | Bearer (admin) | Revoke device certificate |
| `/v1/cert/list` | GET | Bearer | List all devices for tenant |
| `/v1/auth/validate` | POST | Bearer OR Cert headers | Existing endpoint, now accepts certs |

---

## 7. Migration Strategy

### Phase 1: Dual Auth (Current + Certificate)
- Certificate auth **optional**
- mk_/JWT still fully supported
- Users with certs get priority rate limits

### Phase 2: Certificate Preferred
- Certificate auth **recommended**
- Slightly higher rate limits for cert auth
- Dashboard shows registered devices

### Phase 3: Certificate Required (Future)
- Certificate auth **required** for premium features
- mk_/JWT only for initial registration
- Device management in dashboard

---

## 8. Open Questions

1. **Key Algorithm:** ECDSA P-256 (recommended) vs RSA-2048?
2. **Certificate Expiry:** 30 days default, or tier-based?
3. **Device Limits:** Enforce at gateway or client?
4. **Offline Mode:** Allow offline usage until cert expires?

---

## 9. Next Steps

1. Review and approve this architecture
2. Create implementation tasks in plan.md
3. Start Phase 1 implementation: `device_certificate.py`
4. Test certificate generation on all platforms

---

## Sources

- Current auth flow: `src/core/raas_auth.py`, `apps/raas-gateway/src/edge-auth-handler.js`
- Certificate structure: `src/raas/completion_certificate.py`
- Secure storage: `src/auth/secure_storage.py`
- Gateway routing: `apps/raas-gateway/index.js`
