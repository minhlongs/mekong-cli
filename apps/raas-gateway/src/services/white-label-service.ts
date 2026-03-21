/**
 * White-label branding service — per-tenant custom branding with tier-gating
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface BrandingConfig {
  tenant_id: string;
  company_name: string;
  logo_url: string | null;
  favicon_url: string | null;
  primary_color: string;
  secondary_color: string;
  custom_domain: string | null;
  email_from_name: string | null;
  email_from_address: string | null;
  footer_text: string | null;
  support_url: string | null;
  powered_by_visible: boolean;
}

const DEFAULT_BRANDING: Omit<BrandingConfig, 'tenant_id'> = {
  company_name: 'Mekong RaaS',
  logo_url: null,
  favicon_url: null,
  primary_color: '#2563eb',
  secondary_color: '#1e40af',
  custom_domain: null,
  email_from_name: null,
  email_from_address: null,
  footer_text: null,
  support_url: null,
  powered_by_visible: true,
};

// Fields accessible per tier (cumulative upward)
const TIER_BRANDING_FEATURES: Record<string, string[]> = {
  starter: ['company_name'],
  pro: ['company_name', 'primary_color', 'secondary_color', 'support_url'],
  agency: ['company_name', 'logo_url', 'favicon_url', 'primary_color', 'secondary_color', 'footer_text', 'support_url'],
  master: ['company_name', 'logo_url', 'favicon_url', 'primary_color', 'secondary_color', 'footer_text', 'support_url', 'email_from_name'],
  enterprise: ['company_name', 'logo_url', 'favicon_url', 'primary_color', 'secondary_color', 'custom_domain', 'email_from_name', 'email_from_address', 'footer_text', 'support_url', 'powered_by_visible'],
};

const HEX_COLOR_RE = /^#[0-9a-fA-F]{6}$/;

function isValidUrl(value: string): boolean {
  try {
    new URL(value);
    return true;
  } catch {
    return false;
  }
}

function rowToBrandingConfig(row: Record<string, unknown>, tenantId: string): BrandingConfig {
  return {
    tenant_id: tenantId,
    company_name: (row.company_name as string) ?? DEFAULT_BRANDING.company_name,
    logo_url: (row.logo_url as string | null) ?? null,
    favicon_url: (row.favicon_url as string | null) ?? null,
    primary_color: (row.primary_color as string) ?? DEFAULT_BRANDING.primary_color,
    secondary_color: (row.secondary_color as string) ?? DEFAULT_BRANDING.secondary_color,
    custom_domain: (row.custom_domain as string | null) ?? null,
    email_from_name: (row.email_from_name as string | null) ?? null,
    email_from_address: (row.email_from_address as string | null) ?? null,
    footer_text: (row.footer_text as string | null) ?? null,
    support_url: (row.support_url as string | null) ?? null,
    powered_by_visible: row.powered_by_visible !== 0,
  };
}

/** Get branding config merged with defaults */
export async function getBranding(db: D1Database, tenantId: string): Promise<BrandingConfig> {
  const row = await db
    .prepare('SELECT * FROM tenant_branding WHERE tenant_id = ?')
    .bind(tenantId)
    .first<Record<string, unknown>>();

  if (!row) return { ...DEFAULT_BRANDING, tenant_id: tenantId };
  return rowToBrandingConfig(row, tenantId);
}

/** Update branding fields — validates tier access and input values */
export async function updateBranding(
  db: D1Database,
  tenantId: string,
  tier: string,
  updates: Partial<Omit<BrandingConfig, 'tenant_id'>>
): Promise<{ config: BrandingConfig; denied: string[] }> {
  const { allowed, denied } = validateBrandingAccess(tier, Object.keys(updates));

  // Only apply allowed fields
  const safeUpdates: Record<string, unknown> = {};
  for (const field of allowed) {
    const value = (updates as Record<string, unknown>)[field];

    // Validate hex colors
    if ((field === 'primary_color' || field === 'secondary_color') && typeof value === 'string') {
      if (!HEX_COLOR_RE.test(value)) throw new Error(`Invalid hex color for ${field}: ${value}`);
    }

    // Validate URLs
    if (['logo_url', 'favicon_url', 'support_url', 'custom_domain'].includes(field) && typeof value === 'string' && value) {
      const toCheck = field === 'custom_domain' ? `https://${value}` : value;
      if (!isValidUrl(toCheck)) throw new Error(`Invalid URL for ${field}: ${value}`);
    }

    safeUpdates[field] = value;
  }

  // UPSERT
  const fields = Object.keys(safeUpdates);
  if (fields.length > 0) {
    const setClauses = fields.map((f) => `${f} = ?`).join(', ');
    const values = fields.map((f) => {
      const v = safeUpdates[f];
      if (typeof v === 'boolean') return v ? 1 : 0;
      return v ?? null;
    });

    await db
      .prepare(
        `INSERT INTO tenant_branding (tenant_id, ${fields.join(', ')}, updated_at)
         VALUES (?, ${fields.map(() => '?').join(', ')}, datetime('now'))
         ON CONFLICT(tenant_id) DO UPDATE SET ${setClauses}, updated_at = datetime('now')`
      )
      .bind(tenantId, ...values, ...values)
      .run();
  }

  const config = await getBranding(db, tenantId);
  return { config, denied };
}

/** Lookup branding by custom domain — used for white-label routing */
export async function getBrandingByDomain(db: D1Database, domain: string): Promise<BrandingConfig | null> {
  const row = await db
    .prepare('SELECT * FROM tenant_branding WHERE custom_domain = ?')
    .bind(domain)
    .first<Record<string, unknown>>();

  if (!row) return null;
  return rowToBrandingConfig(row, row.tenant_id as string);
}

/** Validate which fields are accessible for a tier */
export function validateBrandingAccess(
  tier: string,
  fields: string[]
): { allowed: string[]; denied: string[] } {
  const allowedSet = new Set(TIER_BRANDING_FEATURES[tier] ?? TIER_BRANDING_FEATURES['starter']);
  const allowed: string[] = [];
  const denied: string[] = [];

  for (const field of fields) {
    if (allowedSet.has(field)) {
      allowed.push(field);
    } else {
      denied.push(field);
    }
  }

  return { allowed, denied };
}

/** Reset branding to defaults by deleting the row */
export async function resetBranding(db: D1Database, tenantId: string): Promise<BrandingConfig> {
  await db.prepare('DELETE FROM tenant_branding WHERE tenant_id = ?').bind(tenantId).run();
  return { ...DEFAULT_BRANDING, tenant_id: tenantId };
}

/** Generate CSS variable snippet for branding preview */
export function previewBranding(config: Partial<BrandingConfig>): string {
  const primary = config.primary_color ?? DEFAULT_BRANDING.primary_color;
  const secondary = config.secondary_color ?? DEFAULT_BRANDING.secondary_color;
  const name = config.company_name ?? DEFAULT_BRANDING.company_name;

  return `:root {
  --brand-primary: ${primary};
  --brand-secondary: ${secondary};
  --brand-name: "${name}";
  --brand-logo: ${config.logo_url ? `url("${config.logo_url}")` : 'none'};
  --brand-powered-by: ${config.powered_by_visible !== false ? '"Powered by Mekong RaaS"' : '""'};
}`;
}

/** List available branding features for a tier */
export function getAvailableFeatures(tier: string): string[] {
  return TIER_BRANDING_FEATURES[tier] ?? TIER_BRANDING_FEATURES['starter'];
}
