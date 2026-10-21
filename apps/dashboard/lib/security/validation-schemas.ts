/**
 * Common Input Validation Schemas
 */

import { z } from 'zod'
import DOMPurify from 'isomorphic-dompurify'

export const commonSchemas = {
  // Basic string validations
  nonEmptyString: z.string().min(1, 'Field cannot be empty'),
  safeString: z
    .string()
    .max(1000, 'Text too long')
    .transform(val => DOMPurify.sanitize(val.trim())),

  // ID validations
  uuid: z.string().uuid('Invalid ID format'),
  numericId: z.string().regex(/^\d+$/, 'Invalid numeric ID'),

  // Email validation
  email: z
    .string()
    .email('Invalid email format')
    .transform(val => val.toLowerCase().trim()),

  // URL validation
  url: z
    .string()
    .url('Invalid URL format')
    .transform(val => DOMPurify.sanitize(val.trim())),

  // Password validation
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain uppercase letter')
    .regex(/[a-z]/, 'Password must contain lowercase letter')
    .regex(/\d/, 'Password must contain number'),

  // Name validation
  name: z
    .string()
    .min(1, 'Name cannot be empty')
    .max(100, 'Name too long')
    .regex(/^[a-zA-Z\s'-]+$/, 'Invalid name format')
    .transform(val => DOMPurify.sanitize(val.trim())),

  // Phone number validation
  phone: z
    .string()
    .regex(/^\+?[\d\s\-()]+$/, 'Invalid phone format')
    .min(10, 'Phone number too short')
    .max(20, 'Phone number too long'),

  // Date validation
  date: z.string().datetime('Invalid date format'),
  futureDate: z
    .string()
    .datetime('Invalid date format')
    .transform(val => {
      const date = new Date(val)
      if (date <= new Date()) {
        throw new Error('Date must be in the future')
      }
      return val
    }),

  // Pagination
  page: z
    .string()
    .regex(/^\d+$/, 'Invalid page number')
    .transform(Number)
    .pipe(z.number().min(1).max(1000).default(1)),
  limit: z
    .string()
    .regex(/^\d+$/, 'Invalid limit')
    .transform(Number)
    .pipe(z.number().min(1).max(100).default(20)),

  // Sort
  sortBy: z.string().optional(),
  sortOrder: z.enum(['asc', 'desc']).default('desc'),

  // IP Address
  ipAddress: z.string().ip('Invalid IP address'),

  // Currency amount
  amount: z
    .string()
    .regex(/^\d+(\.\d{1,2})?$/, 'Invalid amount format')
    .transform(val => parseFloat(val)),

  // Select options
  booleanString: z.enum(['true', 'false']).transform(val => val === 'true'),

  // File upload metadata
  fileName: z
    .string()
    .min(1, 'Filename required')
    .max(255, 'Filename too long')
    .regex(/^[a-zA-Z0-9._-]+$/, 'Invalid filename'),

  fileSize: z.string().regex(/^\d+$/, 'Invalid file size').transform(Number),

  mimeType: z
    .string()
    .regex(
      /^[a-zA-Z0-9][a-zA-Z0-9!#$&\-\^_]*\/[a-zA-Z0-9][a-zA-Z0-9!#$&\-\^_.]*$/,
      'Invalid MIME type'
    ),
}
