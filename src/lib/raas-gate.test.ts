/**
 * RAAS License Gate - Unit Tests
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import {
  validateLicense,
  hasFeature,
  requireFeature,
  getLicenseStatus,
  PREMIUM_FEATURES,
} from './raas-gate';

describe('RAAS License Gate', () => {
  beforeEach(() => {
    // Clear env before each test
    delete process.env.RAAS_LICENSE_KEY;
  });

  afterEach(() => {
    delete process.env.RAAS_LICENSE_KEY;
  });

  describe('validateLicense', () => {
    it('should return free tier when no license key', () => {
      const result = validateLicense();

      expect(result.isValid).toBe(false);
      expect(result.tier).toBe('free');
      expect(result.features).toEqual(PREMIUM_FEATURES.free);
      expect(result.error).toContain('No license key');
    });

    it('should return free tier when license key is empty string', () => {
      process.env.RAAS_LICENSE_KEY = '';
      const result = validateLicense();

      expect(result.isValid).toBe(false);
      expect(result.tier).toBe('free');
    });

    it('should return pro tier for valid pro license', () => {
      process.env.RAAS_LICENSE_KEY = 'raas_pro_abc123def456789';
      const result = validateLicense();

      expect(result.isValid).toBe(true);
      expect(result.tier).toBe('pro');
      expect(result.features).toEqual(PREMIUM_FEATURES.pro);
    });

    it('should return enterprise tier for enterprise license', () => {
      process.env.RAAS_LICENSE_KEY = 'raas_ent_xyz789abc123456';
      const result = validateLicense();

      expect(result.isValid).toBe(true);
      expect(result.tier).toBe('enterprise');
      expect(result.features).toEqual(PREMIUM_FEATURES.enterprise);
    });

    it('should reject short license keys', () => {
      process.env.RAAS_LICENSE_KEY = 'short';
      const result = validateLicense();

      expect(result.isValid).toBe(false);
      expect(result.error).toContain('too short');
    });

    it('should mask license key in response', () => {
      process.env.RAAS_LICENSE_KEY = 'raas_pro_abcdefghij123456';
      const result = validateLicense();

      expect(result.licenseKey).toMatch(/^[a-z0-9]+\.\.\.[a-z0-9]+$/);
      expect(result.licenseKey).not.toContain(process.env.RAAS_LICENSE_KEY);
    });
  });

  describe('hasFeature', () => {
    it('should return true for free tier features without license', () => {
      delete process.env.RAAS_LICENSE_KEY;
      
      expect(hasFeature('basic-cli-commands')).toBe(true);
      expect(hasFeature('open-source-agents')).toBe(true);
      expect(hasFeature('community-patterns')).toBe(true);
    });

    it('should return false for premium features without license', () => {
      delete process.env.RAAS_LICENSE_KEY;
      
      expect(hasFeature('premium-agents')).toBe(false);
      expect(hasFeature('agi-auto-pilot')).toBe(false);
    });

    it('should return true for premium features with pro license', () => {
      process.env.RAAS_LICENSE_KEY = 'raas_pro_test1234567890';
      
      expect(hasFeature('premium-agents')).toBe(true);
      expect(hasFeature('advanced-patterns')).toBe(true);
    });
  });

  describe('requireFeature', () => {
    it('should not throw for available features', () => {
      process.env.RAAS_LICENSE_KEY = 'raas_pro_test1234567890';
      
      expect(() => requireFeature('premium-agents')).not.toThrow();
    });

    it('should throw for unavailable features', () => {
      delete process.env.RAAS_LICENSE_KEY;
      
      expect(() => requireFeature('agi-auto-pilot')).toThrow('Premium feature');
    });
  });

  describe('getLicenseStatus', () => {
    it('should return free tier status message', () => {
      delete process.env.RAAS_LICENSE_KEY;
      const status = getLicenseStatus();

      expect(status).toContain('Free Tier');
      expect(status).toContain('Open Source');
    });

    it('should return pro tier status message', () => {
      process.env.RAAS_LICENSE_KEY = 'raas_pro_test1234567890';
      const status = getLicenseStatus();

      expect(status).toContain('PRO');
      expect(status).toContain('💎');
    });

    it('should return enterprise tier status message', () => {
      process.env.RAAS_LICENSE_KEY = 'raas_ent_test1234567890';
      const status = getLicenseStatus();

      expect(status).toContain('ENTERPRISE');
      expect(status).toContain('🏢');
    });
  });
});
