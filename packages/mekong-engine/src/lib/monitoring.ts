import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { createMiddleware } from 'hono/factory'

type Variables = { tenant: Tenant }

/**
 * Metrics data structure for Prometheus exposition
 */
export interface Metrics {
  request_count: Record<string, number>
  error_count: Record<string, number>
  latency_ms: number[]
  active_missions: number
  uptime_seconds: number
}

/**
 * In-memory metrics store (Cloudflare Workers ephemeral)
 */
let metricsStore: Metrics = {
  request_count: {},
  error_count: {},
  latency_ms: [],
  active_missions: 0,
  uptime_seconds: 0,
}

const startTime = Date.now()

/**
 * Reset metrics (for testing or manual trigger)
 */
export function resetMetrics(): void {
  metricsStore = {
    request_count: {},
    error_count: {},
    latency_ms: [],
    active_missions: 0,
    uptime_seconds: 0,
  }
}

/**
 * Get current metrics snapshot
 */
export function getMetrics(): Metrics {
  return {
    ...metricsStore,
    uptime_seconds: Math.floor((Date.now() - startTime) / 1000),
  }
}

/**
 * Increment request counter by endpoint
 */
export function incrementRequestCounter(endpoint: string): void {
  metricsStore.request_count[endpoint] = (metricsStore.request_count[endpoint] || 0) + 1
}

/**
 * Increment error counter by status code
 */
export function incrementErrorCounter(statusCode: string): void {
  metricsStore.error_count[statusCode] = (metricsStore.error_count[statusCode] || 0) + 1
}

/**
 * Record latency measurement
 */
export function recordLatency(latencyMs: number): void {
  metricsStore.latency_ms.push(latencyMs)
  // Keep only last 1000 measurements to prevent memory bloat
  if (metricsStore.latency_ms.length > 1000) {
    metricsStore.latency_ms = metricsStore.latency_ms.slice(-1000)
  }
}

/**
 * Calculate latency percentiles
 */
export function getLatencyPercentiles(): { p50: number; p95: number; p99: number } {
  const sorted = [...metricsStore.latency_ms].sort((a, b) => a - b)
  const len = sorted.length
  if (len === 0) return { p50: 0, p95: 0, p99: 0 }

  return {
    p50: sorted[Math.floor(len * 0.50)] || 0,
    p95: sorted[Math.floor(len * 0.95)] || 0,
    p99: sorted[Math.floor(len * 0.99)] || 0,
  }
}

/**
 * Middleware: Request logging with structured JSON
 */
export const requestLoggingMiddleware = createMiddleware<{ Bindings: Bindings; Variables: Variables }>(
  async (c, next) => {
    const startTime = Date.now()
    const method = c.req.method
    const path = c.req.path

    await next()

    const latency = Date.now() - startTime
    const status = c.res.status

    // Get tenant ID safely
    let tenantId = 'anonymous'
    try {
      const maybeTenant = c.get('tenant')
      if (maybeTenant && typeof maybeTenant === 'object' && 'id' in maybeTenant) {
        tenantId = (maybeTenant as { id: string }).id
      }
    } catch {
      // Ignore if tenant not set
    }

    // Structured JSON log (Cloudflare Logpush compatible)
    const logEntry = {
      timestamp: new Date().toISOString(),
      method,
      path,
      status,
      latency_ms: latency,
      tenant_id: tenantId,
      user_agent: c.req.header('user-agent') || '',
      ip: c.req.header('x-forwarded-for') || c.req.header('cf-connecting-ip') || '',
    }

    // Log to console (Cloudflare Workers will capture this)
    if (status >= 500) {
      console.error('REQUEST_ERROR', JSON.stringify(logEntry))
    } else if (status >= 400) {
      console.warn('REQUEST_CLIENT_ERROR', JSON.stringify(logEntry))
    } else {
      console.log('REQUEST', JSON.stringify(logEntry))
    }
  },
)

/**
 * Middleware: Metrics collection
 */
export const metricsMiddleware = createMiddleware<{ Bindings: Bindings }>(
  async (c, next) => {
    const path = c.req.path

    // Skip metrics endpoint itself
    if (path === '/metrics') {
      await next()
      return
    }

    incrementRequestCounter(path)
    await next()

    const status = c.res.status
    if (status >= 400) {
      incrementErrorCounter(String(status))
    }
  },
)

/**
 * Format metrics as Prometheus exposition format
 */
export function formatPrometheusMetrics(metrics: Metrics): string {
  const { p50, p95, p99 } = getLatencyPercentiles()

  let output = '# HELP mekong_request_count_total Total number of requests\n'
  output += '# TYPE mekong_request_count_total counter\n'
  for (const [endpoint, count] of Object.entries(metrics.request_count)) {
    output += `mekong_request_count_total{endpoint="${endpoint}"} ${count}\n`
  }

  output += '\n# HELP mekong_error_count_total Total number of errors by status code\n'
  output += '# TYPE mekong_error_count_total counter\n'
  for (const [status, count] of Object.entries(metrics.error_count)) {
    output += `mekong_error_count_total{status="${status}"} ${count}\n`
  }

  output += '\n# HELP mekong_latency_ms Request latency in milliseconds\n'
  output += '# TYPE mekong_latency_ms gauge\n'
  output += `mekong_latency_ms_p50 ${p50}\n`
  output += `mekong_latency_ms_p95 ${p95}\n`
  output += `mekong_latency_ms_p99 ${p99}\n`

  output += '\n# HELP mekong_uptime_seconds Service uptime in seconds\n'
  output += '# TYPE mekong_uptime_seconds counter\n'
  output += `mekong_uptime_seconds ${metrics.uptime_seconds}\n`

  return output
}
