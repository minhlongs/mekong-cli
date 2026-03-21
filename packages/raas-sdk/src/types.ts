/**
 * Full type definitions for Mekong RaaS Gateway SDK
 */

// ─── Enums ────────────────────────────────────────────────────────────────────

export type MissionStatus =
  | 'pending'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type Complexity = 'simple' | 'standard' | 'complex';

export type Tier = 'starter' | 'pro' | 'enterprise';

export type LicenseType = 'personal' | 'team' | 'enterprise' | 'oem';

// ─── Core Models ─────────────────────────────────────────────────────────────

export interface Mission {
  id: string;
  goal: string;
  complexity: Complexity;
  status: MissionStatus;
  result?: string;
  credits_cost: number;
  project?: string;
  callback_url?: string;
  is_public?: boolean;
  created_at: string;
  completed_at?: string;
}

export interface MissionPoll {
  id: string;
  status: MissionStatus;
  credits_cost: number;
  completed_at?: string;
}

export interface Tenant {
  id: string;
  name: string;
  email: string;
  tier: Tier;
  credits: number;
  total_spent: number;
  active: boolean;
  webhook_url?: string;
  notify_email?: boolean;
  notify_telegram?: boolean;
  created_at: string;
}

export interface ApiKey {
  id: string;
  key_prefix: string;
  name?: string;
  created_at: string;
  last_used_at?: string;
}

export interface CreditTransaction {
  id: string;
  type: 'purchase' | 'spend' | 'refund' | 'bonus';
  amount: number;
  balance_after: number;
  description?: string;
  created_at: string;
}

export interface Template {
  id: string;
  name: string;
  description: string;
  goal_template: string;
  complexity: Complexity;
  category: string;
  credits_cost: number;
}

export interface Review {
  id: string;
  mission_id: string;
  tenant_id: string;
  rating: number;
  comment?: string;
  created_at: string;
}

export interface Alert {
  id: string;
  type: string;
  message: string;
  read: boolean;
  created_at: string;
}

export interface WebhookLog {
  id: string;
  event: string;
  url: string;
  status_code?: number;
  attempts: number;
  success: boolean;
  created_at: string;
  delivered_at?: string;
}

export interface License {
  id: string;
  key: string;
  type: LicenseType;
  email?: string;
  name?: string;
  active: boolean;
  activated_at?: string;
  created_at: string;
}

export interface PricingTier {
  tier: Tier;
  credits_per_month: number;
  price_usd: number;
  features: string[];
}

export interface CreditPack {
  id: string;
  credits: number;
  price_usd: number;
  label: string;
}

export interface PublicStats {
  tenants: number;
  missionsCompleted: number;
  creditsProcessed: number;
  updatedAt: string;
}

export interface AnalyticsStats {
  missions_total: number;
  missions_completed: number;
  missions_failed: number;
  credits_spent: number;
  credits_remaining: number;
  period_start: string;
  period_end: string;
}

export interface OnboardingChecklist {
  steps: OnboardingStep[];
  completed_count: number;
  total_count: number;
}

export interface OnboardingStep {
  key: string;
  label: string;
  completed: boolean;
  completed_at?: string;
}

export interface SystemStatus {
  status: 'operational' | 'degraded' | 'outage';
  components: StatusComponent[];
  updated_at: string;
}

export interface StatusComponent {
  name: string;
  status: 'operational' | 'degraded' | 'outage';
}

export interface Incident {
  id: string;
  title: string;
  status: 'investigating' | 'identified' | 'monitoring' | 'resolved';
  created_at: string;
  resolved_at?: string;
}

// ─── Request Params ───────────────────────────────────────────────────────────

export interface SignupParams {
  name: string;
  email: string;
}

export interface SignupResponse {
  token: string;
  tenant: Tenant;
  credits: number;
}

export interface SubmitMissionParams {
  goal: string;
  complexity?: Complexity;
  project?: string;
  callback_url?: string;
}

export interface ListMissionsParams {
  limit?: number;
  offset?: number;
  status?: MissionStatus;
  project?: string;
}

export interface BatchSubmitParams {
  missions: SubmitMissionParams[];
}

export interface UpdateTenantSettingsParams {
  webhook_url?: string;
  notify_email?: boolean;
  notify_telegram?: boolean;
}

export interface CreateApiKeyParams {
  name?: string;
}

export interface CreateApiKeyResponse {
  id: string;
  key: string;
  name?: string;
  created_at: string;
}

export interface CreditCheckParams {
  complexity: Complexity;
}

export interface CreditCheckResponse {
  complexity: Complexity;
  credits_required: number;
  balance: number;
  can_proceed: boolean;
}

export interface RedeemCouponParams {
  code: string;
}

export interface SubmitFeedbackParams {
  type: string;
  message: string;
}

export interface SubmitReviewParams {
  rating: number;
  comment?: string;
}

export interface MarketplaceSearchParams {
  q?: string;
  limit?: number;
  offset?: number;
}

export interface CreateLicenseParams {
  type: LicenseType;
  email?: string;
  name?: string;
}

export interface ActivateLicenseResponse {
  success: boolean;
  license: License;
  message?: string;
}

export interface CreateCheckoutParams {
  pack_id: string;
  success_url?: string;
  cancel_url?: string;
}

export interface CreateCheckoutResponse {
  checkout_url: string;
  session_id: string;
}

export interface HealthResponse {
  status: 'ok' | 'error';
  version?: string;
  timestamp: string;
}

export interface WaitlistResponse {
  success: boolean;
  message: string;
}

// ─── Paginated wrapper ────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  limit: number;
  offset: number;
}
