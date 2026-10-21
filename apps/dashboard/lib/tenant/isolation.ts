/**
 * Tenant Isolation Module
 * Full RLS enforcement and data segregation
 */

import { createClient } from '@supabase/supabase-js'
import type {
  Tenant,
  TenantMember,
  TenantMemberRow,
  TenantRole,
  TenantRow,
  TenantSettings,
} from './isolation-types'
import { mapToMember, mapToTenant } from './isolation-types'
import {
  acceptTenantInvitationWithClient,
  addTenantMemberWithClient,
  generateInviteToken,
  generateTenantSlug,
  getDefaultTenantSettings,
  getTenantsByUserWithClient,
  inviteTenantMemberWithClient,
} from './isolation-context'
import { checkTenantAccessWithClient, getUserTenantRoleWithClient } from './isolation-guards'

export * from './isolation-types'
export * from './isolation-context'
export * from './isolation-guards'

export class TenantManager {
  private supabase

  constructor() {
    this.supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_KEY!
    )
  }

  async createTenant(data: { name: string; ownerId: string; ownerEmail: string }): Promise<Tenant> {
    const slug = this.generateSlug(data.name)
    const { data: tenant, error } = await this.supabase
      .from('tenants')
      .insert({
        name: data.name,
        slug,
        owner_id: data.ownerId,
        plan: 'FREE',
        settings: this.getDefaultSettings('FREE'),
      })
      .select()
      .single()

    if (error) throw new Error(`Failed to create tenant: ${error.message}`)
    await this.addMember(tenant.id, {
      userId: data.ownerId,
      email: data.ownerEmail,
      name: 'Owner',
      role: 'owner',
    })
    return this.mapToTenant(tenant)
  }

  async getTenant(tenantId: string): Promise<Tenant | null> {
    const { data, error } = await this.supabase.from('tenants').select('*').eq('id', tenantId).single()
    return error || !data ? null : this.mapToTenant(data)
  }

  async getTenantBySlug(slug: string): Promise<Tenant | null> {
    const { data, error } = await this.supabase.from('tenants').select('*').eq('slug', slug).single()
    return error || !data ? null : this.mapToTenant(data)
  }

  async getTenantsByUser(userId: string): Promise<Tenant[]> {
    return getTenantsByUserWithClient(this.supabase, userId)
  }

  async updateTenant(tenantId: string, updates: Partial<Tenant>): Promise<Tenant> {
    const { data, error } = await this.supabase
      .from('tenants')
      .update({
        name: updates.name,
        settings: updates.settings,
        updated_at: new Date().toISOString(),
      })
      .eq('id', tenantId)
      .select()
      .single()
    if (error) throw new Error(`Failed to update tenant: ${error.message}`)
    return this.mapToTenant(data)
  }

  async deleteTenant(tenantId: string): Promise<void> {
    await this.supabase.from('tenants').update({ deleted_at: new Date().toISOString() }).eq('id', tenantId)
  }

  async getMembers(tenantId: string): Promise<TenantMember[]> {
    const { data } = await this.supabase
      .from('tenant_members')
      .select('*')
      .eq('tenant_id', tenantId)
      .order('created_at', { ascending: true })
    return (data || []).map(this.mapToMember)
  }

  async addMember(
    tenantId: string,
    member: { userId?: string; email: string; name: string; role: TenantRole }
  ): Promise<TenantMember> {
    return addTenantMemberWithClient(this.supabase, tenantId, member)
  }

  async updateMemberRole(memberId: string, role: TenantRole): Promise<void> {
    await this.supabase.from('tenant_members').update({ role }).eq('id', memberId)
  }

  async removeMember(memberId: string): Promise<void> {
    await this.supabase.from('tenant_members').delete().eq('id', memberId)
  }

  async inviteMember(tenantId: string, email: string, role: TenantRole, invitedBy: string): Promise<string> {
    return inviteTenantMemberWithClient(this.supabase, tenantId, email, role, invitedBy)
  }

  async acceptInvitation(token: string, userId: string): Promise<void> {
    return acceptTenantInvitationWithClient(this.supabase, token, userId)
  }

  async checkAccess(userId: string, tenantId: string, requiredRole?: TenantRole): Promise<boolean> {
    return checkTenantAccessWithClient(this.supabase, userId, tenantId, requiredRole)
  }

  async getUserRole(userId: string, tenantId: string): Promise<TenantRole | null> {
    return getUserTenantRoleWithClient(this.supabase, userId, tenantId)
  }

  private generateSlug(name: string): string {
    return generateTenantSlug(name)
  }
  private generateInviteToken(): string {
    return generateInviteToken()
  }
  private getDefaultSettings(plan: 'FREE' | 'PRO' | 'ENTERPRISE'): TenantSettings {
    return getDefaultTenantSettings(plan)
  }
  private mapToTenant(data: TenantRow): Tenant {
    return mapToTenant(data)
  }
  private mapToMember(data: TenantMemberRow): TenantMember {
    return mapToMember(data)
  }
}

export const tenantManager = new TenantManager()
