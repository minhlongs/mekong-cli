/**
 * RAAS License Gate — Unit Tests
 *
 * Tests for premium feature access control:
 * - License tier validation
 * - Feature gating
 * - ML model access control
 * - Premium data access control
 * - Worker endpoint protection
 */

import { describe, test, expect, beforeEach } from '@jest/globals';
import {
  LicenseService,
  LicenseTier,
  LicenseError,
  isPremium,
  isEnterprise,
  getLicenseTier,
  validateLicense,
  requireMLFeature,
  requirePremiumData,
} from './raas-gate';

describe('RAAS License Gate', () => {
  let licenseService: LicenseService;

  beforeEach(() => {
    // Reset singleton before each test
    licenseService = LicenseService.getInstance();
    licenseService.reset();
    delete process.env.RAAS_LICENSE_KEY;
  });

  describe('License Tier Validation', () => {
    test('should default to FREE tier when no license key', () => {
      const result = validateLicense();
      expect(result.valid).toBe(false);
      expect(result.tier).toBe(LicenseTier.FREE);
      expect(result.features).toContain('basic_strategies');
      expect(result.features).not.toContain('ml_models');
    });

    test('should recognize PRO license key format (raas-pro-*)', () => {
      const result = validateLicense('raas-pro-abc123');
      expect(result.valid).toBe(true);
      expect(result.tier).toBe(LicenseTier.PRO);
      expect(result.features).toContain('ml_models');
      expect(result.features).toContain('premium_data');
    });

    test('should recognize PRO license key format (RPP-*)', () => {
      const result = validateLicense('RPP-2026-XYZ');
      expect(result.valid).toBe(true);
      expect(result.tier).toBe(LicenseTier.PRO);
    });

    test('should recognize ENTERPRISE license key format (raas-ent-*)', () => {
      const result = validateLicense('raas-ent-premium');
      expect(result.valid).toBe(true);
      expect(result.tier).toBe(LicenseTier.ENTERPRISE);
      expect(result.expiresAt).toBe('2027-12-31');
    });

    test('should recognize ENTERPRISE license key format (REP-*)', () => {
      const result = validateLicense('REP-2026-ENTERPRISE');
      expect(result.valid).toBe(true);
      expect(result.tier).toBe(LicenseTier.ENTERPRISE);
    });

    test('should treat invalid key format as FREE tier', () => {
      const result = validateLicense('invalid-key');
      expect(result.valid).toBe(false);
      expect(result.tier).toBe(LicenseTier.FREE);
    });
  });

  describe('Feature Access Control', () => {
    test('FREE tier should have basic features only', () => {
      validateLicense(); // No key = FREE
      const service = LicenseService.getInstance();

      expect(service.hasFeature('basic_strategies')).toBe(true);
      expect(service.hasFeature('live_trading')).toBe(true);
      expect(service.hasFeature('basic_backtest')).toBe(true);
      expect(service.hasFeature('ml_models')).toBe(false);
      expect(service.hasFeature('premium_data')).toBe(false);
    });

    test('PRO tier should have ML and premium data access', () => {
      validateLicense('raas-pro-test');
      const service = LicenseService.getInstance();

      expect(service.hasFeature('ml_models')).toBe(true);
      expect(service.hasFeature('premium_data')).toBe(true);
      expect(service.hasFeature('advanced_optimization')).toBe(true);
    });

    test('ENTERPRISE tier should have all features', () => {
      validateLicense('raas-ent-test');
      const service = LicenseService.getInstance();

      expect(service.hasFeature('priority_support')).toBe(true);
      expect(service.hasFeature('custom_strategies')).toBe(true);
      expect(service.hasFeature('multi_exchange')).toBe(true);
    });
  });

  describe('Tier Hierarchy', () => {
    test('FREE tier cannot access PRO features', () => {
      validateLicense(); // FREE
      const service = LicenseService.getInstance();

      expect(service.hasTier(LicenseTier.FREE)).toBe(true);
      expect(service.hasTier(LicenseTier.PRO)).toBe(false);
      expect(service.hasTier(LicenseTier.ENTERPRISE)).toBe(false);
    });

    test('PRO tier can access PRO and FREE features', () => {
      validateLicense('raas-pro-test');
      const service = LicenseService.getInstance();

      expect(service.hasTier(LicenseTier.FREE)).toBe(true);
      expect(service.hasTier(LicenseTier.PRO)).toBe(true);
      expect(service.hasTier(LicenseTier.ENTERPRISE)).toBe(false);
    });

    test('ENTERPRISE tier can access all features', () => {
      validateLicense('raas-ent-test');
      const service = LicenseService.getInstance();

      expect(service.hasTier(LicenseTier.FREE)).toBe(true);
      expect(service.hasTier(LicenseTier.PRO)).toBe(true);
      expect(service.hasTier(LicenseTier.ENTERPRISE)).toBe(true);
    });
  });

  describe('LicenseError', () => {
    test('should throw LicenseError with correct properties', () => {
      validateLicense(); // FREE tier
      const service = LicenseService.getInstance();

      expect(() => {
        service.requireFeature('ml_models');
      }).toThrow(LicenseError);

      try {
        service.requireFeature('ml_models');
      } catch (err) {
        if (err instanceof LicenseError) {
          expect(err.message).toContain('ml_models');
          expect(err.requiredTier).toBe(LicenseTier.PRO);
          expect(err.feature).toBe('ml_models');
        }
      }
    });

    test('should not throw for allowed features', () => {
      validateLicense('raas-pro-test');
      const service = LicenseService.getInstance();

      expect(() => {
        service.requireFeature('ml_models');
      }).not.toThrow();
    });
  });

  describe('Convenience Helpers', () => {
    test('isPremium() should return false for FREE tier', () => {
      validateLicense();
      expect(isPremium()).toBe(false);
    });

    test('isPremium() should return true for PRO tier', () => {
      validateLicense('raas-pro-test');
      expect(isPremium()).toBe(true);
    });

    test('isEnterprise() should return false for PRO tier', () => {
      validateLicense('raas-pro-test');
      expect(isEnterprise()).toBe(false);
    });

    test('isEnterprise() should return true for ENTERPRISE tier', () => {
      validateLicense('raas-ent-test');
      expect(isEnterprise()).toBe(true);
    });

    test('getLicenseTier() should return current tier', () => {
      validateLicense('raas-pro-test');
      expect(getLicenseTier()).toBe(LicenseTier.PRO);
    });
  });

  describe('ML Feature Gating', () => {
    test('requireMLFeature() should throw for FREE tier', () => {
      validateLicense(); // FREE

      expect(() => {
        requireMLFeature('gru_model');
      }).toThrow(LicenseError);
    });

    test('requireMLFeature() should pass for PRO tier', () => {
      validateLicense('raas-pro-test');

      expect(() => {
        requireMLFeature('gru_model');
      }).not.toThrow();
    });

    test('requireMLFeature() should pass for ENTERPRISE tier', () => {
      validateLicense('raas-ent-test');

      expect(() => {
        LicenseService.getInstance().requireFeature('ml_models');
      }).not.toThrow();
    });
  });

  describe('Premium Data Gating', () => {
    test('requirePremiumData() should throw for FREE tier', () => {
      validateLicense(); // FREE

      expect(() => {
        requirePremiumData();
      }).toThrow(LicenseError);
    });

    test('requirePremiumData() should pass for PRO tier', () => {
      validateLicense('raas-pro-test');

      expect(() => {
        requirePremiumData();
      }).not.toThrow();
    });
  });

  describe('Environment Variable Support', () => {
    test('should read license from environment variable', () => {
      process.env.RAAS_LICENSE_KEY = 'raas-pro-env';
      licenseService.reset();

      const result = licenseService.validate();
      expect(result.tier).toBe(LicenseTier.PRO);
    });

    test('explicit key should override environment', () => {
      process.env.RAAS_LICENSE_KEY = 'raas-pro-env';
      licenseService.reset();

      // Explicit invalid key should override env
      const result = licenseService.validate('invalid-key');
      expect(result.tier).toBe(LicenseTier.FREE);
    });
  });

  describe('License Caching', () => {
    test('should cache validation result', () => {
      const service = LicenseService.getInstance();

      // First validation
      service.validate('raas-pro-test');

      // Modify internal state to check if cached
      const cached = service.hasTier(LicenseTier.PRO);
      expect(cached).toBe(true);

      // Should still be cached
      expect(service.hasTier(LicenseTier.PRO)).toBe(true);
    });

    test('reset() should clear cache', () => {
      validateLicense('raas-pro-test');
      licenseService.reset();

      // After reset, should need re-validation
      expect(() => {
        licenseService.requireFeature('ml_models');
      }).toThrow(LicenseError);
    });
  });
});

describe('Worker Endpoint Protection', () => {
  beforeEach(() => {
    LicenseService.getInstance().reset();
    delete process.env.RAAS_LICENSE_KEY;
  });

  test('optimization worker should require PRO license', () => {
    // FREE tier
    validateLicense();

    expect(() => {
      LicenseService.getInstance().requireFeature('advanced_optimization');
    }).toThrow(LicenseError);

    // PRO tier
    validateLicense('raas-pro-test');

    expect(() => {
      LicenseService.getInstance().requireFeature('advanced_optimization');
    }).not.toThrow();
  });

  test('backtest worker premium data should require PRO license', () => {
    // FREE tier
    validateLicense();

    expect(() => {
      requirePremiumData();
    }).toThrow(LicenseError);

    // PRO tier
    validateLicense('raas-pro-test');

    expect(() => {
      requirePremiumData();
    }).not.toThrow();
  });
});
