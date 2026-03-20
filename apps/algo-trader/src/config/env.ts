/**
 * Environment Configuration
 * Centralized config for environment variables
 */

export const config = {
  // Audit Log Configuration
  AUDIT_LOG_ENABLED: process.env.AUDIT_LOG_ENABLED || 'true',
  AUDIT_RETENTION_DAYS: process.env.AUDIT_RETENTION_DAYS || '90',
  AUDIT_BATCH_SIZE: process.env.AUDIT_BATCH_SIZE || '100',

  // License Configuration
  LICENSE_KEY_PREFIX: process.env.LICENSE_KEY_PREFIX || 'raas',

  // Usage Metering
  USAGE_METERING_ENABLED: process.env.USAGE_METERING_ENABLED || 'true',
  OVERAGE_ENABLED: process.env.OVERAGE_ENABLED || 'true',
  OVERAGE_PRICE_PER_CALL: process.env.OVERAGE_PRICE_PER_CALL || '0.01',

  // Dunning Configuration
  DUNNING_ENABLED: process.env.DUNNING_ENABLED || 'true',
  DUNNING_GRACE_PERIOD_DAYS: process.env.DUNNING_GRACE_PERIOD_DAYS || '7',

  // Polar.sh Configuration
  POLAR_API_KEY: process.env.POLAR_API_KEY || '',
  POLAR_WEBHOOK_SECRET: process.env.POLAR_WEBHOOK_SECRET || '',
};
