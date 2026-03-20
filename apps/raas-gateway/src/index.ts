/**
 * RaaS Gateway — Cloudflare Worker Entry Point
 */

import { Hono } from 'hono';
import { cors } from './middleware/cors';
import { logger } from './middleware/logger';
import { createRoutes } from './routes';
import { errorResponse } from './utils/response';
import { ApiError } from './utils/errors';

export interface Env {
  DB: D1Database;
  RATE_LIMIT_KV: KVNamespace;
  SESSION_KV: KVNamespace;
  AI: Ai;
  JWT_SECRET=REDACTED: string;
  POLAR_WEBHOOK_SECRET: string;
  ENVIRONMENT: string;
  LOG_LEVEL: string;
}

const app = new Hono<{ Bindings: Env }>();

// Global middleware
app.use('*', logger());
app.use('*', cors());

// Mount routes
app.route('/', createRoutes());

// Global error handler
app.onError((err, c) => {
  console.error(`[Error] ${err.name}: ${err.message}`, err.stack);

  if (err instanceof ApiError) {
    return errorResponse(err.toJSON(), err.status);
  }

  return errorResponse(
    { error: 'Internal Server Error', code: 'INTERNAL_ERROR' },
    500
  );
});

export default app;

export const handler = {
  async fetch(
    request: Request,
    env: Env,
    ctx: ExecutionContext
  ): Promise<Response> {
    return app.fetch(request, env, ctx);
  },
};
