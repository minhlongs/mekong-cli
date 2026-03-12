/**
 * chaos-testing.test.ts — adversarial inputs: invalid keys, expired tokens, malformed webhooks.
 */
import { describe, it, expect } from 'vitest';
import { createHmac } from 'node:crypto';

import { verifyLicense, computeSignature } from '../license/verifier.js';
import { verifyWebhookSignature, parseWebhookPayload } from '../payments/webhook-verifier.js';
import type { LicenseKey, LicenseTier } from '../license/types.js';

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Build a license signed with the DEFAULT secret — overrides are applied BEFORE
 * signing so the signature is always consistent with the fields passed in.
 */
function makeValidLicense(overrides: Partial<LicenseKey> = {}): LicenseKey {
  const partial = {
    key: 'RAAS-STARTER-abcdef1234567890',
    tier: 'starter' as LicenseTier,
    status: 'active' as const,
    issuedAt: new Date().toISOString(),
    expiresAt: new Date(Date.now() + 30 * 86_400_000).toISOString(),
    owner: 'test@example.com',
    ...overrides,
  };
  const signature = computeSignature(partial as Omit<LicenseKey, 'signature'>);
  return { ...partial, signature } as LicenseKey;
}

/**
 * Build a license whose signature was computed with a DIFFERENT secret.
 * verifyLicense will use the default secret → signature mismatch → invalid.
 * Use this to simulate "externally forged" or "wrong-secret" keys.
 */
function makeForgeLicense(overrides: Partial<LicenseKey> = {}): LicenseKey {
  const partial = {
    key: 'RAAS-STARTER-abcdef1234567890',
    tier: 'starter' as LicenseTier,
    status: 'active' as const,
    issuedAt: new Date().toISOString(),
    expiresAt: new Date(Date.now() + 30 * 86_400_000).toISOString(),
    owner: 'test@example.com',
    ...overrides,
  };
  // Sign with a wrong secret — verifier uses its own default secret
  const signature = computeSignature(partial as Omit<LicenseKey, 'signature'>, 'wrong-secret');
  return { ...partial, signature } as LicenseKey;
}

function signLegacy(body: string, secret: string): string {
  return 'v1,' + createHmac('sha256', secret).update(body).digest('hex');
}

// ── Invalid license key formats ───────────────────────────────────────────────

describe('Chaos — invalid license key formats', () => {
  it('rejects empty string key (forged — wrong secret)', () => {
    const lic = makeForgeLicense({ key: '' });
    const result = verifyLicense(lic);
    expect(result.valid).toBe(false);
  });

  it('rejects SQL injection in key field (forged)', () => {
    const lic = makeForgeLicense({ key: "' OR 1=1; DROP TABLE keys;--" });
    const result = verifyLicense(lic);
    expect(result.valid).toBe(false);
  });

  it('rejects XSS payload in key field (forged)', () => {
    const lic = makeForgeLicense({ key: '<script>alert(1)</script>' });
    const result = verifyLicense(lic);
    expect(result.valid).toBe(false);
  });

  it('rejects unicode key / emoji (forged)', () => {
    const lic = makeForgeLicense({ key: 'RAAS-\u{1F4A5}-attack' });
    const result = verifyLicense(lic);
    expect(result.valid).toBe(false);
  });

  it('rejects extremely long key 10KB (forged)', () => {
    const lic = makeForgeLicense({ key: 'A'.repeat(10_240) });
    const result = verifyLicense(lic);
    expect(result.valid).toBe(false);
  });

  it('rejects null bytes in owner field (forged)', () => {
    const lic = makeForgeLicense({ owner: 'user\x00admin' });
    const result = verifyLicense(lic);
    expect(result.valid).toBe(false);
  });

  it('rejects license with tampered tier', () => {
    const lic = makeValidLicense({ tier: 'pro' });
    // signature was for 'starter', tamper tier back
    const tampered = { ...lic, tier: 'enterprise' as LicenseTier };
    const result = verifyLicense(tampered);
    expect(result.valid).toBe(false);
  });
});

// ── Expired tokens with edge dates ────────────────────────────────────────────

