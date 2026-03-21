/**
 * GraphQL route — lightweight GraphQL endpoint for flexible frontend consumption
 * GET  /graphql        — schema info (public, no auth)
 * POST /graphql        — execute query or mutation (auth required)
 * GET  /graphql/schema — introspection-like schema listing (auth required)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth } from '../middleware/auth';
import { json } from '../utils/response';
import { getTenant } from '../middleware/auth';
import { executeQuery, SCHEMA_INFO } from '../services/graphql-service';

export const graphql = new Hono<{ Bindings: Env }>();

/** GET /graphql — public schema info, no auth required */
graphql.get('/', (c) => {
  return json({ success: true, data: SCHEMA_INFO });
});

/** POST /graphql — execute query or mutation (auth required) */
graphql.post('/', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as {
    query?: string;
    variables?: Record<string, unknown>;
  };

  if (!body.query || typeof body.query !== 'string') {
    return json({ errors: [{ message: 'query is required' }] }, { status: 400 });
  }

  const result = await executeQuery(
    c.env.DB,
    tenant.tenantId,
    { query: body.query, variables: body.variables }
  );

  return json(result);
});

/** GET /graphql/schema — introspection-like listing of available types (auth required) */
graphql.get('/schema', auth(), (c) => {
  return json({
    types: {
      Query: ['me', 'missions', 'mission', 'credits', 'apiKeys', 'usage', 'health'],
      Mutation: ['createMission', 'updateProfile'],
    },
    fieldArgs: {
      me: {},
      missions: { status: 'string', limit: 'number', offset: 'number' },
      mission: { id: 'string (required)' },
      credits: {},
      apiKeys: {},
      usage: {},
      health: {},
      createMission: { goal: 'string (required)', complexity: 'simple|standard|complex' },
      updateProfile: { name: 'string', email: 'string' },
    },
    description: 'Lightweight GraphQL API for RaaS Gateway',
    example: SCHEMA_INFO.example,
  });
});
