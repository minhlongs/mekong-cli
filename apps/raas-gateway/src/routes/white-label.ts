/**
 * White-label branding routes — per-tenant custom branding management
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  getBranding,
  updateBranding,
  resetBranding,
  getBrandingByDomain,
  previewBranding,
  getAvailableFeatures,
} from '../services/white-label-service';

export const whiteLabel = new Hono<{ Bindings: Env }>();

// All branding routes require auth (except domain lookup)
whiteLabel.use('/branding', auth());
whiteLabel.use('/branding/*', auth());

/** GET /branding — get tenant branding config */
whiteLabel.get('/branding', async (c) => {
  const tenant = getTenant(c);
  const config = await getBranding(c.env.DB, tenant.tenantId);
  return json({ branding: config });
});

/** PUT /branding — update branding (tier-gated) */
whiteLabel.put('/branding', async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));

  // Strip unknown keys
  const allowedKeys = [
    'company_name', 'logo_url', 'favicon_url', 'primary_color', 'secondary_color',
    'custom_domain', 'email_from_name', 'email_from_address', 'footer_text',
    'support_url', 'powered_by_visible',
  ];
  const updates: Record<string, unknown> = {};
  for (const key of allowedKeys) {
    if (key in body) updates[key] = body[key];
  }

  if (Object.keys(updates).length === 0) {
    return json({ error: 'No valid fields provided', code: 'INVALID_INPUT' }, { status: 400 });
  }

  try {
    const { config, denied } = await updateBranding(c.env.DB, tenant.tenantId, tenant.tier, updates as any);
    return json({
      branding: config,
      ...(denied.length > 0 && { denied, message: `Fields denied for ${tenant.tier} tier: ${denied.join(', ')}` }),
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Update failed';
    return json({ error: msg, code: 'VALIDATION_ERROR' }, { status: 400 });
  }
});

/** DELETE /branding — reset to defaults */
whiteLabel.delete('/branding', async (c) => {
  const tenant = getTenant(c);
  const config = await resetBranding(c.env.DB, tenant.tenantId);
  return json({ branding: config, message: 'Branding reset to defaults' });
});

/** GET /branding/features — available features for tenant tier */
whiteLabel.get('/branding/features', (c) => {
  const tenant = getTenant(c);
  const features = getAvailableFeatures(tenant.tier);
  return json({ tier: tenant.tier, features });
});

/** GET /branding/preview — preview branding as CSS variables */
whiteLabel.get('/branding/preview', async (c) => {
  const tenant = getTenant(c);
  const config = await getBranding(c.env.DB, tenant.tenantId);
  const css = previewBranding(config);
  return new Response(css, { headers: { 'Content-Type': 'text/css' } });
});

/** GET /branding/domain/:domain — lookup branding by custom domain (public) */
whiteLabel.get('/branding/domain/:domain', async (c) => {
  const domain = c.req.param('domain');
  if (!domain) return json({ error: 'Domain required', code: 'INVALID_INPUT' }, { status: 400 });

  const config = await getBrandingByDomain(c.env.DB, domain);
  if (!config) return json({ error: 'Domain not found', code: 'NOT_FOUND' }, { status: 404 });

  // Return safe subset — don't expose internal email config publicly
  return json({
    company_name: config.company_name,
    logo_url: config.logo_url,
    favicon_url: config.favicon_url,
    primary_color: config.primary_color,
    secondary_color: config.secondary_color,
    footer_text: config.footer_text,
    support_url: config.support_url,
    powered_by_visible: config.powered_by_visible,
  });
});
