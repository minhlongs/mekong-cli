/**
 * @agencyos/vibe-auth — RBAC (Role-Based Access Control) Utilities
 *
 * Hierarchical role checking, permission evaluation, multi-tenant role support.
 * Extracted from apps/well admin-panel and apps/apex-os patterns.
 *
 * Usage:
 *   import { hasRole, hasPermission, createRBACEvaluator } from '@agencyos/vibe-auth/rbac';
 */

import type { VibeAuthUser } from './types';

// ─── Role Hierarchy ──────────────────────────────────────────────

/**
 * Default role hierarchy (higher index = more privilege).
 * Override with createRBACEvaluator for custom hierarchies.
 */
export const DEFAULT_ROLE_HIERARCHY = [
  'viewer',
  'member',
  'editor',
  'manager',
  'admin',
  'super_admin',
  'founder',
  'owner',
] as const;

export type DefaultRole = (typeof DEFAULT_ROLE_HIERARCHY)[number];

// ─── Permission Types ────────────────────────────────────────────

export interface Permission {
  resource: string;
  action: 'create' | 'read' | 'update' | 'delete' | 'manage';
}

export interface RBACConfig {
  roleHierarchy: readonly string[];
  rolePermissions: Record<string, Permission[]>;
}

// ─── Role Checking ───────────────────────────────────────────────

/**
 * Check if user has a specific role (exact match).
 */
export function hasRole(user: VibeAuthUser | null, role: string): boolean {
  if (!user) return false;
  return user.role === role;
}

/**
 * Check if user has ANY of the specified roles.
 */
export function hasAnyRole(user: VibeAuthUser | null, roles: string[]): boolean {
  if (!user || !user.role) return false;
  return roles.includes(user.role);
}

/**
 * Check if user's role meets minimum level in hierarchy.
 */
export function hasMinimumRole(
  user: VibeAuthUser | null,
  minimumRole: string,
  hierarchy: readonly string[] = DEFAULT_ROLE_HIERARCHY,
): boolean {
  if (!user || !user.role) return false;

  const userLevel = hierarchy.indexOf(user.role);
  const requiredLevel = hierarchy.indexOf(minimumRole);

  if (userLevel === -1 || requiredLevel === -1) return false;

  return userLevel >= requiredLevel;
}

// ─── Permission Checking ─────────────────────────────────────────

/**
 * Check if user has a specific permission based on role→permission mapping.
 */
export function hasPermission(
  user: VibeAuthUser | null,
  permission: Permission,
  config: RBACConfig,
): boolean {
  if (!user || !user.role) return false;

  // Owner/founder bypass
  if (user.isAdmin) return true;

  const userPermissions = config.rolePermissions[user.role] ?? [];

  return userPermissions.some(
    p =>
      (p.resource === permission.resource || p.resource === '*') &&
      (p.action === permission.action || p.action === 'manage'),
  );
}

// ─── RBAC Evaluator Factory ──────────────────────────────────────

/**
 * Create a configured RBAC evaluator with custom role hierarchy and permissions.
 *
 * @example
 *   const rbac = createRBACEvaluator({
 *     roleHierarchy: ['viewer', 'editor', 'admin', 'owner'],
 *     rolePermissions: {
 *       viewer: [{ resource: 'posts', action: 'read' }],
 *       editor: [{ resource: 'posts', action: 'manage' }],
 *       admin: [{ resource: '*', action: 'manage' }],
 *     },
 *   });
 *
 *   rbac.canAccess(user, { resource: 'posts', action: 'update' }); // true/false
 */
export function createRBACEvaluator(config: RBACConfig) {
  return {
    canAccess: (user: VibeAuthUser | null, permission: Permission) =>
      hasPermission(user, permission, config),

    meetsRole: (user: VibeAuthUser | null, minimumRole: string) =>
      hasMinimumRole(user, minimumRole, config.roleHierarchy),

    getUserPermissions: (user: VibeAuthUser | null): Permission[] => {
      if (!user || !user.role) return [];
      return config.rolePermissions[user.role] ?? [];
    },
  };
}
