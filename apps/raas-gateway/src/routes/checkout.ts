/**
 * Checkout routes — Polar.sh checkout session creation
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';

export const checkout = new Hono<{ Bindings: Env }>();

/**
 * Product catalog — first 8 chars of Polar product_id as key
 */
const PRODUCTS: Record<string, { name: string; tier: string; type: 'subscription' | 'credit_pack' }> = {
  'ce215739': { name: 'Starter', tier: 'starter', type: 'subscription' },
  'b810b7eb': { name: 'Pro', tier: 'pro', type: 'subscription' },
  '0e752654': { name: 'Agency', tier: 'agency', type: 'subscription' },
  'dc82a4bb': { name: 'Master', tier: 'master', type: 'subscription' },
};

/**
 * GET /billing/checkout/products — public product listing
 */
checkout.get('/products', (c) => {
  const products = Object.entries(PRODUCTS).map(([id, p]) => ({
    product_id: id,
    name: p.name,
    tier: p.tier,
    type: p.type,
  }));
  return json({ products });
});

/**
 * POST /billing/checkout — create Polar checkout session (authenticated)
 */
checkout.use('/', auth());

checkout.post('/', async (c) => {
  const tenant = getTenant(c);

  // Parse + validate body
  let body: { product_id?: string; success_url?: string; cancel_url?: string };
  try {
    body = await c.req.json();
  } catch {
    return json({ error: 'Invalid JSON body', code: 'INVALID_BODY' }, { status: 400 });
  }

  const { product_id } = body;
  if (!product_id) {
    return json({ error: 'product_id is required', code: 'MISSING_PRODUCT_ID' }, { status: 400 });
  }

  // Validate product exists (match by prefix)
  const prefix = product_id.slice(0, 8);
  const product = PRODUCTS[prefix];
  if (!product) {
    return json({ error: 'Unknown product_id', code: 'INVALID_PRODUCT' }, { status: 400 });
  }

  // Use full product_id as provided (or prefix if short)
  const fullProductId = product_id;
  const successUrl = body.success_url || 'https://mekong-raas.pages.dev/success';

  // Dev/test: return mock if no token configured
  if (!c.env.POLAR_ACCESS_TOKEN) {
    return json({
      checkout_url: `https://sandbox.polar.sh/checkout/${fullProductId}?mock=true`,
      product_id: fullProductId,
      tier: product.tier,
    });
  }

  // Fetch tenant email for pre-filling checkout
  let tenantEmail: string | undefined;
  if (c.env.DB) {
    const row = await c.env.DB.prepare('SELECT email FROM tenants WHERE id = ?')
      .bind(tenant.tenantId)
      .first<{ email: string }>();
    tenantEmail = row?.email;
  }

  // Call Polar API
  let polarResponse: Response;
  try {
    polarResponse = await fetch('https://api.polar.sh/v1/checkouts/custom/', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${c.env.POLAR_ACCESS_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        product_id: fullProductId,
        customer_external_id: tenant.tenantId,
        ...(tenantEmail ? { customer_email: tenantEmail } : {}),
        success_url: successUrl,
        metadata: { tenant_id: tenant.tenantId },
      }),
    });
  } catch (err) {
    return json({ error: 'Failed to reach Polar API', code: 'POLAR_UNAVAILABLE' }, { status: 502 });
  }

  if (!polarResponse.ok) {
    const errBody = await polarResponse.text().catch(() => '');
    return json(
      { error: 'Polar checkout creation failed', code: 'POLAR_ERROR', details: errBody },
      { status: polarResponse.status >= 400 && polarResponse.status < 500 ? 400 : 502 }
    );
  }

  const data = await polarResponse.json<{ url?: string; checkout_url?: string }>();
  const checkoutUrl = data.url || data.checkout_url || '';

  return json({
    checkout_url: checkoutUrl,
    product_id: fullProductId,
    tier: product.tier,
  });
});
