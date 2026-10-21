/**
 * Centralized Security Logging Framework
 * Structured logging with security events and audit trails
 */

import {
  defaultConfig,
  type LogEntry,
  LogEntrySchema,
  type LogLevel,
  LogLevelEnum,
  type SecurityEvent,
  SecurityEventEnum,
  type SecurityLoggerConfig,
} from './logger-types'
import { DataSanitizer, dispatchLogEntry } from './logger-transports'

export class SecurityLogger {
  private config: SecurityLoggerConfig
  private sanitizer: DataSanitizer
  private logBuffer: LogEntry[] = []
  private flushTimer: NodeJS.Timeout | null = null

  constructor(config: Partial<SecurityLoggerConfig> = {}) {
    this.config = { ...defaultConfig, ...config }
    this.sanitizer = new DataSanitizer(this.config.sanitizeFields)
    if (this.config.enableFileOutput || this.config.enableRemoteLogging) {
      this.startFlushTimer()
    }
  }

  private generateId(): string {
    return `log_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  private shouldLog(level: LogLevel): boolean {
    const levels: LogLevel[] = ['debug', 'info', 'warn', 'error', 'critical']
    return levels.indexOf(level) >= levels.indexOf(this.config.level)
  }

  private createLogEntry(
    level: LogLevel,
    event: SecurityEvent | undefined,
    message: string,
    context: Record<string, unknown> = {}
  ): LogEntry {
    return {
      id: this.generateId(),
      timestamp: new Date().toISOString(),
      level,
      event,
      message,
      severity: 5,
      tags: [],
      ...this.sanitizer.sanitize(context),
    }
  }

  private startFlushTimer(): void {
    if (this.flushTimer) clearInterval(this.flushTimer)
    this.flushTimer = setInterval(() => {
      void this.flush()
    }, this.config.flushInterval)
  }

  private async flush(): Promise<void> {
    if (this.logBuffer.length === 0) return
    const batch = this.logBuffer.splice(0, this.config.batchSize)
    await Promise.allSettled(batch.map(entry => dispatchLogEntry(entry, this.config)))
  }

  async log(
    level: LogLevel,
    event: SecurityEvent | undefined,
    message: string,
    context: Record<string, unknown> = {}
  ): Promise<void> {
    if (!this.shouldLog(level)) return
    const entry = this.createLogEntry(level, event, message, context)

    if (this.config.enableFileOutput || this.config.enableRemoteLogging) {
      this.logBuffer.push(entry)
      if (this.logBuffer.length >= this.config.batchSize) await this.flush()
    } else {
      await dispatchLogEntry(entry, this.config)
    }
  }

  async debug(message: string, context: Record<string, unknown> = {}): Promise<void> {
    await this.log('debug', undefined, message, context)
  }

  async info(message: string, context: Record<string, unknown> = {}): Promise<void> {
    await this.log('info', undefined, message, context)
  }

  async warn(message: string, context: Record<string, unknown> = {}): Promise<void> {
    await this.log('warn', undefined, message, context)
  }

  async error(message: string, error?: Error, context: Record<string, unknown> = {}): Promise<void> {
    await this.log('error', 'system_error', message, {
      ...context,
      error: error?.message,
      stack: error?.stack,
    })
  }

  async critical(message: string, context: Record<string, unknown> = {}): Promise<void> {
    await this.log('critical', undefined, message, context)
  }

  async security(event: SecurityEvent, message: string, context: Record<string, unknown> = {}): Promise<void> {
    await this.log('warn', event, message, context)
  }

  async authentication(success: boolean, userId?: string, context: Record<string, unknown> = {}): Promise<void> {
    const event = success ? 'authentication_success' : 'authentication_failure'
    await this.log(success ? 'info' : 'warn', event, `Authentication ${success ? 'success' : 'failure'}`, {
      userId,
      ...context,
    })
  }

  async authorization(
    success: boolean,
    userId: string,
    resource: string,
    action: string,
    context: Record<string, unknown> = {}
  ): Promise<void> {
    const event = success ? undefined : 'authorization_failure'
    const level = success ? 'debug' : 'warn'
    await this.log(level, event, `Authorization ${success ? 'success' : 'failure'} for ${action} on ${resource}`, {
      userId,
      resource,
      action,
      ...context,
    })
  }

  async audit(action: string, resource: string, userId: string, context: Record<string, unknown> = {}): Promise<void> {
    await this.log('info', 'admin_action', `Audit: ${action} on ${resource}`, { userId, resource, action, ...context })
  }

  async close(): Promise<void> {
    if (this.flushTimer) clearInterval(this.flushTimer)
    await this.flush()
  }
}

export const securityLogger = new SecurityLogger()

process.on('SIGTERM', async () => {
  await securityLogger.close()
})
process.on('SIGINT', async () => {
  await securityLogger.close()
})

export {
  DataSanitizer,
  type LogEntry,
  type LogEntry as LogEntryType,
  LogEntrySchema,
  LogLevelEnum,
  LogLevelEnum as LogLevel,
  SecurityEventEnum,
  SecurityEventEnum as SecurityEvent,
  type SecurityLoggerConfig,
}
export default securityLogger
