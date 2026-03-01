/**
 * @agencyos/vibe-auth — Supabase Auth Provider
 *
 * Concrete implementation of VibeAuthProvider for Supabase.
 * Extracted from apps/well, apps/apex-os, apps/com-anh-duong-10x patterns.
 *
 * Usage:
 *   import { createSupabaseAuthProvider } from '@agencyos/vibe-auth/supabase';
 *   const auth = createSupabaseAuthProvider(supabaseClient);
 *   const result = await auth.signIn('user@example.com', 'password');
 */

import type {
  VibeAuthProvider,
  VibeAuthResult,
  VibeAuthSession,
  VibeAuthUser,
  VibeAuthError,
  AuthEventCallback,
  AuthEventType,
} from './types';

// ─── Supabase Type Stubs (avoid hard dependency) ─────────────────

interface SupabaseClient {
  auth: {
    signInWithPassword(credentials: { email: string; password: string }): Promise<SupabaseAuthResponse>;
    signUp(credentials: { email: string; password: string; options?: { data?: Record<string, unknown> } }): Promise<SupabaseAuthResponse>;
    signOut(): Promise<{ error: SupabaseError | null }>;
    getSession(): Promise<{ data: { session: SupabaseSession | null }; error: SupabaseError | null }>;
    onAuthStateChange(callback: (event: string, session: SupabaseSession | null) => void): { data: { subscription: { unsubscribe: () => void } } };
  };
}

interface SupabaseSession {
  access_token: string;
  refresh_token?: string;
  expires_at?: number;
  user: SupabaseUser;
}

interface SupabaseUser {
  id: string;
  email?: string;
  user_metadata?: Record<string, unknown>;
  app_metadata?: Record<string, unknown>;
}

interface SupabaseError {
  message: string;
  status?: number;
}

interface SupabaseAuthResponse {
  data: { session: SupabaseSession | null; user: SupabaseUser | null };
  error: SupabaseError | null;
}

// ─── Event Mapping ──────────────────────────────────────────────

const SUPABASE_EVENT_MAP: Record<string, AuthEventType> = {
  SIGNED_IN: 'SIGNED_IN',
  SIGNED_OUT: 'SIGNED_OUT',
  TOKEN_REFRESHED: 'TOKEN_REFRESHED',
  USER_UPDATED: 'USER_UPDATED',
};

// ─── Mapper Helpers ─────────────────────────────────────────────

function mapSupabaseUser(user: SupabaseUser): VibeAuthUser {
  const meta = user.user_metadata ?? {};
  const appMeta = user.app_metadata ?? {};
  const role = (appMeta['role'] as string) ?? (meta['role'] as string);

  return {
    id: user.id,
    email: user.email ?? '',
    name: (meta['full_name'] as string) ?? (meta['name'] as string),
    role,
    isAdmin: role === 'admin' || role === 'super_admin' || role === 'founder',
    avatarUrl: meta['avatar_url'] as string | undefined,
    metadata: { ...meta, ...appMeta },
  };
}

function mapSupabaseSession(session: SupabaseSession): VibeAuthSession {
  return {
    accessToken: session.access_token,
    refreshToken: session.refresh_token,
    expiresAt: session.expires_at,
    user: mapSupabaseUser(session.user),
  };
}

function mapSupabaseError(error: SupabaseError): VibeAuthError {
  return {
    message: error.message,
    status: error.status,
    code: `supabase_${error.status ?? 'unknown'}`,
  };
}

// ─── Provider Implementation ────────────────────────────────────

class SupabaseAuthProvider implements VibeAuthProvider {
  readonly name = 'supabase' as const;
  private client: SupabaseClient;

  constructor(client: SupabaseClient) {
    this.client = client;
  }

  async signIn(email: string, password: string): Promise<VibeAuthResult<VibeAuthSession>> {
    const { data, error } = await this.client.auth.signInWithPassword({ email, password });

    if (error) {
      return { data: null, error: mapSupabaseError(error) };
    }

    if (!data.session) {
      return { data: null, error: { message: 'No session returned', code: 'no_session' } };
    }

    return { data: mapSupabaseSession(data.session), error: null };
  }

  async signUp(
    email: string,
    password: string,
    metadata?: Record<string, unknown>,
  ): Promise<VibeAuthResult<VibeAuthSession>> {
    const { data, error } = await this.client.auth.signUp({
      email,
      password,
      options: metadata ? { data: metadata } : undefined,
    });

    if (error) {
      return { data: null, error: mapSupabaseError(error) };
    }

    if (!data.session) {
      return { data: null, error: { message: 'Email confirmation required', code: 'confirmation_required' } };
    }

    return { data: mapSupabaseSession(data.session), error: null };
  }

  async signOut(): Promise<VibeAuthResult<void>> {
    const { error } = await this.client.auth.signOut();

    if (error) {
      return { data: null, error: mapSupabaseError(error) };
    }

    return { data: undefined, error: null };
  }

  async getSession(): Promise<VibeAuthSession | null> {
    const { data, error } = await this.client.auth.getSession();

    if (error || !data.session) return null;

    return mapSupabaseSession(data.session);
  }

  onAuthStateChange(callback: AuthEventCallback): () => void {
    const { data: { subscription } } = this.client.auth.onAuthStateChange(
      (event: string, session: SupabaseSession | null) => {
        const mappedType = SUPABASE_EVENT_MAP[event];
        if (mappedType) {
          callback({
            type: mappedType,
            session: session ? mapSupabaseSession(session) : null,
          });
        }
      },
    );

    return () => subscription.unsubscribe();
  }

  isConfigured(): boolean {
    return !!this.client;
  }
}

// ─── Factory ─────────────────────────────────────────────────────

/**
 * Create a Supabase-backed VibeAuthProvider.
 *
 * @param client - Supabase client instance (from createClient())
 * @returns VibeAuthProvider implementation
 */
export function createSupabaseAuthProvider(client: SupabaseClient): VibeAuthProvider {
  return new SupabaseAuthProvider(client);
}

export { mapSupabaseUser, mapSupabaseSession };
