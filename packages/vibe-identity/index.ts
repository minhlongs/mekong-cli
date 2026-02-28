/**
 * @agencyos/vibe-identity — Decentralized Identity Facade SDK
 *
 * Verifiable credentials, DID wallets, trust chain verification, selective disclosure.
 *
 * Usage:
 *   import { createCredentialIssuer, createIdentityWallet, createVerificationEngine } from '@agencyos/vibe-identity';
 */

// ─── Types ──────────────────────────────────────────────────────

export type CredentialStatus = 'active' | 'revoked' | 'suspended' | 'expired';
export type ProofType = 'Ed25519Signature2020' | 'BbsBlsSignature2020' | 'JsonWebSignature2020';
export type DIDMethod = 'did:key' | 'did:web' | 'did:ion' | 'did:ethr';

export interface DIDDocument {
  id: string;
  method: DIDMethod;
  controller: string;
  verificationMethod: VerificationMethod[];
  authentication: string[];
  assertionMethod: string[];
  created: string;
  updated: string;
}

export interface VerificationMethod {
  id: string;
  type: string;
  controller: string;
  publicKeyMultibase?: string;
  publicKeyJwk?: Record<string, string>;
}

export interface VerifiableCredential {
  id: string;
  type: string[];
  issuerDid: string;
  subjectDid: string;
  status: CredentialStatus;
  claims: Record<string, unknown>;
  proofType: ProofType;
  proofValue: string;
  issuedAt: string;
  expiresAt?: string;
  revokedAt?: string;
  revocationReason?: string;
}

export interface PresentationRequest {
  id: string;
  verifierDid: string;
  requiredCredentialTypes: string[];
  requiredClaims: string[];
  challenge: string;
  domain: string;
  expiresAt: string;
}

export interface VerificationResult {
  credentialId: string;
  valid: boolean;
  checks: {
    signatureValid: boolean;
    notExpired: boolean;
    notRevoked: boolean;
    issuerTrusted: boolean;
  };
  errors: string[];
  verifiedAt: string;
}

export interface SelectiveDisclosure {
  credentialId: string;
  disclosedClaims: Record<string, unknown>;
  proofValue: string;
  presentedAt: string;
}

// ─── Credential Issuer ──────────────────────────────────────────

export function createCredentialIssuer(config: { issuerDid: string; proofType: ProofType }) {
  const revocationRegistry = new Map<string, { reason: string; revokedAt: string }>();

  return {
    /** Phát hành credential mới */
    issue(params: {
      id: string;
      subjectDid: string;
      type: string[];
      claims: Record<string, unknown>;
      expiresInDays?: number;
    }): VerifiableCredential {
      const issuedAt = new Date().toISOString();
      const expiresAt = params.expiresInDays
        ? new Date(Date.now() + params.expiresInDays * 86400000).toISOString()
        : undefined;
      // Proof value is a deterministic hash-like string (real impl would use crypto signing)
      const proofInput = `${params.id}:${config.issuerDid}:${params.subjectDid}:${issuedAt}`;
      const proofValue = Buffer.from(proofInput).toString('base64');
      return {
        id: params.id,
        type: ['VerifiableCredential', ...params.type],
        issuerDid: config.issuerDid,
        subjectDid: params.subjectDid,
        status: 'active',
        claims: params.claims,
        proofType: config.proofType,
        proofValue,
        issuedAt,
        expiresAt,
      };
    },

    /** Thu hồi credential */
    revoke(credentialId: string, reason: string): { ok: boolean; revokedAt: string } {
      const revokedAt = new Date().toISOString();
      revocationRegistry.set(credentialId, { reason, revokedAt });
      return { ok: true, revokedAt };
    },

    /** Tạm ngưng credential (có thể phục hồi) */
    suspend(credentialId: string): { ok: boolean } {
      const existing = revocationRegistry.get(credentialId);
      if (!existing) {
        revocationRegistry.set(credentialId, { reason: 'suspended', revokedAt: new Date().toISOString() });
      }
      return { ok: true };
    },

    /** Check credential có bị revoke không */
    isRevoked(credentialId: string): boolean {
      return revocationRegistry.has(credentialId);
    },

    /** Lấy thông tin revocation */
    getRevocationInfo(credentialId: string): { reason: string; revokedAt: string } | null {
      return revocationRegistry.get(credentialId) ?? null;
    },

    getIssuerDid: () => config.issuerDid,
  };
}

// ─── Identity Wallet ─────────────────────────────────────────────

