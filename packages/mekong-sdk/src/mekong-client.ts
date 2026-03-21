/**
 * MekongClient — HTTP client for RaaS Gateway API
 * Supports Bearer token OR X-API-Key authentication
 * Zero external dependencies — uses native fetch()
 */

import { MekongError } from './mekong-error.js'
import type {
  MekongClientConfig,
  SignupRequest, SignupResponse,
  LoginRequest, LoginResponse,
  TenantProfile, UpgradeResponse, ReferralsResponse, DigestResponse,
  CreateApiKeyRequest, CreateApiKeyResponse,
  ListApiKeysResponse, RevokeApiKeyResponse,
  SubmitMissionRequest, SubmitMissionResponse,
  Mission, ListMissionsRequest, ListMissionsResponse,
  CancelMissionResponse, ShareMissionResponse,
  BatchMissionsRequest, BatchMissionsResponse,
  MissionTemplate,
  CreditsResponse, CheckCostRequest, CheckCostResponse,
  PurchaseCreditsRequest, PurchaseCreditsResponse,
  PricingResponse,
  AnalyticsResponse,
  StatsResponse,
} from './types.js'

const DEFAULT_BASE_URL = 'https://raas.agencyos.network'
const DEFAULT_TIMEOUT = 30_000

export class MekongClient {
  private readonly baseUrl: string
  private readonly timeout: number
  private token: string | undefined
  private apiKey: string | undefined

  constructor(config: MekongClientConfig = {}) {
    this.baseUrl = (config.baseUrl ?? DEFAULT_BASE_URL).replace(/\/$/, '')
    this.timeout = config.timeout ?? DEFAULT_TIMEOUT
    this.token = config.token ?? undefined
    this.apiKey = config.apiKey ?? undefined
  }

  /** Update the bearer token (e.g. after login/signup) */
  setToken(token: string): void {
    this.token = token
    this.apiKey = void 0
  }

  /** Switch to API key auth */
  setApiKey(apiKey: string): void {
    this.apiKey = apiKey
    this.token = void 0
  }

  // ─── Internal ───────────────────────────────────────────────────────────────

