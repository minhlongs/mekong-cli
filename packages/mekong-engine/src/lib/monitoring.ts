import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { createMiddleware } from 'hono/factory'
import {
  type Metrics,
  resetMetrics,
  getMetrics,
  incrementRequestCounter,
  incrementErrorCounter,
  recordLatency,
  getLatencyPercentiles,
  formatPrometheusMetrics,
} from './monitoring-metrics'

export type { Metrics }
export {
  resetMetrics,
  getMetrics,
  incrementRequestCounter,
  incrementErrorCounter,
  recordLatency,
  getLatencyPercentiles,
  formatPrometheusMetrics,
}

type Variables = { tenant: Tenant }

/**
 * Logger utility - structured logging without console.* pollution
 */
export const logger = {
  error: (message: string, context?: Record<string, unknown>) => {
    const logEntry = {
      level: 'error',
      timestamp: new Date().toISOString(),
      message,
      ...context,
    }
    console.error(JSON.stringify(logEntry))
  },
  warn: (message: string, context?: Record<string, unknown>) => {
    const logEntry = {
      level: 'warn',
      timestamp: new Date().toISOString(),
      message,
      ...context,
    }
    console.warn(JSON.stringify(logEntry))
  },
  info: (message: string, context?: Record<string, unknown>) => {
    const logEntry = {
      level: 'info',
      timestamp: new Date().toISOString(),
      message,
      ...context,
    }
    console.log(JSON.stringify(logEntry))
  },
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

    let tenantId = 'anonymous'
    try {
      const maybeTenant = c.get('tenant')
      if (maybeTenant && typeof maybeTenant === 'object' && 'id' in maybeTenant) {
        tenantId = (maybeTenant as { id: string }).id
      }
    } catch {
      // Ignore if tenant not set
    }

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

    if (status >= 500) {
      logger.error('REQUEST_ERROR', logEntry)
    } else if (status >= 400) {
      logger.warn('REQUEST_CLIENT_ERROR', logEntry)
    } else {
      logger.info('REQUEST', logEntry)
    }
  }
)

/**
 * Middleware: Metrics collection
 */
export const metricsMiddleware = createMiddleware<{ Bindings: Bindings }>(
  async (c, next) => {
    const path = c.req.path

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
  }
)

// Re-export from observability module for convenience
export type { MetricsData } from '../observability/metrics'
export {
  trackCommand,
  trackMcuConsumption,
  trackSession,
  endSession,
  trackError,
  recordLatency as recordObservabilityLatency,
  recordDbQuery,
  getMetrics as getObservabilityMetrics,
  formatPrometheusMetrics as formatObservabilityMetrics,
  createMetricsMiddleware as createObservabilityMetricsMiddleware,
} from '../observability/metrics'
export {
  checkAlerts,
  sendSlackAlert,
  sendAlertsToSlack,
  getAlertStatus,
  initAlerts,
  createAlertsMiddleware,
} from '../observability/alerts'
