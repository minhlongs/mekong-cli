/**
 * Stripe Checkout routes — fallback payment for international customers
 * Uses fetch() directly, no SDK dependency
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';

export const stripe = new Hono<{ Bindings: Env }>();

// Credit pack definitions — mirrors /billing/pricing credit_packs
const CREDIT_PACKS = [
  { id: 'credits-10', credits: 10, priceInCents: 500, name: '10 MCU Credits' },
  { id: 'credits-50', credits: 50, priceInCents: 2000, name: '50 MCU Credits' },
  { id: 'credits-100', credits: 100, priceInCents: 3500, name: '100 MCU Credits' },
  { id: 'credits-500', credits: 500, priceInCents: 15000, name: '500 MCU Credits' },
];

/**
 * GET /billing/stripe/packs — List available credit packs with prices
 */
stripe.get('/packs', (c) => {
  return json({ packs: CREDIT_PACKS });
});

/**
 * POST /billing/stripe/checkout — Create Stripe Checkout Session
 * Requires auth — tenant context populated by auth middleware
 */
stripe.post('/checkout', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  const packId = body.packId;
  const pack = CREDIT_PACKS.find(p => p.id === packId);

  if (!pack) {
    return json(
      { error: 'Invalid pack ID', available: CREDIT_PACKS.map(p => p.id) },
      { status: 400 }
    );
  }

  const stripeKey = c.env.STRIPE_SECRET_KEY;
  if (!stripeKey) {
    return json({ error: 'Stripe not configured' }, { status: 503 });
  }

  // Build Checkout Session params (no SDK, raw URLSearchParams)
  const params = new URLSearchParams({
    'mode': 'payment',
    'success_url': 'https://app.agencyos.network/dashboard?payment=success',
    'cancel_url': 'https://app.agencyos.network/dashboard?payment=cancelled',
    'line_items[0][price_data][currency]': 'usd',
    'line_items[0][price_data][unit_amount]': pack.priceInCents.toString(),
    'line_items[0][price_data][product_data][name]': pack.name,
    'line_items[0][quantity]': '1',
    'metadata[tenant_id]': tenant.tenantId,
    'metadata[pack_id]': pack.id,
    'metadata[credits]': pack.credits.toString(),
    'client_reference_id': tenant.tenantId,
  });

  const res = await fetch('https://api.stripe.com/v1/checkout/sessions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${stripeKey}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: params.toString(),
  });

  const session = await res.json() as any;
  if (!res.ok) {
    return json(
      { error: 'Failed to create checkout', detail: session.error?.message },
      { status: 502 }
    );
  }

  return json({ checkoutUrl: session.url, sessionId: session.id });
});

/**
 * POST /billing/stripe/webhook — Handle Stripe webhook events
 * PUBLIC endpoint — no auth middleware
 * Verifies HMAC-SHA256 signature, then adds credits atomically on checkout.session.completed
 */
stripe.post('/webhook', async (c) => {
  const stripeWebhookSecret = c.env.STRIPE_WEBHOOK_SECRET;
  const signature = c.req.header('stripe-signature') || '';
  const payload = await c.req.text();

  // Verify webhook signature if secret is configured
  if (stripeWebhookSecret && signature) {
    const parts = signature.split(',').reduce((acc: Record<string, string>, part) => {
      const [k, v] = part.split('=');
      if (k && v) acc[k] = v;
      return acc;
    }, {});

    const timestamp = parts['t'];
    const sig = parts['v1'];

    if (timestamp && sig) {
      const signedPayload = `${timestamp}.${payload}`;
      const key = await crypto.subtle.importKey(
        'raw',
        new TextEncoder().encode(stripeWebhookSecret),
        { name: 'HMAC', hash: 'SHA-256' },
        false,
        ['sign']
      );
      const expected = await crypto.subtle.sign(
        'HMAC', key, new TextEncoder().encode(signedPayload)
      );
      const expectedHex = Array.from(new Uint8Array(expected))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');

      if (expectedHex !== sig) {
        return json({ error: 'Invalid signature' }, { status: 401 });
      }
    }
  }

  let event: any;
  try {
    event = JSON.parse(payload);
  } catch {
    return json({ error: 'Invalid JSON payload' }, { status: 400 });
  }

  // Only handle checkout completion
  if (event.type === 'checkout.session.completed') {
    const session = event.data?.object;
    const tenantId = session?.metadata?.tenant_id || session?.client_reference_id;
    const credits = parseInt(session?.metadata?.credits || '0', 10);

    if (tenantId && credits > 0) {
      // Add credits atomically
      await c.env.DB.prepare(
        'UPDATE tenants SET balance = balance + ?, total_earned = total_earned + ? WHERE id = ?'
      ).bind(credits, credits, tenantId).run();

      // Record transaction for audit trail
      await c.env.DB.prepare(
        `INSERT INTO credit_transactions (id, tenant_id, amount, type, description, metadata, created_at)
         VALUES (?, ?, ?, 'purchase', ?, ?, datetime('now'))`
      ).bind(
        crypto.randomUUID(),
        tenantId,
        credits,
        `Stripe purchase: ${session?.metadata?.pack_id}`,
        JSON.stringify({
          provider: 'stripe',
          sessionId: session?.id,
          packId: session?.metadata?.pack_id,
        })
      ).run();
    }
  }

  return json({ received: true });
});