  private buildHeaders(): HeadersInit {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    } else if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey
    }
    return headers
  }

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const controller = new AbortController()
    const tid = setTimeout(() => controller.abort(), this.timeout)

    try {
      const init: RequestInit = {
        method,
        headers: this.buildHeaders(),
        signal: controller.signal,
      }
      if (body !== undefined) {
        init.body = JSON.stringify(body)
      }
      const res = await fetch(`${this.baseUrl}${path}`, init)
      clearTimeout(tid)

      if (!res.ok) {
        const raw = await res.json().catch(() => ({ error: `HTTP ${res.status}` }))
        throw MekongError.fromResponse(res.status, raw as Record<string, unknown>)
      }

      return res.json() as Promise<T>
    } catch (err) {
      clearTimeout(tid)
      if (err instanceof MekongError) throw err
      if (err instanceof Error && err.name === 'AbortError') throw MekongError.timeout()
      throw MekongError.network(err)
    }
  }

  private buildQuery(params: Record<string, string | number | undefined>): string {
    const qs = new URLSearchParams()
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined) qs.set(k, String(v))
    }
    const str = qs.toString()
    return str ? `?${str}` : ''
  }

  // ─── Auth ───────────────────────────────────────────────────────────────────

  /** Register a new tenant. Sets token automatically after success. */
  async signup(req: SignupRequest): Promise<SignupResponse> {
    const res = await this.request<SignupResponse>('POST', '/v1/tenants/signup', req)
    this.token = res.token
    this.apiKey = void 0
    return res
  }

  /** Login (magic-link / OTP flow). Sets token automatically. */
  async login(req: LoginRequest): Promise<LoginResponse> {
    const res = await this.request<LoginResponse>('POST', '/v1/tenants/login', req)
    this.token = res.token
    this.apiKey = void 0
    return res
  }

  // ─── Profile ────────────────────────────────────────────────────────────────

  async getProfile(): Promise<TenantProfile> {
    return this.request<TenantProfile>('GET', '/v1/tenants/profile')
  }

  async getUpgrade(): Promise<UpgradeResponse> {
    return this.request<UpgradeResponse>('GET', '/v1/tenants/upgrade')
  }

  async getReferrals(): Promise<ReferralsResponse> {
    return this.request<ReferralsResponse>('GET', '/v1/tenants/referrals')
  }

  async getDigest(): Promise<DigestResponse> {
    return this.request<DigestResponse>('GET', '/v1/tenants/digest')
  }

  // ─── API Keys ───────────────────────────────────────────────────────────────

  async createApiKey(req: CreateApiKeyRequest): Promise<CreateApiKeyResponse> {
    return this.request<CreateApiKeyResponse>('POST', '/v1/tenants/api-keys', req)
  }

  async listApiKeys(): Promise<ListApiKeysResponse> {
    return this.request<ListApiKeysResponse>('GET', '/v1/tenants/api-keys')
  }

  async revokeApiKey(keyId: string): Promise<RevokeApiKeyResponse> {
    return this.request<RevokeApiKeyResponse>('DELETE', `/v1/tenants/api-keys/${keyId}`)
  }

  // ─── Missions ───────────────────────────────────────────────────────────────

  async submitMission(req: SubmitMissionRequest): Promise<SubmitMissionResponse> {
    return this.request<SubmitMissionResponse>('POST', '/v1/missions', req)
  }

  async getMission(id: string): Promise<Mission> {
    return this.request<Mission>('GET', `/v1/missions/${id}`)
  }

  async listMissions(opts: ListMissionsRequest = {}): Promise<ListMissionsResponse> {
    const qs = this.buildQuery({ status: opts.status, limit: opts.limit, offset: opts.offset })
    return this.request<ListMissionsResponse>('GET', `/v1/missions${qs}`)
  }

  async pollMission(id: string): Promise<Mission> {
    return this.request<Mission>('GET', `/v1/missions/${id}/poll`)
  }

  async cancelMission(id: string): Promise<CancelMissionResponse> {
    return this.request<CancelMissionResponse>('POST', `/v1/missions/${id}/cancel`)
  }

  async shareMission(id: string): Promise<ShareMissionResponse> {
    return this.request<ShareMissionResponse>('POST', `/v1/missions/${id}/share`)
  }

  async batchMissions(req: BatchMissionsRequest): Promise<BatchMissionsResponse> {
    return this.request<BatchMissionsResponse>('POST', '/v1/missions/batch', req)
  }

  // ─── Credits ────────────────────────────────────────────────────────────────

  async getCredits(): Promise<CreditsResponse> {
    return this.request<CreditsResponse>('GET', '/credits')
  }

  async checkCost(req: CheckCostRequest): Promise<CheckCostResponse> {
    return this.request<CheckCostResponse>('POST', '/credits/check', req)
  }

  async purchaseCredits(req: PurchaseCreditsRequest): Promise<PurchaseCreditsResponse> {
    return this.request<PurchaseCreditsResponse>('POST', '/credits/purchase', req)
  }

  // ─── Analytics ──────────────────────────────────────────────────────────────

  async getAnalytics(): Promise<AnalyticsResponse> {
    return this.request<AnalyticsResponse>('GET', '/v1/analytics')
  }

  // ─── Templates ──────────────────────────────────────────────────────────────

  async getTemplates(category?: string): Promise<any> {
    const qs = this.buildQuery({ category })
    return this.request<any>('GET', `/v1/missions/templates${qs}`)
  }

  // ─── Marketplace ────────────────────────────────────────────────────────────

  async getLeaderboard(): Promise<any> {
    return this.request<any>('GET', '/marketplace/leaderboard')
  }

  async getReviews(missionId: string): Promise<any> {
    return this.request<any>('GET', `/marketplace/${missionId}/reviews`)
  }

  async submitReview(missionId: string, rating: number, comment?: string): Promise<any> {
    return this.request<any>('POST', `/marketplace/${missionId}/reviews`, { rating, comment })
  }

  // ─── Credits Extended ───────────────────────────────────────────────────────

  async redeemCoupon(code: string): Promise<any> {
    return this.request<any>('POST', '/v1/credits/redeem', { code })
  }

  async submitFeedback(type: string, message: string): Promise<any> {
    return this.request<any>('POST', '/v1/credits/feedback', { type, message })
  }

  // ─── Tenant Extended ────────────────────────────────────────────────────────

  async trialExtend(): Promise<any> {
    return this.request<any>('POST', '/v1/tenants/trial-extend')
  }

  async updateSettings(settings: { webhook_url?: string; notify_email?: boolean; notify_telegram?: boolean }): Promise<any> {
    return this.request<any>('PUT', '/v1/tenants/settings', settings)
  }

  async getUsage(): Promise<any> {
    return this.request<any>('GET', '/v1/tenants/usage')
  }

  async getInvoices(params?: { limit?: number; offset?: number; type?: string }): Promise<any> {
    const qs = this.buildQuery({ limit: params?.limit, offset: params?.offset, type: params?.type })
    return this.request<any>('GET', `/v1/tenants/invoices${qs}`)
  }

  // ─── Health ─────────────────────────────────────────────────────────────────

  async deepHealthCheck(): Promise<any> {
    return this.request<any>('GET', '/health/deep')
  }

  // ─── Public (no auth required) ──────────────────────────────────────────────

  static async getStats(baseUrl: string = DEFAULT_BASE_URL): Promise<StatsResponse> {
    const res = await fetch(`${baseUrl.replace(/\/$/, '')}/stats`)
    if (!res.ok) throw MekongError.fromResponse(res.status, await res.json().catch(() => ({})))
    return res.json()
  }

  static async getTemplates(baseUrl: string = DEFAULT_BASE_URL): Promise<MissionTemplate[]> {
    const res = await fetch(`${baseUrl.replace(/\/$/, '')}/v1/missions/templates`)
    if (!res.ok) throw MekongError.fromResponse(res.status, await res.json().catch(() => ({})))
    return res.json()
  }

  static async getPricing(baseUrl: string = DEFAULT_BASE_URL): Promise<PricingResponse> {
    const res = await fetch(`${baseUrl.replace(/\/$/, '')}/billing/pricing`)
    if (!res.ok) throw MekongError.fromResponse(res.status, await res.json().catch(() => ({})))
    return res.json()
  }
}
