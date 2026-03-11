import { createServerClient, createServerClientWithUser } from './client';

/**
 * Helper để execute query với RLS enabled
 * Tự động attach user JWT vào request
 */
export async function withRLS<T>(
  accessToken: string,
  query: (client: ReturnType<typeof createServerClientWithUser>) => Promise<T>
): Promise<T> {
  const client = createServerClientWithUser(accessToken);
  return query(client);
}

/**
 * Check nếu user có quyền admin
 * Dùng trong middleware hoặc API routes
 */
export async function checkAdminRole(
  accessToken: string
): Promise<{ isAdmin: boolean; error?: string }> {
  try {
    const result = await withRLS<{ role?: string } | null>(accessToken, async (client) => {
      const { data, error } = await client
        .from('profiles')
        .select('role')
        .single();

      if (error) throw error;
      return data as { role?: string } | null;
    });

    return { isAdmin: result?.role === 'admin' };
  } catch (error) {
    return { isAdmin: false, error: 'Failed to check admin role' };
  }
}

/**
 * Helper để tạo subscription record
 * Dùng sau khi Stripe webhook xác nhận payment thành công
 */
export async function createSubscription(
  userId: string,
  stripeCustomerId: string,
  stripeSubscriptionId: string,
  plan: 'free' | 'pro' | 'enterprise'
): Promise<{ success: boolean; error?: string }> {
  try {
    const client = createServerClient();
    const { error } = await client.from('subscriptions').insert({
      user_id: userId,
      stripe_customer_id: stripeCustomerId,
      stripe_subscription_id: stripeSubscriptionId,
      status: 'active',
      plan,
      current_period_end: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    } as any);

    if (error) throw error;
    return { success: true };
  } catch (error) {
    return { success: false, error: (error as Error).message };
  }
}
