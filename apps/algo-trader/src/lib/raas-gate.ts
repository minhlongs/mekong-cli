/**
 * RAAS License Gate — Premium Feature Protection
 *
 * Gates ML model weights loading and premium backtest data behind RAAS_LICENSE_KEY.
 * Trading engine source and base strategies remain open source.
 */

/**
 * License tier levels
 */
export enum LicenseTier {
  FREE = 'free',
  PRO = 'pro',
  ENTERPRISE = 'enterprise',
}

/**
 * License validation result
 */
export interface LicenseValidation {
  valid: boolean;
  tier: LicenseTier;
  expiresAt?: string;
  features: string[];
}

/**
 * Custom error for license violations
 */
export class LicenseError extends Error {
  constructor(
    message: string,
    public readonly requiredTier: LicenseTier,
    public readonly feature: string
  ) {
    super(message);
    this.name = 'LicenseError';
  }
}

/**
 * RAAS License Service
 *
 * Validates license keys and gates premium features.
 * In production, this would call a license server.
 * For now, uses environment variable validation.
 */
export class LicenseService {
  private static instance: LicenseService;
  private validatedLicense: LicenseValidation | null = null;

  private constructor() {}

  static getInstance(): LicenseService {
    if (!LicenseService.instance) {
      LicenseService.instance = new LicenseService();
    }
    return LicenseService.instance;
  }

  /**
   * Validate RAAS license key
   *
   * Free tier: No license key required (basic features only)
   * Pro tier: Valid license key (ML models + premium data)
   * Enterprise: Valid enterprise key (all features + priority)
   */
  validate(key?: string): LicenseValidation {
    const licenseKey = key || process.env.RAAS_LICENSE_KEY;

    // No key = free tier
    if (!licenseKey) {
      this.validatedLicense = {
        valid: false,
        tier: LicenseTier.FREE,
        features: ['basic_strategies', 'live_trading', 'basic_backtest'],
      };
      return this.validatedLicense;
    }

    // Validate key format (in production, verify against license server)
    if (licenseKey.startsWith('raas-pro-') || licenseKey.startsWith('RPP-')) {
      this.validatedLicense = {
        valid: true,
        tier: LicenseTier.PRO,
        features: [
          'basic_strategies',
          'live_trading',
          'basic_backtest',
          'ml_models',
          'premium_data',
          'advanced_optimization',
        ],
      };
      return this.validatedLicense;
    }

    if (licenseKey.startsWith('raas-ent-') || licenseKey.startsWith('REP-')) {
      this.validatedLicense = {
        valid: true,
        tier: LicenseTier.ENTERPRISE,
        expiresAt: '2027-12-31',
        features: [
          'basic_strategies',
          'live_trading',
          'basic_backtest',
          'ml_models',
          'premium_data',
          'advanced_optimization',
          'priority_support',
          'custom_strategies',
          'multi_exchange',
        ],
      };
      return this.validatedLicense;
    }

    // Invalid key
    this.validatedLicense = {
      valid: false,
      tier: LicenseTier.FREE,
      features: ['basic_strategies', 'live_trading', 'basic_backtest'],
    };
    return this.validatedLicense;
  }

  /**
   * Check if current license has required tier
   */
  hasTier(required: LicenseTier): boolean {
    if (!this.validatedLicense) {
      this.validate();
    }

    const tierOrder = {
      [LicenseTier.FREE]: 0,
      [LicenseTier.PRO]: 1,
      [LicenseTier.ENTERPRISE]: 2,
    };

    return tierOrder[this.validatedLicense!.tier] >= tierOrder[required];
  }

  /**
   * Check if specific feature is enabled
   */
  hasFeature(feature: string): boolean {
    if (!this.validatedLicense) {
      this.validate();
    }

    return this.validatedLicense!.features.includes(feature);
  }

  /**
   * Get current tier
   */
  getTier(): LicenseTier {
    if (!this.validatedLicense) {
      this.validate();
    }
    return this.validatedLicense!.tier;
  }

  /**
   * Require specific tier or throw LicenseError
   */
  requireTier(required: LicenseTier, feature: string): void {
    if (!this.hasTier(required)) {
      throw new LicenseError(
        `Feature "${feature}" requires ${required.toUpperCase()} license. Current tier: ${this.getTier()}`,
        required,
        feature
      );
    }
  }

  /**
   * Require specific feature or throw LicenseError
   */
  requireFeature(feature: string): void {
    if (!this.hasFeature(feature)) {
      throw new LicenseError(
        `Feature "${feature}" is not enabled. Current tier: ${this.getTier()}`,
        LicenseTier.PRO,
        feature
      );
    }
  }

  /**
   * Reset cached license (for testing)
   */
  reset(): void {
    this.validatedLicense = null;
  }
}

// ─── Convenience helpers ─────────────────────────────────────────────────────

/**
 * Check if running with premium license
 */
export function isPremium(): boolean {
  return LicenseService.getInstance().hasTier(LicenseTier.PRO);
}

/**
 * Check if running with enterprise license
 */
export function isEnterprise(): boolean {
  return LicenseService.getInstance().hasTier(LicenseTier.ENTERPRISE);
}

/**
 * Get current license tier
 */
export function getLicenseTier(): LicenseTier {
  return LicenseService.getInstance().getTier();
}

/**
 * Validate license and return tier
 */
export function validateLicense(key?: string): LicenseValidation {
  return LicenseService.getInstance().validate(key);
}

/**
 * Require premium tier for ML features
 */
export function requireMLFeature(_feature: string): void {
  LicenseService.getInstance().requireFeature('ml_models');
}

/**
 * Require premium tier for historical data access
 */
export function requirePremiumData(): void {
  LicenseService.getInstance().requireFeature('premium_data');
}

// ─── Express/Fastify middleware helper ───────────────────────────────────────

/**
 * Middleware factory for API routes
 * Usage: app.use('/api/premium/*', requireLicense('pro'))
 */
export function requireLicenseMiddleware(tier: LicenseTier = LicenseTier.PRO) {
  return (req: any, res: any, next: (err?: any) => void) => {
    try {
      LicenseService.getInstance().requireTier(tier, req.path);
      next();
    } catch (err) {
      if (err instanceof LicenseError) {
        res.status(403).json({
          error: 'License Required',
          message: err.message,
          requiredTier: tier,
          currentTier: getLicenseTier(),
        });
      } else {
        next(err);
      }
    }
  };
}
