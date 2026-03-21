/**
 * RaaS Gateway — Cloudflare Worker Entry Point
 */

import { Hono } from 'hono';
import { cors } from './middleware/cors';
import { logger } from './middleware/logger';
import { securityHeaders } from './middleware/security-headers';
import { requestMetrics } from './middleware/request-metrics';
import { requestId } from './middleware/request-id';
import { createRoutes } from './routes';
import { errorResponse } from './utils/response';
import { ApiError } from './utils/errors';
import { handleScheduled } from './services/scheduled-handler';

export interface Env {
  DB: D1Database;
  RATE_LIMIT_KV: KVNamespace;
  SESSION_KV: KVNamespace;
  AI: Ai;
  JWT_SECRET=REDACTED: string;
  POLAR_WEBHOOK_SECRET: string;
  TELEGRAM_BOT_TOKEN: string;
  ENVIRONMENT: string;
  LOG_LEVEL: string;
  RESEND_API_KEY?: string;
  STRIPE_SECRET_KEY?: string;
  STRIPE_WEBHOOK_SECRET?: string;
  ADMIN_API_KEY?: string;
  POLAR_API_TOKEN?: string;
  POLAR_ACCESS_TOKEN?: string;
}

// Export app for test imports
export const app = new Hono<{ Bindings: Env }>();

// Global middleware
app.use('*', requestId());
app.use('*', logger());
app.use('*', cors());
app.use('*', securityHeaders());
app.use('*', requestMetrics());

// Mount routes
app.route('/', createRoutes());

// Global error handler
app.onError((err, c) => {
  console.error(`[Error] ${err.name}: ${err.message}`, err.stack);

  if (err instanceof ApiError) {
    return errorResponse(err.toJSON(c.get('requestId')), err.status);
  }

  return errorResponse(
    { error: 'Internal Server Error', code: 'INTERNAL_ERROR' },
    500
  );
});

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    return app.fetch(request, env, ctx);
  },

  // Scheduled handler — orchestrates all periodic background tasks
  async scheduled(_event: ScheduledEvent, env: Env, ctx: ExecutionContext): Promise<void> {
    ctx.waitUntil(handleScheduled(env));
  },
};
