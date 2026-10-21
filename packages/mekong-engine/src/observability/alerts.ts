import type { Context, Next } from 'hono'
import type { MetricsData } from './metrics'
import {
  type AlertPayload,
  formatSlackMessage,
  sendSlackAlert,
  sendAlertsToSlack,
} from './alert-notifier'

export type { AlertPayload }
export { formatSlackMessage, sendSlackAlert, sendAlertsToSlack }

/**
 * Alerting System for RaaS Gateway
 * Threshold-based alerts with Slack webhook integration
 */

export interface AlertConfig {
  id: string
  name: string
  description: string
  threshold: number
  comparator: 'gt' | 'lt' | 'gte' | 'lte' | 'eq'
  metric: keyof MetricsData
  enabled: boolean
  cooldownMinutes: number
}

export interface AlertState {
  lastTriggered: number | null
  triggerCount: number
  isFiring: boolean
}

export const DEFAULT_ALERTS: AlertConfig[] = [
  {
    id: 'error_rate_high',
    name: 'High Error Rate',
    description: 'Error rate exceeds 1%',
    threshold: 1,
    comparator: 'gt',
    metric: 'error_rate',
    enabled: true,
    cooldownMinutes: 5,
  },
  {
    id: 'latency_p99_high',
    name: 'High P99 Latency',
    description: 'P99 latency exceeds 500ms',
    threshold: 500,
    comparator: 'gt',
    metric: 'latency_p99',
    enabled: true,
    cooldownMinutes: 5,
  },
  {
    id: 'mcu_balance_low',
    name: 'Low MCU Balance',
    description: 'MCU balance below 10% threshold',
    threshold: 10,
    comparator: 'lt',
    metric: 'mcu_consumed_total',
    enabled: true,
    cooldownMinutes: 60,
  },
  {
    id: 'uptime_low',
    name: 'Service Uptime Degraded',
    description: 'Service may be experiencing downtime',
    threshold: 99.9,
    comparator: 'lt',
    metric: 'uptime_seconds',
    enabled: true,
    cooldownMinutes: 1,
  },
]

const alertStates: Map<string, AlertState> = new Map()

export function initAlerts(): void {
  for (const alert of DEFAULT_ALERTS) {
    alertStates.set(alert.id, { lastTriggered: null, triggerCount: 0, isFiring: false })
  }
}

export function getAlertState(alertId: string): AlertState | undefined {
  return alertStates.get(alertId)
}

export function getAllAlertStates(): Record<string, AlertState> {
  const result: Record<string, AlertState> = {}
  for (const [id, state] of alertStates.entries()) {
    result[id] = { ...state }
  }
  return result
}

export function checkThreshold(
  value: number,
  threshold: number,
  comparator: 'gt' | 'lt' | 'gte' | 'lte' | 'eq'
): boolean {
  switch (comparator) {
    case 'gt': return value > threshold
    case 'lt': return value < threshold
    case 'gte': return value >= threshold
    case 'lte': return value <= threshold
    case 'eq': return value === threshold
  }
}

function determineSeverity(
  value: number,
  threshold: number
): 'info' | 'warning' | 'critical' {
  const ratio = threshold !== 0 ? Math.abs(value - threshold) / Math.abs(threshold) : 0
  if (ratio > 0.5) return 'critical'
  if (ratio > 0.2) return 'warning'
  return 'info'
}

export function checkAlerts(metrics: MetricsData): AlertPayload[] {
  const triggered: AlertPayload[] = []
  const now = Date.now()

  for (const alert of DEFAULT_ALERTS) {
    if (!alert.enabled) continue
    const state = alertStates.get(alert.id)
    if (!state) continue
    if (state.lastTriggered !== null && now - state.lastTriggered < alert.cooldownMinutes * 60 * 1000) {
      continue
    }

    let currentValue = metrics[alert.metric] as number
    if (alert.metric === 'mcu_consumed_total' && alert.comparator === 'lt') {
      currentValue = 100 - (metrics.mcu_consumed_total % 100)
    }

    if (checkThreshold(currentValue, alert.threshold, alert.comparator)) {
      triggered.push({
        alertId: alert.id,
        alertName: alert.name,
        currentValue,
        threshold: alert.threshold,
        timestamp: new Date().toISOString(),
        severity: determineSeverity(currentValue, alert.threshold),
        description: alert.description,
      })
      state.lastTriggered = now
      state.triggerCount++
      state.isFiring = true
    } else {
      state.isFiring = false
    }
  }

  return triggered
}

export function createAlertsMiddleware(webhookUrls: string[] = []) {
  return async (c: Context, next: Next) => {
    await next()
    const { getMetrics } = await import('./metrics')
    const triggeredAlerts = checkAlerts(getMetrics())
    if (triggeredAlerts.length > 0 && webhookUrls.length > 0) {
      c.executionCtx.waitUntil(sendAlertsToSlack(webhookUrls, triggeredAlerts))
    }
  }
}

export function getAlertStatus(): Record<string, unknown> {
  const states = getAllAlertStates()
  return {
    alerts: DEFAULT_ALERTS.map((alert) => ({
      ...alert,
      state: states[alert.id] || { lastTriggered: null, triggerCount: 0, isFiring: false },
    })),
  }
}
