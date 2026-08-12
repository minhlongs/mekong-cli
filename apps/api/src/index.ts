/**
 * Mekong API Gateway Worker
 *
 * Edge-located API gateway that:
 * - Routes requests to appropriate backend services
 * - Handles authentication and rate limiting
 * - Provides caching layer
 * - Manages webhooks
 * - Implements request validation
 * - Captures errors with Sentry
 *
 * Deploy with: npx wrangler deploy
 */

import { initSentry, captureException, addBreadcrumb } from '@mekong/observability';

// Initialize Sentry error tracking (async, non-blocking)
initSentry().catch(console.error);

export interface Env {
  // KV namespace for rate limiting and caching
  RATE_LIMIT_KV: KVNamespace;
  CACHE_KV: KVNamespace;

  // D1 database for sessions and audit logs
  SESSIONS_DB: D1Database;
  AUDIT_DB: D1Database;

  // AI binding for LLM routing
  AI: Ai;

  // Environment configuration
  ENVIRONMENT: string;
  BACKEND_API_URL: string;
  WEBHOOK_SECRET: string;
}

interface RateLimitInfo {
  requests: number;
  reset: number;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;

    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS, PATCH',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Key, X-Requested-With',
      'Access-Control-Max-Age': '86400',
    };

    // Handle preflight
    if (method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Skip rate limiting for health checks
    if (path === '/health') {
      return handleHealth(request, env);
    }

    // Rate limiting (except for health)
    const rateLimitCheck = await checkRateLimit(request, env);
    if (!rateLimitCheck.allowed) {
      return new Response(JSON.stringify({
        error: 'Rate limit exceeded',
        retryAfter: rateLimitCheck.retryAfter,
      }), {
        status: 429,
        headers: {
          ...corsHeaders,
          'Retry-After': String(rateLimitCheck.retryAfter),
          'Content-Type': 'application/json',
        },
      });
    }

    // Route requests
    try {
      if (path.startsWith('/api/v1/')) {
        return await handleApiV1(request, env, path, corsHeaders);
      }
      if (path.startsWith('/api/webhooks/')) {
        return await handleWebhook(request, env, path, corsHeaders);
      }
      if (path.startsWith('/api/auth/')) {
        return await handleAuth(request, env, path, corsHeaders);
      }
      if (path.startsWith('/api/llm/')) {
        return await handleLlmRoute(request, env, path, corsHeaders);
      }

      return new Response('Not Found', { status: 404 });
    } catch (error) {
      console.error('API Gateway Error:', error);
      // Capture error in Sentry
      captureException(error as Error, {
        path,
        method,
        user_agent: request.headers.get('User-Agent') || 'unknown',
        ip: request.headers.get('CF-Connecting-IP') || 'unknown',
      }).catch(() => {}); // Fail silently if Sentry unavailable
      await logAudit(env, {
        path,
        method,
        status: 500,
        error: String(error),
        timestamp: new Date().toISOString(),
      });
      return new Response(JSON.stringify({ error: 'Internal server error' }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }
  },
};

async function handleHealth(request: Request, env: Env): Promise<Response> {
  const services = {
    'rate-limit-kv': env.RATE_LIMIT_KV ? 'connected' : 'disabled',
    'cache-kv': env.CACHE_KV ? 'connected' : 'disabled',
    'sessions-db': env.SESSIONS_DB ? 'connected' : 'disabled',
    'audit-db': env.AUDIT_DB ? 'connected' : 'disabled',
    'ai-binding': env.AI ? 'connected' : 'disabled',
  };

  return Response.json({
    status: 'healthy',
    service: 'mekong-api-gateway',
    environment: env.ENVIRONMENT,
    timestamp: new Date().toISOString(),
    version: '6.0.0',
    services,
    uptime: Math.floor(performance.now() / 1000),
  });
}

async function checkRateLimit(request: Request, env: Env): Promise<RateLimitInfo & { allowed: boolean }> {
  const clientIp = request.headers.get('CF-Connecting-IP') || 'unknown';
  const key = `rate-limit:${clientIp}`;
  const now = Math.floor(Date.now() / 1000);
  const windowSize = 60; // 60 seconds
  const maxRequests = 100; // 100 requests per minute

  try {
    const data = await env.RATE_LIMIT_KV.get(key, 'json');
    if (!data) {
      await env.RATE_LIMIT_KV.put(key, JSON.stringify({ requests: 1, reset: now + windowSize }), {
        expirationTtl: windowSize,
      });
      return { allowed: true, requests: 1, reset: now + windowSize };
    }

    if (now > data.reset) {
      // Reset window
      await env.RATE_LIMIT_KV.put(key, JSON.stringify({ requests: 1, reset: now + windowSize }), {
        expirationTtl: windowSize,
      });
      return { allowed: true, requests: 1, reset: now + windowSize };
    }

    if (data.requests >= maxRequests) {
      return { allowed: false, requests: data.requests, reset: data.reset };
    }

    data.requests++;
    await env.RATE_LIMIT_KV.put(key, JSON.stringify(data), { expirationTtl: data.reset - now });
    return { allowed: true, requests: data.requests, reset: data.reset };
  } catch (error) {
    // If KV fails, allow the request (fail open)
    console.warn('Rate limit check failed:', error);
    return { allowed: true, requests: 0, reset: now };
  }
}

async function handleApiV1(
  request: Request,
  env: Env,
  path: string,
  corsHeaders: Record<string, string>
): Promise<Response> {
  // Proxy to backend API
  const backendPath = path.replace(/^\/api\/v1/, '');
  const backendUrl = `${env.BACKEND_API_URL}${backendPath}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout

  try {
    const response = await fetch(backendUrl, {
      method: request.method,
      headers: {
        ...Object.fromEntries(request.headers.entries()),
        'Host': new URL(env.BACKEND_API_URL).host,
      },
      body: request.body,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    const headers: Record<string, string> = { ...corsHeaders };
    response.headers.forEach((value, key) => {
      if (!key.toLowerCase().startsWith('set-cookie')) {
        headers[key] = value;
      }
    });

    // Log the request
    await logAudit(env, {
      path,
      method: request.method,
      status: response.status,
      timestamp: new Date().toISOString(),
    });

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      return new Response(JSON.stringify({ error: 'Request timeout' }), {
        status: 504,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }
    throw error;
  }
}

async function handleWebhook(
  request: Request,
  env: Env,
  path: string,
  corsHeaders: Record<string, string>
): Promise<Response> {
  const body = await request.text();
  const signature = request.headers.get('X-Webhook-Signature') || '';

  // Verify webhook signature
  const expectedSignature = crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(env.WEBHOOK_SECRET),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign', 'verify']
  ).then(key => crypto.subtle.verify('HMAC', key, new TextEncoder().encode(body), hexToArray(signature)));

  const isValid = await expectedSignature;
  if (!isValid) {
    return new Response(JSON.stringify({ error: 'Invalid signature' }), {
      status: 401,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }

  // Parse webhook payload
  const payload = JSON.parse(body);

  // Route webhook based on type
  if (payload.type === 'payment.succeeded') {
    await handlePaymentWebhook(env, payload);
  } else if (payload.type === 'user.created') {
    await handleUserWebhook(env, payload);
  }

  return Response.json({ received: true });
}

async function handleAuth(
  request: Request,
  env: Env,
  path: string,
  corsHeaders: Record<string, string>
): Promise<Response> {
  const body = await request.json();

  if (path === '/api/auth/session') {
    // Create or validate session
    const sessionId = crypto.randomUUID();
    const sessionData = {
      sessionId,
      createdAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days
      ...body,
    };

    await env.SESSIONS_DB.prepare(
      'INSERT OR REPLACE INTO sessions (id, data, created_at, expires_at) VALUES (?, ?, ?, ?)'
    ).bind(
      sessionId,
      JSON.stringify(sessionData),
      sessionData.createdAt,
      sessionData.expiresAt
    ).run();

    return Response.json({ sessionId, ...sessionData });
  }

  return new Response('Not Found', { status: 404 });
}

async function handleLlmRoute(
  request: Request,
  env: Env,
  path: string,
  corsHeaders: Record<string, string>
): Promise<Response> {
  const body = await request.json();

  try {
    const response = await env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
      messages: body.messages || [],
      max_tokens: body.max_tokens || 1024,
      temperature: body.temperature || 0.7,
    });

    return Response.json({
      choices: [{ message: { content: response } }],
      model: '@cf/meta/llama-3.1-8b-instruct',
      usage: { prompt_tokens: 0, completion_tokens: 0 },
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'LLM request failed' }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
}

async function handlePaymentWebhook(env: Env, payload: any): Promise<void> {
  // Store payment event in audit DB
  await env.AUDIT_DB.prepare(
    'INSERT INTO payment_events (id, user_id, amount, currency, status, raw_payload, received_at) VALUES (?, ?, ?, ?, ?, ?, ?)'
  ).bind(
    crypto.randomUUID(),
    payload.data?.object?.metadata?.userId || 'unknown',
    payload.data?.object?.amount || 0,
    payload.data?.object?.currency || 'usd',
    payload.data?.object?.status || 'unknown',
    JSON.stringify(payload),
    new Date().toISOString()
  ).run();
}

async function handleUserWebhook(env: Env, payload: any): Promise<void> {
  // Store user creation event
  await env.AUDIT_DB.prepare(
    'INSERT INTO user_events (id, user_id, email, event_type, raw_payload, received_at) VALUES (?, ?, ?, ?, ?, ?)'
  ).bind(
    crypto.randomUUID(),
    payload.data?.id || 'unknown',
    payload.data?.email || '',
    'user.created',
    JSON.stringify(payload),
    new Date().toISOString()
  ).run();
}

async function logAudit(env: Env, data: any): Promise<void> {
  if (!env.AUDIT_DB) return;

  try {
    await env.AUDIT_DB.prepare(
      'INSERT INTO request_logs (id, path, method, status, timestamp, user_agent, ip) VALUES (?, ?, ?, ?, ?, ?, ?)'
    ).bind(
      crypto.randomUUID(),
      data.path,
      data.method,
      data.status,
      data.timestamp,
      'worker', // Would need to extract from request if needed
      'cf-edge' // Cloudflare edge IP
    ).run();
  } catch (error) {
    console.warn('Failed to log audit:', error);
  }
}

function hexToArray(hex: string): Uint8Array {
  const arr = new Uint8Array(hex.length / 2);
  for (let i = 0; i < arr.length; i++) {
    arr[i] = parseInt(hex.substr(i * 2, 2), 16);
  }
  return arr;
}
