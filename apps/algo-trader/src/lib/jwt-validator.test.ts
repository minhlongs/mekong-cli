/**
 * JWT Validator Tests
 */

import {
  validateLicenseKeyFormat,
  verifyLicenseJWT,
  generateLicenseJWT,
  decodeLicenseJWT,
} from './jwt-validator';

const TEST_SECRET = 'test-secret-key-min-32-characters!';

describe('JWT Validator', () => {
  describe('validateLicenseKeyFormat', () => {
    it('rejects null/undefined', () => {
      expect(validateLicenseKeyFormat('')).toEqual({
        valid: false,
        error: 'License key too short',
      });
      expect(validateLicenseKeyFormat(null as any)).toEqual({
        valid: false,
        error: 'License key too short',
      });
    });

    it('rejects short keys', () => {
      expect(validateLicenseKeyFormat('short')).toEqual({
        valid: false,
        error: 'License key too short',
      });
    });

    it('rejects too long keys', () => {
      const longKey = 'a'.repeat(1025);
      expect(validateLicenseKeyFormat(longKey)).toEqual({
        valid: false,
        error: 'License key too long',
      });
    });

    it('rejects non-JWT format', () => {
      expect(validateLicenseKeyFormat('not-a-jwt')).toEqual({
        valid: false,
        error: 'Invalid JWT format',
      });
    });

    it('rejects invalid base64url encoding', () => {
      expect(validateLicenseKeyFormat('abc!.def?.ghi@')).toEqual({
        valid: false,
        error: 'Invalid base64url encoding',
      });
    });

    it('accepts valid JWT format', () => {
      const validJWT = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U';
      expect(validateLicenseKeyFormat(validJWT)).toEqual({ valid: true });
    });
  });

  describe('verifyLicenseJWT', () => {
    it('rejects invalid format', async () => {
      const result = await verifyLicenseJWT('not-a-jwt', TEST_SECRET);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('JWT format');
    });

    it('rejects invalid signature', async () => {
      const fakeJWT = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.invalid-signature';
      const result = await verifyLicenseJWT(fakeJWT, TEST_SECRET);
      expect(result.valid).toBe(false);
    });

    it('rejects expired tokens', async () => {
      const expiredPayload = {
        sub: 'test-key',
        tier: 'pro' as const,
        features: ['feature1'],
        iss: 'raas',
        exp: Math.floor(Date.now() / 1000) - 100,
      };

      const expiredToken = await generateLicenseJWT(expiredPayload, TEST_SECRET);
      const result = await verifyLicenseJWT(expiredToken, TEST_SECRET);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('expired');
    });

    it('accepts valid token', async () => {
      const validPayload = {
        sub: 'test-key-123',
        tier: 'pro' as const,
        features: ['ml_models', 'premium_data'],
        iss: 'raas',
      };

      const token = await generateLicenseJWT(validPayload, TEST_SECRET);
      const result = await verifyLicenseJWT(token, TEST_SECRET);

      expect(result.valid).toBe(true);
      expect(result.payload?.sub).toBe('test-key-123');
      expect(result.payload?.tier).toBe('pro');
    });

    it('rejects invalid tier', async () => {
      const invalidTierPayload = {
        sub: 'test-key',
        tier: 'invalid-tier' as any,
        features: [],
        iss: 'raas',
      };

      const token = await generateLicenseJWT(invalidTierPayload, TEST_SECRET);
      const result = await verifyLicenseJWT(token, TEST_SECRET);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('Invalid tier');
    });

    it('accepts enterprise tier', async () => {
      const enterprisePayload = {
        sub: 'ent-key',
        tier: 'enterprise' as const,
        features: ['all_features'],
        iss: 'raas',
      };

      const token = await generateLicenseJWT(enterprisePayload, TEST_SECRET);
      const result = await verifyLicenseJWT(token, TEST_SECRET);

      expect(result.valid).toBe(true);
      expect(result.payload?.tier).toBe('enterprise');
    });
  });

  describe('generateLicenseJWT', () => {
    it('generates valid JWT token', async () => {
      const payload = {
        sub: 'generated-key',
        tier: 'pro' as const,
        features: ['feature1', 'feature2'],
        iss: 'raas',
      };

      const token = await generateLicenseJWT(payload, TEST_SECRET);

      const parts = token.split('.');
      expect(parts.length).toBe(3);

      const result = await verifyLicenseJWT(token, TEST_SECRET);
      expect(result.valid).toBe(true);
      expect(result.payload?.sub).toBe('generated-key');
    });

    it('sets expiration when provided', async () => {
      const payload = {
        sub: 'expiring-key',
        tier: 'pro' as const,
        features: [],
        iss: 'raas',
        exp: Math.floor(Date.now() / 1000) + 3600,
      };

      const token = await generateLicenseJWT(payload, TEST_SECRET);
      const result = await verifyLicenseJWT(token, TEST_SECRET);

      expect(result.valid).toBe(true);
      expect(result.payload?.exp).toBe(payload.exp);
    });
  });

  describe('decodeLicenseJWT', () => {
    it('decodes valid JWT without verification', async () => {
      const payload = {
        sub: 'decode-test',
        tier: 'pro' as const,
        features: ['test_feature'],
        iss: 'raas',
      };

      const token = await generateLicenseJWT(payload, TEST_SECRET);
      const decoded = decodeLicenseJWT(token);

      expect(decoded).not.toBeNull();
      expect(decoded?.sub).toBe('decode-test');
      expect(decoded?.tier).toBe('pro');
    });

    it('returns null for invalid format', () => {
      const decoded = decodeLicenseJWT('not-a-jwt');
      expect(decoded).toBeNull();
    });

    it('returns null for malformed payload', () => {
      const decoded = decodeLicenseJWT('abc.def.ghi');
      expect(decoded).toBeNull();
    });
  });
});