export function createIdentityWallet() {
  const credentials = new Map<string, VerifiableCredential>();

  return {
    /** Lưu credential vào wallet */
    store(credential: VerifiableCredential): void {
      credentials.set(credential.id, { ...credential });
    },

    /** Lấy credential theo id */
    get(credentialId: string): VerifiableCredential | null {
      return credentials.get(credentialId) ?? null;
    },

    /** Xoá credential khỏi wallet */
    remove(credentialId: string): boolean {
      return credentials.delete(credentialId);
    },

    /** Lọc credentials theo type */
    getByType(credentialType: string): VerifiableCredential[] {
      return [...credentials.values()].filter(c => c.type.includes(credentialType));
    },

    /** Selective disclosure — chỉ tiết lộ một số claims nhất định */
    presentWithDisclosure(credentialId: string, claimsToReveal: string[]): SelectiveDisclosure | null {
      const cred = credentials.get(credentialId);
      if (!cred) return null;
      const disclosedClaims: Record<string, unknown> = {};
      for (const key of claimsToReveal) {
        if (key in cred.claims) disclosedClaims[key] = cred.claims[key];
      }
      const presentedAt = new Date().toISOString();
      const proofInput = `${credentialId}:${claimsToReveal.join(',')}:${presentedAt}`;
      return {
        credentialId,
        disclosedClaims,
        proofValue: Buffer.from(proofInput).toString('base64'),
        presentedAt,
      };
    },

    /** Đáp lại PresentationRequest — tìm credentials phù hợp */
    fulfillRequest(request: PresentationRequest): { credentials: VerifiableCredential[]; missing: string[] } {
      const now = new Date().toISOString();
      if (now > request.expiresAt) return { credentials: [], missing: request.requiredCredentialTypes };
      const fulfilled: VerifiableCredential[] = [];
      const missing: string[] = [];
      for (const reqType of request.requiredCredentialTypes) {
        const match = [...credentials.values()].find(c => c.type.includes(reqType) && c.status === 'active');
        if (match) fulfilled.push(match);
        else missing.push(reqType);
      }
      return { credentials: fulfilled, missing };
    },

    /** Liệt kê tất cả credentials */
    listAll(): VerifiableCredential[] {
      return [...credentials.values()];
    },

    getCount: () => credentials.size,
  };
}

// ─── Verification Engine ─────────────────────────────────────────

export function createVerificationEngine() {
  const trustedIssuers = new Set<string>();

  return {
    /** Thêm issuer vào danh sách tin cậy */
    addTrustedIssuer(did: string): void {
      trustedIssuers.add(did);
    },

    /** Xoá issuer khỏi danh sách tin cậy */
    removeTrustedIssuer(did: string): void {
      trustedIssuers.delete(did);
    },

    /** Xác thực credential đầy đủ */
    verify(
      credential: VerifiableCredential,
      isRevoked: (id: string) => boolean,
    ): VerificationResult {
      const now = new Date().toISOString();
      const errors: string[] = [];

      // Signature check (real impl verifies crypto proof)
      const expectedInput = `${credential.id}:${credential.issuerDid}:${credential.subjectDid}:${credential.issuedAt}`;
      const signatureValid = credential.proofValue === Buffer.from(expectedInput).toString('base64');
      if (!signatureValid) errors.push('Invalid proof signature');

      const notExpired = !credential.expiresAt || now <= credential.expiresAt;
      if (!notExpired) errors.push(`Credential expired at ${credential.expiresAt}`);

      const notRevoked = !isRevoked(credential.id);
      if (!notRevoked) errors.push('Credential has been revoked');

      const issuerTrusted = trustedIssuers.has(credential.issuerDid);
      if (!issuerTrusted) errors.push(`Issuer ${credential.issuerDid} not in trust registry`);

      return {
        credentialId: credential.id,
        valid: signatureValid && notExpired && notRevoked && issuerTrusted,
        checks: { signatureValid, notExpired, notRevoked, issuerTrusted },
        errors,
        verifiedAt: now,
      };
    },

    /** Xác thực selective disclosure presentation */
    verifyDisclosure(disclosure: SelectiveDisclosure, originalCredential: VerifiableCredential): { valid: boolean; reason?: string } {
      if (disclosure.credentialId !== originalCredential.id) return { valid: false, reason: 'Credential ID mismatch' };
      if (originalCredential.status !== 'active') return { valid: false, reason: `Credential status: ${originalCredential.status}` };
      for (const [key, val] of Object.entries(disclosure.disclosedClaims)) {
        if (originalCredential.claims[key] !== val) return { valid: false, reason: `Claim mismatch for key: ${key}` };
      }
      return { valid: true };
    },

    getTrustedIssuers: () => [...trustedIssuers],
  };
}
