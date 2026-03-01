/**
 * @agencyos/vibe-auth — Provider-Agnostic Auth SDK
 *
 * Reusable across all RaaS projects.
 * Route guards, auto-logout, admin checks, RBAC, middleware, Supabase provider.
 *
 * Usage:
 *   import { evaluateRouteGuard, checkAdminAccess } from '@agencyos/vibe-auth';
 *   import { createSupabaseAuthProvider } from '@agencyos/vibe-auth/supabase';
 *   import { extractAuth, parseCookies } from '@agencyos/vibe-auth/middleware';
 *   import { createRBACEvaluator, hasMinimumRole } from '@agencyos/vibe-auth/rbac';
 */

// Re-export all types
export type {
  AuthProviderName,
  VibeAuthUser,
  VibeAuthResult,
  VibeAuthError,
  VibeAuthState,
  VibeAuthSession,
  AuthEventType,
  VibeAuthEvent,
  AuthEventCallback,
  RouteGuardVerdict,
  RouteGuardConfig,
  AutoLogoutConfig,
  AdminCheckConfig,
  VibeAuthProvider,
} from './types';

// Auth guard utilities
export {
  evaluateRouteGuard,
  createAutoLogoutController,
  checkAdminAccess,
} from './auth-guard-utils';

// Supabase provider
export { createSupabaseAuthProvider } from './supabase-provider';

// Middleware utilities
export { decodeJWT, jwtToUser, parseCookies, extractAuthToken, extractAuth, validateCSRF } from './middleware-utils';

// RBAC utilities
export { hasRole, hasAnyRole, hasMinimumRole, hasPermission, createRBACEvaluator } from './rbac-utils';
