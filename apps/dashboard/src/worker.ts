/**
 * Mekong Dashboard - Edge API Worker
 *
 * This worker provides edge-located API endpoints for:
 * - Health checks
 * - Rate limiting
 * - Request routing to backend
 * - Authentication middleware
 * - Caching layer
 * - Error tracking with Sentry
 *
 * Deploy with: npx wrangler deploy
 */

import { initSentry, captureException, addBreadcrumb } from '@mekong/observability';

// Initialize Sentry error tracking (async, non-blocking)
initSentry().catch(console.error);

export interface Env {
  // KV namespace for caching
  // CACHE: KVNamespace;

  // D1 database for session storage
  // DB: D1Database;

  // Environment configuration
  ENVIRONMENT: string;
  API_BACKEND_URL: string;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': process.env.NEXT_PUBLIC_SUPABASE_URL || '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
      'Access-Control-Max-Age': '86400',
    };

    // Handle preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Health check endpoint
    if (path === '/health' || path === '/api/health') {
      return Response.json({
        status: 'healthy',
        service: 'mekong-dashboard-api',
        environment: env.ENVIRONMENT,
        timestamp: new Date().toISOString(),
        version: '6.0.0',
      });
    }

    // API proxy - forward requests to backend
    if (path.startsWith('/api/') && env.API_BACKEND_URL) {
      return handleApiProxy(request, env, path, corsHeaders);
    }

    // Dashboard static file serving fallback
    if (path.endsWith('.html') || path.endsWith('.css') || path.endsWith('.js')) {
      return handleStaticFiles(request, path);
    }

    // Default: redirect to dashboard or return 404
    return new Response('Not Found', { status: 404 });
  },
};

async function handleApiProxy(
  request: Request,
  env: Env,
  path: string,
  corsHeaders: Record<string, string>
): Promise<Response> {
  try {
    const backendUrl = `${env.API_BACKEND_URL}${path}`;
    const response = await fetch(backendUrl, {
      method: request.method,
      headers: {
        ...Object.fromEntries(request.headers.entries()),
        'Host': new URL(env.API_BACKEND_URL).host,
      },
      body: request.body,
    });

    const headers: Record<string, string> = { ...corsHeaders };
    response.headers.forEach((value, key) => {
      if (!key.toLowerCase().startsWith('set-cookie')) {
        headers[key] = value;
      }
    });

    // Add breadcrumb for successful proxy
    addBreadcrumb('api', `Proxy success: ${path}`, 'info', {
      status: response.status,
      backend_url: backendUrl,
    }).catch(() => {});

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  } catch (error) {
    // Capture error in Sentry
    captureException(error as Error, {
      path,
      backend_url: env.API_BACKEND_URL,
      user_agent: request.headers.get('User-Agent') || 'unknown',
      ip: request.headers.get('CF-Connecting-IP') || 'unknown',
    }).catch(() => {}); // Fail silently if Sentry unavailable

    addBreadcrumb('api', `Proxy error: ${path}`, 'error', {
      error: String(error),
      backend_url: env.API_BACKEND_URL,
    }).catch(() => {});

    return new Response(JSON.stringify({ error: 'API proxy error' }), {
      status: 502,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
}

async function handleStaticFiles(request: Request, path: string): Promise<Response> {
  // In production, Cloudflare Pages handles static files
  // This is a fallback for Workers-only deployments
  return new Response('Dashboard static files - serve via Cloudflare Pages', {
    status: 200,
    headers: { 'Content-Type': 'text/plain' },
  });
}
