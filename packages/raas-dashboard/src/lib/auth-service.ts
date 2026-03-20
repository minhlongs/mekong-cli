/**
 * Auth Service - Supabase Authentication
 *
 * Manages user authentication, session, and tenant context
 */

import { getSupabaseClient, isSupabaseConfigured, type Session, type User } from './supabase';

export interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  session: Session | null;
  tenantId: string | null;
  tier: string;
  error: string | null;
}

export interface TenantProfile {
  id: string;
  email: string;
  full_name: string | null;
  tenant_id: string | null;
  tier: string;
  created_at: string;
}

const API = 'https://mekong-engine.agencyos.network';

class AuthService {
  private state: AuthState = {
    isAuthenticated: false,
    isLoading: true,
    user: null,
    session: null,
    tenantId: null,
    tier: 'free',
    error: null,
  };

  private listeners: Set<(state: AuthState) => void> = new Set();

  constructor() {
    this.init();
  }

  private setState(newState: Partial<AuthState>) {
    this.state = { ...this.state, ...newState };
    this.listeners.forEach((listener) => listener(this.state));
  }

  getState(): AuthState {
    return { ...this.state };
  }

  subscribe(listener: (state: AuthState) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private async init() {
    const supabase = getSupabaseClient();

    // Check existing session
    const { data } = await supabase.auth.getSession();
    if (data.session) {
      await this.loadUserProfile(data.session);
    } else {
      // Fallback to localStorage API key auth
      const apiKey = localStorage.getItem('mk_api_key');
      if (apiKey) {
        await this.validateApiKey(apiKey);
      } else {
        this.setState({ isLoading: false });
      }
    }
  }

  private async loadUserProfile(session: Session) {
    try {
      const supabase = getSupabaseClient();
      const { data: profile } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', session.user.id)
        .single();

      this.setState({
        isAuthenticated: true,
        isLoading: false,
        user: session.user,
        session,
        tenantId: profile?.tenant_id || session.user.id,
        tier: profile?.tier || 'free',
      });

      // Sync API key for backward compatibility
      if (profile?.tenant_id) {
        localStorage.setItem('mk_api_key', `mk_${profile.tenant_id}`);
        localStorage.setItem('mk_biz_name', profile?.full_name || 'Doanh nghiệp của bạn');
      }
    } catch (error) {
      console.error('Failed to load profile:', error);
      this.setState({
        isAuthenticated: true,
        isLoading: false,
        user: session.user,
        session,
        tenantId: session.user.id,
      });
    }
  }

  private async validateApiKey(apiKey: string) {
    try {
      const response = await fetch(`${API}/v1/verify`, {
        headers: {
          Authorization: `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        this.setState({
          isAuthenticated: true,
          isLoading: false,
          tenantId: data.tenant_id,
          tier: data.tier || 'free',
        });
      } else {
        this.setState({ isLoading: false });
      }
    } catch {
      this.setState({ isLoading: false });
    }
  }

  async signIn(email: string, password: string): Promise<{ success: boolean; error?: string }> {
    const supabase = getSupabaseClient();
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });

    if (error) {
      this.setState({ error: error.message });
      return { success: false, error: error.message };
    }

    await this.loadUserProfile(data.session);
    return { success: true };
  }

  async signUp(
    email: string,
    password: string,
    fullName: string,
  ): Promise<{ success: boolean; error?: string }> {
    const supabase = getSupabaseClient();
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
        },
      },
    });

    if (error) {
      this.setState({ error: error.message });
      return { success: false, error: error.message };
    }

    return { success: true };
  }

  async signOut(): Promise<void> {
    const supabase = getSupabaseClient();
    await supabase.auth.signOut();
    localStorage.removeItem('mk_api_key');
    localStorage.removeItem('mk_biz_name');
    this.setState({
      isAuthenticated: false,
      user: null,
      session: null,
      tenantId: null,
      tier: 'free',
    });
  }

  onAuthStateChange(callback: (event: string, session: Session | null) => void): () => void {
    const supabase = getSupabaseClient();
    const { data } = supabase.auth.onAuthStateChange(callback);
    return () => data.subscription.unsubscribe();
  }

  async generateApiKey(name: string, permissions: string[]): Promise<{ key?: string; error?: string }> {
    try {
      const supabase = getSupabaseClient();
      const { data: session } = await supabase.auth.getSession();

      if (!session.session) {
        return { error: 'Not authenticated' };
      }

      // Generate key via backend
      const response = await fetch(`${API}/v1/api-keys`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${session.session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, permissions }),
      });

      if (!response.ok) {
        return { error: 'Failed to generate API key' };
      }

      return await response.json();
    } catch (error) {
      return { error: 'Network error' };
    }
  }

  async revokeApiKey(keyId: string): Promise<{ success: boolean }> {
    try {
      const supabase = getSupabaseClient();
      const { data: session } = await supabase.auth.getSession();

      if (!session.session) {
        return { success: false };
      }

      const response = await fetch(`${API}/v1/api-keys/${keyId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${session.session.access_token}`,
        },
      });

      return { success: response.ok };
    } catch {
      return { success: false };
    }
  }

  async getUsageStats(days: number = 30) {
    try {
      const supabase = getSupabaseClient();
      const { data: session } = await supabase.auth.getSession();

      if (!session.session || !this.state.tenantId) {
        return null;
      }

      const response = await fetch(`${API}/v1/usage/stats?days=${days}`, {
        headers: {
          Authorization: `Bearer ${session.session.access_token}`,
        },
      });

      if (!response.ok) {
        return null;
      }

      return await response.json();
    } catch {
      return null;
    }
  }

  async getBillingInfo() {
    try {
      const supabase = getSupabaseClient();
      const { data: session } = await supabase.auth.getSession();

      if (!session.session) {
        return null;
      }

      const response = await fetch(`${API}/billing/credits`, {
        headers: {
          Authorization: `Bearer ${session.session.access_token}`,
        },
      });

      if (!response.ok) {
        return null;
      }

      return await response.json();
    } catch {
      return null;
    }
  }

  async getPaymentUrl(tier: string): Promise<{ url?: string; error?: string }> {
    try {
      const supabase = getSupabaseClient();
      const { data: session } = await supabase.auth.getSession();

      if (!session.session) {
        return { error: 'Not authenticated' };
      }

      const response = await fetch(`${API}/billing/payment-url`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${session.session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ tier }),
      });

      if (!response.ok) {
        return { error: 'Failed to generate payment URL' };
      }

      return await response.json();
    } catch {
      return { error: 'Network error' };
    }
  }
}

export const authService = new AuthService();
export { API };
