/**
 * SSO/SAML stub routes - enterprise feature placeholder
 */
import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';

export const sso = new Hono<{ Bindings: Env }>();

/** GET /v1/sso/config */
sso.get('/v1/sso/config', auth(), async (c) => {
  return c.json({ success: true, data: { enabled: false, provider: null, message: 'SSO coming soon for enterprise plans' } });
});

/** POST /v1/sso/config */
sso.post('/v1/sso/config', auth(), async (c) => {
  const tenant = getTenant(c);
  if (tenant.tier !== 'enterprise') {
    return c.json({ success: false, error: 'SSO requires enterprise plan', upgrade_url: '/billing/checkout' }, 403);
  }
  return c.json({ success: false, error: 'SSO configuration not yet available', status: 'coming_soon' }, 501);
});

/** GET /v1/sso/metadata - SAML metadata */
sso.get('/v1/sso/metadata', (c) => {
  const xml = '<?xml version="1.0"?><EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"><SPSSODescriptor AuthnRequestsSigned="true" WantAssertionsSigned="true" protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"><NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</NameIDFormat></SPSSODescriptor></EntityDescriptor>';
  return new Response(xml, { headers: { 'Content-Type': 'application/xml' } });
});

/** POST /v1/sso/callback */
sso.post('/v1/sso/callback', (c) => {
  return c.json({ error: 'SSO callback not implemented', code: 'NOT_IMPLEMENTED' }, 501);
});
