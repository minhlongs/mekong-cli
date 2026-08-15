import { z } from 'zod';
import { Hono } from 'hono';
import { VideoJobSchema, VideoJob } from '../video/pipeline';

export const DIDWebhookPayloadSchema = z.object({
  id: z.string(),
  status: z.enum(['created', 'started', 'done', 'error']),
  result_url: z.string().url().optional(),
  error: z.string().optional(),
  created_at: z.string(),
  started_at: z.string().optional(),
  finished_at: z.string().optional(),
  metadata: z.object({
    jobId: z.string().optional(),
  }).optional(),
});

export type DIDWebhookPayload = z.infer<typeof DIDWebhookPayloadSchema>;

export const ElevenLabsWebhookPayloadSchema = z.object({
  history_item_id: z.string(),
  status: z.enum(['pending', 'done', 'failed']),
  audio_url: z.string().url().optional(),
  error: z.string().optional(),
  metadata: z.object({
    jobId: z.string().optional(),
  }).optional(),
});

export type ElevenLabsWebhookPayload = z.infer<typeof ElevenLabsWebhookPayloadSchema>;

export const WebhookHandlerConfigSchema = z.object({
  didWebhookSecret: z.string().optional(),
  elevenlabsWebhookSecret: z.string().optional(),
  videoPipelineBinding: z.any(), // DurableObjectNamespace
});

export type WebhookHandlerConfig = z.infer<typeof WebhookHandlerConfigSchema>;

export function createWebhookRoutes(config: WebhookHandlerConfig) {
  const app = new Hono();

  // D-ID webhook handler
  app.post('/webhooks/did', async (c) => {
    try {
      const body = await c.req.json();
      const payload = DIDWebhookPayloadSchema.parse(body);

      const jobId = payload.metadata?.jobId;
      if (!jobId) {
        return c.json({ error: 'Missing jobId in metadata' }, 400);
      }

      const pipelineStub = config.videoPipelineBinding.get(
        config.videoPipelineBinding.idFromName(jobId)
      );

      await pipelineStub.fetch(`https://internal/did-webhook`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      return c.json({ success: true });
    } catch (error) {
      console.error('D-ID webhook error:', error);
      return c.json({ error: 'Invalid payload' }, 400);
    }
  });

  // ElevenLabs webhook handler
  app.post('/webhooks/elevenlabs', async (c) => {
    try {
      const body = await c.req.json();
      const payload = ElevenLabsWebhookPayloadSchema.parse(body);

      const jobId = payload.metadata?.jobId;
      if (!jobId) {
        return c.json({ error: 'Missing jobId in metadata' }, 400);
      }

      const pipelineStub = config.videoPipelineBinding.get(
        config.videoPipelineBinding.idFromName(jobId)
      );

      await pipelineStub.fetch(`https://internal/elevenlabs-webhook`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      return c.json({ success: true });
    } catch (error) {
      console.error('ElevenLabs webhook error:', error);
      return c.json({ error: 'Invalid payload' }, 400);
    }
  });

  // OpenRouter webhook handler (for script generation completion)
  app.post('/webhooks/openrouter', async (c) => {
    try {
      const body = await c.req.json();

      // OpenRouter doesn't have native webhooks yet, but we can support it
      // for future use or custom implementations

      return c.json({ success: true });
    } catch (error) {
      console.error('OpenRouter webhook error:', error);
      return c.json({ error: 'Invalid payload' }, 400);
    }
  });

  // Generic job status webhook for external systems
  app.post('/webhooks/job-status', async (c) => {
    try {
      const body = await c.req.json();
      const { jobId, status, data } = z.object({
        jobId: z.string(),
        status: z.string(),
        data: z.record(z.unknown()).optional(),
      }).parse(body);

      const pipelineStub = config.videoPipelineBinding.get(
        config.videoPipelineBinding.idFromName(jobId)
      );

      await pipelineStub.fetch(`https://internal/external-webhook`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jobId, status, data, timestamp: Date.now() }),
      });

      return c.json({ success: true });
    } catch (error) {
      console.error('Job status webhook error:', error);
      return c.json({ error: 'Invalid payload' }, 400);
    }
  });

  return app;
}

export const CallbackHandlerConfigSchema = z.object({
  mcuBillingBinding: z.any(), // DurableObjectNamespace
});

export type CallbackHandlerConfig = z.infer<typeof CallbackHandlerConfigSchema>;

export function createCallbackRoutes(config: CallbackHandlerConfig) {
  const app = new Hono();

  // Video completion callback - fires user webhook
  app.post('/callbacks/video-complete', async (c) => {
    try {
      const body = await c.req.json();
      const { jobId, videoUrl, durationSeconds, userId } = z.object({
        jobId: z.string(),
        videoUrl: z.string().url(),
        durationSeconds: z.number().positive(),
        userId: z.string(),
      }).parse(body);

      // Charge MCU credits
      const billingStub = config.mcuBillingBinding.get(
        config.mcuBillingBinding.idFromName(userId)
      );

      const chargeResponse = await billingStub.fetch('https://internal/charge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId, seconds: durationSeconds }),
      });

      const chargeResult = await chargeResponse.json();

      // Get the job to find user's webhook URL
      const pipelineStub = config.mcuBillingBinding.get(
        config.mcuBillingBinding.idFromName(jobId)
      );

      const jobResponse = await pipelineStub.fetch(`https://internal/job/${jobId}`);
      const job = await jobResponse.json() as VideoJob;

      if (job?.webhookUrl) {
        try {
          await fetch(job.webhookUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              jobId,
              status: 'completed',
              data: {
                videoUrl,
                durationSeconds,
                creditsCharged: chargeResult.creditsCharged,
                remainingBalance: chargeResult.remainingBalance,
              },
              timestamp: Date.now(),
            }),
          });
        } catch (webhookError) {
          console.error('User webhook failed:', webhookError);
        }
      }

      return c.json({ success: true, chargeResult });
    } catch (error) {
      console.error('Video complete callback error:', error);
      return c.json({ error: 'Internal error' }, 500);
    }
  });

  // Video failure callback
  app.post('/callbacks/video-failed', async (c) => {
    try {
      const body = await c.req.json();
      const { jobId, error, userId } = z.object({
        jobId: z.string(),
        error: z.string(),
        userId: z.string(),
      }).parse(body);

      const pipelineStub = config.mcuBillingBinding.get(
        config.mcuBillingBinding.idFromName(jobId)
      );

      const jobResponse = await pipelineStub.fetch(`https://internal/job/${jobId}`);
      const job = await jobResponse.json() as VideoJob;

      if (job?.webhookUrl) {
        try {
          await fetch(job.webhookUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              jobId,
              status: 'failed',
              data: { error },
              timestamp: Date.now(),
            }),
          });
        } catch (webhookError) {
          console.error('User webhook failed:', webhookError);
        }
      }

      return c.json({ success: true });
    } catch (error) {
      console.error('Video failed callback error:', error);
      return c.json({ error: 'Internal error' }, 500);
    }
  });

  return app;
}

export type { VideoJobSchema, VideoJob };