/**
 * Platform Localization routes — i18n config, translation keys, translations
 * Mount path: /v1/i18n
 *
 * Public:  GET /translations/:locale  GET /keys  GET /namespaces/:ns/:locale  GET /locales
 * Auth:    GET /config  PUT /config
 * Admin:   POST /translations  POST /keys  GET /admin/overview
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import {
  getLocaleConfig,
  updateLocaleConfig,
  getTranslations,
  upsertTranslation,
  listKeys,
  createKey,
  getNamespaceTranslations,
  getAdminOverview,
} from '../services/platform-localization-service';

type Env = {
  Bindings: {
    DB: any;
    RATE_LIMIT_KV: any;
    SESSION_KV: any;
    AI: any;
    JWT_SECRET=REDACTED: string;
    POLAR_WEBHOOK_SECRET: string;
    TELEGRAM_BOT_TOKEN: string;
    ENVIRONMENT: string;
    LOG_LEVEL: string;
    ADMIN_API_KEY: string;
  };
};

const app = new Hono<Env>();

function isAdmin(c: { req: { header: (k: string) => string | undefined }; env: Env['Bindings'] }): boolean {
  return !!c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY;
}

// ── Auth: get tenant locale config ────────────────────────────────────────────
app.get('/config', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const config = await getLocaleConfig(c.env.DB, tenantId);
  if (!config) return c.json({ success: true, data: { tenant_id: tenantId, default_locale: 'en', supported_locales: ['en'], timezone: 'UTC', date_format: 'YYYY-MM-DD', number_format: 'en-US', currency_locale: 'en-US' } });
  return c.json({ success: true, data: { ...config, supported_locales: JSON.parse(config.supported_locales) } });
});

// ── Auth: update tenant locale config ─────────────────────────────────────────
app.put('/config', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json<{
    default_locale?: string;
    supported_locales?: string[];
    timezone?: string;
    date_format?: string;
    number_format?: string;
    currency_locale?: string;
  }>();
  const updates: Record<string, string> = {};
  if (body.default_locale) updates.default_locale = body.default_locale;
  if (body.supported_locales) updates.supported_locales = JSON.stringify(body.supported_locales);
  if (body.timezone) updates.timezone = body.timezone;
  if (body.date_format) updates.date_format = body.date_format;
  if (body.number_format) updates.number_format = body.number_format;
  if (body.currency_locale) updates.currency_locale = body.currency_locale;
  const config = await updateLocaleConfig(c.env.DB, tenantId, updates as any);
  return c.json({ success: true, data: { ...config, supported_locales: JSON.parse(config.supported_locales) } });
});

// ── Public: get all translations for a locale ─────────────────────────────────
app.get('/translations/:locale', async (c) => {
  const locale = c.req.param('locale');
  const items = await getTranslations(c.env.DB, locale);
  return c.json({ success: true, data: { locale, count: items.length, translations: items } });
});

// ── Admin: upsert a translation ───────────────────────────────────────────────
app.post('/translations', async (c) => {
  if (!isAdmin(c as any)) return c.json({ success: false, error: 'Admin key required' }, 403);
  const body = await c.req.json<{ key_id: string; locale: string; value: string; translated_by?: string; is_verified?: boolean }>();
  if (!body.key_id || !body.locale || !body.value) {
    return c.json({ success: false, error: 'key_id, locale, and value are required' }, 400);
  }
  try {
    const translation = await upsertTranslation(c.env.DB, body);
    return c.json({ success: true, data: translation }, 201);
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to upsert translation';
    return c.json({ success: false, error: msg }, 400);
  }
});

// ── Public: list translation keys ─────────────────────────────────────────────
app.get('/keys', async (c) => {
  const namespace = c.req.query('namespace');
  const keys = await listKeys(c.env.DB, namespace);
  return c.json({ success: true, data: { count: keys.length, keys } });
});

// ── Admin: create translation key ─────────────────────────────────────────────
app.post('/keys', async (c) => {
  if (!isAdmin(c as any)) return c.json({ success: false, error: 'Admin key required' }, 403);
  const body = await c.req.json<{ key_path: string; namespace?: string; default_value: string; description?: string }>();
  if (!body.key_path || !body.default_value) {
    return c.json({ success: false, error: 'key_path and default_value are required' }, 400);
  }
  try {
    const key = await createKey(c.env.DB, body);
    return c.json({ success: true, data: key }, 201);
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to create key';
    return c.json({ success: false, error: msg }, 409);
  }
});

// ── Public: get namespace translations as flat map ────────────────────────────
app.get('/namespaces/:ns/:locale', async (c) => {
  const { ns, locale } = c.req.param();
  const map = await getNamespaceTranslations(c.env.DB, ns, locale);
  return c.json({ success: true, data: { namespace: ns, locale, translations: map } });
});

// ── Public: list all distinct locales that have translations ──────────────────
app.get('/locales', async (c) => {
  const { results } = await c.env.DB.prepare(
    'SELECT DISTINCT locale FROM translations ORDER BY locale'
  ).all() as { results: Array<{ locale: string }> };
  const locales = (results ?? []).map((r: { locale: string }) => r.locale);
  if (!locales.includes('en')) locales.unshift('en');
  return c.json({ success: true, data: { locales } });
});

// ── Admin: overview ───────────────────────────────────────────────────────────
app.get('/admin/overview', async (c) => {
  if (!isAdmin(c as any)) return c.json({ success: false, error: 'Admin key required' }, 403);
  const overview = await getAdminOverview(c.env.DB);
  return c.json({ success: true, data: overview });
});

export { app as platformLocalization };
