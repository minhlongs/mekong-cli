/**
 * Onboarding Zod Schemas & Shared Types
 */

import { z } from 'zod'
import { TUTORIAL_STEPS } from '../onboarding/flows'
import type { Tenant } from '../types/raas'

export type Variables = { tenant: Tenant }

export const profileSchema = z.object({
  business_name: z.string().min(1, 'business_name is required').max(200, 'business_name must be ≤200 chars'),
  industry: z.string().max(100, 'industry must be ≤100 chars').optional(),
  address: z.string().max(300, 'address must be ≤300 chars').optional(),
  phone: z.string().max(20, 'phone must be ≤20 chars').optional(),
  hours: z.string().max(200, 'hours must be ≤200 chars').optional(),
  logo_url: z.string().url('logo_url must be a valid URL').optional(),
})

export const channelSchema = z.object({
  type: z.enum(['zalo_oa', 'facebook_page']),
  external_id: z.string().min(1, 'external_id is required').max(100, 'external_id must be ≤100 chars'),
  access_token: z.string().max(500, 'access_token must be ≤500 chars').optional(),
  name: z.string().max(200, 'name must be ≤200 chars').optional(),
})

export const menuItemSchema = z.object({
  name: z.string().max(200, 'item name must be ≤200 chars'),
  price: z.number().positive('price must be positive').max(1_000_000, 'price too large'),
  description: z.string().max(500, 'description must be ≤500 chars').optional(),
  category: z.string().max(100, 'category must be ≤100 chars').optional(),
})

export const menuSchema = z.object({
  menu_data: z.object({
    categories: z.array(z.string()).max(50, 'max 50 categories').optional(),
    items: z.array(menuItemSchema).max(500, 'max 500 items'),
  }).refine((data) => JSON.stringify(data).length < 100_000, 'Menu data exceeds size limit (100KB)'),
})

export type ProfileBody = z.infer<typeof profileSchema>
export type ChannelBody = z.infer<typeof channelSchema>
export type MenuBody = z.infer<typeof menuSchema>

export const signupSchema = z.object({
  email: z.string().email('Invalid email address'),
  business_name: z.string().min(1, 'Business name is required').max(200),
  invite_code: z.string().min(1).max(128).optional(),
})

export const verifyEmailSchema = z.object({
  code: z.string().length(6, 'Verification code must be 6 digits'),
})

export const tutorialStepSchema = z.object({
  step_id: z.number().min(1).max(TUTORIAL_STEPS.length),
})

export const npsSchema = z.object({
  score: z.number().min(0).max(10, 'NPS score must be between 0 and 10'),
})

export const feedbackSchema = z.object({
  type: z.enum(['feature', 'general']),
  feedback: z.string().min(1, 'Feedback is required').max(2000),
  category: z.string().optional(),
})

export function generateVerificationCode(): string {
  return Math.floor(100000 + Math.random() * 900000).toString()
}
