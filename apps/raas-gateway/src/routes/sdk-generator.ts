/**
 * SDK Generator routes — public, no auth required
 * GET /sdk/endpoints      — list all documented API endpoints
 * GET /sdk/snippet        — generate a single code snippet
 * GET /sdk/:language      — generate a full client SDK (javascript | python)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { SdkGeneratorService, type Language } from '../services/sdk-generator-service';

export const sdkGenerator = new Hono<{ Bindings: Env }>();

const SUPPORTED_LANGUAGES: Language[] = ['curl', 'javascript', 'python', 'go', 'ruby'];
const FULL_SDK_LANGUAGES = ['javascript', 'python'] as const;

/** GET /sdk/endpoints — list all documented API endpoints */
sdkGenerator.get('/endpoints', (c) => {
  const svc = new SdkGeneratorService();
  return c.json({ success: true, data: svc.getEndpointList() });
});

/**
 * GET /sdk/snippet — generate a code snippet
 * Query params: language, endpoint, method, api_key (optional)
 */
sdkGenerator.get('/snippet', (c) => {
  const language = c.req.query('language') as Language | undefined;
  const endpoint = c.req.query('endpoint');
  const method   = c.req.query('method') ?? 'GET';
  const apiKey   = c.req.query('api_key');

  if (!language) {
    return c.json(
      { success: false, error: `Missing required query param: language. Supported: ${SUPPORTED_LANGUAGES.join(', ')}` },
      400,
    );
  }
  if (!SUPPORTED_LANGUAGES.includes(language)) {
    return c.json(
      { success: false, error: `Unsupported language "${language}". Supported: ${SUPPORTED_LANGUAGES.join(', ')}` },
      400,
    );
  }
  if (!endpoint) {
    return c.json({ success: false, error: 'Missing required query param: endpoint' }, 400);
  }

  try {
    const svc = new SdkGeneratorService();
    const snippet = svc.generateSnippet({ language, endpoint, method, apiKey });
    return c.json({ success: true, data: { language, endpoint, method, snippet } });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return c.json({ success: false, error: message }, 400);
  }
});

/**
 * GET /sdk/:language — generate a complete SDK client
 * Supports: javascript, python
 */
sdkGenerator.get('/:language', (c) => {
  const language = c.req.param('language') as (typeof FULL_SDK_LANGUAGES)[number];

  if (!(FULL_SDK_LANGUAGES as readonly string[]).includes(language)) {
    return c.json(
      { success: false, error: `Full SDK only available for: ${FULL_SDK_LANGUAGES.join(', ')}` },
      400,
    );
  }

  const svc = new SdkGeneratorService();
  const code = svc.generateFullSDK(language);
  return c.json({ success: true, data: { language, code } });
});
