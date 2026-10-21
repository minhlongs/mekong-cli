/**
 * Slack Alert Formatting & Webhook Dispatch
 */

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
 * Format Slack message for alert
 */
export function formatSlackMessage(alert: AlertPayload): Record<string, unknown> {
  const colorMap = {
    info: '#36a64f',
    warning: '#ff9800',
    critical: '#ff0000',
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
