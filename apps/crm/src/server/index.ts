import { Hono } from 'hono';
import { api } from './api-routes';

interface Env {
  DB: D1Database;
  ASSETS: Fetcher;
}

const app = new Hono<{ Bindings: Env }>();

// API routes
app.route('/api', api);

// Serve frontend assets
app.get('/*', async (c) => {
  const res = await c.env.ASSETS.fetch(new Request(new URL(c.req.url)));
  return res;
});

export default app;
