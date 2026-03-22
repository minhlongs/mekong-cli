/**
 * Tenant Notification Preferences Service
 * Manages notification settings and channel configurations per tenant
 */

export const tenantNotificationPreferencesService = {
  /** List all notification preferences for a tenant */
  async listPreferences(db: any, tenantId: string) {
    try {
      const { results } = await db
        .prepare('SELECT * FROM notification_preferences WHERE tenant_id = ? ORDER BY created_at DESC')
        .bind(tenantId)
        .all();
      return { success: true, data: { preferences: results } };
    } catch (err) {
      console.error('[notification-preferences] listPreferences error', err);
      return { success: false, error: 'Failed to list preferences' };
    }
  },

  /** Create a new notification preference for a tenant */
  async createPreference(db: any, tenantId: string, data: Record<string, any>) {
    try {
      const id = crypto.randomUUID();
      const now = new Date().toISOString();
      await db
        .prepare(
          `INSERT INTO notification_preferences
           (id, tenant_id, channel, event_type, enabled, frequency, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
        )
        .bind(
          id,
          tenantId,
          data.channel ?? 'email',
          data.event_type,
          data.enabled ?? 1,
          data.frequency ?? 'immediate',
          now,
          now
        )
        .run();
      return { success: true, data: { id, tenant_id: tenantId, ...data, created_at: now, updated_at: now } };
    } catch (err) {
      console.error('[notification-preferences] createPreference error', err);
      return { success: false, error: 'Failed to create preference' };
    }
  },

  /** List all notification channels for a tenant */
  async getChannels(db: any, tenantId: string) {
    try {
      const { results } = await db
        .prepare('SELECT * FROM notification_channels WHERE tenant_id = ? ORDER BY created_at DESC')
        .bind(tenantId)
        .all();
      return { success: true, data: { channels: results } };
    } catch (err) {
      console.error('[notification-preferences] getChannels error', err);
      return { success: false, error: 'Failed to get channels' };
    }
  },

  /** Admin overview — counts across all tenants */
  async getAdminOverview(db: any) {
    try {
      const [preferences, channels] = await Promise.all([
        db.prepare('SELECT COUNT(*) as count, channel, enabled FROM notification_preferences GROUP BY channel, enabled').all(),
        db.prepare('SELECT COUNT(*) as count, channel_type, verified FROM notification_channels GROUP BY channel_type, verified').all(),
      ]);
      return {
        success: true,
        data: {
          preferences: preferences.results,
          channels: channels.results,
        },
      };
    } catch (err) {
      console.error('[notification-preferences] getAdminOverview error', err);
      return { success: false, error: 'Failed to get admin overview' };
    }
  },
};
