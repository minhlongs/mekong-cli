/**
 * RaaS HTTP Server — lightweight API on port 9090
 * Wires existing pure function handlers to HTTP endpoints.
 */
import { createServer } from 'node:http';
import { handleValidate, handleGetBalance, handleRegisterTenant, handleGetUsage, handleListTiers } from './raas-api.js';
import { handleOnboardTenant, validateApiKey, type OnboardingRequest } from './raas-onboarding.js';
import { executeBillableCommand, getUsageAnalytics } from './raas-billing.js';

const PORT = parseInt(process.env.RAAS_PORT ?? '9090');

async function parseBody(req: import('node:http').IncomingMessage): Promise<Record<string, unknown>> {
  return new Promise((resolve) => {
    let body = '';
    req.on('data', (chunk: Buffer) => { body += chunk.toString(); });
    req.on('end', () => {
      try { resolve(JSON.parse(body)); }
      catch { resolve({}); }
    });
  });
}

function json(res: import('node:http').ServerResponse, status: number, data: unknown) {
  res.writeHead(status, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
  res.end(JSON.stringify(data));
}

function getApiKey(req: import('node:http').IncomingMessage): string | null {
  const auth = req.headers['authorization'] ?? '';
  return auth.startsWith('Bearer ') ? auth.slice(7) : null;
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url ?? '/', `http://localhost:${PORT}`);
  const path = url.pathname;
  const method = req.method ?? 'GET';

  if (method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    });
    res.end();
    return;
  }

  if (path === '/health') { json(res, 200, { ok: true, service: 'mekong-raas', version: '1.0.0' }); return; }
  if (path === '/raas/tiers') { json(res, 200, handleListTiers()); return; }

  if (path === '/raas/onboard' && method === 'POST') {
    const body = await parseBody(req);
    json(res, 201, handleOnboardTenant(body as unknown as OnboardingRequest));
    return;
  }

  const apiKey = getApiKey(req);
  if (!apiKey) { json(res, 401, { ok: false, error: 'Missing Bearer token' }); return; }

  const validation = validateApiKey(apiKey);
  if (!validation.ok) { json(res, validation.status, validation); return; }
  const tenantId = validation.data!.tenantId;

  if (path === '/raas/balance') { json(res, 200, handleGetBalance(tenantId)); return; }
  if (path === '/raas/usage') { json(res, 200, getUsageAnalytics(tenantId)); return; }

  if (path === '/raas/execute' && method === 'POST') {
    const body = await parseBody(req);
    const result = executeBillableCommand(tenantId, (body.command as string) ?? '', (body.credits as number) ?? 2, 0);
    json(res, result.status, result);
    return;
  }

  json(res, 404, { ok: false, error: 'Not found' });
});

server.listen(PORT, () => console.log(`RaaS server listening on :${PORT}`));
