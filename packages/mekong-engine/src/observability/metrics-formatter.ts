/**
 * Prometheus Exposition Formatter for RaaS Gateway Metrics
 */

import type { MetricsData } from './metrics'

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
