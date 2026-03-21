/**
 * Playground routes — interactive API explorer HTML page
 */

import { Hono } from 'hono';
import type { Env } from '../index';

export const playground = new Hono<{ Bindings: Env }>();

/**
 * GET /playground — Returns interactive API explorer HTML page
 * No auth required — uses client-side token input
 */
playground.get('/playground', (c) => {
  return c.html(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mekong RaaS API Playground</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }
    .container { max-width: 960px; margin: 0 auto; padding: 24px; }
    h1 { color: #06b6d4; margin-bottom: 8px; }
    .subtitle { color: #94a3b8; margin-bottom: 24px; }
    .card { background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 16px; border: 1px solid #334155; }
    label { display: block; color: #94a3b8; font-size: 13px; margin-bottom: 4px; }
    input, select, textarea { width: 100%; padding: 10px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; color: #e2e8f0; font-family: monospace; font-size: 14px; margin-bottom: 12px; }
    textarea { min-height: 80px; resize: vertical; }
    button { background: #06b6d4; color: #0f172a; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 700; cursor: pointer; font-size: 14px; }
    button:hover { background: #22d3ee; }
    .row { display: flex; gap: 12px; }
    .row > * { flex: 1; }
    pre { background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 16px; overflow-x: auto; font-size: 13px; max-height: 400px; overflow-y: auto; white-space: pre-wrap; }
    .status { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
    .s2xx { background: #065f46; color: #6ee7b7; }
    .s4xx { background: #7c2d12; color: #fdba74; }
    .s5xx { background: #7f1d1d; color: #fca5a5; }
    .endpoints { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 8px; margin-bottom: 16px; }
    .ep { padding: 8px 12px; background: #0f172a; border: 1px solid #334155; border-radius: 6px; cursor: pointer; font-size: 13px; transition: border-color 0.2s; }
    .ep:hover { border-color: #06b6d4; }
    .ep .method { font-weight: 700; font-size: 11px; }
    .ep .method.GET { color: #22d3ee; }
    .ep .method.POST { color: #a78bfa; }
    .ep .method.PUT { color: #fbbf24; }
    .ep .method.DELETE { color: #f87171; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Mekong RaaS API Playground</h1>
    <p class="subtitle">Interactive API explorer — test endpoints directly</p>
    <div class="card">
      <label>API Key or JWT Token</label>
      <input type="password" id="auth" placeholder="Enter API key or JWT token">
      <div class="row">
        <div><label>Method</label><select id="method"><option>GET</option><option>POST</option><option>PUT</option><option>DELETE</option></select></div>
        <div style="flex:3"><label>Path</label><input id="path" value="/health" placeholder="/v1/missions"></div>
      </div>
      <label>Request Body (JSON)</label>
      <textarea id="body" placeholder='{"goal": "Write a blog post"}'></textarea>
      <button onclick="send()">Send Request</button>
    </div>
    <div class="card">
      <label>Quick Endpoints</label>
      <div class="endpoints" id="endpoints"></div>
    </div>
    <div class="card" id="result" style="display:none">
      <label>Response <span id="status" class="status"></span> <span id="time" style="color:#64748b;font-size:12px"></span></label>
      <pre id="response"></pre>
    </div>
  </div>
  <script>
    const eps = [
      ['GET', '/health'], ['GET', '/v1/status/public'],
      ['GET', '/v1/missions'], ['POST', '/v1/missions'],
      ['GET', '/v1/credits/balance'], ['GET', '/v1/credits/history'],
      ['GET', '/v1/billing/pricing'], ['GET', '/v1/templates'],
      ['GET', '/v1/marketplace'], ['GET', '/v1/dashboard'],
      ['GET', '/v1/onboarding/progress'], ['GET', '/v1/tenants/profile'],
      ['GET', '/v1/analytics'], ['GET', '/v1/webhooks/delivery-logs'],
    ];
    const epEl = document.getElementById('endpoints');
    eps.forEach(([m, p]) => {
      const d = document.createElement('div');
      d.className = 'ep';
      d.innerHTML = '<span class="method ' + m + '">' + m + '</span> ' + p;
      d.onclick = () => { document.getElementById('method').value = m; document.getElementById('path').value = p; };
      epEl.appendChild(d);
    });
    async function send() {
      const auth = document.getElementById('auth').value;
      const method = document.getElementById('method').value;
      const path = document.getElementById('path').value;
      const body = document.getElementById('body').value;
      const headers = { 'Content-Type': 'application/json' };
      if (auth) { if (auth.startsWith('ey')) headers['Authorization'] = 'Bearer ' + auth; else headers['X-API-Key'] = auth; }
      const t0 = performance.now();
      try {
        const opts = { method, headers };
        if (method !== 'GET' && body) opts.body = body;
        const res = await fetch(location.origin + path, opts);
        const ms = Math.round(performance.now() - t0);
        const text = await res.text();
        let formatted; try { formatted = JSON.stringify(JSON.parse(text), null, 2); } catch { formatted = text; }
        document.getElementById('result').style.display = 'block';
        const s = document.getElementById('status');
        s.textContent = res.status + ' ' + res.statusText;
        s.className = 'status s' + (res.status < 300 ? '2' : res.status < 500 ? '4' : '5') + 'xx';
        document.getElementById('time').textContent = ms + 'ms';
        document.getElementById('response').textContent = formatted;
      } catch (e) {
        document.getElementById('result').style.display = 'block';
        document.getElementById('status').textContent = 'Error';
        document.getElementById('status').className = 'status s5xx';
        document.getElementById('response').textContent = e.message;
      }
    }
  </script>
</body>
</html>`);
});
