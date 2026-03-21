/**
 * GraphQL route — lightweight GraphQL endpoint for flexible frontend consumption
 * POST /graphql        — execute query or mutation
 * GET  /graphql/schema — introspection-like schema listing
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth } from '../middleware/auth';
import { json } from '../utils/response';
import { executeGraphQL } from '../services/graphql-schema';
import { getTenant } from '../middleware/auth';

export const graphql = new Hono<{ Bindings: Env }>();

/** POST /graphql — execute query or mutation */
graphql.post('/', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as { query?: string; variables?: Record<string, unknown> };

  if (!body.query || typeof body.query !== 'string') {
    return json(
      { errors: [{ message: 'query is required' }] },
      { status: 400 }
    );
  }

  const result = await executeGraphQL(
    { query: body.query, variables: body.variables },
    c.env.DB,
    tenant.tenantId
  );

  return json(result);
});

/** GET /graphql/schema — introspection-like listing of available types */
graphql.get('/schema', auth(), (c) => {
  return json({
    types: {
      Query: ['missions', 'tenant', 'billing', 'analytics', 'models', 'apiKeys'],
      Mutation: ['createMission', 'updateProfile'],
    },
    fieldArgs: {
      missions: { status: 'string', limit: 'number' },
      createMission: { goal: 'string (required)', complexity: 'simple|standard|complex' },
      updateProfile: { name: 'string', email: 'string' },
    },
    description: 'Lightweight GraphQL API for RaaS Gateway',
  });
});
