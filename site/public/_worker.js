/**
 * site/public/_worker.js — Cloudflare Pages Advanced Mode Edge Worker API
 * Intercepts /api/v1/* requests and serves explicitly synthetic demo responses.
 * Non-API routes are delegated directly to env.ASSETS.fetch(request).
 */

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
  'Content-Type': 'application/json; charset=utf-8'
};

const ALL_20_SCREENS = [
  { href: "index.html", title: "01 Landing — Hero & Open-Core Overview", group: "Core", stitch_id: "87ad4560e1ca44a0a45d2e09cb436d3a" },
  { href: "pricing.html", title: "02 Pricing — Transparent Pricing Matrix", group: "Core", stitch_id: "5bb5af1c510642249d80437147ab92c8" },
  { href: "cockpit.html", title: "03 Cockpit — Desktop Agent Swarm Topology", group: "Operations", stitch_id: "f496e91c170a4ade8dc8284d0ec5b1c0" },
  { href: "billing.html", title: "04 Billing — Cloud Control Plane & MCU Meter", group: "Operations", stitch_id: "be5b9d1d081148e8b661653bc542199c" },
  { href: "audit.html", title: "05 Audit — Immutable SHA-256 Compliance Ledger", group: "Compliance", stitch_id: "d47c7bedd4ab4081b22b5dd7355829b1" },
  { href: "marketplace.html", title: "06 Marketplace — Strategy Recipe Creator Hub", group: "Recipes", stitch_id: "e4066339f9fe4c76a74dd7f4cb4d2237" },
  { href: "settings.html", title: "07 Settings — Enterprise Multi-Tenant & Vault", group: "Operations", stitch_id: "f3173dda4bca469e8461afaad763f0df" },
  { href: "styleguide.html", title: "08 Styleguide — Component Style Guide Catalog", group: "Design", stitch_id: "dabed64cfa4a45b2b013780d15358ebc" },
  { href: "docs.html", title: "09 Docs — Developer CLI & SDK Reference", group: "Core", stitch_id: "db0ead813f6344fba5505734fa02e65e" },
  { href: "playground.html", title: "10 Playground — WebAssembly CLI Sandbox", group: "Developer", stitch_id: "26c7a8a9498340958f5f8cf11d1305c2" },
  { href: "invoice-verifier.html", title: "11 Invoice Verifier — TT78 / NĐ 123 Inspector", group: "Compliance", stitch_id: "af7fe94874ad4dcb85ca58bd3c07407c" },
  { href: "swarm-monitor.html", title: "12 Swarm Monitor — Distributed WebSocket Stream", group: "Operations", stitch_id: "dff59f17ccf74a35a4966815f2eb90f7" },
  { href: "status.html", title: "13 Status — Global Microservice SLA Dashboard", group: "Operations", stitch_id: "88b2469fde664b4bbc2cdb981392570d" },
  { href: "recipe-builder.html", title: "14 Recipe Builder — Visual Workflow Studio", group: "Recipes", stitch_id: "467f39c14d504611bf62eadbb25030c6" },
  { href: "zalo-oa-console.html", title: "15 Zalo OA — Engagement & Broadcast Console", group: "Integrations", stitch_id: "24a56db3ecb44983bba4e2379c26a63a" },
  { href: "agent-debugger.html", title: "16 Agent Debugger — Live DAG & Execution Visualizer", group: "Developer", stitch_id: "a199abedbe004fc0adaf30ff6d5fcd5a" },
  { href: "vietqr-webhook-tester.html", title: "17 VietQR Tester — Webhook Receiver Simulator", group: "Integrations", stitch_id: "7e9686a21d794569bf319f3ed141aa30" },
  { href: "compliance-vault.html", title: "18 Compliance Vault — SOC-2 & Merkle Proof Browser", group: "Compliance", stitch_id: "2058b0b534704dc493c5204814afcc4e" },
  { href: "c-suite-boardroom.html", title: "19 C-Suite Boardroom — Executive War Room & OKR Telemetry", group: "Executive", stitch_id: "7a7122ec87844012b62aa1f95ebd7916" },
  { href: "fintech-treasury.html", title: "20 Fintech Treasury — Multi-Bank VietQR & Cashflow Runway", group: "Fintech", stitch_id: "5bbdb79f45fd4d78bfa0eae01a768486" },
  { href: "zero-to-ipo-launchpad.html", title: "21 Zero-to-IPO Launchpad — Cap Table & SBV Compliance", group: "Executive", stitch_id: "e856db6b532e4facbd997edb6bada3c9" }
];

