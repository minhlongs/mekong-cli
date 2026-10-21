/**
 * Legacy In-Memory Metrics Store & Prometheus Exposition Helpers
 */

export interface Metrics {
  request_count: Record<string, number>
  error_count: Record<string, number>
  latency_ms: number[]
  active_missions: number
  uptime_seconds: number
}

let metricsStore: Metrics = {
  request_count: {},
  error_count: {},
  latency_ms: [],
  active_missions: 0,
  uptime_seconds: 0,
}

const startTime = Date.now()

export function resetMetrics(): void {
  metricsStore = {
    request_count: {},
    error_count: {},
    latency_ms: [],
    active_missions: 0,
    uptime_seconds: 0,
  }
}

export function getMetrics(): Metrics {
  return {
    ...metricsStore,
    uptime_seconds: Math.floor((Date.now() - startTime) / 1000),
  }
}

export function incrementRequestCounter(endpoint: string): void {
  metricsStore.request_count[endpoint] = (metricsStore.request_count[endpoint] || 0) + 1
}

export function incrementErrorCounter(statusCode: string): void {
  metricsStore.error_count[statusCode] = (metricsStore.error_count[statusCode] || 0) + 1
}

export function recordLatency(latencyMs: number): void {
  metricsStore.latency_ms.push(latencyMs)
  if (metricsStore.latency_ms.length > 1000) {
    metricsStore.latency_ms = metricsStore.latency_ms.slice(-1000)
  }
}

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
 * Format metrics as Prometheus exposition format
 * @deprecated Use formatPrometheusMetrics from observability/metrics.ts
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
