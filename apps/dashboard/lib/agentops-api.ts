// AgentOps API Service - Connect Frontend to AgentOps Engine

import { logger } from '@/lib/utils/logger'
import { resolveEngineApiUrl } from '@/lib/demo-guard'

const AGENTOPS_API = resolveEngineApiUrl()

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
  agent_clusters: {
    [key: string]: { agents: number; status: string; value: string }
  }
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

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T | null> {
  try {
    const response = await fetch(`${AGENTOPS_API}${path}`, init)
    if (!response.ok) throw new Error(`Failed request: ${path}`)
    return await response.json()
  } catch (error) {
    logger.error('AgentOps API error', error)
    return null
  }
}

export async function getWin3Metrics(): Promise<Win3Metrics | null> {
  return fetchJson<Win3Metrics>('/metrics/win3')
}

export async function getSummary(): Promise<AgentSummary | null> {
  return fetchJson<AgentSummary>('/summary')
}

export async function getPortfolio(): Promise<{ total: number; startups: Startup[] } | null> {
  return fetchJson<{ total: number; startups: Startup[] }>('/portfolio')
}

export async function getAlerts(): Promise<{ total_alerts: number; alerts: Alert[] } | null> {
  return fetchJson<{ total_alerts: number; alerts: Alert[] }>('/alerts')
}

export async function getPipeline(): Promise<{ total_deals: number; deals: Deal[] } | null> {
  return fetchJson<{ total_deals: number; deals: Deal[] }>('/dealflow/pipeline')
}

export async function reviewTermSheet(data: {
  valuation?: number
  investment?: number
  liquidation_preference?: number
  equity_percentage?: number
  anti_dilution?: string
  participation?: boolean
}): Promise<Record<string, unknown> | null> {
  return fetchJson<Record<string, unknown>>('/guardian/review', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

export async function scoreStartup(data: {
  name: string
  industry?: string
  stage?: string
  mrr?: number
  growth?: number
}): Promise<Record<string, unknown> | null> {
  return fetchJson<Record<string, unknown>>('/dealflow/score', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

export default {
  getWin3Metrics,
  getSummary,
  getPortfolio,
  getAlerts,
  getPipeline,
  reviewTermSheet,
  scoreStartup,
}