async function sha256Hex(str) {
  const enc = new TextEncoder();
  const digest = await crypto.subtle.digest('SHA-256', enc.encode(str));
  return Array.from(new Uint8Array(digest)).map(b => b.toString(16).padStart(2, '0')).join('');
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const pathname = url.pathname;

    // Handle CORS Preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        status: 204,
        headers: CORS_HEADERS
      });
    }

    // Intercept Edge API Routes (/api/v1/*)
    if (pathname.startsWith('/api/v1/')) {
      const endpoint = pathname.replace('/api/v1', '');

      // 1. /api/v1/status
      if (endpoint === '/status' || endpoint === '/status/') {
        const body = {
          status: 'demo',
          uptime_seconds: 0,
          version: '6.0.0-pro',
          mode: 'synthetic_demo',
          screens_count: 21,
          active_agents: 0,
          swarm_sync: 'NOT_CONNECTED',
          timestamp: Date.now() / 1000,
          demo_only: true
        };
        return new Response(JSON.stringify(body), { headers: CORS_HEADERS });
      }

      // 2. /api/v1/screens
      if (endpoint === '/screens' || endpoint === '/screens/') {
        return new Response(JSON.stringify({
          count: ALL_20_SCREENS.length,
          screens: ALL_20_SCREENS,
          source: 'synthetic_demo',
          demo_only: true
        }), { headers: CORS_HEADERS });
      }

      // 3. /api/v1/vietqr/simulate
      if (endpoint === '/vietqr/simulate' || endpoint === '/vietqr/simulate/') {
        if (request.method !== 'POST') {
          return new Response(JSON.stringify({ error: 'POST required', demo_only: true }), {
            status: 405,
            headers: CORS_HEADERS
          });
        }
        let reqData = {};
        if (request.method === 'POST') {
          try {
            reqData = await request.json();
          } catch {
            reqData = {};
          }
        }
        const requestedAmount = Number(reqData.amount);
        const amount = Number.isFinite(requestedAmount) && requestedAmount > 0
          ? Math.min(Math.floor(requestedAmount), 100000000)
          : 250000;
        const bankCode = typeof reqData.bank_code === 'string' ? reqData.bank_code.slice(0, 12) : 'VCB';
        const orderId = typeof reqData.order_id === 'string'
          ? reqData.order_id.slice(0, 64)
          : `DEMO-${Date.now().toString().slice(-6)}`;
        return new Response(JSON.stringify({
          success: true,
          simulated: true,
          demo_only: true,
          order_id: orderId,
          amount_vnd: amount,
          simulated_mcu: Math.floor(amount / 1000),
          bank_code: bankCode,
          verified: false,
          notice: 'Demo only. No payment, webhook verification, or MCU credit was performed.',
          timestamp: Date.now() / 1000,
          mode: 'demo_simulation'
        }), { headers: CORS_HEADERS });
      }

      // 4. /api/v1/tt78/verify
      if (endpoint === '/tt78/verify' || endpoint === '/tt78/verify/') {
        let reqData = {};
        if (request.method === 'POST') {
          try {
            reqData = await request.json();
          } catch {
            reqData = {};
          }
        }
        const invoiceId = reqData.invoice_id || 'INV-2026-009842';
        const sellerTaxId = reqData.seller_tax_id || '0312345678';
        const buyerTaxId = reqData.buyer_tax_id || '0109876543';
        const amountVnd = reqData.amount_vnd || 15400000;
        const vatRate = reqData.vat_rate || 10;
        const vatAmount = Math.round(amountVnd * (vatRate / 100));
        const total = amountVnd + vatAmount;

        const canonical = `${invoiceId}|${sellerTaxId}|${buyerTaxId}|${amountVnd}|${vatRate}|${total}`;
        const stampHash = await sha256Hex(canonical);

        return new Response(JSON.stringify({
          valid: false,
          demo_only: true,
          invoice_id: invoiceId,
          seller_tax_id: sellerTaxId,
          buyer_tax_id: buyerTaxId,
          amount_vnd: amountVnd,
          vat_amount: vatAmount,
          total_with_vat: total,
          vat_rate: vatRate,
          hash_payload: stampHash,
          canonical_string: canonical,
          digital_stamp: `DEMO-HASH-ONLY-${stampHash.substring(0, 16).toUpperCase()}`,
          standard: 'TT78/2021/TT-BTC & ND123/2020/ND-CP',
          mode: 'synthetic_demo',
          timestamp: Date.now() / 1000
        }), { headers: CORS_HEADERS });
      }

      // 5. /api/v1/c-suite/quorum
      if (endpoint === '/c-suite/quorum' || endpoint === '/c-suite/quorum/') {
        return new Response(JSON.stringify({
          demo_only: true,
          quorum_reached: false,
          required_approvals: 5,
          total_votes: 0,
          signoff_hash: '',
          signers: [],
          resolution: 'Demo only. No executive approvals were recorded.',
          mode: 'synthetic_demo',
          timestamp: Date.now() / 1000
        }), { headers: CORS_HEADERS });
      }

      // 6. /api/v1/audit/merkle
      if (endpoint === '/audit/merkle' || endpoint === '/audit/merkle/') {
        let reqData = {};
        if (request.method === 'POST') {
          try {
            reqData = await request.json();
          } catch {
            reqData = {};
          }
        }
        const records = Array.isArray(reqData.records) && reqData.records.length > 0
          ? reqData.records.slice(0, 256).map(record => String(record).slice(0, 1000))
          : [
              "demo_record:session_root_sample",
              "demo_record:invoice_hash_sample",
              "demo_record:payment_not_processed"
            ];

        const leaves = await Promise.all(records.map(r => sha256Hex(r)));
        let level = leaves;
        let depth = 0;
        while (level.length > 1) {
          const nextLevel = [];
          for (let index = 0; index < level.length; index += 2) {
            const left = level[index];
            const right = level[index + 1] || left;
            nextLevel.push(await sha256Hex(`${left}${right}`));
          }
          level = nextLevel;
          depth += 1;
        }
        const root = level[0];

        return new Response(JSON.stringify({
          demo_only: true,
          merkle_root: root,
          leaf_count: leaves.length,
          leaves,
          depth,
          verified: false,
          standard: 'NIST-FIPS-180-4',
          mode: 'synthetic_demo',
          timestamp: Date.now() / 1000
        }), { headers: CORS_HEADERS });
      }

      return new Response(JSON.stringify({ error: 'Endpoint not found', endpoint: pathname }), {
        status: 404,
        headers: CORS_HEADERS
      });
    }

    // Default: Delegate to Cloudflare Pages Static Assets
    return env.ASSETS.fetch(request);
  }
};
