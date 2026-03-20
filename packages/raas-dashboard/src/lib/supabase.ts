/**
 * Supabase Client for RaaS Dashboard
 *
 * Environment variables (set in .env or cloudflare pages):
 * - PUBLIC_SUPABASE_URL
 * - PUBLIC_SUPABASE_ANON_KEY
 */

import { createClient, type SupabaseClient, type Session, type User } from '@supabase/supabase-js';

// Type stubs for Supabase
interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string;
          email: string;
          full_name: string | null;
          tenant_id: string | null;
          tier: string;
          created_at: string;
        };
      };
      api_keys: {
        Row: {
          id: string;
          user_id: string;
          name: string;
          key_hash: string;
          permissions: string[];
          created_at: string;
          last_used_at: string | null;
        };
      };
      usage_logs: {
        Row: {
          id: string;
          tenant_id: string;
          command: string;
          mcu_consumed: number;
          created_at: string;
        };
      };
    };
  };
}

let supabaseInstance: SupabaseClient<Database> | null = null;

export function getSupabaseClient(): SupabaseClient<Database> {
  if (!supabaseInstance) {
    const supabaseUrl = import.meta.env.PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co';
    const supabaseAnonKey = import.meta.env.PUBLIC_SUPABASE_ANON_KEY || 'placeholder';

    supabaseInstance = createClient<Database>(supabaseUrl, supabaseAnonKey, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
      },
    });
  }
  return supabaseInstance;
}

export function isSupabaseConfigured(): boolean {
  const url = import.meta.env.PUBLIC_SUPABASE_URL;
  const key = import.meta.env.PUBLIC_SUPABASE_ANON_KEY;
  return !!(url && key && url !== 'https://placeholder.supabase.co' && key !== 'placeholder');
}

export type { Session, User };
