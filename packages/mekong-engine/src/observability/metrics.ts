import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'

/**
 * Custom Metrics for RaaS Gateway
 * Tracks commands executed, MCU consumed, active users, error rates
 */

export interface MetricsData {
  // Command execution metrics
  commands_executed: Record<string, number> // per command type
  commands_by_tenant: Record<string, number> // per tenant

  // MCU metrics
  mcu_consumed_total: number
  mcu_by_tenant: Record<string, number>

  // User/session metrics
  active_sessions: number
  active_users_24h: number

  // Error metrics
  error_count_by_type: Record<string, number>
  error_rate: number // percentage

  // Performance metrics
  latency_p50: number
  latency_p95: number
  latency_p99: number
  request_count: number

  // Database metrics
  db_query_count: number
  db_query_latency_avg: number

  // Uptime
  uptime_seconds: number
  timestamp: string
}

/**
 * In-memory metrics store (Cloudflare Workers ephemeral)
 */
let metricsStore: {
  commands_executed: Record<string, number>
  commands_by_tenant: Record<string, number>
  mcu_consumed_total: number
  mcu_by_tenant: Record<string, number>
  active_sessions: Set<string>
  active_users_24h: Set<string>
  error_count_by_type: Record<string, number>
  latencies: number[]
  request_count: number
  db_queries: number[]
  startTime: number
} = {
  commands_executed: {},
  commands_by_tenant: {},
  mcu_consumed_total: 0,
  mcu_by_tenant: {},
  active_sessions: new Set(),
  active_users_24h: new Set(),
  error_count_by_type: {},
  latencies: [],
  request_count: 0,
  db_queries: [],
  startTime: Date.now(),
}

/**
 * Reset all metrics (for testing)
 */
export function resetMetrics(): void {
  metricsStore = {
    commands_executed: {},
    commands_by_tenant: {},
    mcu_consumed_total: 0,
    mcu_by_tenant: {},
    active_sessions: new Set(),
    active_users_24h: new Set(),
    error_count_by_type: {},
    latencies: [],
    request_count: 0,
    db_queries: [],
    startTime: Date.now(),
  }
}

/**
 * Track command execution
 */
export function trackCommand(
  commandType: string,
  tenantId?: string,
  latencyMs?: number
): void {
  metricsStore.commands_executed[commandType] =
    (metricsStore.commands_executed[commandType] || 0) + 1

  if (tenantId) {
    metricsStore.commands_by_tenant[tenantId] =
      (metricsStore.commands_by_tenant[tenantId] || 0) + 1
  }

  metricsStore.request_count++

  if (latencyMs !== undefined) {
    recordLatency(latencyMs)
  }
}

/**
 * Track MCU consumption
 */
export function trackMcuConsumption(
  tenantId: string,
  mcuAmount: number
): void {
  metricsStore.mcu_consumed_total += mcuAmount
  metricsStore.mcu_by_tenant[tenantId] =
    (metricsStore.mcu_by_tenant[tenantId] || 0) + mcuAmount
}

/**
 * Track active session
 */
export function trackSession(sessionId: string, userId?: string): void {
  metricsStore.active_sessions.add(sessionId)
  if (userId) {
    metricsStore.active_users_24h.add(userId)
  }
}

/**
 * Remove session when ended
 */
export function endSession(sessionId: string): void {
  metricsStore.active_sessions.delete(sessionId)
}

/**
 * Track error
 */
export function trackError(
  errorType: string,
  tenantId?: string,
  context?: Record<string, unknown>
): void {
  metricsStore.error_count_by_type[errorType] =
    (metricsStore.error_count_by_type[errorType] || 0) + 1

  // Structured logging for errors
  const logEntry = {
    level: 'error',
    timestamp: new Date().toISOString(),
    error_type: errorType,
    tenant_id: tenantId,
    context,
  }
  console.error(JSON.stringify(logEntry))
}

/**
 * Record latency measurement
 */
export function recordLatency(latencyMs: number): void {
  metricsStore.latencies.push(latencyMs)
  // Keep only last 1000 measurements
  if (metricsStore.latencies.length > 1000) {
    metricsStore.latencies = metricsStore.latencies.slice(-1000)
  }
}

/**
 * Record database query
 */
export function recordDbQuery(latencyMs: number): void {
  metricsStore.db_queries.push(latencyMs)
  if (metricsStore.db_queries.length > 100) {
    metricsStore.db_queries = metricsStore.db_queries.slice(-100)
  }
}

/**
 * Calculate percentile from array
 */
function percentile(arr: number[], p: number): number {
  if (arr.length === 0) return 0
  const sorted = [...arr].sort((a, b) => a - b)
  const index = Math.floor(sorted.length * p)
  return sorted[Math.min(index, sorted.length - 1)] || 0
}

/**
 * Get current metrics snapshot
 */
