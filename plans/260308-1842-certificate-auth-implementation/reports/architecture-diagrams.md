# Certificate Authentication Architecture

## System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CERTIFICATE AUTH ECOSYSTEM                          │
└─────────────────────────────────────────────────────────────────────────────┘

                                          ┌──────────────────────┐
                                          │   AgencyOS Dashboard │
                                          │                      │
                                          │  - Device management │
                                          │  - Revocation UI     │
                                          └──────────┬───────────┘
                                                     │ Admin API
                                          ┌──────────▼───────────┐
┌────────────────┐  X-Cert-ID   ┌─────────┴──────────┐            │
│  mekong-cli    │  X-Cert-Sig  │   RaaS Gateway     │◄───────────┘
│                │  Bearer      │  (Cloudflare)      │
│  - Cert store  │─────────────▶│                    │
│  - ECDSA keys  │              │  - Cert validation │
│  - HTTP client │◀─────────────│  - Device registry │
│                │  JWT + cert  │  - Rate limiting   │
└────────────────┘              └─────────┬──────────┘
                                          │
                                          │ Sync
                                          │
                                 ┌────────▼──────────┐
                                 │   KV Storage      │
                                 │                   │
                                 │  - CERT_KV        │
                                 │  - REVOCATION_KV  │
                                 └───────────────────┘
```

## Certificate Generation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: DEVICE CERTIFICATE GENERATION (mekong init)                        │
└─────────────────────────────────────────────────────────────────────────────┘

    User runs: mekong init --raas
              │
              ▼
    ┌───────────────────┐
    │ DeviceFingerprint │
    │ Generator         │
    └─────────┬─────────┘
              │ Collect hardware IDs:
              │ - CPU serial
              │ - Disk serial
              │ - MAC address hash
              │ - OS UUID
              ▼
    ┌───────────────────┐
    │ SHA3-256 Hash     │
    └─────────┬─────────┘
              │
              ▼
    device_id = "DEV-{hash[:16]}"
              │
              ▼
    ┌───────────────────┐
    │ ECDSA P-256       │
    │ Key Generation    │
    └─────────┬─────────┘
              │
        ┌─────┴─────┐
        │           │
        ▼           ▼
  Private Key   Public Key
  (Secure       (PEM →
  Storage)      Certificate)
              │
              ▼
    ┌───────────────────┐
    │ Sign Payload:     │
    │ {device_id,       │
    │  tenant_id,       │
    │  license_hash,    │
    │  issued_at,       │
    │  expires_at}      │
    └─────────┬─────────┘
              │ ECDSA.sign()
              ▼
    ┌───────────────────┐
    │ DeviceCertificate │
    │ - certificate_id  │
    │ - device_id       │
    │ - fingerprint     │
    │ - signature       │
    │ - public_key_pem  │
    └─────────┬─────────┘
              │
              ▼
    Store: ~/.mekong/device-certificate.json
    Private Key: Keychain/Windows Vault
```

## Certificate Validation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: REQUEST AUTHENTICATION (Every API call)                            │
└─────────────────────────────────────────────────────────────────────────────┘

    mekong-cli sends request:
    POST /v1/usage
    Headers:
      - Authorization: Bearer {license_key}
      - X-Cert-ID: CERT-DEV-123456
      - X-Cert-Sig: {ecdsa_signature}
              │
              ▼
    ┌─────────────────────────────────────┐
    │ RaaS Gateway (Cloudflare Worker)    │
    └─────────────────────────────────────┘
              │
        ┌─────┴─────┬─────────────┬──────────┐
        │           │             │          │
        ▼           ▼             ▼          ▼
  ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐
  │ Extract  │ │ Lookup   │ │ Check   │ │ Verify   │
  │ Headers  │ │ Cert KV  │ │ Revocat.│ │ Signature│
  └────┬─────┘ └────┬─────┘ └────┬────┘ └────┬─────┘
       │            │            │           │
       │            │            │           │
       ▼            ▼            ▼           ▼
  cert_id=    cert_data=   revoked=     valid=
  CERT-...    {...}        false        true/false
       │            │            │           │
       └────────────┴────────────┴───────────┘
                        │
                        ▼
              ┌─────────────────┐
              │  All checks     │
              │  passed?        │
              └────────┬────────┘
                       │
           ┌───────────┴───────────┐
           │ Yes                   │ No
           ▼                       ▼
    ┌─────────────┐         ┌─────────────┐
    │ Allow       │         │ Reject 401  │
    │ Process     │         │ Error:      │
    │ Request     │         │ - Expired   │
    │             │         │ - Revoked   │
    │             │         │ - Invalid   │
    └─────────────┘         └─────────────┘
```

## Certificate Rotation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: AUTOMATIC CERTIFICATE ROTATION (Before expiry)                     │
└─────────────────────────────────────────────────────────────────────────────┘

    Background job: Check cert expiry daily
              │
              ▼
    ┌───────────────────┐
    │ Days until        │
    │ expiry < 7?       │
    └─────────┬─────────┘
              │
        ┌─────┴─────┐
        │ Yes       │ No
        │           │
        ▼           │
    ┌───────────┐   │
    │ Generate  │   │
    │ new cert  │   │
    └─────┬─────┘   │
          │         │
          ▼         │
    ┌───────────┐   │
    │ Register  │   │
    │ with      │   │
    │ Gateway   │   │
    └─────┬─────┘   │
          │         │
          ▼         │
    ┌───────────┐   │
    │ Store new │   │
    │ cert +    │   │
    │ key       │   │
    └─────┬─────┘   │
          │         │
          ▼         │
    ┌───────────┐   │
    │ Delete    │   │
    │ old cert  │◄──┘
    └───────────┘
```

