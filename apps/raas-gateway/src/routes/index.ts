/**
 * Route registry — combines all route handlers
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { health } from './health';
import { api } from './api';
import { credits } from './credits';
import { billing } from './billing';
import { tenants } from './tenants';
import { telegram } from './telegram';
import { notFound } from '../utils/response';

export function createRoutes() {
  const routes = new Hono<{ Bindings: Env }>();

  // Mount routes (tenants before api — signup is public, must bypass api auth)
  routes.route('/health', health);
  routes.route('/v1/tenants', tenants);
  routes.route('/v1', api);
  routes.route('/credits', credits);
  routes.route('/billing', billing);
  routes.route('/webhook/telegram', telegram);

  // Catch-all 404
  routes.notFound((c) => {
    return notFound(`Route ${c.req.path} not found`);
  });

  return routes;
}
