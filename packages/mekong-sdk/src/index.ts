/**
 * @mekong/sdk — RaaS Gateway TypeScript SDK
 *
 * @example
 * ```ts
 * import { MekongClient } from '@mekong/sdk'
 *
 * const client = new MekongClient({ apiKey: 'mk_...' })
 * const mission = await client.submitMission({ goal: 'Write a landing page copy' })
 * ```
 */

export { MekongClient } from './mekong-client.js'
export { MekongError } from './mekong-error.js'
export type {
  MekongClientConfig,
  // Auth
  SignupRequest, SignupResponse,
  LoginRequest, LoginResponse,
  // Profile & Tenant
  TenantProfile, UpgradeResponse, ReferralsResponse, DigestResponse, DigestMissions,
  // API Keys
  ApiKey, CreateApiKeyRequest, CreateApiKeyResponse,
  ListApiKeysResponse, RevokeApiKeyResponse,
  // Missions
  MissionComplexity, MissionStatus,
  SubmitMissionRequest, SubmitMissionResponse,
  Mission, ListMissionsRequest, ListMissionsResponse,
  CancelMissionResponse, ShareMissionResponse,
  BatchMissionGoal, BatchMissionsRequest, BatchMissionsResponse,
  MissionTemplate,
  // Credits
  CreditsResponse, CheckCostRequest, CheckCostResponse,
  PurchaseCreditsRequest, PurchaseCreditsResponse,
  PricingResponse, PricingPack,
  // Analytics
  AnalyticsResponse, AnalyticsSummary, DailyAnalytics,
  // Stats
  StatsResponse,
} from './types.js'
