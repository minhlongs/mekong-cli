/**
 * @agencyos/vibe-notifications — Multi-Channel Notification Hub SDK
 *
 * Unified notification delivery across email, push, SMS, Telegram, in-app.
 * Template engine, user preferences, delivery tracking.
 *
 * Usage:
 *   import { createNotificationHub, NotificationChannel } from '@agencyos/vibe-notifications';
 *   const hub = createNotificationHub();
 *   hub.route({ userId: '...', type: 'order_confirmed', data: {...} });
 */

// ─── Types ──────────────────────────────────────────────────────

export type NotificationChannel = 'email' | 'push' | 'sms' | 'telegram' | 'in_app';
export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent';
export type DeliveryStatus = 'queued' | 'sent' | 'delivered' | 'failed' | 'read';

export interface Notification {
  id: string;
  userId: string;
  type: string;
  channel: NotificationChannel;
  priority: NotificationPriority;
  title: string;
  body: string;
  data?: Record<string, unknown>;
  status: DeliveryStatus;
  createdAt: string;
  sentAt?: string;
  readAt?: string;
}

export interface UserPreferences {
  userId: string;
  channels: Record<NotificationChannel, boolean>;
  quietHours?: { start: string; end: string }; // "22:00" - "07:00"
  frequency: 'realtime' | 'hourly_digest' | 'daily_digest';
}

export interface NotificationTemplate {
  type: string;
  channels: NotificationChannel[];
  priority: NotificationPriority;
  titleTemplate: string;
  bodyTemplate: string;
}

// ─── Template Engine ────────────────────────────────────────────

export function createTemplateEngine() {
  return {
    /**
     * Render template with data interpolation
     * Supports {{variable}} syntax
     */
    render(template: string, data: Record<string, string | number>): string {
      return template.replace(/\{\{(\w+)\}\}/g, (_, key) => String(data[key] ?? `{{${key}}}`));
    },
  };
}

// ─── Notification Hub ───────────────────────────────────────────

export function createNotificationHub() {
  const templateEngine = createTemplateEngine();

  return {
    /**
     * Determine which channels to use based on user prefs + template config
     */
    resolveChannels(
      template: NotificationTemplate,
      preferences: UserPreferences,
    ): NotificationChannel[] {
      return template.channels.filter((ch) => preferences.channels[ch] !== false);
    },

    /**
     * Check if notification should be delayed (quiet hours)
     */
    isQuietHours(preferences: UserPreferences): boolean {
      if (!preferences.quietHours) return false;
      const now = new Date();
      const currentTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
      const { start, end } = preferences.quietHours;

      // Handle overnight quiet hours (e.g., 22:00 - 07:00)
      if (start > end) {
        return currentTime >= start || currentTime < end;
      }
      return currentTime >= start && currentTime < end;
    },

    /**
     * Build notification from template + data
     */
    buildFromTemplate(
      template: NotificationTemplate,
      data: Record<string, string | number>,
      channel: NotificationChannel,
    ): Omit<Notification, 'id' | 'userId' | 'status' | 'createdAt'> {
      return {
        type: template.type,
        channel,
        priority: template.priority,
        title: templateEngine.render(template.titleTemplate, data),
        body: templateEngine.render(template.bodyTemplate, data),
        data: data as Record<string, unknown>,
      };
    },

    /**
     * Prioritize notification queue — urgent first, then by age
     */
    sortByPriority(notifications: Notification[]): Notification[] {
      const priorityOrder: Record<NotificationPriority, number> = { urgent: 0, high: 1, normal: 2, low: 3 };
      return [...notifications].sort((a, b) => {
        const pDiff = priorityOrder[a.priority] - priorityOrder[b.priority];
        if (pDiff !== 0) return pDiff;
        return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
      });
    },
  };
}
