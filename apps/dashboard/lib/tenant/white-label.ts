/**
 * White-Label Module
 * Custom branding that makes each tenant feel like their own product
 */

import { createClient } from '@supabase/supabase-js'
import type { DomainVerification, WhiteLabelConfig, WhiteLabelRow } from './white-label-types'
import {
  buildBrandingRowPayload,
  generateWhiteLabelCssVariables,
  getDefaultWhiteLabelConfig,
  mapToWhiteLabelConfig,
  verifyDomainWithClient,
} from './white-label-themes'

export type { DomainVerification, WhiteLabelConfig, WhiteLabelRow }
export {
  buildBrandingRowPayload,
  generateWhiteLabelCssVariables,
  getDefaultWhiteLabelConfig,
  mapToWhiteLabelConfig,
  verifyDomainWithClient,
}

export class WhiteLabelManager {
  private supabase

  constructor() {
    this.supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_KEY!
    )
  }

  async getBrandingConfig(tenantId: string): Promise<WhiteLabelConfig> {
    const { data } = await this.supabase
      .from('tenant_branding')
      .select('*')
      .eq('tenant_id', tenantId)
      .single()

    if (!data) {
      return this.getDefaultConfig()
    }

    return this.mapToConfig(data)
  }

  async updateBranding(
    tenantId: string,
    config: Partial<WhiteLabelConfig>
  ): Promise<WhiteLabelConfig> {
    const { data: existing } = await this.supabase
      .from('tenant_branding')
      .select('id')
      .eq('tenant_id', tenantId)
      .single()

    const brandingData = buildBrandingRowPayload(tenantId, config)

    if (existing) {
      const { data } = await this.supabase
        .from('tenant_branding')
        .update(brandingData)
        .eq('tenant_id', tenantId)
        .select()
        .single()
      return this.mapToConfig(data)
    } else {
      const { data } = await this.supabase
        .from('tenant_branding')
        .insert(brandingData)
        .select()
        .single()
      return this.mapToConfig(data)
    }
  }

  async setupCustomDomain(tenantId: string, domain: string): Promise<DomainVerification> {
    const txtRecord = `agencyos-verify=${tenantId.substring(0, 8)}`
    const cnameRecord = `${tenantId.substring(0, 8)}.tenant.agencyos.network`

    const { data } = await this.supabase
      .from('custom_domains')
      .insert({
        tenant_id: tenantId,
        domain: domain.toLowerCase(),
        txt_record: txtRecord,
        cname_record: cnameRecord,
        verified: false,
      })
      .select()
      .single()

    return {
      domain: data.domain,
      txtRecord: data.txt_record,
      cnameRecord: data.cname_record,
      verified: false,
    }
  }

  async verifyDomain(tenantId: string, domain: string): Promise<boolean> {
    return verifyDomainWithClient(this.supabase, tenantId, domain)
  }

  async getCustomDomain(tenantId: string): Promise<DomainVerification | null> {
    const { data } = await this.supabase
      .from('custom_domains')
      .select('*')
      .eq('tenant_id', tenantId)
      .single()

    if (!data) return null

    return {
      domain: data.domain,
      txtRecord: data.txt_record,
      cnameRecord: data.cname_record,
      verified: data.verified,
      verifiedAt: data.verified_at ? new Date(data.verified_at) : undefined,
    }
  }

  async removeDomain(tenantId: string): Promise<void> {
    await this.supabase.from('custom_domains').delete().eq('tenant_id', tenantId)

    await this.supabase
      .from('tenant_branding')
      .update({
        custom_domain: null,
        domain_verified: false,
        ssl_enabled: false,
      })
      .eq('tenant_id', tenantId)
  }

  generateCssVariables(config: WhiteLabelConfig): string {
    return generateWhiteLabelCssVariables(config)
  }

  private getDefaultConfig(): WhiteLabelConfig {
    return getDefaultWhiteLabelConfig()
  }

  private mapToConfig(data: WhiteLabelRow): WhiteLabelConfig {
    return mapToWhiteLabelConfig(data)
  }
}

export const whiteLabelManager = new WhiteLabelManager()
