import type { MetricsData } from './metrics'

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
  cooldownMinutes: number // Prevent alert spam
}

export interface AlertState {
  lastTriggered: number | null
  triggerCount: number
  isFiring: boolean
}

export interface AlertPayload {
  alertId: string
  alertName: string
  currentValue: number
  threshold: number
  timestamp: string
  severity: 'info' | 'warning' | 'critical'
  description: string
}

/**
 * Default alert configurations
 */
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
    metric: 'mcu_consumed_total', // Will be checked as percentage
    enabled: true,
    cooldownMinutes: 60,
  },
  {
    id: 'uptime_low',
    name: 'Service Uptime Degraded',
    description: 'Service may be experiencing downtime',
    threshold: 99.9,
    comparator: 'lt',
    metric: 'uptime_seconds', // Will be calculated as uptime percentage
    enabled: true,
    cooldownMinutes: 1,
  },
]

/**
 * Alert states store
 */
const alertStates: Map<string, AlertState> = new Map()

/**
 * Initialize alert states
 */
export function initAlerts(): void {
  for (const alert of DEFAULT_ALERTS) {
    alertStates.set(alert.id, {
      lastTriggered: null,
      triggerCount: 0,
      isFiring: false,
    })
  }
}

/**
 * Get alert state
 */
export function getAlertState(alertId: string): AlertState | undefined {
  return alertStates.get(alertId)
}

/**
 * Get all alert states
 */
export function getAllAlertStates(): Record<string, AlertState> {
  const result: Record<string, AlertState> = {}
  for (const [id, state] of alertStates.entries()) {
    result[id] = { ...state }
  }
  return result
}

/**
 * Check if value meets threshold condition
 */
export function checkThreshold(
  value: number,
  threshold: number,
  comparator: 'gt' | 'lt' | 'gte' | 'lte' | 'eq'
): boolean {
  switch (comparator) {
    case 'gt':
      return value > threshold
    case 'lt':
      return value < threshold
    case 'gte':
      return value >= threshold
    case 'lte':
      return value <= threshold
    case 'eq':
      return value === threshold
  }
}

/**
 * Determine alert severity based on how much threshold is exceeded
 */
function determineSeverity(
  value: number,
  threshold: number,
  comparator: 'gt' | 'lt' | 'gte' | 'lte' | 'eq'
): 'info' | 'warning' | 'critical' {
  const ratio = threshold !== 0 ? Math.abs(value - threshold) / Math.abs(threshold) : 0

  if (ratio > 0.5) return 'critical'
  if (ratio > 0.2) return 'warning'
  return 'info'
}

/**
 * Check alerts against current metrics
 * Returns array of triggered alerts
 */
export function checkAlerts(metrics: MetricsData): AlertPayload[] {
  const triggered: AlertPayload[] = []
  const now = Date.now()

  for (const alert of DEFAULT_ALERTS) {
    if (!alert.enabled) continue

    const state = alertStates.get(alert.id)
    if (!state) continue

    // Check cooldown
    if (
      state.lastTriggered !== null &&
      now - state.lastTriggered < alert.cooldownMinutes * 60 * 1000
    ) {
      continue
    }

    // Get current metric value
    let currentValue = metrics[alert.metric] as number

    // Special handling for MCU balance (check as percentage of limit)
    if (alert.metric === 'mcu_consumed_total' && alert.comparator === 'lt') {
      // For MCU balance, we check if remaining is below threshold
      // This is a simplified check - actual implementation would check tenant balances
      currentValue = 100 - (metrics.mcu_consumed_total % 100) // Mock percentage
    }

    // Check threshold
    if (checkThreshold(currentValue, alert.threshold, alert.comparator)) {
      const severity = determineSeverity(currentValue, alert.threshold, alert.comparator)

      triggered.push({
        alertId: alert.id,
        alertName: alert.name,
        currentValue,
        threshold: alert.threshold,
        timestamp: new Date().toISOString(),
        severity,
        description: alert.description,
      })

      // Update state
      state.lastTriggered = now
      state.triggerCount++
      state.isFiring = true
    } else {
      state.isFiring = false
    }
  }

  return triggered
}

/**
 * Format Slack message for alert
 */
export function formatSlackMessage(alert: AlertPayload): Record<string, unknown> {
  const colorMap = {
    info: '#36a64f', // green
    warning: '#ff9800', // orange
    critical: '#ff0000', // red
  }

  const emojiMap = {
    info: ':information_source:',
    warning: ':warning:',
    critical: ':rotating_light:',
  }

  return {
    attachments: [
      {
        color: colorMap[alert.severity],
        fallback: `[${alert.severity.toUpperCase()}] ${alert.alertName}: ${alert.description}`,
        pretext: `${emojiMap[alert.severity]} *Alert Triggered*`,
        title: alert.alertName,
        text: alert.description,
        fields: [
          {
            title: 'Alert ID',
            value: alert.alertId,
            short: true,
          },
          {
            title: 'Severity',
            value: alert.severity.toUpperCase(),
            short: true,
          },
          {
            title: 'Current Value',
            value: String(alert.currentValue),
            short: true,
          },
          {
            title: 'Threshold',
            value: String(alert.threshold),
            short: true,
          },
          {
            title: 'Timestamp',
            value: alert.timestamp,
            short: false,
          },
        ],
        footer: 'Mekong Engine RaaS Gateway',
        ts: Math.floor(new Date(alert.timestamp).getTime() / 1000),
      },
    ],
  }
}

/**
 * Send alert to Slack webhook
 */
export async function sendSlackAlert(
  webhookUrl: string,
  alert: AlertPayload
): Promise<boolean> {
  try {
    const payload = formatSlackMessage(alert)

    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      console.error(`Slack webhook failed: ${response.status} ${response.statusText}`)
      return false
    }

    console.log(`Slack alert sent: ${alert.alertId}`)
    return true
  } catch (error) {
    console.error(`Failed to send Slack alert: ${error}`)
    return false
  }
}

/**
 * Send alerts to multiple Slack webhooks
 */
export async function sendAlertsToSlack(
  webhookUrls: string[],
  alerts: AlertPayload[]
): Promise<void> {
  if (alerts.length === 0) return

  const promises = webhookUrls.flatMap((url) =>
    alerts.map((alert) => sendSlackAlert(url, alert))
  )

  await Promise.all(promises)
}

/**
 * Middleware factory for alert checking
 */
export function createAlertsMiddleware(
  webhookUrls: string[] = []
) {
  return async (c: any, next: () => Promise<void>) => {
    await next()

    // Only check alerts on main thread, not for every request
    const { getMetrics } = await import('./metrics')
    const metrics = getMetrics()
    const triggeredAlerts = checkAlerts(metrics)

    if (triggeredAlerts.length > 0 && webhookUrls.length > 0) {
      // Send alerts asynchronously (don't block response)
      c.executionCtx.waitUntil(sendAlertsToSlack(webhookUrls, triggeredAlerts))
    }
  }
}

/**
 * Get alert status endpoint response
 */
export function getAlertStatus(): Record<string, unknown> {
  const states = getAllAlertStates()

  return {
    alerts: DEFAULT_ALERTS.map((alert) => ({
      ...alert,
      state: states[alert.id] || {
        lastTriggered: null,
        triggerCount: 0,
        isFiring: false,
      },
    })),
  }
}