export function getMetrics(): MetricsData {
  const errorTotal = Object.values(metricsStore.error_count_by_type).reduce(
    (sum, n) => sum + n,
    0
  )

  return {
    commands_executed: { ...metricsStore.commands_executed },
    commands_by_tenant: { ...metricsStore.commands_by_tenant },
    mcu_consumed_total: metricsStore.mcu_consumed_total,
    mcu_by_tenant: { ...metricsStore.mcu_by_tenant },
    active_sessions: metricsStore.active_sessions.size,
    active_users_24h: metricsStore.active_users_24h.size,
    error_count_by_type: { ...metricsStore.error_count_by_type },
    error_rate: metricsStore.request_count > 0
      ? (errorTotal / metricsStore.request_count) * 100
      : 0,
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

/**
 * Format metrics as Prometheus exposition format
 */
export function formatPrometheusMetrics(metrics: MetricsData): string {
  let output = '# HELP mekong_commands_executed_total Total commands executed by type\n'
  output += '# TYPE mekong_commands_executed_total counter\n'
  for (const [cmd, count] of Object.entries(metrics.commands_executed)) {
    output += `mekong_commands_executed_total{command="${cmd}"} ${count}\n`
  }

  output += '\n# HELP mekong_commands_by_tenant_total Commands executed per tenant\n'
  output += '# TYPE mekong_commands_by_tenant_total counter\n'
  for (const [tenant, count] of Object.entries(metrics.commands_by_tenant)) {
    output += `mekong_commands_by_tenant_total{tenant="${tenant}"} ${count}\n`
  }

  output += '\n# HELP mekong_mcu_consumed_total Total MCU consumed\n'
  output += '# TYPE mekong_mcu_consumed_total counter\n'
  output += `mekong_mcu_consumed_total ${metrics.mcu_consumed_total}\n`

  output += '\n# HELP mekong_mcu_by_tenant_total MCU consumed per tenant\n'
  output += '# TYPE mekong_mcu_by_tenant_total counter\n'
  for (const [tenant, mcu] of Object.entries(metrics.mcu_by_tenant)) {
    output += `mekong_mcu_by_tenant_total{tenant="${tenant}"} ${mcu}\n`
  }

  output += '\n# HELP mekong_active_sessions Current active sessions\n'
  output += '# TYPE mekong_active_sessions gauge\n'
  output += `mekong_active_sessions ${metrics.active_sessions}\n`

  output += '\n# HELP mekong_active_users_24h Active users in last 24 hours\n'
  output += '# TYPE mekong_active_users_24h gauge\n'
  output += `mekong_active_users_24h ${metrics.active_users_24h}\n`

  output += '\n# HELP mekong_error_count_total Total errors by type\n'
  output += '# TYPE mekong_error_count_total counter\n'
  for (const [type, count] of Object.entries(metrics.error_count_by_type)) {
    output += `mekong_error_count_total{type="${type}"} ${count}\n`
  }

  output += '\n# HELP mekong_error_rate_percent Current error rate percentage\n'
  output += '# TYPE mekong_error_rate_percent gauge\n'
  output += `mekong_error_rate_percent ${metrics.error_rate.toFixed(2)}\n`

  output += '\n# HELP mekong_latency_p50_ms 50th percentile latency\n'
  output += '# TYPE mekong_latency_p50_ms gauge\n'
  output += `mekong_latency_p50_ms ${metrics.latency_p50.toFixed(2)}\n`

  output += '\n# HELP mekong_latency_p95_ms 95th percentile latency\n'
  output += '# TYPE mekong_latency_p95_ms gauge\n'
  output += `mekong_latency_p95_ms ${metrics.latency_p95.toFixed(2)}\n`

  output += '\n# HELP mekong_latency_p99_ms 99th percentile latency\n'
  output += '# TYPE mekong_latency_p99_ms gauge\n'
  output += `mekong_latency_p99_ms ${metrics.latency_p99.toFixed(2)}\n`

  output += '\n# HELP mekong_db_query_count_total Total database queries\n'
  output += '# TYPE mekong_db_query_count_total counter\n'
  output += `mekong_db_query_count_total ${metrics.db_query_count}\n`

  output += '\n# HELP mekong_db_query_latency_avg_ms Average database query latency\n'
  output += '# TYPE mekong_db_query_latency_avg_ms gauge\n'
  output += `mekong_db_query_latency_avg_ms ${metrics.db_query_latency_avg.toFixed(2)}\n`

  output += '\n# HELP mekong_uptime_seconds Service uptime in seconds\n'
  output += '# TYPE mekong_uptime_seconds counter\n'
  output += `mekong_uptime_seconds ${metrics.uptime_seconds}\n`

  return output
}

/**
 * Middleware factory for metrics collection
 */
export function createMetricsMiddleware() {
  return async (c: any, next: () => Promise<void>) => {
    const startTime = Date.now()
    const path = c.req.path
    const method = c.req.method

    // Skip metrics endpoint
    if (path === '/metrics') {
      await next()
      return
    }

    await next()

    const latency = Date.now() - startTime
    const status = c.res.status

    // Track command/request
    const commandType = `${method}:${path}`
    let tenantId: string | undefined

    try {
      const tenant = c.get('tenant')
      if (tenant && typeof tenant === 'object' && 'id' in tenant) {
        tenantId = (tenant as { id: string }).id
      }
    } catch {
      // Ignore if tenant not set
    }

    trackCommand(commandType, tenantId, latency)

    // Track errors
    if (status >= 400) {
      trackError(`HTTP_${status}`, tenantId, { path, method })
    }
  }
}
