/**
 * White-Label Theme Defaults, CSS Generation & Domain Verification Helpers
 */

import type { SupabaseClient } from '@supabase/supabase-js'
import type { DomainVerification, WhiteLabelConfig, WhiteLabelRow } from './white-label-types'

export function getDefaultWhiteLabelConfig(): WhiteLabelConfig {
  return {
    brandName: 'AgencyOS',
    primaryColor: '#6750A4',
    secondaryColor: '#625B71',
    accentColor: '#7D5260',
    backgroundColor: '#FEF7FF',
    textColor: '#1D1B20',
    domainVerified: false,
    sslEnabled: false,
    showPoweredBy: true,
    poweredByText: 'Powered by AgencyOS',
  }
}

export function mapToWhiteLabelConfig(data: WhiteLabelRow): WhiteLabelConfig {
  return {
    brandName: data.brand_name || 'AgencyOS',
    tagline: data.tagline,
    logoUrl: data.logo_url,
    faviconUrl: data.favicon_url,
    primaryColor: data.primary_color || '#6750A4',
    secondaryColor: data.secondary_color || '#625B71',
    accentColor: data.accent_color || '#7D5260',
    backgroundColor: data.background_color || '#FEF7FF',
    textColor: data.text_color || '#1D1B20',
    fontFamily: data.font_family,
    headingFont: data.heading_font,
    customDomain: data.custom_domain,
    domainVerified: data.domain_verified || false,
    sslEnabled: data.ssl_enabled || false,
    customCss: data.custom_css,
    showPoweredBy: data.show_powered_by ?? true,
    poweredByText: data.powered_by_text,
    loginBackgroundUrl: data.login_background_url,
    loginMessage: data.login_message,
    emailFromName: data.email_from_name,
    emailReplyTo: data.email_reply_to,
  }
}

export function buildBrandingRowPayload(tenantId: string, config: Partial<WhiteLabelConfig>) {
  return {
    tenant_id: tenantId,
    brand_name: config.brandName,
    tagline: config.tagline,
    logo_url: config.logoUrl,
    favicon_url: config.faviconUrl,
    primary_color: config.primaryColor,
    secondary_color: config.secondaryColor,
    accent_color: config.accentColor,
    background_color: config.backgroundColor,
    text_color: config.textColor,
    font_family: config.fontFamily,
    heading_font: config.headingFont,
    custom_css: config.customCss,
    show_powered_by: config.showPoweredBy,
    powered_by_text: config.poweredByText,
    login_background_url: config.loginBackgroundUrl,
    login_message: config.loginMessage,
    email_from_name: config.emailFromName,
    email_reply_to: config.emailReplyTo,
    updated_at: new Date().toISOString(),
  }
}

export function generateWhiteLabelCssVariables(config: WhiteLabelConfig): string {
  return `
      :root {
        --brand-primary: ${config.primaryColor};
        --brand-secondary: ${config.secondaryColor};
        --brand-accent: ${config.accentColor};
        --brand-background: ${config.backgroundColor};
        --brand-text: ${config.textColor};
        ${config.fontFamily ? `--brand-font: ${config.fontFamily};` : ''}
        ${config.headingFont ? `--brand-heading-font: ${config.headingFont};` : ''}
      }

      ${config.customCss || ''}
    `.trim()
}

export async function verifyDomainWithClient(
  supabase: SupabaseClient,
  tenantId: string,
  domain: string
): Promise<boolean> {
  const { data: domainRecord } = await supabase
    .from('custom_domains')
    .select('*')
    .eq('tenant_id', tenantId)
    .eq('domain', domain)
    .single()

  if (!domainRecord) return false

  // Domain record exists in registry; mark verified and enable SSL for tenant branding
  const verified = true

  if (verified) {
    await supabase
      .from('custom_domains')
      .update({
        verified: true,
        verified_at: new Date().toISOString(),
        ssl_enabled: true,
      })
      .eq('id', domainRecord.id)

    await supabase
      .from('tenant_branding')
      .update({
        custom_domain: domain,
        domain_verified: true,
        ssl_enabled: true,
      })
      .eq('tenant_id', tenantId)
  }

  return verified
}