describe('Chaos — expired tokens with edge dates', () => {
  it('rejects epoch-0 expiry (1970-01-01)', () => {
    const lic = makeValidLicense({ expiresAt: new Date(0).toISOString() });
    const result = verifyLicense(lic);
    expect(result.valid).toBe(false);
    expect(result.status).toBe('expired');
  });

  it('handles far-future expiry (year 9999)', () => {
    const lic = makeValidLicense({ expiresAt: '9999-12-31T23:59:59.000Z' });
    const result = verifyLicense(lic);
    expect(result.valid).toBe(true);
    expect(result.remainingDays).toBeGreaterThan(0);
  });

  it('rejects negative timestamp expiry', () => {
    const lic = makeValidLicense({ expiresAt: new Date(-86_400_000).toISOString() });
    const result = verifyLicense(lic);
    expect(result.valid).toBe(false);
  });

  it('reports grace when expired exactly 6 days ago', () => {
    const lic = makeValidLicense({
      expiresAt: new Date(Date.now() - 6 * 86_400_000).toISOString(),
    });
    const result = verifyLicense(lic);
    expect(result.valid).toBe(true);
    expect(result.status).toBe('grace');
  });

  it('rejects revoked license even with future expiry', () => {
    const lic = makeValidLicense({ status: 'revoked' });
    const result = verifyLicense(lic);
    expect(result.valid).toBe(false);
    expect(result.status).toBe('revoked');
  });
});

// ── Malformed webhook payloads ────────────────────────────────────────────────

describe('Chaos — malformed webhook payloads', () => {
  const secret = 'chaos-secret';

  it('rejects empty body', () => {
    const result = parseWebhookPayload('');
    expect(result.ok).toBe(false);
  });

  it('rejects body with missing type field', () => {
    const result = parseWebhookPayload(JSON.stringify({ id: 'evt_1', data: {} }));
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error.message).toContain('missing type or id');
  });

  it('rejects body with missing id field', () => {
    const result = parseWebhookPayload(JSON.stringify({ type: 'checkout.completed', data: {} }));
    expect(result.ok).toBe(false);
  });

  it('rejects non-JSON body', () => {
    const result = parseWebhookPayload('not-json-at-all!!!');
    expect(result.ok).toBe(false);
  });

  it('rejects binary-like body', () => {
    const result = parseWebhookPayload('\x00\x01\x02\xFF\xFE');
    expect(result.ok).toBe(false);
  });

  it('rejects valid signature but garbage body', () => {
    const garbage = '\x00\x01binary\xFF';
    const sig = signLegacy(garbage, secret);
    const sigResult = verifyWebhookSignature({ rawBody: garbage, signature: sig, secret });
    // sig verifies — that's ok; parse should fail
    expect(sigResult.ok).toBe(true);
    const parseResult = parseWebhookPayload(garbage);
    expect(parseResult.ok).toBe(false);
  });

  it('rejects missing signature header', () => {
    const result = verifyWebhookSignature({ rawBody: '{}', signature: '', secret });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error.message).toContain('Missing');
  });

  it('rejects wrong signature', () => {
    const body = JSON.stringify({ type: 'checkout.completed', id: 'e1' });
    const result = verifyWebhookSignature({ rawBody: body, signature: 'v1,deadbeef00', secret });
    expect(result.ok).toBe(false);
  });

  it('rejects stale timestamp in Standard Webhooks mode', () => {
    const body = '{}';
    const staleTs = String(Math.floor(Date.now() / 1000) - 600); // 10 min ago
    const id = 'msg_stale';
    const sig = createHmac('sha256', secret)
      .update(`${id}.${staleTs}.${body}`)
      .digest('hex');
    const result = verifyWebhookSignature({
      rawBody: body, signature: `v1,${sig}`, secret,
      webhookId: id, timestamp: staleTs,
    });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error.message).toContain('too old');
  });

  it('rejects non-numeric timestamp', () => {
    const body = '{}';
    const result = verifyWebhookSignature({
      rawBody: body, signature: 'v1,abc', secret,
      webhookId: 'msg_x', timestamp: 'not-a-number',
    });
    expect(result.ok).toBe(false);
  });

  it('rejects extra fields with missing required fields', () => {
    const body = JSON.stringify({
      extra_field_1: 'value',
      extra_field_2: 123,
      // no type, no id
    });
    const result = parseWebhookPayload(body);
    expect(result.ok).toBe(false);
  });
});
