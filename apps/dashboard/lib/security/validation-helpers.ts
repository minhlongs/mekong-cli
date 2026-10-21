/**
 * Security Pattern Validators & Upload Checks
 */

import { securityLogger } from './logger'

export class SecurityValidator {
  // SQL Injection patterns
  private static readonly SQL_PATTERNS = [
    /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)/i,
    /(--|\*\/|\/\*)/,
    /(\bOR\b.*=.*\bOR\b)/i,
    /(\bAND\b.*=.*\bAND\b)/i,
    /('|"`).*\1.*\1/,
  ]

  // XSS patterns
  private static readonly XSS_PATTERNS = [
    /<script[^>]*>.*?<\/script>/gi,
    /javascript:/gi,
    /on\w+\s*=/gi,
    /<iframe[^>]*>/gi,
    /<object[^>]*>/gi,
    /<embed[^>]*>/gi,
  ]

  // Command injection patterns
  private static readonly CMD_PATTERNS = [
    /[;&|`$(){}[\]]/,
    /\b(rm|mv|cp|cat|ls|ps|kill|chmod|chown)\s/i,
    /\b(curl|wget|nc|netcat)\s/i,
  ]

  // Path traversal patterns
  private static readonly PATH_TRAVERSAL = [/\.\.[\/\\]/, /[\/\\]\.\.[\/\\]/, /%2e%2e[\/\\]/i]

  static async validateSqlInjection(value: string): Promise<boolean> {
    for (const pattern of this.SQL_PATTERNS) {
      if (pattern.test(value)) {
        await securityLogger.security('sql_injection_attempt', 'SQL injection pattern detected', {
          value: value.substring(0, 100),
        })
        return false
      }
    }
    return true
  }

  static async validateXss(value: string): Promise<boolean> {
    for (const pattern of this.XSS_PATTERNS) {
      if (pattern.test(value)) {
        await securityLogger.security('xss_attempt', 'XSS pattern detected', {
          value: value.substring(0, 100),
        })
        return false
      }
    }
    return true
  }

  static async validateCommandInjection(value: string): Promise<boolean> {
    for (const pattern of this.CMD_PATTERNS) {
      if (pattern.test(value)) {
        await securityLogger.security('malicious_request', 'Command injection pattern detected', {
          value: value.substring(0, 100),
        })
        return false
      }
    }
    return true
  }

  static async validatePathTraversal(value: string): Promise<boolean> {
    for (const pattern of this.PATH_TRAVERSAL) {
      if (pattern.test(value)) {
        await securityLogger.security('malicious_request', 'Path traversal pattern detected', {
          value: value.substring(0, 100),
        })
        return false
      }
    }
    return true
  }

  static async validateFileUpload(
    fileName: string,
    mimeType: string,
    size: number
  ): Promise<boolean> {
    const allowedExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.txt']
    const extension = fileName.toLowerCase().substring(fileName.lastIndexOf('.'))

    if (!allowedExtensions.includes(extension)) {
      await securityLogger.security('file_upload_violation', 'Invalid file extension', {
        fileName,
        extension,
      })
      return false
    }

    const allowedMimeTypes = [
      'image/jpeg',
      'image/png',
      'image/gif',
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
    ]

    if (!allowedMimeTypes.includes(mimeType.toLowerCase())) {
      await securityLogger.security('file_upload_violation', 'Invalid MIME type', {
        fileName,
        mimeType,
      })
      return false
    }

    const maxSize = 10 * 1024 * 1024
    if (size > maxSize) {
      await securityLogger.security('file_upload_violation', 'File too large', { fileName, size })
      return false
    }

    return true
  }
}

export class InputValidationError extends Error {
  constructor(
    public field: string,
    message: string,
    public code: string = 'VALIDATION_ERROR'
  ) {
    super(message)
    this.name = 'InputValidationError'
  }
}
