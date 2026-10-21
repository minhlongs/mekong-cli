/**
 * Tenant Context Provisioning, Defaults & Invitation Lifecycle
 */

import type { SupabaseClient } from '@supabase/supabase-js'
import type { Tenant, TenantMember, TenantRole, TenantSettings } from './isolation-types'
import { mapToMember, mapToTenant } from './isolation-types'

export function generateTenantSlug(name: string): string {
  return (
    name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '') +
    '-' +
    Math.random().toString(36).substring(2, 8)
  )
}

export function generateInviteToken(): string {
  return crypto.randomUUID() + '-' + Date.now().toString(36)
}

export function getDefaultTenantSettings(plan: 'FREE' | 'PRO' | 'ENTERPRISE'): TenantSettings {
  const baseLimits = {
    FREE: { teamMembers: 3, projects: 5, storage: 1, apiCalls: 1000 },
    PRO: { teamMembers: 10, projects: -1, storage: 50, apiCalls: 50000 },
    ENTERPRISE: { teamMembers: -1, projects: -1, storage: 500, apiCalls: -1 },
  }

  return {
    features: {
      whiteLabel: plan === 'ENTERPRISE',
      customDomain: plan !== 'FREE',
      apiAccess: plan !== 'FREE',
      sso: plan === 'ENTERPRISE',
      auditLog: plan !== 'FREE',
    },
    limits: baseLimits[plan],
  }
}

export async function getTenantsByUserWithClient(
  supabase: SupabaseClient,
  userId: string
): Promise<Tenant[]> {
  const { data: memberships } = await supabase
    .from('tenant_members')
    .select('tenant_id')
    .eq('user_id', userId)
    .eq('status', 'active')

  if (!memberships?.length) return []

  const tenantIds = memberships.map(m => m.tenant_id)
  const { data: tenants } = await supabase.from('tenants').select('*').in('id', tenantIds)
  return (tenants || []).map(mapToTenant)
}

export async function addTenantMemberWithClient(
  supabase: SupabaseClient,
  tenantId: string,
  member: { userId?: string; email: string; name: string; role: TenantRole }
): Promise<TenantMember> {
  const { data, error } = await supabase
    .from('tenant_members')
    .insert({
      tenant_id: tenantId,
      user_id: member.userId,
      email: member.email,
      name: member.name,
      role: member.role,
      status: member.userId ? 'active' : 'pending',
    })
    .select()
    .single()

  if (error) throw new Error(`Failed to add member: ${error.message}`)
  return mapToMember(data)
}

export async function inviteTenantMemberWithClient(
  supabase: SupabaseClient,
  tenantId: string,
  email: string,
  role: TenantRole,
  invitedBy: string
): Promise<string> {
  const { data: existing } = await supabase
    .from('tenant_members')
    .select('id')
    .eq('tenant_id', tenantId)
    .eq('email', email)
    .single()

  if (existing) throw new Error('User is already a member of this tenant')

  const { data: member } = await supabase
    .from('tenant_members')
    .insert({
      tenant_id: tenantId,
      email,
      role,
      status: 'pending',
      invited_by: invitedBy,
    })
    .select()
    .single()

  const token = generateInviteToken()

  await supabase.from('invitations').insert({
    tenant_id: tenantId,
    member_id: member.id,
    email,
    token,
    expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
  })

  return token
}

export async function acceptTenantInvitationWithClient(
  supabase: SupabaseClient,
  token: string,
  userId: string
): Promise<void> {
  const { data: invite } = await supabase
    .from('invitations')
    .select('*')
    .eq('token', token)
    .single()

  if (!invite) throw new Error('Invalid invitation')
  if (new Date(invite.expires_at) < new Date()) throw new Error('Invitation expired')

  await supabase
    .from('tenant_members')
    .update({
      user_id: userId,
      status: 'active',
      joined_at: new Date().toISOString(),
    })
    .eq('id', invite.member_id)

  await supabase.from('invitations').delete().eq('id', invite.id)
}
