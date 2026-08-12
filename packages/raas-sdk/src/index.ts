/**
 * @mekong/raas-sdk — Typed TypeScript SDK for the Mekong RaaS Gateway
 *
 * Usage:
 *   import { createRaaSClient } from '@mekong/raas-sdk';
 *   const client = createRaaSClient({ jwt: 'your-token' });
 *   const mission = await client.missions.submit({ goal: 'Write a blog post' });
 */

import { MekongClient, type MekongClientConfig } from './client.js';

/** Factory — create a configured MekongClient in one call */
export function createRaaSClient(config: MekongClientConfig): MekongClient {
  return new MekongClient(config);
}

export { MekongClient };
export type { MekongClientConfig };

export type {
  Agent,
  AgentExecuteInput,
  AgentExecuteResult,
  AgentListParams,
} from './resources/agents-resource.js';

export {
  MekongApiError,
  MekongAuthError,
  MekongInsufficientCreditsError,
  MekongNotFoundError,
  MekongRateLimitError,
  MekongNetworkError,
} from './errors.js';

export type {
  // Enums
  MissionStatus,
  Complexity,
  Tier,
  LicenseType,
  // Models
  Mission,
  MissionPoll,
  Tenant,
  ApiKey,
  CreditTransaction,
  Template,
  Review,
  Alert,
  WebhookLog,
  License,
  PricingTier,
  CreditPack,
  PublicStats,
  AnalyticsStats,
  OnboardingChecklist,
  OnboardingStep,
  SystemStatus,
  StatusComponent,
  Incident,
  HealthResponse,
  WaitlistResponse,
  PaginatedResponse,
  // Request params
  SignupParams,
  SignupResponse,
  SubmitMissionParams,
  ListMissionsParams,
  BatchSubmitParams,
  UpdateTenantSettingsParams,
  CreateApiKeyParams,
  CreateApiKeyResponse,
  CreditCheckParams,
  CreditCheckResponse,
  RedeemCouponParams,
  SubmitFeedbackParams,
  SubmitReviewParams,
  MarketplaceSearchParams,
  CreateLicenseParams,
  ActivateLicenseResponse,
  CreateCheckoutParams,
  CreateCheckoutResponse,
} from './types.js';
