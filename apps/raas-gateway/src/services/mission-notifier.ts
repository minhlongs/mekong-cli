/**
 * Mission Notifier — handles Telegram notifications and webhook delivery for completed missions
 */

import type { Env } from '../index';

export class MissionNotifier {
  constructor(private env: Env) {}

  /**
   * Send Telegram notification when mission completes
   */
  async notifyTelegram(tenantId: string, missionId: string, result: string): Promise<void> {
    const botToken = (this.env as any).TELEGRAM_BOT_TOKEN;
    if (!botToken) return;

    const tenant = await this.env.DB.prepare(
      'SELECT telegram_chat_id FROM tenants WHERE id = ?'
    ).bind(tenantId).first<{ telegram_chat_id: string }>();

    if (!tenant?.telegram_chat_id) return;

    const text = `Mission ${missionId.slice(0, 8)}... completed!\n\n${result.slice(0, 3500)}`;
    try {
      await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: parseInt(tenant.telegram_chat_id), text }),
      });
    } catch (error) {
      console.error('[Notifier] Telegram notify failed:', error);
    }
  }

  /**
   * Get callback URL from mission metadata
   */
  async getCallbackUrl(missionId: string): Promise<string | null> {
    const row = await this.env.DB.prepare(
      'SELECT metadata FROM missions WHERE id = ?'
    ).bind(missionId).first<{ metadata: string }>();

    if (!row?.metadata) return null;
    try {
      const meta = JSON.parse(row.metadata);
      return meta.callback_url || null;
    } catch { return null; }
  }

  /**
   * Deliver webhook with exponential backoff retry (immediate, 1s, 5s).
   * Returns true if delivered, false if all retries exhausted.
   */
  async deliverWebhook(url: string, payload: unknown, maxRetries = 3): Promise<boolean> {
    const delays = [0, 1000, 5000];

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      if (attempt > 0) {
        await new Promise(r => setTimeout(r, delays[attempt] || 5000));
      }

      try {
        const resp = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-Webhook-Attempt': String(attempt + 1) },
          body: JSON.stringify(payload),
        });

        // 2xx or 4xx = stop retrying (4xx won't fix itself on retry)
        if (resp.ok || resp.status < 500) return true;
      } catch {
        // Network error — will retry
      }
    }

    return false;
  }
}
