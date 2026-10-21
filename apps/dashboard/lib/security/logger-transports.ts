/**
 * Security Logger Data Sanitizer & Output Transports
 */

import type { LogEntry, SecurityLoggerConfig } from './logger-types'

export class DataSanitizer {
  private sanitizeFields: string[]

  constructor(sanitizeFields: string[]) {
    this.sanitizeFields = sanitizeFields
  }

  sanitize<T extends Record<string, unknown>>(obj: T): T {
    if (!obj || typeof obj !== 'object') return obj

    if (Array.isArray(obj)) {
      return obj.map(item => this.sanitize(item as Record<string, unknown>)) as unknown as T
    }

    const sanitized: Record<string, unknown> = {}
    for (const [key, value] of Object.entries(obj)) {
      if (this.shouldSanitize(key)) {
        sanitized[key] = '[REDACTED]'
      } else if (typeof value === 'object' && value !== null) {
        sanitized[key] = this.sanitize(value as Record<string, unknown>)
      } else {
        sanitized[key] = value
      }
    }
    return sanitized as T
  }

  private shouldSanitize(key: string): boolean {
    const lowerKey = key.toLowerCase()
    return this.sanitizeFields.some(field => lowerKey.includes(field.toLowerCase()))
  }
}

const LEVEL_LABELS: Record<string, string> = {
  debug: '[DEBUG]',
  info: '[INFO]',
  warn: '[WARN]',
  error: '[ERROR]',
  critical: '[CRITICAL]',
}

export function writeToConsoleTransport(entry: LogEntry): void {
  const prefix = LEVEL_LABELS[entry.level] || `[${entry.level.toUpperCase()}]`
  const eventTag = entry.event ? `[${entry.event.toUpperCase()}]` : ''
  const payload = JSON.stringify({
    id: entry.id,
    timestamp: entry.timestamp,
    userId: entry.userId,
    ipAddress: entry.ipAddress,
    ...entry.context,
  })
  if (typeof process !== 'undefined' && process.stdout?.write) {
    process.stdout.write(`${prefix} ${eventTag} ${entry.message} ${payload}\n`)
  }
}

export async function writeToFileTransport(entry: LogEntry): Promise<void> {
  const _logLine = JSON.stringify(entry) + '\n'
}

export async function writeToRemoteTransport(
  entry: LogEntry,
  remoteEndpoint?: string
): Promise<void> {
  if (!remoteEndpoint) return

  const response = await fetch(remoteEndpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${process.env.SECURITY_LOG_TOKEN}`,
    },
    body: JSON.stringify(entry),
  })

  if (!response.ok) {
    throw new Error(`Remote logging failed: ${response.statusText}`)
  }
}

export async function dispatchLogEntry(
  entry: LogEntry,
  config: SecurityLoggerConfig
): Promise<void> {
  try {
    if (config.enableConsoleOutput) {
      writeToConsoleTransport(entry)
    }
    if (config.enableFileOutput) {
      await writeToFileTransport(entry)
    }
    if (config.enableRemoteLogging && config.remoteEndpoint) {
      await writeToRemoteTransport(entry, config.remoteEndpoint)
    }
  } catch (error) {
    if (typeof process !== 'undefined' && process.stderr?.write) {
      process.stderr.write(`Failed to write security log: ${String(error)}\n`)
    }
  }
}
