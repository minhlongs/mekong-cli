import { logger } from '@/lib/utils/logger'

const AGENTOPS_API = process.env.NEXT_PUBLIC_GATEWAY_API_URL || 'http://localhost:8000'

export interface Win3Metrics {
  anh_win: {
    visibility: string
    portfolio_tracked: number
    deals_pipeline: number
    cash_flow: string
  }
  agency_win: {
    automation: string
    revenue: string
    agents_active: number
    hours_saved: string
  }
  startup_win: {
    protection: string
    term_sheets_reviewed: number
    bad_deals_blocked: number
    deals_sourced: number
  }
  overall: string
  target: string
  gap: string
}

export interface AgentSummary {
  agentops_version: string
  total_agents: number
  agent_clusters: Record<string, { agents: number; status: string; value: string }>
  win3_metrics: {
    anh_win: string
    agency_win: string
    startup_win: string
    overall: string
  }
  key_achievements: string[]
  binh_phap_applied: string[]
}

export interface Startup {
  id: string
  name: string
  mrr: number
  health_score: number
  runway: number
}

export interface Alert {
  source: string
  startup: string
  type: string
  severity: string
}

export interface Deal {
  id: string
  name: string
  stage: string
  binh_phap_score: number
  source: string
}

export interface TermSheetReviewResult {
  score: number
  risk_level: 'low' | 'medium' | 'high'
  red_flags: string[]
  recommendations: string[]
  details?: Record<string, unknown>
}

export interface StartupScoreResult {
  startup_name: string
  total_score: number
  binh_phap_score: number
  market_fit_tier: string
  breakdown: Record<string, number>
}

export interface DualRailCheckoutRequest {
  tier: 'BASIC' | 'PREMIUM' | 'ENTERPRISE' | 'MASTER'
  rail: 'vietqr' | 'nowpayments'
  billing_period?: 'monthly' | 'annual'
  customer_email?: string
  customer_name?: string
}

export interface DualRailCheckoutResponse {
  order_id: string
  tier: string
  rail: string
  amount_usd: number
  amount_vnd: number
  checkout_url: string
  qr_code_url?: string
  status: string
}

export interface CheckoutStatusResponse {
  order_id: string
  status: 'pending' | 'paid' | 'expired'
  tier: string
  license_key?: string | null
  tenant_id?: string | null
}

export interface LicenseStatusResponse {
  active: boolean
  tier: string
  tenant_id: string
  expires_at?: number | null
  features: string[]
  mcu_balance: number
}

export interface PricingTierInfo {
  usd: number
  vnd: number
  mcu: number
}

export interface PricingCatalogResponse {
  rails: string[]
  tiers: Record<string, PricingTierInfo>
}

export async function getWin3Metrics(): Promise<Win3Metrics | null> {
  try {
    const response = await fetch(`${AGENTOPS_API}/metrics/win3`)
    if (!response.ok) throw new Error('Failed to fetch')
    return (await response.json()) as Win3Metrics
  } catch (error) {
    logger.error('AgentOps API error', error)
    return null
  }
}

export async function getSummary(): Promise<AgentSummary | null> {
  try {
    const response = await fetch(`${AGENTOPS_API}/summary`)
    if (!response.ok) throw new Error('Failed to fetch')
    return (await response.json()) as AgentSummary
  } catch (error) {
    logger.error('AgentOps API error', error)
    return null
  }
}

export async function getPortfolio(): Promise<{ total: number; startups: Startup[] } | null> {
  try {
    const response = await fetch(`${AGENTOPS_API}/portfolio`)
    if (!response.ok) throw new Error('Failed to fetch')
    return (await response.json()) as { total: number; startups: Startup[] }
  } catch (error) {
    logger.error('AgentOps API error', error)
    return null
  }
}

export async function getAlerts(): Promise<{ total_alerts: number; alerts: Alert[] } | null> {
  try {
    const response = await fetch(`${AGENTOPS_API}/alerts`)
    if (!response.ok) throw new Error('Failed to fetch')
    return (await response.json()) as { total_alerts: number; alerts: Alert[] }
  } catch (error) {
    logger.error('AgentOps API error', error)
    return null
  }
}

export async function getPipeline(): Promise<{ total_deals: number; deals: Deal[] } | null> {
  try {
    const response = await fetch(`${AGENTOPS_API}/dealflow/pipeline`)
    if (!response.ok) throw new Error('Failed to fetch')
    return (await response.json()) as { total_deals: number; deals: Deal[] }
  } catch (error) {
    logger.error('AgentOps API error', error)
    return null
  }
}

export async function reviewTermSheet(data: {
  valuation?: number
  investment?: number
  liquidation_preference?: number
  equity_percentage?: number
  anti_dilution?: string
  participation?: boolean
}): Promise<TermSheetReviewResult | null> {
  try {
    const response = await fetch(`${AGENTOPS_API}/guardian/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error('Failed to review')
    return (await response.json()) as TermSheetReviewResult
  } catch (error) {
    logger.error('AgentOps API error', error)
    return null
  }
}

export async function scoreStartup(data: {
  name: string
  industry?: string
  stage?: string
  mrr?: number
  growth?: number
}): Promise<StartupScoreResult | null> {
  try {
    const response = await fetch(`${AGENTOPS_API}/dealflow/score`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error('Failed to score')
    return (await response.json()) as StartupScoreResult
  } catch (error) {
    logger.error('AgentOps API error', error)
    return null
  }
}

export async function createDualRailCheckout(
  req: DualRailCheckoutRequest
): Promise<DualRailCheckoutResponse | null> {
  try {
    const response = await fetch(`${AGENTOPS_API}/v1/checkout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    })
    if (!response.ok) throw new Error('Failed to create checkout')
    return (await response.json()) as DualRailCheckoutResponse
  } catch (error) {
    logger.error('AgentOps API error', error)
    return null
  }
}

export async function getCheckoutStatus(
  orderId: string
): Promise<CheckoutStatusResponse | null> {
  try {
    const response = await fetch(
      `${AGENTOPS_API}/v1/checkout/status?order_id=${encodeURIComponent(orderId)}`
    )
    if (!response.ok) throw new Error('Failed to fetch checkout status')
    return (await response.json()) as CheckoutStatusResponse
  } catch (error) {
    logger.error('AgentOps API error', error)
    return null
  }
}

export async function activateLicenseKey(
  licenseKey: string
): Promise<LicenseStatusResponse | null> {
  try {
    const response = await fetch(`${AGENTOPS_API}/v1/license/activate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ license_key: licenseKey }),
    })
    if (!response.ok) throw new Error('Failed to activate license')
    return (await response.json()) as LicenseStatusResponse
  } catch (error) {
    logger.error('AgentOps API error', error)
    return null
  }
}

export async function getLicenseStatus(
  licenseKey?: string
): Promise<LicenseStatusResponse | null> {
  try {
    const query = licenseKey ? `?license_key=${encodeURIComponent(licenseKey)}` : ''
    const response = await fetch(`${AGENTOPS_API}/v1/license/status${query}`)
    if (!response.ok) throw new Error('Failed to fetch license status')
    return (await response.json()) as LicenseStatusResponse
  } catch (error) {
    logger.error('AgentOps API error', error)
    return null
  }
}

export async function getPricingCatalog(): Promise<PricingCatalogResponse | null> {
  try {
    const response = await fetch(`${AGENTOPS_API}/v1/pricing`)
    if (!response.ok) throw new Error('Failed to fetch pricing catalog')
    return (await response.json()) as PricingCatalogResponse
  } catch (error) {
    logger.error('AgentOps API error', error)
    return null
  }
}
