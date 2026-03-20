/**
 * Health check endpoint
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';

const VERSION = '0.1.0';
const startTime = Date.now();

export const health = new Hono<{ Bindings: Env }>();

health.get('/', (c) => {
  return json({
    status: 'healthy',
    version: VERSION,
    uptime: Date.now() - startTime,
    timestamp: Date.now(),
    environment: c.env.ENVIRONMENT,
  });
});

health.get('/ready', async (c) => {
  // Check database connection
  try {
    await c.env.DB.prepare('SELECT 1').first();
    return json({ status: 'ready', checks: { database: 'ok' } });
  } catch (error) {
    return json(
      { status: 'not_ready', checks: { database: 'error' } },
      { status: 503 }
    );
  }
});

health.get('/live', (c) => {
  return json({ status: 'alive' });
});
