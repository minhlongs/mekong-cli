/**
 * Admin Platform Notifications Service
 * CRUD for platform_notifications + platform_notification_deliveries tables
 * All functions: db: any, try/catch, return { success, data/error }
 */

// List all platform notifications, optional ?notification_type= filter
async function listNotifications(
  db: any,
  notification_type?: string
): Promise<{ success: boolean; data?: any[]; error?: string }> {
  try {
    let stmt: any;
    if (notification_type) {
      stmt = db
        .prepare(
          `SELECT * FROM platform_notifications WHERE notification_type = ? ORDER BY created_at DESC`
        )
        .bind(notification_type);
    } else {
      stmt = db.prepare(
        `SELECT * FROM platform_notifications ORDER BY created_at DESC`
      );
    }
    const result = await stmt.all();
    return { success: true, data: result.results ?? [] };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Insert a new platform notification
async function createNotification(
  db: any,
  payload: {
    id: string;
    title: string;
    message: string;
    notification_type?: string;
    target_audience?: string;
    published_at?: string;
  }
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const {
      id,
      title,
      message,
      notification_type = 'info',
      target_audience = 'all',
      published_at,
    } = payload;
    const now = new Date().toISOString();
    await db
      .prepare(
        `INSERT INTO platform_notifications
           (id, title, message, notification_type, target_audience, read_count, published_at, created_at)
         VALUES (?, ?, ?, ?, ?, 0, ?, ?)`
      )
      .bind(id, title, message, notification_type, target_audience, published_at ?? null, now)
      .run();
    return {
      success: true,
      data: { id, title, message, notification_type, target_audience, read_count: 0, published_at: published_at ?? null, created_at: now },
    };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// List delivery records, optional ?notification_id= filter
async function getDeliveries(
  db: any,
  notification_id?: string
): Promise<{ success: boolean; data?: any[]; error?: string }> {
  try {
    let stmt: any;
    if (notification_id) {
      stmt = db
        .prepare(
          `SELECT * FROM platform_notification_deliveries WHERE notification_id = ? ORDER BY created_at DESC`
        )
        .bind(notification_id);
    } else {
      stmt = db.prepare(
        `SELECT * FROM platform_notification_deliveries ORDER BY created_at DESC`
      );
    }
    const result = await stmt.all();
    return { success: true, data: result.results ?? [] };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Aggregated dashboard: totals + unread count + per-type breakdown
async function getDashboard(
  db: any
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const [totals, byType, deliveryStats] = await Promise.all([
      db
        .prepare(
          `SELECT COUNT(*) as total_notifications,
                  COALESCE(SUM(read_count), 0) as total_reads
           FROM platform_notifications`
        )
        .first(),
      db
        .prepare(
          `SELECT notification_type, COUNT(*) as count
           FROM platform_notifications
           GROUP BY notification_type
           ORDER BY count DESC`
        )
        .all(),
      db
        .prepare(
          `SELECT COUNT(*) as total_deliveries,
                  COUNT(read_at) as total_read_deliveries
           FROM platform_notification_deliveries`
        )
        .first(),
    ]);

    return {
      success: true,
      data: {
        total_notifications: totals?.total_notifications ?? 0,
        total_reads: totals?.total_reads ?? 0,
        total_deliveries: deliveryStats?.total_deliveries ?? 0,
        total_read_deliveries: deliveryStats?.total_read_deliveries ?? 0,
        by_type: byType.results ?? [],
      },
    };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

export const adminPlatformNotificationsService = {
  listNotifications,
  createNotification,
  getDeliveries,
  getDashboard,
};
