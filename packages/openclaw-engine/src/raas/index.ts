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

export {
  type BillingEvent,
  type UsageAnalytics,
  executeBillableCommand,
  getUsageAnalytics,
  monthlyReset,
  getBillingLog,
} from './raas-billing.js';

export {
  type RateLimitConfig,
  type RateLimitResult,
  type RateLimitHeaders,
  checkRateLimit,
  buildRateLimitHeaders,
  getTierRateLimit,
  resetRateLimit,
  getRateLimitStatus,
} from './raas-rate-limiter.js';

export {
  type ComponentStatus,
  type ComponentHealth,
  type HealthReport,
  checkHealth,
  getUptime,
  getVersion,
} from './raas-health.js';

export {
  type DashboardSummary,
  trackTenantForDashboard,
  untrackTenant,
  getDashboardSummary,
} from './raas-dashboard.js';
