import type { Context, Next } from 'hono'
import { formatPrometheusMetrics } from './metrics-formatter'

export { formatPrometheusMetrics }

/**
 * Custom Metrics for RaaS Gateway
 * Tracks commands executed, MCU consumed, active users, error rates
 */
export interface MetricsData {
  commands_executed: Record<string, number>
  commands_by_tenant: Record<string, number>
  mcu_consumed_total: number
  mcu_by_tenant: Record<string, number>
  active_sessions: number
  active_users_24h: number
  error_count_by_type: Record<string, number>
  error_rate: number
  latency_p50: number
  latency_p95: number
  latency_p99: number
  request_count: number
  db_query_count: number
  db_query_latency_avg: number
  uptime_seconds: number
  timestamp: string
}

function createInitialStore() {
  return {
    commands_executed: {} as Record<string, number>,
    commands_by_tenant: {} as Record<string, number>,
    mcu_consumed_total: 0,
    mcu_by_tenant: {} as Record<string, number>,
    active_sessions: new Set<string>(),
    active_users_24h: new Set<string>(),
    error_count_by_type: {} as Record<string, number>,
    latencies: [] as number[],
    request_count: 0,
    db_queries: [] as number[],
    startTime: Date.now(),
  }
}

let metricsStore = createInitialStore()

export function resetMetrics(): void {
  metricsStore = createInitialStore()
}

export function trackCommand(
  commandType: string,
  tenantId?: string,
  latencyMs?: number
): void {
  metricsStore.commands_executed[commandType] = (metricsStore.commands_executed[commandType] || 0) + 1
  if (tenantId) {
    metricsStore.commands_by_tenant[tenantId] = (metricsStore.commands_by_tenant[tenantId] || 0) + 1
  }
  metricsStore.request_count++
  if (latencyMs !== undefined) {
    recordLatency(latencyMs)
  }
}

export function trackMcuConsumption(tenantId: string, mcuAmount: number): void {
  metricsStore.mcu_consumed_total += mcuAmount
  metricsStore.mcu_by_tenant[tenantId] = (metricsStore.mcu_by_tenant[tenantId] || 0) + mcuAmount
}

export function trackSession(sessionId: string, userId?: string): void {
  metricsStore.active_sessions.add(sessionId)
  if (userId) metricsStore.active_users_24h.add(userId)
}

export function endSession(sessionId: string): void {
  metricsStore.active_sessions.delete(sessionId)
}

export function trackError(
  errorType: string,
  tenantId?: string,
  context?: Record<string, unknown>
): void {
  metricsStore.error_count_by_type[errorType] = (metricsStore.error_count_by_type[errorType] || 0) + 1
  console.error(JSON.stringify({
    level: 'error',
    timestamp: new Date().toISOString(),
    error_type: errorType,
    tenant_id: tenantId,
    context,
  }))
}

export function recordLatency(latencyMs: number): void {
  metricsStore.latencies.push(latencyMs)
  if (metricsStore.latencies.length > 1000) {
    metricsStore.latencies = metricsStore.latencies.slice(-1000)
  }
}

export function recordDbQuery(latencyMs: number): void {
  metricsStore.db_queries.push(latencyMs)
  if (metricsStore.db_queries.length > 100) {
    metricsStore.db_queries = metricsStore.db_queries.slice(-100)
  }
}

function percentile(arr: number[], p: number): number {
  if (arr.length === 0) return 0
  const sorted = [...arr].sort((a, b) => a - b)
  const index = Math.floor(sorted.length * p)
  return sorted[Math.min(index, sorted.length - 1)] || 0
}

export function getMetrics(): MetricsData {
  const errorTotal = Object.values(metricsStore.error_count_by_type).reduce((sum, n) => sum + n, 0)
  return {
    commands_executed: { ...metricsStore.commands_executed },
    commands_by_tenant: { ...metricsStore.commands_by_tenant },
    mcu_consumed_total: metricsStore.mcu_consumed_total,
    mcu_by_tenant: { ...metricsStore.mcu_by_tenant },
    active_sessions: metricsStore.active_sessions.size,
    active_users_24h: metricsStore.active_users_24h.size,
    error_count_by_type: { ...metricsStore.error_count_by_type },
    error_rate: metricsStore.request_count > 0 ? (errorTotal / metricsStore.request_count) * 100 : 0,
    latency_p50: percentile(metricsStore.latencies, 0.50),
    latency_p95: percentile(metricsStore.latencies, 0.95),
    latency_p99: percentile(metricsStore.latencies, 0.99),
    request_count: metricsStore.request_count,
    db_query_count: metricsStore.db_queries.length,
    db_query_latency_avg: metricsStore.db_queries.length > 0
      ? metricsStore.db_queries.reduce((a, b) => a + b, 0) / metricsStore.db_queries.length
      : 0,
    uptime_seconds: Math.floor((Date.now() - metricsStore.startTime) / 1000),
    timestamp: new Date().toISOString(),
  }
}

export function createMetricsMiddleware() {
  return async (c: Context, next: Next) => {
    const startTime = Date.now()
    const path = c.req.path
    const method = c.req.method
    if (path === '/metrics') {
      await next()
      return
    }
    await next()
    const latency = Date.now() - startTime
    const status = c.res.status
    let tenantId: string | undefined
    try {
      const tenant = c.get('tenant')
      if (tenant && typeof tenant === 'object' && 'id' in tenant) {
        tenantId = (tenant as { id: string }).id
      }
    } catch {
      // Ignore if tenant not set
    }
    trackCommand(`${method}:${path}`, tenantId, latency)
    if (status >= 400) {
      trackError(`HTTP_${status}`, tenantId, { path, method })
    }
  }
}
