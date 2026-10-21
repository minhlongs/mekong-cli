/**
 * Tenant Isolation Types & Row Mappers
 */

export interface Tenant {
  id: string
  name: string
  slug: string
  ownerId: string
  plan: 'FREE' | 'PRO' | 'ENTERPRISE'
  settings: TenantSettings
  createdAt: Date
  updatedAt: Date
}

export interface TenantSettings {
  // Branding
  brandName?: string
  logoUrl?: string
  faviconUrl?: string
  primaryColor?: string
  accentColor?: string

  // Custom Domain
  customDomain?: string
  domainVerified?: boolean

  // Features
  features: {
    whiteLabel: boolean
    customDomain: boolean
    apiAccess: boolean
    sso: boolean
    auditLog: boolean
  }

  // Limits
  limits: {
    teamMembers: number
    projects: number
    storage: number // GB
    apiCalls: number // per month
  }
}

export interface TenantMember {
  id: string
  tenantId: string
  userId: string
  email: string
  name: string
  role: TenantRole
  status: 'active' | 'pending' | 'suspended'
  invitedBy: string
  joinedAt?: Date
  createdAt: Date
}

export type TenantRole = 'owner' | 'admin' | 'manager' | 'member' | 'viewer'

export interface TenantRow {
  id: string
  name: string
  slug: string
  owner_id: string
  plan: 'FREE' | 'PRO' | 'ENTERPRISE'
  settings: TenantSettings
  created_at: string
  updated_at: string
}

export interface TenantMemberRow {
  id: string
  tenant_id: string
  user_id: string
  email: string
  name: string
  role: TenantRole
  status: 'active' | 'pending' | 'suspended'
  invited_by: string
  joined_at?: string
  created_at: string
}

export function mapToTenant(data: TenantRow): Tenant {
  return {
    id: data.id,
    name: data.name,
    slug: data.slug,
    ownerId: data.owner_id,
    plan: data.plan,
    settings: data.settings,
    createdAt: new Date(data.created_at),
    updatedAt: new Date(data.updated_at),
  }
}

export function mapToMember(data: TenantMemberRow): TenantMember {
  return {
    id: data.id,
    tenantId: data.tenant_id,
    userId: data.user_id,
    email: data.email,
    name: data.name,
    role: data.role,
    status: data.status,
    invitedBy: data.invited_by,
    joinedAt: data.joined_at ? new Date(data.joined_at) : undefined,
    createdAt: new Date(data.created_at),
  }
}
