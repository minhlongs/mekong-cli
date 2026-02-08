import { z } from 'zod';

const WebhookEventType = z.enum([
  'checkout.completed',
  'subscription.created',
  'subscription.updated',
  'subscription.cancelled',
]);

export const WebhookEventSchema = z.object({
  type: WebhookEventType,
  data: z.record(z.string(), z.unknown()),
});

export type WebhookEvent = z.infer<typeof WebhookEventSchema>;
export type WebhookEventType = z.infer<typeof WebhookEventType>;
