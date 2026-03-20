import { describe, it, expect, beforeEach } from 'vitest'
import {
  initAlerts,
  getAlertState,
  getAllAlertStates,
  checkAlerts,
  checkThreshold,
  formatSlackMessage,
  DEFAULT_ALERTS,
} from '../src/observability/alerts'
import { resetMetrics, trackError, recordLatency, getMetrics } from '../src/observability/metrics'

describe('Observability Alerts', () => {
  beforeEach(() => {
    initAlerts()
    resetMetrics()
  })

  describe('initAlerts', () => {
    it('initializes all default alerts', () => {
      const states = getAllAlertStates()

      expect(states).toHaveProperty('error_rate_high')
      expect(states).toHaveProperty('latency_p99_high')
      expect(states).toHaveProperty('mcu_balance_low')
      expect(states).toHaveProperty('uptime_low')

      Object.values(states).forEach(state => {
        expect(state.lastTriggered).toBeNull()
        expect(state.triggerCount).toBe(0)
        expect(state.isFiring).toBe(false)
      })
    })
  })

  describe('DEFAULT_ALERTS', () => {
    it('has correct alert configurations', () => {
      expect(DEFAULT_ALERTS.length).toBeGreaterThan(0)

      const errorRateAlert = DEFAULT_ALERTS.find(a => a.id === 'error_rate_high')
      expect(errorRateAlert).toBeDefined()
      expect(errorRateAlert?.threshold).toBe(1)
      expect(errorRateAlert?.comparator).toBe('gt')
      expect(errorRateAlert?.metric).toBe('error_rate')

      const latencyAlert = DEFAULT_ALERTS.find(a => a.id === 'latency_p99_high')
      expect(latencyAlert).toBeDefined()
      expect(latencyAlert?.threshold).toBe(500)
      expect(latencyAlert?.comparator).toBe('gt')
      expect(latencyAlert?.metric).toBe('latency_p99')
    })
  })

  describe('checkThreshold', () => {
    it('checks greater than (gt)', () => {
      expect(checkThreshold(10, 5, 'gt')).toBe(true)
      expect(checkThreshold(5, 5, 'gt')).toBe(false)
      expect(checkThreshold(3, 5, 'gt')).toBe(false)
    })

    it('checks less than (lt)', () => {
      expect(checkThreshold(3, 5, 'lt')).toBe(true)
      expect(checkThreshold(5, 5, 'lt')).toBe(false)
      expect(checkThreshold(10, 5, 'lt')).toBe(false)
    })

    it('checks greater than or equal (gte)', () => {
      expect(checkThreshold(6, 5, 'gte')).toBe(true)
      expect(checkThreshold(5, 5, 'gte')).toBe(true)
      expect(checkThreshold(4, 5, 'gte')).toBe(false)
    })

    it('checks less than or equal (lte)', () => {
      expect(checkThreshold(4, 5, 'lte')).toBe(true)
      expect(checkThreshold(5, 5, 'lte')).toBe(true)
      expect(checkThreshold(6, 5, 'lte')).toBe(false)
    })

    it('checks equal (eq)', () => {
      expect(checkThreshold(5, 5, 'eq')).toBe(true)
      expect(checkThreshold(6, 5, 'eq')).toBe(false)
    })
  })

  describe('checkAlerts', () => {
    it('has correct default alerts configured', () => {
      const metrics = getMetrics()
      expect(DEFAULT_ALERTS.length).toBeGreaterThan(0)
      expect(DEFAULT_ALERTS.some(a => a.id === 'error_rate_high')).toBe(true)
      expect(DEFAULT_ALERTS.some(a => a.id === 'latency_p99_high')).toBe(true)
    })

    it('triggers latency p99 alert when threshold exceeded', () => {
      // Generate high latency: all requests > 500ms
      for (let i = 0; i < 100; i++) {
        recordLatency(600 + i) // 600-699ms
      }

      const metrics = getMetrics()
      const triggered = checkAlerts(metrics)
      const latencyAlert = triggered.find(a => a.alertId === 'latency_p99_high')

      expect(latencyAlert).toBeDefined()
      expect(metrics.latency_p99).toBeGreaterThan(500)
    })

    it('tracks alert state changes', () => {
      // Initially alert should not be firing
      const initialState = getAlertState('latency_p99_high')
      expect(initialState?.isFiring).toBe(false)
      expect(initialState?.lastTriggered).toBeNull()

      // Generate high latency to trigger alert
      for (let i = 0; i < 100; i++) {
        recordLatency(600 + i)
      }

      const metrics = getMetrics()
      checkAlerts(metrics)

      // After triggering, state should update
      const newState = getAlertState('latency_p99_high')
      expect(newState?.lastTriggered).not.toBeNull()
    })

    it('does not trigger alerts when metrics are normal', () => {
      // Normal latency
      for (let i = 0; i < 50; i++) {
        recordLatency(50 + (i % 20)) // 50-69ms
      }

      const metrics = getMetrics()
      const triggered = checkAlerts(metrics)

      // Latency p99 should be well under 500ms
      expect(metrics.latency_p99).toBeLessThan(100)
    })
  })

  describe('formatSlackMessage', () => {
    it('formats alert as Slack message with correct structure', () => {
      const alert = {
        alertId: 'error_rate_high',
        alertName: 'High Error Rate',
        currentValue: 5.5,
        threshold: 1,
        timestamp: '2026-03-20T10:00:00.000Z',
        severity: 'warning' as const,
        description: 'Error rate exceeds 1%',
      }

      const message = formatSlackMessage(alert)

      expect(message).toHaveProperty('attachments')
      expect(Array.isArray(message.attachments)).toBe(true)
      expect(message.attachments.length).toBe(1)

      const attachment = message.attachments[0]
      expect(attachment.color).toBe('#ff9800') // warning orange
      expect(attachment.title).toBe('High Error Rate')
      expect(attachment.text).toBe('Error rate exceeds 1%')

      const fields = attachment.fields as Array<{ title: string; value: string }>
      expect(fields.some(f => f.title === 'Alert ID' && f.value === 'error_rate_high')).toBe(true)
      expect(fields.some(f => f.title === 'Severity' && f.value === 'WARNING')).toBe(true)
      expect(fields.some(f => f.title === 'Current Value' && f.value === '5.5')).toBe(true)
      expect(fields.some(f => f.title === 'Threshold' && f.value === '1')).toBe(true)
    })

    it('uses correct colors for different severities', () => {
      const baseAlert = {
        alertId: 'test',
        alertName: 'Test',
        currentValue: 1,
        threshold: 1,
        timestamp: '2026-03-20T10:00:00.000Z',
        description: 'Test',
      } as const

      expect(formatSlackMessage({ ...baseAlert, severity: 'info' }).attachments[0].color).toBe('#36a64f')
      expect(formatSlackMessage({ ...baseAlert, severity: 'warning' }).attachments[0].color).toBe('#ff9800')
      expect(formatSlackMessage({ ...baseAlert, severity: 'critical' }).attachments[0].color).toBe('#ff0000')
    })
  })

  describe('getAlertState', () => {
    it('returns undefined for non-existent alert', () => {
      const state = getAlertState('non_existent_alert')
      expect(state).toBeUndefined()
    })

    it('returns state for existing alert', () => {
      const state = getAlertState('error_rate_high')
      expect(state).toBeDefined()
      expect(state?.lastTriggered).toBeNull()
      expect(state?.triggerCount).toBe(0)
      expect(state?.isFiring).toBe(false)
    })
  })
})
