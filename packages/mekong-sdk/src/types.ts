/**
 * @mekong/sdk — TypeScript interfaces for RaaS Gateway API
 * Base URL: https://raas.agencyos.network
 */

// ─── Config ───────────────────────────────────────────────────────────────────

export interface MekongClientConfig {
  /** Gateway base URL. Defaults to https://raas.agencyos.network */
  baseUrl?: string
  /** JWT bearer token (from login/signup) */
  token?: string
  /** API key (via X-API-Key header) */
  apiKey?: string
  /** Request timeout in ms. Default 30000 */
  timeout?: number
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export interface SignupRequest {
  name: string
  email: string
  /** Optional referral code */
  ref?: string
}

export interface SignupResponse {
  tenantId: string
  token: string
  credits: number
  referralCode: string
}

export interface LoginRequest {
  email: string
}

export interface LoginResponse {
  tenantId: string
  token: string
  tier: string
}

// ─── Profile & Tenant ─────────────────────────────────────────────────────────

export interface TenantProfile {
  id: string
  name: string
  email: string
  tier: string
  balance: number
}

export interface UpgradeResponse {
  checkoutUrl: string
  tier: string
}

export interface ReferralsResponse {
  referralCode: string
  totalReferred: number
  creditsEarned: number
}

export interface DigestResponse {
  period: string
  missions: DigestMissions
  balance: number
  recentGoals: string[]
}

export interface DigestMissions {
  total: number
  completed: number
  failed: number
  pending: number
}

// ─── API Keys ─────────────────────────────────────────────────────────────────

export interface ApiKey {
  id: string
  name: string
  revoked: number
}

export interface CreateApiKeyRequest {
  name: string
}

export interface CreateApiKeyResponse {
  keyId: string
  apiKey: string
}

export interface ListApiKeysResponse {
  keys: ApiKey[]
}

export interface RevokeApiKeyResponse {
  revoked: boolean
}

// ─── Missions ─────────────────────────────────────────────────────────────────

export type MissionComplexity = 'low' | 'medium' | 'high'
export type MissionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface SubmitMissionRequest {
  goal: string
  complexity?: MissionComplexity
  project?: string
  model?: string
  callback_url?: string
}

export interface SubmitMissionResponse {
  id: string
  status: MissionStatus
  creditsCost: number
}

export interface Mission {
  id: string
  status: MissionStatus
  goal: string
  creditsCost: number
  result?: string
  createdAt?: string
  updatedAt?: string
}

export interface ListMissionsRequest {
  status?: MissionStatus
  limit?: number
  offset?: number
}

export interface ListMissionsResponse {
  missions: Mission[]
  total: number
}

export interface CancelMissionResponse {
  cancelled: boolean
}

export interface ShareMissionResponse {
  shared: boolean
  shareUrl: string
}

export interface BatchMissionGoal {
  goal: string
  complexity?: MissionComplexity
}

export interface BatchMissionsRequest {
  goals: BatchMissionGoal[]
}

export interface BatchMissionsResponse {
  submitted: number
  failed: number
  missions: Mission[]
}

export interface MissionTemplate {
  id: string
  name: string
  description: string
  goal: string
  complexity?: MissionComplexity
}

// ─── Credits ──────────────────────────────────────────────────────────────────

export interface CreditsResponse {
  balance: number
  totalEarned: number
  totalSpent: number
}

export interface CheckCostRequest {
  complexity: MissionComplexity
}

export interface CheckCostResponse {
  cost: number
  balance: number
  sufficient: boolean
}

export interface PurchaseCreditsRequest {
  pack: string
}

export interface PurchaseCreditsResponse {
  checkoutUrl: string
  credits: number
  price: number
}

export interface PricingResponse {
  packs: PricingPack[]
}

export interface PricingPack {
  id: string
  credits: number
  price: number
  label?: string
}

// ─── Analytics ────────────────────────────────────────────────────────────────

export interface AnalyticsResponse {
  summary: AnalyticsSummary
  byComplexity: Record<string, number>
  byStatus: Record<string, number>
  daily: DailyAnalytics[]
}

export interface AnalyticsSummary {
  totalMissions: number
  completedMissions: number
  failedMissions: number
  creditsSpent: number
}

export interface DailyAnalytics {
  date: string
  missions: number
  creditsSpent: number
}

// ─── Stats (public) ───────────────────────────────────────────────────────────

export interface StatsResponse {
  totalMissions: number
  totalTenants: number
  uptime?: number
}
