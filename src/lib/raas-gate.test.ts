/**
 * RAAS License Gate - Unit Tests
 *
 * Tests for LicenseService singleton with rate limiting and audit logging.
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import {
  LicenseService,
  LicenseError,
  PREMIUM_FEATURES,
  hasFeature,
  requireFeature,
  getLicenseStatus,
  isPremium,
  isEnterprise,
  getLicenseTier,
} from './raas-gate';

describe('RAAS License Gate', () => {
  let licenseService: LicenseService;

  beforeEach(() => {
    licenseService = LicenseService.getInstance();
    licenseService.reset();
    delete process.env.RAAS_LICENSE_KEY;
    delete process.env.DEBUG_AUDIT;
  });

  afterEach(() => {
    delete process.env.RAAS_LICENSE_KEY;
    delete process.env.DEBUG_AUDIT;
  });

  describe('LicenseService Singleton', () => {
    it('should return same instance on multiple calls', () => {
      expect(LicenseService.getInstance()).toBe(LicenseService.getInstance());
    });

    it('should reset license and rate limits', () => {
      licenseService.validateSync('raas_pro_test1234567890');
      expect(licenseService.hasTier('pro')).toBe(true);
      licenseService.reset();
      expect(licenseService.hasTier('pro')).toBe(false);
    });
  });

  describe('validateLicense', () => {
    it('should return free tier when no license key or empty string', () => {
      const r1 = licenseService.validateSync();
      expect(r1.valid).toBe(false);
      expect(r1.tier).toBe('free');
      expect(r1.features).toEqual(PREMIUM_FEATURES.free);

      process.env.RAAS_LICENSE_KEY = '';
      const r2 = licenseService.validateSync();
      expect(r2.valid).toBe(false);
      expect(r2.tier).toBe('free');
    });

    it('should return pro tier for valid pro, sk-raas-, and RPP- license keys', () => {
      for (const key of ['raas_pro_abc123def456789', 'sk-raas-abc123def456', 'RPP-abc123def456789']) {
        process.env.RAAS_LICENSE_KEY = key;
        const result = licenseService.validateSync();
        expect(result.valid).toBe(true);
        expect(result.tier).toBe('pro');
        expect(result.features).toEqual(PREMIUM_FEATURES.pro);
      }
    });

    it('should return enterprise tier for enterprise and REP- license keys', () => {
      for (const key of ['raas_ent_xyz789abc123456', 'REP-abc123def456789']) {
        process.env.RAAS_LICENSE_KEY = key;
        const result = licenseService.validateSync();
        expect(result.valid).toBe(true);
        expect(result.tier).toBe('enterprise');
        expect(result.features).toEqual(PREMIUM_FEATURES.enterprise);
      }
    });

    it('should handle async validate', async () => {
      process.env.RAAS_LICENSE_KEY = 'raas_pro_test1234567890';
      const result = await licenseService.validate();
      expect(result.valid).toBe(true);
      expect(result.tier).toBe('pro');
    });
  });

  describe('hasTier & hasFeature', () => {
    it('should enforce tier hierarchy (FREE < PRO < ENTERPRISE)', () => {
      expect([licenseService.hasTier('free'), licenseService.hasTier('pro'), licenseService.hasTier('enterprise')]).toEqual([true, false, false]);
      licenseService.validateSync('raas_pro_test1234567890');
      expect([licenseService.hasTier('free'), licenseService.hasTier('pro'), licenseService.hasTier('enterprise')]).toEqual([true, true, false]);
      licenseService.validateSync('raas_ent_test1234567890');
      expect([licenseService.hasTier('free'), licenseService.hasTier('pro'), licenseService.hasTier('enterprise')]).toEqual([true, true, true]);
    });

    it('should check free, pro, and enterprise features', () => {
      expect(hasFeature('basic_cli_commands')).toBe(true);
      expect(hasFeature('premium_agents')).toBe(false);
      licenseService.validateSync('raas_pro_test1234567890');
      expect(hasFeature('premium_agents')).toBe(true);
      expect(hasFeature('ml_models')).toBe(true);
      licenseService.validateSync('raas_ent_test1234567890');
      expect(hasFeature('agi_auto_pilot')).toBe(true);
      expect(hasFeature('team_collaboration')).toBe(true);
    });
  });

  describe('requireFeature, helpers, status, and checksum', () => {
    it('should enforce requireFeature and tier helpers', () => {
      expect(isPremium()).toBe(false);
      expect(getLicenseTier()).toBe('free');
      expect(() => requireFeature('agi_auto_pilot')).toThrow(LicenseError);

      licenseService.validateSync('raas_pro_test1234567890');
      expect(() => requireFeature('premium_agents')).not.toThrow();
      expect([isPremium(), isEnterprise(), getLicenseTier()]).toEqual([true, false, 'pro']);

      licenseService.validateSync('raas_ent_test1234567890');
      expect([isPremium(), isEnterprise(), getLicenseTier()]).toEqual([true, true, 'enterprise']);
    });

    it('should format getLicenseStatus for free, pro, and enterprise tiers', () => {
      expect(getLicenseStatus()).toContain('Free Tier');
      process.env.RAAS_LICENSE_KEY = 'raas_pro_test1234567890';
      expect(getLicenseStatus()).toContain('PRO');
      process.env.RAAS_LICENSE_KEY = 'raas_ent_test1234567890';
      expect(getLicenseStatus()).toContain('ENTERPRISE');
    });

    it('should activate, deactivate, and validate checksums', async () => {
      await licenseService.activateLicense('test-key', 'pro');
      expect(licenseService.hasTier('pro')).toBe(true);
      await licenseService.deactivateLicense();
      expect(licenseService.hasTier('pro')).toBe(false);

      const key = 'raas_pro_test1234567890';
      const checksum = licenseService.generateChecksum(key);
      expect(checksum).toHaveLength(4);
      expect(licenseService.validateWithChecksum(key, checksum)).toBe(true);
      expect(licenseService.validateWithChecksum(key, 'abcd')).toBe(false);
    });
  });
});
