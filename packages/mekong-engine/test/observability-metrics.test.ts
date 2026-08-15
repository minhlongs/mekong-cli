import { describe, it, expect, beforeEach } from 'vitest'
import {
  resetMetrics,
  getMetrics,
  trackCommand,
  trackMcuConsumption,
  trackSession,
  endSession,
  trackError,
  recordLatency,
  recordDbQuery,
  formatPrometheusMetrics,
} from '../src/observability/metrics'

describe('Observability Metrics', () => {
  beforeEach(() => {
    resetMetrics()
  })

  describe('trackCommand', () => {
    it('tracks command execution by type', () => {
      trackCommand('/cook')
      trackCommand('/cook')
      trackCommand('/plan')

      const metrics = getMetrics()
      expect(metrics.commands_executed['/cook']).toBe(2)
      expect(metrics.commands_executed['/plan']).toBe(1)
    })

    it('tracks commands by tenant', () => {
      trackCommand('/cook', 'tenant-1')
      trackCommand('/cook', 'tenant-2')
      trackCommand('/cook', 'tenant-1')

      const metrics = getMetrics()
      expect(metrics.commands_by_tenant['tenant-1']).toBe(2)
      expect(metrics.commands_by_tenant['tenant-2']).toBe(1)
    })

    it('records latency when provided', () => {
      trackCommand('/cook', 'tenant-1', 150)
      trackCommand('/cook', 'tenant-1', 200)

      const metrics = getMetrics()
      expect(metrics.latency_p50).toBeGreaterThan(0)
      expect(metrics.request_count).toBe(2)
    })
  })

  describe('trackMcuConsumption', () => {
    it('tracks MCU consumption total', () => {
      trackMcuConsumption('tenant-1', 100)
      trackMcuConsumption('tenant-2', 50)
      trackMcuConsumption('tenant-1', 25)

      const metrics = getMetrics()
      expect(metrics.mcu_consumed_total).toBe(175)
      expect(metrics.mcu_by_tenant['tenant-1']).toBe(125)
      expect(metrics.mcu_by_tenant['tenant-2']).toBe(50)
    })
  })

  describe('trackSession', () => {
    it('tracks active sessions', () => {
      trackSession('session-1', 'user-1')
      trackSession('session-2', 'user-2')
      trackSession('session-3', 'user-1')

      const metrics = getMetrics()
      expect(metrics.active_sessions).toBe(3)
      expect(metrics.active_users_24h).toBe(2) // user-1 counted once
    })

    it('removes ended sessions', () => {
      trackSession('session-1', 'user-1')
      trackSession('session-2', 'user-2')
      endSession('session-1')

      const metrics = getMetrics()
      expect(metrics.active_sessions).toBe(1)
      expect(metrics.active_users_24h).toBe(2) // user-1 still in 24h window
    })
  })

  describe('trackError', () => {
    it('tracks errors by type', () => {
      trackError('VALIDATION_ERROR', 'tenant-1')
      trackError('DATABASE_ERROR', 'tenant-1')
      trackError('VALIDATION_ERROR', 'tenant-2')

      const metrics = getMetrics()
      expect(metrics.error_count_by_type['VALIDATION_ERROR']).toBe(2)
      expect(metrics.error_count_by_type['DATABASE_ERROR']).toBe(1)
    })

    it('calculates error rate', () => {
      trackCommand('/cook', 'tenant-1')
      trackCommand('/plan', 'tenant-1')
      trackCommand('/fix', 'tenant-1')
      trackError('ERROR_400', 'tenant-1')
      trackError('ERROR_500', 'tenant-1')

      const metrics = getMetrics()
      // 2 errors / 3 requests * 100 = 66.67%
      expect(metrics.error_rate).toBeCloseTo(66.67, 1)
    })
  })

  describe('recordLatency', () => {
    it('records and calculates percentiles', () => {
      // Record 100 latency measurements (1 to 100)
      for (let i = 1; i <= 100; i++) {
        recordLatency(i)
      }

      const metrics = getMetrics()
      // p50 of [1..100] = 50th value = 50 or 51 depending on calculation
      // p95 of [1..100] = 95th value = 95 or 96
      // p99 of [1..100] = 99th value = 99 or 100
      expect(metrics.latency_p50).toBeGreaterThanOrEqual(50)
      expect(metrics.latency_p50).toBeLessThanOrEqual(51)
      expect(metrics.latency_p95).toBeGreaterThanOrEqual(95)
      expect(metrics.latency_p95).toBeLessThanOrEqual(96)
      expect(metrics.latency_p99).toBeGreaterThanOrEqual(99)
      expect(metrics.latency_p99).toBeLessThanOrEqual(100)
    })

    it('keeps only last 1000 measurements', () => {
      // Record 1500 measurements
      for (let i = 0; i < 1500; i++) {
        recordLatency(100)
      }

      const metrics = getMetrics()
      // Should not throw and should have reasonable percentiles
      expect(metrics.latency_p50).toBe(100)
    })
  })

  describe('recordDbQuery', () => {
    it('records database query latency', () => {
      recordDbQuery(10)
      recordDbQuery(20)
      recordDbQuery(30)

      const metrics = getMetrics()
      expect(metrics.db_query_count).toBe(3)
      expect(metrics.db_query_latency_avg).toBe(20)
    })

    it('keeps only last 100 queries', () => {
      for (let i = 0; i < 150; i++) {
        recordDbQuery(50)
      }

      const metrics = getMetrics()
      expect(metrics.db_query_count).toBeLessThanOrEqual(100)
    })
  })

  describe('formatPrometheusMetrics', () => {
    it('formats metrics as Prometheus exposition format', () => {
      trackCommand('/cook', 'tenant-1', 100)
      trackCommand('/plan', 'tenant-1', 200)
      trackMcuConsumption('tenant-1', 50)
      trackError('VALIDATION_ERROR', 'tenant-1')

      const metrics = getMetrics()
      const output = formatPrometheusMetrics(metrics)

      expect(output).toContain('# HELP mekong_commands_executed_total')
      expect(output).toContain('# TYPE mekong_commands_executed_total counter')
      expect(output).toContain('mekong_commands_executed_total{command="/cook"}')
      expect(output).toContain('mekong_mcu_consumed_total 50')
      expect(output).toContain('mekong_error_count_total{type="VALIDATION_ERROR"} 1')
      expect(output).toContain('mekong_latency_p50_ms')
      expect(output).toContain('mekong_latency_p95_ms')
      expect(output).toContain('mekong_latency_p99_ms')
      expect(output).toContain('mekong_uptime_seconds')
    })
  })

  describe('getMetrics', () => {
    it('returns complete metrics snapshot', () => {
      trackCommand('/cook', 'tenant-1', 100)
      trackSession('session-1', 'user-1')
      trackError('TEST_ERROR', 'tenant-1')

      const metrics = getMetrics()

      expect(metrics).toHaveProperty('commands_executed')
      expect(metrics).toHaveProperty('commands_by_tenant')
      expect(metrics).toHaveProperty('mcu_consumed_total')
      expect(metrics).toHaveProperty('mcu_by_tenant')
      expect(metrics).toHaveProperty('active_sessions')
      expect(metrics).toHaveProperty('active_users_24h')
      expect(metrics).toHaveProperty('error_count_by_type')
      expect(metrics).toHaveProperty('error_rate')
      expect(metrics).toHaveProperty('latency_p50')
      expect(metrics).toHaveProperty('latency_p95')
      expect(metrics).toHaveProperty('latency_p99')
      expect(metrics).toHaveProperty('request_count')
      expect(metrics).toHaveProperty('db_query_count')
      expect(metrics).toHaveProperty('db_query_latency_avg')
      expect(metrics).toHaveProperty('uptime_seconds')
      expect(metrics).toHaveProperty('timestamp')
    })
  })
})
