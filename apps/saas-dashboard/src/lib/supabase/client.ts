import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import type { Database } from '@/types/database';

/**
 * Browser client - dùng trong React components
 * Lưu ý: Chỉ dùng cho client-side, không dùng trong Server Components
 */
export function createBrowserClient(): SupabaseClient<Database> {
  return createClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}

/**
 * Server client - dùng trong Server Components, API Routes, Server Actions
 * Sử dụng service role key cho admin operations
 */
export function createServerClient(): SupabaseClient<Database> {
  return createClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
      },
    }
  );
}

/**
 * Server client với user context - dùng khi cần RLS
 * Truyền JWT token từ user session
 */
export function createServerClientWithUser(
  accessToken: string
): SupabaseClient<Database> {
  return createClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      global: {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      },
      auth: {
        autoRefreshToken: false,
        persistSession: false,
      },
    }
  );
}
