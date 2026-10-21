/**
 * Security Logger Schemas, Types & Configuration
 */

import { z } from 'zod'

export const LogLevelEnum = z.enum(['debug', 'info', 'warn', 'error', 'critical'])
export type LogLevel = z.infer<typeof LogLevelEnum>

export const SecurityEventEnum = z.enum([
  'authentication_success',
  'authentication_failure',
  'authorization_failure',
  'rate_limit_exceeded',
  'suspicious_activity',
  'data_breach_attempt',
  'privilege_escalation',
  'malicious_request',
  'sql_injection_attempt',
  'xss_attempt',
  'csrf_attempt',
  'file_upload_violation',
  'api_key_abuse',
  'session_hijack',
  'brute_force_attempt',
  'data_export',
  'data_deletion',
  'consent_change',
  'admin_action',
  'system_error',
  'configuration_change',
])
export type SecurityEvent = z.infer<typeof SecurityEventEnum>

export const LogEntrySchema = z.object({
  id: z.string(),
  timestamp: z.string(),
  level: LogLevelEnum,
  event: SecurityEventEnum.optional(),
  message: z.string(),
  userId: z.string().optional(),
  sessionId: z.string().optional(),
  ipAddress: z.string().optional(),
  userAgent: z.string().optional(),
  requestId: z.string().optional(),
  resource: z.string().optional(),
  action: z.string().optional(),
  context: z.record(z.unknown()).optional(),
  metadata: z.record(z.unknown()).optional(),
  severity: z.number().min(1).max(10).default(5),
  tags: z.array(z.string()).default([]),
})

export type LogEntry = z.infer<typeof LogEntrySchema>

export interface SecurityLoggerConfig {
  level: LogLevel
  enableConsoleOutput: boolean
  enableFileOutput: boolean
  enableRemoteLogging: boolean
  remoteEndpoint?: string
  maxRetries: number
  batchSize: number
  flushInterval: number
  sanitizeFields: string[]
}

export const defaultConfig: SecurityLoggerConfig = {
  level: process.env.NODE_ENV === 'production' ? 'info' : 'debug',
  enableConsoleOutput: process.env.NODE_ENV !== 'production',
  enableFileOutput: true,
  enableRemoteLogging: process.env.NODE_ENV === 'production',
  remoteEndpoint: process.env.SECURITY_LOG_ENDPOINT,
  maxRetries: 3,
  batchSize: 100,
  flushInterval: 5000,
  sanitizeFields: ['password', 'token', 'secret', 'key', 'auth', 'cookie'],
}
