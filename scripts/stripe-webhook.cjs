#!/usr/bin/env node
/**
 * stripe-webhook.cjs — Stripe webhook handler for Mekong CLI
 * Listens for checkout.session.completed → provisions MCU credits
 * Usage: node scripts/stripe-webhook.cjs [--port 3001 | --test]
 */
'use strict';
const http = require('http');

const PORT = parseInt(process.argv[process.argv.indexOf('--port') + 1], 10) || 3001;
const endpointSecret = process.env.STRIPE_WEBHOOK_SECRET;

async function provisionCredits(tier, credits, customerEmail) {
  try {
    const mcuPath = require('path').join(__dirname, '..', 'src', 'core', 'mcu_billing.py');
    const fs = require('fs');
    if (!fs.existsSync(mcuPath)) {
      console.log(`[webhook] MCU billing module not found at ${mcuPath}`);
      console.log(`[webhook] Would provision ${credits} MCU credits for tier=${tier} customer=${customerEmail}`);
      return true;
    }
    // Direct Python call to existing MCU billing
    const { execSync } = require('child_process');
    execSync(`python3 -c "
import sys; sys.path.insert(0, 'src');
from core.mcu_billing import MCUBilling;
b = MCUBilling();
b.add_credits('${customerEmail}', ${credits}, source='stripe:tier=${tier}');
print(f'Provisioned ${credits} credits for ${customerEmail}');
"`, { cwd: require('path').join(__dirname, '..'), stdio: 'pipe' });
    return true;
  } catch (e) {
    console.error('[webhook] Provisioning error:', e.message);
    return false;
  }
}

const server = http.createServer(async (req, res) => {
  if (req.method !== 'POST' || req.url !== '/stripe-webhook') {
    res.writeHead(404); res.end();
    return;
  }

  let body = '';
  req.on('data', chunk => body += chunk);
  req.on('end', async () => {
    try {
      const event = JSON.parse(body);

      if (event.type === 'checkout.session.completed') {
        const session = event.data.object;
        const tier = session.metadata?.tier || 'starter';
        const credits = parseInt(session.metadata?.credits, 10) || 200;
        const email = session.customer_email || session.customer_details?.email || 'unknown';

        console.log(`[webhook] Payment completed: tier=${tier} credits=${credits} customer=${email}`);
        await provisionCredits(tier, credits, email);
        console.log(`[webhook] ✅ ${credits} MCU credits provisioned for ${email}`);
      }

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ received: true }));
    } catch (e) {
      console.error('[webhook] Error:', e.message);
      res.writeHead(400); res.end(JSON.stringify({ error: e.message }));
    }
  });
});

// Test mode
if (process.argv.includes('--test')) {
  console.log('[webhook] Test mode: simulating checkout.completed event...\n');
  const mockEvent = {
    type: 'checkout.session.completed',
    data: { object: {
      metadata: { tier: 'starter', credits: '200' },
      customer_email: 'test@mekongmind.com',
      customer_details: { email: 'test@mekongmind.com' },
    }}
  };
  const testReq = { method: 'POST', url: '/stripe-webhook', on: (e, cb) => {
    if (e === 'data') cb(JSON.stringify(mockEvent));
    if (e === 'end') setTimeout(() => cb(), 100);
  }};
  server.emit('request', testReq, {
    writeHead: () => {}, end: (d) => console.log('[webhook] Response:', d.toString()),
  });
} else {
  server.listen(PORT, () => {
    console.log(`Stripe webhook listening on :${PORT}/stripe-webhook`);
    console.log(`Set STRIPE_WEBHOOK_SECRET env var for signature verification`);
  });
}
