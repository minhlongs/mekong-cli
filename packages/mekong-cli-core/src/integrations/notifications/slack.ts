/** Slack webhook sender — HTTP POST, no SDK required */
import type { Result } from '../../types/common.js';
import { ok, err } from '../../types/common.js';

export interface SlackPayload {
  text: string;
  channel?: string;
  username?: string;
  icon_emoji?: string;
  blocks?: unknown[];
  attachments?: unknown[];
}

export class SlackNotifier {
  async send(webhookUrl: string, message: string, channel?: string): Promise<Result<void>> {
    const payload: SlackPayload = { text: message };
    if (channel) payload.channel = channel;

    try {
      const response = await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const body = await response.text();
        return err(new Error(`Slack webhook failed: ${response.status} ${body}`));
      }

      return ok(undefined);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async sendRich(webhookUrl: string, payload: SlackPayload): Promise<Result<void>> {
    try {
      const response = await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const body = await response.text();
        return err(new Error(`Slack webhook failed: ${response.status} ${body}`));
      }

      return ok(undefined);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }
}
