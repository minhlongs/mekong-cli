/**
 * RaaS (ROIaaS-as-a-Service) — License validation, credit metering, and pricing
 */
export {
  type RaasTier,
  type TierConfig,
  type UsageRecord,
  TIER_CONFIGS,
  calculateMonthlyCost,
  hasCreditsRemaining,
  getOverageCredits,
} from './raas-pricing.js';

export {
  type TenantLicense,
  type MeteringResult,
  registerTenant,
  getTenant,
  validateAndMeter,
  recordUsage,
  getUsageLog,
  resetTenantUsage,
} from './raas-gateway.js';

export {
  type ApiResponse,
  handleValidate,
  handleGetBalance,
  handleRegisterTenant,
  handleGetUsage,
  handleListTiers,
} from './raas-api.js';

export {
  type OnboardingRequest,
  type OnboardingResult,
  type ApiKeyRecord,
  generateApiKey,
  handleOnboardTenant,
  validateApiKey,
  revokeApiKey,
  listTenantApiKeys,
} from './raas-onboarding.js';
