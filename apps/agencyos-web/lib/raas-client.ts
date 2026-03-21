/**
 * RaaS Gateway Client — unified client for raas.agencyos.network
 */

export interface RaasConfig {
  baseUrl: string
  token?: string
  apiKey?: string
  timeout?: number
}

export class RaasClient {
  private baseUrl: string
  private token?: string
  private apiKey?: string
  private timeout: number

  constructor(config: RaasConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, '')
    this.token = config.token
    this.apiKey = config.apiKey
    this.timeout = config.timeout || 30000
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = { 'Content-Type': 'application/json' }
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`
    else if (this.apiKey) headers['X-API-Key'] = this.apiKey
    return headers
  }

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const controller = new AbortController()
    const tid = setTimeout(() => controller.abort(), this.timeout)
    try {
      const res = await fetch(`${this.baseUrl}${path}`, {
        method, headers: this.getHeaders(), signal: controller.signal,
        body: body ? JSON.stringify(body) : undefined,
      })
      clearTimeout(tid)
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }))
        throw Object.assign(new Error(err.error || `HTTP ${res.status}`), { status: res.status, data: err })
      }
      return res.json()
    } catch (e) {
      clearTimeout(tid)
      throw e
    }
  }

  // Auth
  async signup(name: string, email: string, ref?: string) {
    return this.request<{ tenantId: string; token: string; credits: number; referralCode: string }>(
      'POST', '/v1/tenants/signup', { name, email, ref }
    )
  }

  async login(email: string) {
    return this.request<{ tenantId: string; token: string; tier: string }>(
      'POST', '/v1/tenants/login', { email }
    )
  }

  // Profile
  async getProfile() {
    return this.request<{ id: string; name: string; email: string; tier: string; balance: number }>(
      'GET', '/v1/tenants/profile'
    )
  }

  // API Keys
  async createApiKey(name: string) {
    return this.request<{ keyId: string; apiKey: string }>('POST', '/v1/tenants/api-keys', { name })
  }

  async listApiKeys() {
    return this.request<{ keys: Array<{ id: string; name: string; revoked: number }> }>('GET', '/v1/tenants/api-keys')
  }

  async revokeApiKey(keyId: string) {
    return this.request<{ revoked: boolean }>('DELETE', `/v1/tenants/api-keys/${keyId}`)
  }

  // Missions
  async submitMission(goal: string, opts?: { complexity?: string; project?: string; model?: string; callback_url?: string }) {
    return this.request<{ id: string; status: string; creditsCost: number }>(
      'POST', '/v1/missions', { goal, ...opts }
    )
  }

  async getMission(id: string) {
    return this.request<{ id: string; status: string; result?: string; goal: string; creditsCost: number }>(
      'GET', `/v1/missions/${id}`
    )
  }

  async listMissions(opts?: { status?: string; limit?: number; offset?: number }) {
    const params = new URLSearchParams()
    if (opts?.status) params.set('status', opts.status)
    if (opts?.limit) params.set('limit', String(opts.limit))
    if (opts?.offset) params.set('offset', String(opts.offset))
    const qs = params.toString() ? `?${params}` : ''
    return this.request<{ missions: any[]; total: number }>('GET', `/v1/missions${qs}`)
  }

  async cancelMission(id: string) {
    return this.request<{ cancelled: boolean }>('POST', `/v1/missions/${id}/cancel`)
  }

  async shareMission(id: string) {
    return this.request<{ shared: boolean; shareUrl: string }>('POST', `/v1/missions/${id}/share`)
  }

  async batchMissions(goals: Array<{ goal: string; complexity?: string }>) {
    return this.request<{ submitted: number; failed: number; missions: any[] }>(
      'POST', '/v1/missions/batch', { goals }
    )
  }

  // Credits
  async getCredits() {
    return this.request<{ balance: number; totalEarned: number; totalSpent: number }>('GET', '/credits')
  }

  async checkCost(complexity: string) {
    return this.request<{ cost: number; balance: number; sufficient: boolean }>(
      'POST', '/credits/check', { complexity }
    )
  }

  async purchaseCredits(pack: string) {
    return this.request<{ checkoutUrl: string; credits: number; price: number }>(
      'POST', '/credits/purchase', { pack }
    )
  }

  // Analytics
  async getAnalytics() {
    return this.request<{ summary: any; byComplexity: any; byStatus: any; daily: any[] }>('GET', '/v1/analytics')
  }

  // Referrals
  async getReferrals() {
    return this.request<{ referralCode: string; totalReferred: number; creditsEarned: number }>(
      'GET', '/v1/tenants/referrals'
    )
  }

  // Digest
  async getDigest() {
    return this.request<{ period: string; missions: any; balance: number; recentGoals: any[] }>(
      'GET', '/v1/tenants/digest'
    )
  }

  // Marketplace
  async getMarketplace(params?: { limit?: number; q?: string }): Promise<any> {
    const sp = new URLSearchParams()
    if (params?.limit) sp.set('limit', String(params.limit))
    if (params?.q) sp.set('q', params.q)
    return this.request<any>('GET', `/marketplace?${sp}`)
  }

  // Alerts
  async getAlerts(): Promise<any> {
    return this.request<any>('GET', '/v1/alerts')
  }

  async getAlertCount(): Promise<any> {
    return this.request<any>('GET', '/v1/alerts/count')
  }

  async markAlertRead(alertId: string): Promise<any> {
    return this.request<any>('POST', `/v1/alerts/${alertId}/read`)
  }

  // Stripe billing
  async createStripeCheckout(packId: string): Promise<any> {
    return this.request<any>('POST', '/billing/stripe/checkout', { packId })
  }

  async getStripePacks(): Promise<any> {
    return this.request<any>('GET', '/billing/stripe/packs')
  }

  // Public (no auth)
  static async getStats(baseUrl: string) {
    const res = await fetch(`${baseUrl}/stats`)
    return res.json()
  }

  static async getTemplates(baseUrl: string) {
    const res = await fetch(`${baseUrl}/v1/missions/templates`)
    return res.json()
  }

  static async getPricing(baseUrl: string) {
    const res = await fetch(`${baseUrl}/billing/pricing`)
    return res.json()
  }
}

export function createRaasClient(config?: Partial<RaasConfig>): RaasClient {
  return new RaasClient({
    baseUrl: config?.baseUrl || process.env.NEXT_PUBLIC_RAAS_GATEWAY_URL || 'https://raas.agencyos.network',
    token: config?.token || process.env.NEXT_PUBLIC_RAAS_TOKEN,
    apiKey: config?.apiKey || process.env.NEXT_PUBLIC_RAAS_API_KEY,
    timeout: config?.timeout,
  })
}

export default RaasClient
