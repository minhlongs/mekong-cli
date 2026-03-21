/**
 * Developer Portal - public HTML page
 */
import { Hono } from 'hono';
import type { Env } from '../index';

export const developerPortal = new Hono<{ Bindings: Env }>();

developerPortal.get('/developers', (c) => {
  return c.html(`<!DOCTYPE html><html><head><title>Mekong RaaS Developer Portal</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:system-ui;background:#0a0a0a;color:#e5e5e5;line-height:1.6;max-width:800px;margin:0 auto;padding:2rem 1rem}h1{color:#22d3ee;font-size:2rem}h2{color:#22d3ee;font-size:1.3rem;margin:2rem 0 .75rem;border-bottom:1px solid #222;padding-bottom:.5rem}p{margin:.5rem 0;color:#94a3b8}a{color:#22d3ee}pre{background:#111;border:1px solid #222;border-radius:8px;padding:1rem;overflow-x:auto;font-size:.85rem;margin:.75rem 0}.g{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem;margin:1rem 0}.d{background:#111;border:1px solid #222;border-radius:8px;padding:1rem}.d h3{color:#e5e5e5;margin:0 0 .5rem}.n{display:flex;gap:1rem;flex-wrap:wrap;margin:1rem 0}.n a{background:#111;border:1px solid #333;padding:.5rem 1rem;border-radius:6px;font-size:.85rem}.b{display:inline-block;background:#22d3ee20;color:#22d3ee;padding:2px 8px;border-radius:4px;font-size:.75rem}</style></head><body>
<h1>Mekong RaaS</h1><p style="color:#64748b">Developer Portal</p>
<div class="n"><a href="/playground">Playground</a><a href="/docs">API Ref</a><a href="/sdk/endpoints">SDKs</a><a href="/status">Status</a><a href="/changelog">Changelog</a></div>
<h2 id="getting-started">Getting Started</h2>
<pre>curl -X POST /v1/tenants/signup -H "Content-Type: application/json" -d '{"name":"My Co","email":"dev@example.com"}'</pre>
<pre>curl -X POST /v1/missions -H "Authorization: Bearer TOKEN" -d '{"goal":"Write blog post"}'</pre>
<h2>Auth</h2><p><span class="b">Bearer</span> JWT from signup | <span class="b">API Key</span> X-API-Key header</p>
<h2>SDKs</h2><div class="g"><div class="d"><h3>JavaScript</h3><a href="/sdk/javascript">Get</a></div><div class="d"><h3>Python</h3><a href="/sdk/python">Get</a></div></div>
<h2>Rate Limits</h2><div class="g"><div class="d"><h3>Free</h3><p>10/min</p></div><div class="d"><h3>Pro</h3><p>60/min</p></div><div class="d"><h3>Enterprise</h3><p>Custom</p></div></div>
<p style="margin-top:2rem;color:#475569;font-size:.8rem">Built with Mekong CLI v5.0</p></body></html>`);
});

developerPortal.get('/developers/quickstart', (c) => c.redirect('/developers#getting-started'));
