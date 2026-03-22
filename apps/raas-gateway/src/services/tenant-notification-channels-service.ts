/**
 * Tenant Notification Channels service — channel management and delivery tracking
 */

export interface NotificationChannel {
  id: string;
  tenant_id: string;
  channel_type: string;
  config_json: string | null;
  is_active: number;
  created_at: string;
  updated_at: string;
}

export interface NotificationDelivery {
  id: string;
  tenant_id: string;
  channel_id: string;
  event_type: string;
  status: string;
  payload_json: string | null;
  delivered_at: string | null;
  created_at: string;
}

export interface CreateChannelData {
  channel_type: string;
  config_json?: string;
  is_active?: number;
}

export interface AdminChannelOverview {
  total_channels: number;
  active_channels: number;
  total_deliveries: number;
  pending_deliveries: number;
  failed_deliveries: number;
}

function generateId(): string {
  return `nc_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

/** List all notification channels for a tenant */
export async function listChannels(db: any, tenantId: string): Promise<NotificationChannel[]> {
  try {
    const result = await db
      .prepare('SELECT * FROM notification_channels WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return (result.results ?? []) as NotificationChannel[];
  } catch {
    return [];
  }
}

/** Create a new notification channel for a tenant */
export async function createChannel(
  db: any,
  tenantId: string,
  data: CreateChannelData
): Promise<NotificationChannel> {
  const id = generateId();
  const now = new Date().toISOString();
  const isActive = data.is_active ?? 1;
  const configJson = data.config_json ?? null;

  await db
    .prepare(
      `INSERT INTO notification_channels (id, tenant_id, channel_type, config_json, is_active, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    )
    .bind(id, tenantId, data.channel_type, configJson, isActive, now, now)
    .run();

  return {
    id,
    tenant_id: tenantId,
    channel_type: data.channel_type,
    config_json: configJson,
    is_active: isActive,
    created_at: now,
    updated_at: now,
  };
}

/** List all notification deliveries for a tenant */
export async function getDeliveries(db: any, tenantId: string): Promise<NotificationDelivery[]> {
  try {
    const result = await db
      .prepare('SELECT * FROM notification_deliveries WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return (result.results ?? []) as NotificationDelivery[];
  } catch {
    return [];
  }
}

/** Admin overview — aggregate stats across all tenants */
export async function getAdminOverview(db: any): Promise<AdminChannelOverview> {
  try {
    const channels = await db
      .prepare('SELECT COUNT(*) as total, SUM(is_active) as active FROM notification_channels')
      .first() as { total: number; active: number } | null;

    const deliveries = await db
      .prepare(
        `SELECT
           COUNT(*) as total,
           SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
           SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
         FROM notification_deliveries`
      )
      .first() as { total: number; pending: number; failed: number } | null;

    return {
      total_channels: channels?.total ?? 0,
      active_channels: channels?.active ?? 0,
      total_deliveries: deliveries?.total ?? 0,
      pending_deliveries: deliveries?.pending ?? 0,
      failed_deliveries: deliveries?.failed ?? 0,
    };
  } catch {
    return {
      total_channels: 0,
      active_channels: 0,
      total_deliveries: 0,
      pending_deliveries: 0,
      failed_deliveries: 0,
    };
  }
}

export const tenantNotificationChannelsService = {
  listChannels,
  createChannel,
  getDeliveries,
  getAdminOverview,
};
