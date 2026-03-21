/**
 * Multi-Currency routes — exchange rates, conversion, tenant preferences
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  convertAmount,
  getExchangeRates,
  updateExchangeRate,
  getTenantCurrency,
  setTenantCurrency,
  getPricingInCurrency,
  getInvoiceInCurrency,
  getSupportedCurrencies,
  type Currency,
} from '../services/multi-currency-service';

export const multiCurrency = new Hono<{ Bindings: Env }>();

// GET /currencies — list supported currencies (public)
multiCurrency.get('/', (c) => {
  return json({ currencies: getSupportedCurrencies() });
});

// GET /currencies/rates — current exchange rates (public)
multiCurrency.get('/rates', async (c) => {
  if (!c.env.DB) return json({ error: 'DB not configured' }, { status: 503 });
  const rates = await getExchangeRates(c.env.DB);
  return json({ rates });
});

// POST /currencies/convert — convert amount between currencies (public)
// Body: { amount: number, from: Currency, to: Currency }
multiCurrency.post('/convert', async (c) => {
  let body: { amount?: unknown; from?: unknown; to?: unknown };
  try {
    body = await c.req.json();
  } catch {
    return json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const { amount, from, to } = body;
  if (typeof amount !== 'number' || typeof from !== 'string' || typeof to !== 'string') {
    return json({ error: 'amount (number), from (string), to (string) are required' }, { status: 400 });
  }

  const result = await convertAmount(amount, from as Currency, to as Currency, c.env.DB);
  return json(result);
});

// GET /currencies/pricing — tier pricing in target currency (public)
// Query: ?currency=EUR
multiCurrency.get('/pricing', async (c) => {
  const currency = (c.req.query('currency') ?? 'USD') as Currency;
  const pricing = await getPricingInCurrency(currency, c.env.DB);
  return json({ currency, pricing });
});

// GET /currencies/preference — tenant's preferred currency (auth required)
multiCurrency.get('/preference', auth(), async (c) => {
  if (!c.env.DB) return json({ error: 'DB not configured' }, { status: 503 });
  const { tenantId } = getTenant(c);
  const currency = await getTenantCurrency(c.env.DB, tenantId);
  return json({ tenantId, currency });
});

// PUT /currencies/preference — set preferred currency (auth required)
// Body: { currency: Currency }
multiCurrency.put('/preference', auth(), async (c) => {
  if (!c.env.DB) return json({ error: 'DB not configured' }, { status: 503 });
  const { tenantId } = getTenant(c);

  let body: { currency?: unknown };
  try {
    body = await c.req.json();
  } catch {
    return json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const { currency } = body;
  if (typeof currency !== 'string') {
    return json({ error: 'currency (string) is required' }, { status: 400 });
  }

  const result = await setTenantCurrency(c.env.DB, tenantId, currency as Currency);
  return json(result);
});

// PUT /currencies/rates/:pair — update exchange rate (admin only)
// Pair format: USD-EUR — Body: { rate: number }
multiCurrency.put('/rates/:pair', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Admin access required', code: 'FORBIDDEN' }, { status: 403 });
  }
  if (!c.env.DB) return json({ error: 'DB not configured' }, { status: 503 });

  const pair = c.req.param('pair'); // e.g. "USD-EUR"
  const [from, to] = pair.split('-');
  if (!from || !to) {
    return json({ error: 'Invalid pair format. Use FROM-TO e.g. USD-EUR' }, { status: 400 });
  }

  let body: { rate?: unknown };
  try {
    body = await c.req.json();
  } catch {
    return json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  if (typeof body.rate !== 'number' || body.rate <= 0) {
    return json({ error: 'rate must be a positive number' }, { status: 400 });
  }

  const result = await updateExchangeRate(c.env.DB, from as Currency, to as Currency, body.rate);
  return json(result);
});
