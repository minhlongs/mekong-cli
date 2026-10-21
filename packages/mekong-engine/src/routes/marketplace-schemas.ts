import { z } from 'zod'

export const configSchemaItemSchema = z.object({
  type: z.enum(['string', 'number', 'boolean', 'select']),
  label: z.string().max(100),
  required: z.boolean().optional().default(false),
  default: z.unknown().optional(),
  options: z.array(z.string()).max(20).optional(),
})

export const configSchemaSchema = z.record(configSchemaItemSchema).refine(
  (data) => Object.keys(data).length <= 50,
  'Config schema must have at most 50 keys'
)

export const pluginSchema = z.object({
  developer_id: z.string().uuid('developer_id must be a valid UUID'),
  name: z.string().min(1, 'name is required').max(200, 'name must be ≤200 chars'),
  slug: z.string().min(1, 'slug is required').max(100, 'slug must be ≤100 chars'),
  description: z.string().max(500, 'description must be ≤500 chars').optional(),
  category: z.string().max(100, 'category must be ≤100 chars').optional(),
  version: z.string().max(20, 'version must be ≤20 chars').optional().default('1.0.0'),
  pricing_type: z.enum(['free', 'paid', 'freemium']).optional().default('free'),
  price_credits: z.number().int().positive('price_credits must be positive').max(10_000, 'price too high').optional().default(0),
  webhook_url: z.string().url('webhook_url must be a valid URL').max(500, 'webhook_url too long').optional(),
  config_schema: configSchemaSchema.optional(),
})

export type PublishPluginBody = z.infer<typeof pluginSchema>

export const reviewPluginSchema = z.object({
  plugin_id: z.string().min(1, 'plugin_id is required'),
  reviewer_id: z.string().min(1, 'reviewer_id is required'),
  rating: z.number().int().min(1).max(5, 'rating must be between 1 and 5'),
  review_text: z.string().optional(),
})
