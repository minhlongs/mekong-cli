import { Hono } from 'hono';
import { z } from 'zod';
import { createWebhookRoutes } from './webhooks/callbacks';
import { createCallbackRoutes } from './webhooks/callbacks';

export interface Env {
  VIDEO_PIPELINE: DurableObjectNamespace;
  MCU_BILLING: DurableObjectNamespace;

  DID_API_KEY: string;
  DID_BASE_URL?: string;
  ELEVENLABS_API_KEY: string;
  ELEVENLABS_BASE_URL?: string;
  OPENROUTER_API_KEY: string;
  OPENROUTER_BASE_URL?: string;
  OPENROUTER_SITE_URL?: string;
  OPENROUTER_SITE_NAME?: string;
  DEFAULT_AVATAR_URL: string;
  DEFAULT_VOICE_ID: string;
  MCU_CONFIG?: string;
  DID_WEBHOOK_SECRET?: string;
  ELEVENLABS_WEBHOOK_SECRET?: string;
}

const app = new Hono<{ Bindings: Env }>();

// Health check
app.get('/health', (c) => c.json({ status: 'ok', timestamp: Date.now() }));

// Video Pipeline Routes
app.post('/api/videos', async (c) => {
  const body = await c.req.json();
  const schema = z.object({
    userId: z.string(),
    topic: z.string().min(1).max(500),
    durationSeconds: z.number().min(5).max(300),
    language: z.enum(['en', 'vi']).default('en'),
    tone: z.enum(['professional', 'casual', 'energetic', 'educational']).default('professional'),
    targetAudience: z.string().optional(),
    keyPoints: z.array(z.string()).max(5).optional(),
    webhookUrl: z.string().url().optional(),
    avatarUrl: z.string().url().optional(),
    voiceId: z.string().optional(),
  });

  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    return c.json({ error: 'Invalid request', details: parsed.error.flatten() }, 400);
  }

  const pipelineStub = c.env.VIDEO_PIPELINE.get(
    c.env.VIDEO_PIPELINE.idFromName(`user:${parsed.data.userId}`)
  );

  const response = await pipelineStub.fetch('https://internal/create-job', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(parsed.data),
  });

  const job = await response.json();
  return c.json(job, response.ok ? 201 : 400);
});

app.get('/api/videos/:jobId', async (c) => {
  const jobId = c.req.param('jobId');
  const pipelineStub = c.env.VIDEO_PIPELINE.get(
    c.env.VIDEO_PIPELINE.idFromName(jobId)
  );

  const response = await pipelineStub.fetch(`https://internal/job/${jobId}`);
  const job = await response.json();

  if (!response.ok) {
    return c.json({ error: 'Job not found' }, 404);
  }

  return c.json(job);
});

app.get('/api/videos/user/:userId', async (c) => {
  const userId = c.req.param('userId');
  const pipelineStub = c.env.VIDEO_PIPELINE.get(
    c.env.VIDEO_PIPELINE.idFromName(`user:${userId}`)
  );

  const response = await pipelineStub.fetch(`https://internal/user-jobs/${userId}`);
  const jobs = await response.json();

  return c.json(jobs);
});

// MCU Billing Routes
app.post('/api/billing/charge', async (c) => {
  const body = await c.req.json();
  const schema = z.object({
    userId: z.string(),
    seconds: z.number().positive(),
    tier: z.enum(['BASIC', 'PREMIUM', 'ENTERPRISE', 'MASTER']).optional(),
    idempotencyKey: z.string().optional(),
  });

  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    return c.json({ error: 'Invalid request', details: parsed.error.flatten() }, 400);
  }

  const billingStub = c.env.MCU_BILLING.get(
    c.env.MCU_BILLING.idFromName(parsed.data.userId)
  );

  const response = await billingStub.fetch('https://internal/charge', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(parsed.data),
  });

  const result = await response.json();
  return c.json(result, response.ok ? 200 : 400);
});

app.post('/api/billing/topup', async (c) => {
  const body = await c.req.json();
  const schema = z.object({
    userId: z.string(),
    credits: z.number().positive(),
    idempotencyKey: z.string().optional(),
  });

  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    return c.json({ error: 'Invalid request', details: parsed.error.flatten() }, 400);
  }

  const billingStub = c.env.MCU_BILLING.get(
    c.env.MCU_BILLING.idFromName(parsed.data.userId)
  );

  const response = await billingStub.fetch('https://internal/topup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(parsed.data),
  });

  const balance = await response.json();
  return c.json(balance, response.ok ? 200 : 400);
});

app.get('/api/billing/balance/:userId', async (c) => {
  const userId = c.req.param('userId');
  const billingStub = c.env.MCU_BILLING.get(
    c.env.MCU_BILLING.idFromName(userId)
  );

  const response = await billingStub.fetch(`https://internal/balance/${userId}`);
  const balance = await response.json();

  if (!response.ok) {
    return c.json({ error: 'User not found' }, 404);
  }

  return c.json(balance);
});

app.post('/api/billing/tier', async (c) => {
  const body = await c.req.json();
  const schema = z.object({
    userId: z.string(),
    tier: z.enum(['BASIC', 'PREMIUM', 'ENTERPRISE', 'MASTER']),
  });

  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    return c.json({ error: 'Invalid request', details: parsed.error.flatten() }, 400);
  }

  const billingStub = c.env.MCU_BILLING.get(
    c.env.MCU_BILLING.idFromName(parsed.data.userId)
  );

  const response = await billingStub.fetch('https://internal/set-tier', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(parsed.data),
  });

  const balance = await response.json();
  return c.json(balance, response.ok ? 200 : 400);
});

// Webhook routes
app.route('/webhooks', createWebhookRoutes({
  didWebhookSecret: '',
  elevenlabsWebhookSecret: '',
  videoPipelineBinding: {} as any, // Will be replaced at runtime
}));

// Callback routes
app.route('/callbacks', createCallbackRoutes({
  mcuBillingBinding: {} as any, // Will be replaced at runtime
}));

// The actual DO fetch handlers are in their respective DO classes
// This worker just routes to the appropriate DO

export default {
  fetch: app.fetch,
} satisfies ExportedHandler<Env>;