## Revocation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: CERTIFICATE REVOCATION (Security/Admin)                            │
└─────────────────────────────────────────────────────────────────────────────┘

    Admin Dashboard
          │
          ▼
    ┌───────────────────┐
    │ Select device     │
    │ to revoke         │
    └─────────┬─────────┘
              │
              ▼
    ┌───────────────────┐
    │ POST /v1/cert/    │
    │      revoke       │
    │ {cert_id}         │
    └─────────┬─────────┘
              │
              ▼
    ┌───────────────────┐
    │ Gateway sets:     │
    │ REVOCATION_KV     │
    │ cert_id =         │
    │ "revoked"         │
    └─────────┬─────────┘
              │
              ▼
    Next request with cert:
              │
              ▼
    ┌───────────────────┐
    │ Gateway checks    │
    │ REVOCATION_KV     │
    └─────────┬─────────┘
              │
              ▼
    ┌───────────────────┐
    │ Found = "revoked" │
    └─────────┬─────────┘
              │
              ▼
    ┌───────────────────┐
    │ Reject 403        │
    │ "Certificate      │
    │  revoked"         │
    └───────────────────┘
```

## Data Flow: Certificate Registration

```
┌──────────────┐                     ┌──────────────┐                     ┌──────────────┐
│  mekong-cli  │                     │ RaaS Gateway │                     │  KV Storage  │
└──────┬───────┘                     └──────┬───────┘                     └──────┬───────┘
       │                                    │                                    │
       │ POST /v1/cert/register             │                                    │
       │ Headers:                           │                                    │
       │   Authorization: Bearer {key}      │                                    │
       │ Body: {                            │                                    │
       │   certificate: {...},              │                                    │
       │   device_fingerprint: {...}        │                                    │
       │ }                                  │                                    │
       │───────────────────────────────────▶│                                    │
       │                                    │                                    │
       │                                    │ 1. Validate Bearer token           │
       │                                    │ 2. Extract tenant_id               │
       │                                    │ 3. Verify certificate signature    │
       │                                    │                                    │
       │                                    │ PUT CERT_KV[cert_id] = {...}       │
       │                                    │───────────────────────────────────▶│
       │                                    │                                    │
       │                                    │◀───────────────────────────────────│
       │                                    │                                    │
       │                                    │ PUT CERT_KV[device:{device_id}]    │
       │                                    │───────────────────────────────────▶│
       │                                    │                                    │
       │                                    │◀───────────────────────────────────│
       │                                    │                                    │
       │ 200 OK                             │                                    │
       │ {                                  │                                    │
       │   success: true,                   │                                    │
       │   cert_id: "CERT-...",             │                                    │
       │   device_id: "DEV-..."             │                                    │
       │ }                                  │                                    │
       │◀───────────────────────────────────│                                    │
       │                                    │                                    │
       │ Store cert + private key           │                                    │
       │                                    │                                    │
```

## Security Boundary Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SECURITY BOUNDARIES                               │
└─────────────────────────────────────────────────────────────────────────────┘

                         ┌─────────────────────┐
                         │   TRUST ZONE:       │
                         │   Device            │
                         │                     │
    ┌────────────────────┤  ┌───────────────┐  │
    │  mekong-cli        │  │ Secure Store  │  │
    │                    │  │ (Keychain/    │  │
    │  ┌──────────────┐  │  │  Vault)       │  │
    │  │ Cert Store   │  │  │               │  │
    │  │ ~/.mekong/   │  │  │ ┌───────────┐ │  │
    │  │ device-cert  │  │  │ │Private Key│ │  │
    │  │ .json        │  │  │ │(Protected)│ │  │
    │  └──────────────┘  │  │ └───────────┘ │  │
    │                    │  └───────────────┘  │
    │  ┌──────────────┐  │                     │
    │  │ HTTP Client  │  │                     │
    │  │ + Cert       │  │                     │
    │  │ Headers      │  │                     │
    │  └──────────────┘  │                     │
    │                    │                     │
    └────────────────────┤                     │
                         └─────────────────────┘
                                   │
                         X-Cert-ID + X-Cert-Sig
                         (Signed Headers)
                                   │
                         ┌─────────▼──────────┐
                         │   TRUST ZONE:      │
                         │   RaaS Gateway     │
                         │                    │
                         │  ┌──────────────┐  │
                         │  │ Cert         │  │
                         │  │ Validator    │  │
                         │  └──────────────┘  │
                         │                    │
                         │  ┌──────────────┐  │
                         │  │ Device       │  │
                         │  │ Registry     │  │
                         │  └──────────────┘  │
                         │                    │
                         └─────────┬──────────┘
                                   │
                         ┌─────────▼──────────┐
                         │   TRUST ZONE:      │
                         │   KV Storage       │
                         │                    │
                         │  ┌──────────────┐  │
                         │  │ CERT_KV      │  │
                         │  │ (Certificates│  │
                         │  │  + Metadata) │  │
                         │  └──────────────┘  │
                         │                    │
                         │  ┌──────────────┐  │
                         │  │ REVOCATION_KV│  │
                         │  │ (Revoked     │  │
                         │  │  Cert IDs)   │  │
                         │  └──────────────┘  │
                         │                    │
                         └────────────────────┘
```
