import type { Bindings } from '../index'
import type { Context, Next } from 'hono'
import type { Tenant } from '../types/raas'

// ─── RBAC POLICY ENGINE ───
// Tam giác ngược: community (level 6) = most operational power
// owner (level 1) = constitutional decisions only

export interface Policy {
  resource: string
  action: string
  min_level: number        // governance_level must be >= this (lower = more restricted)
  max_level: number        // governance_level must be <= this (higher = more access)
  description: string
}

// 15 policy rules — level 1=owner, 6=community
// Lower governance_level = higher authority (tam giác ngược)
export const POLICIES: Policy[] = [
  // Constitutional — owner only (level 1)
  { resource: 'constitution', action: 'amend', min_level: 1, max_level: 1, description: 'Amend constitutional documents' },
  { resource: 'tenant', action: 'delete', min_level: 1, max_level: 1, description: 'Delete tenant/organization' },

  // Strategic — admin+ (level 1-2)
  { resource: 'stakeholders', action: 'promote', min_level: 1, max_level: 2, description: 'Promote stakeholder governance level' },
  { resource: 'equity', action: 'grant', min_level: 1, max_level: 2, description: 'Issue equity grants' },
  { resource: 'treasury', action: 'withdraw', min_level: 1, max_level: 2, description: 'Withdraw from treasury' },

  // Operational — operator+ (level 1-3)
  { resource: 'proposals', action: 'create', min_level: 1, max_level: 3, description: 'Create governance proposals' },
  { resource: 'missions', action: 'cancel', min_level: 1, max_level: 3, description: 'Cancel running missions' },
  { resource: 'conflicts', action: 'dismiss', min_level: 1, max_level: 3, description: 'Dismiss conflict reports' },

  // Expert/Founder level (level 1-5)
  { resource: 'matching', action: 'create_request', min_level: 1, max_level: 5, description: 'Create expert match requests' },
  { resource: 'proposals', action: 'vote', min_level: 1, max_level: 5, description: 'Vote on proposals' },
  { resource: 'reputation', action: 'award', min_level: 1, max_level: 5, description: 'Award reputation points' },

  // Community level — all stakeholders (level 1-6)
  { resource: 'conflicts', action: 'report', min_level: 1, max_level: 6, description: 'Report conflicts' },
  { resource: 'skill_profiles', action: 'update', min_level: 1, max_level: 6, description: 'Update own skill profile' },
  { resource: 'proposals', action: 'comment', min_level: 1, max_level: 6, description: 'Comment on proposals' },
  { resource: 'missions', action: 'create', min_level: 1, max_level: 6, description: 'Create new missions' },
]

export interface PermissionResult {
  allowed: boolean
  reason: string
  policy?: Policy
}

// checkPermission — evaluate resource+action against stakeholder governance_level
export function checkPermission(
  resource: string,
  action: string,
  stakeholder: { governance_level: number; role: string; id: string }
): PermissionResult {
  const policy = POLICIES.find(p => p.resource === resource && p.action === action)

  if (!policy) {
    return {
      allowed: false,
      reason: `No policy defined for ${resource}:${action}`,
    }
  }

  const level = stakeholder.governance_level
  const allowed = level >= policy.min_level && level <= policy.max_level

  if (!allowed) {
    return {
      allowed: false,
      reason: `governance_level ${level} (${stakeholder.role}) not permitted for ${resource}:${action}. Required: level ${policy.min_level}-${policy.max_level}`,
      policy,
    }
  }

  return {
    allowed: true,
    reason: `Permitted: ${policy.description}`,
    policy,
  }
}

// getPolicies — return full RBAC policy list
export function getPolicies(): Policy[] {
  return POLICIES
}

// requirePermission — Hono middleware factory
export function requirePermission(resource: string, action: string) {
  return async (c: Context<{ Bindings: Bindings; Variables: { tenant: Tenant } }>, next: Next) => {
    if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

    const stakeholderId = c.req.header('X-Stakeholder-Id')
    if (!stakeholderId) {
      return c.json({ error: 'X-Stakeholder-Id header required for permission check' }, 401)
    }

    const tenant = c.get('tenant')
    const stakeholder = await c.env.DB.prepare(
      'SELECT id, role, governance_level FROM stakeholders WHERE id = ? AND tenant_id = ?'
    ).bind(stakeholderId, tenant.id).first<{ id: string; role: string; governance_level: number }>()

    if (!stakeholder) {
      return c.json({ error: 'Stakeholder not found' }, 404)
    }

    const result = checkPermission(resource, action, stakeholder)
    if (!result.allowed) {
      return c.json({ error: 'Permission denied', reason: result.reason }, 403)
    }

    await next()
  }
}
