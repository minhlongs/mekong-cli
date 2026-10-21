/**
 * Tenant Access Control & Role Hierarchy Guards
 */

import type { SupabaseClient } from '@supabase/supabase-js'
import type { TenantRole } from './isolation-types'

export const TENANT_ROLE_HIERARCHY: Record<TenantRole, number> = {
  owner: 100,
  admin: 80,
  manager: 60,
  member: 40,
  viewer: 20,
}

export async function checkTenantAccessWithClient(
  supabase: SupabaseClient,
  userId: string,
  tenantId: string,
  requiredRole?: TenantRole
): Promise<boolean> {
  const { data: member } = await supabase
    .from('tenant_members')
    .select('role, status')
    .eq('user_id', userId)
    .eq('tenant_id', tenantId)
    .single()

  if (!member || member.status !== 'active') return false

  if (!requiredRole) return true

  const memberRole = member.role as TenantRole
  return TENANT_ROLE_HIERARCHY[memberRole] >= TENANT_ROLE_HIERARCHY[requiredRole]
}

export async function getUserTenantRoleWithClient(
  supabase: SupabaseClient,
  userId: string,
  tenantId: string
): Promise<TenantRole | null> {
  const { data } = await supabase
    .from('tenant_members')
    .select('role')
    .eq('user_id', userId)
    .eq('tenant_id', tenantId)
    .eq('status', 'active')
    .single()

  return data?.role || null
}
