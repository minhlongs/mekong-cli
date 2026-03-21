/**
 * GraphQL service — public façade over the graphql-schema executor
 * Provides parseQuery, executeQuery, and buildResponse helpers
 * used by the /graphql route handler.
 */

import { executeGraphQL } from './graphql-schema';
import type { GraphQLRequest, GraphQLResponse } from './graphql-schema';

// ─── Types ───────────────────────────────────────────────────────────────────

export interface ParsedQuery {
  operation: 'query' | 'mutation';
  fields: string[];
  args: Record<string, unknown>;
  subSelections: Record<string, string[]>;
}

// ─── Query parser ────────────────────────────────────────────────────────────

/**
 * Parse a simple GraphQL query string into structured metadata.
 * Supports: query { fieldName(args) { subField1 subField2 } }
 */
export function parseQuery(queryString: string): ParsedQuery {
  const trimmed = queryString.trim();
  const operation: 'query' | 'mutation' = trimmed.startsWith('mutation')
    ? 'mutation'
    : 'query';

  // Extract body between outermost braces
  const open = trimmed.indexOf('{');
  const close = trimmed.lastIndexOf('}');
  const body = open !== -1 ? trimmed.slice(open + 1, close === -1 ? undefined : close) : '';

  const fields: string[] = [];
  const args: Record<string, unknown> = {};
  const subSelections: Record<string, string[]> = {};

  // Match: fieldName or fieldName(args) followed by optional { subfields }
  const fieldPattern = /(\w+)\s*(?:\(([^)]*)\))?\s*(?:\{([^}]*)\})?/g;
  const keywords = new Set(['query', 'mutation', 'fragment', 'on']);
  let m: RegExpExecArray | null;

  while ((m = fieldPattern.exec(body)) !== null) {
    const name = m[1];
    if (keywords.has(name)) continue;

    fields.push(name);

    // Parse args for this field
    if (m[2]) {
      const argPattern = /(\w+)\s*:\s*("([^"]*)"|([\d.]+)|(true|false))/g;
      let am: RegExpExecArray | null;
      while ((am = argPattern.exec(m[2])) !== null) {
        const key = am[1];
        if (am[3] !== undefined) args[key] = am[3];
        else if (am[4] !== undefined) args[key] = parseFloat(am[4]);
        else if (am[5] !== undefined) args[key] = am[5] === 'true';
      }
    }

    // Extract sub-selections
    if (m[3]) {
      subSelections[name] = m[3].trim().split(/\s+/).filter(Boolean);
    }
  }

  return { operation, fields, args, subSelections };
}

// ─── Query executor ──────────────────────────────────────────────────────────

/**
 * Execute a GraphQL query against D1 for the given tenant.
 * Delegates to the graphql-schema executor which owns resolver logic.
 */
export async function executeQuery(
  db: D1Database,
  tenantId: string,
  request: GraphQLRequest
): Promise<GraphQLResponse> {
  return executeGraphQL(request, db, tenantId);
}

// ─── Response builder ────────────────────────────────────────────────────────

/**
 * Wrap resolver output in standard GraphQL response envelope.
 */
export function buildResponse(
  data: Record<string, unknown>,
  errors?: Array<{ message: string; path?: string[] }>
): GraphQLResponse {
  return {
    ...(Object.keys(data).length ? { data } : {}),
    ...(errors?.length ? { errors } : {}),
  };
}

// ─── Schema descriptor (public, no auth) ─────────────────────────────────────

/**
 * Static schema info returned by GET /graphql.
 * No auth required — safe to expose publicly.
 */
export const SCHEMA_INFO = {
  schema: 'RaaS GraphQL API',
  version: '1.0',
  types: ['Query', 'Mutation'],
  queries: {
    me: 'Tenant info (tenantId, tier, credits)',
    missions: 'List missions — args: limit, offset, status',
    mission: 'Single mission by ID — args: id',
    credits: 'Credit balance and transactions',
    apiKeys: 'List API keys (non-revoked)',
    usage: 'Usage statistics summary',
    health: 'System health status',
  },
  mutations: {
    createMission: 'Create a mission — args: goal (required), complexity',
    updateProfile: 'Update tenant profile — args: name, email',
  },
  example: 'query { missions(limit: 5, status: "queued") { id goal status } }',
};
