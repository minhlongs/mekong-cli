/** Multi-channel notification dispatcher with priority routing and low-priority queue */
import { SlackNotifier } from './slack.js';
import { TelegramNotifier } from './telegram.js';
import type { EmailIntegration } from '../email/sender.js';
import type { NotificationPayload } from '../types.js';
import type { Result } from '../../types/common.js';
import { ok, err } from '../../types/common.js';

export interface ChannelConfig {
  slack?: { webhookUrl: string; defaultChannel?: string };
  telegram?: { botToken: string; defaultChatId: string };
  email?: { integration: EmailIntegration; defaultFrom?: string };
}

export interface DispatchResult {
  channel: string;
  success: boolean;
  error?: string;
}

export class NotificationDispatcher {
  private slack = new SlackNotifier();
  private telegram = new TelegramNotifier();
  private queue: NotificationPayload[] = [];
  private channels: ChannelConfig = {};

  configure(channels: ChannelConfig): void {
    this.channels = channels;
  }

  async dispatch(payload: NotificationPayload): Promise<Result<DispatchResult[]>> {
    try {
      const results: DispatchResult[] = [];
      switch (payload.priority) {
        case 'critical':
          // Send to all configured channels
          results.push(...await this.sendToAll(payload));
          break;
        case 'high':
          // Primary (slack/telegram) + email
          results.push(...await this.sendToPrimary(payload));
          if (this.channels.email) results.push(...await this.sendToEmail(payload));
          break;
        case 'normal':
          // Primary channel only
          results.push(...await this.sendToPrimary(payload));
          break;
        case 'low':
          // Queue for batch dispatch
          this.queue.push(payload);
          results.push({ channel: 'queue', success: true });
          break;
      }
      return ok(results);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async flushQueue(): Promise<Result<DispatchResult[]>> {
    if (this.queue.length === 0) return ok([]);
    const batch = [...this.queue];
    this.queue = [];
    const all: DispatchResult[] = [];
    for (const payload of batch) {
      const result = await this.sendToPrimary(payload);
      all.push(...result);
    }
    return ok(all);
  }

  async sendToChannel(channel: 'slack' | 'telegram' | 'email', payload: NotificationPayload): Promise<DispatchResult> {
    switch (channel) {
      case 'slack': {
        const cfg = this.channels.slack;
        if (!cfg) return { channel: 'slack', success: false, error: 'Slack not configured' };
        const target = payload.channel === 'slack' ? payload.to : cfg.defaultChannel;
        const result = await this.slack.send(cfg.webhookUrl, payload.message, target);
        return { channel: 'slack', success: result.ok, error: result.ok ? undefined : result.error.message };
      }
      case 'telegram': {
        const cfg = this.channels.telegram;
        if (!cfg) return { channel: 'telegram', success: false, error: 'Telegram not configured' };
        const chatId = payload.channel === 'telegram' ? payload.to : cfg.defaultChatId;
        const result = await this.telegram.send(cfg.botToken, chatId, payload.message);
        return { channel: 'telegram', success: result.ok, error: result.ok ? undefined : result.error.message };
      }
      case 'email': {
        const cfg = this.channels.email;
        if (!cfg) return { channel: 'email', success: false, error: 'Email not configured' };
        const result = await cfg.integration.send({
          to: payload.channel === 'email' ? payload.to : payload.to,
          subject: payload.subject ?? payload.message.slice(0, 80),
          text: payload.message,
        });
        return { channel: 'email', success: result.ok, error: result.ok ? undefined : result.error.message };
      }
    }
  }

  private async sendToPrimary(payload: NotificationPayload): Promise<DispatchResult[]> {
    const results: DispatchResult[] = [];
    if (this.channels.slack) results.push(await this.sendToChannel('slack', payload));
    else if (this.channels.telegram) results.push(await this.sendToChannel('telegram', payload));
    return results;
  }

  private async sendToEmail(payload: NotificationPayload): Promise<DispatchResult[]> {
    if (!this.channels.email) return [];
    return [await this.sendToChannel('email', payload)];
  }

  private async sendToAll(payload: NotificationPayload): Promise<DispatchResult[]> {
    const results: DispatchResult[] = [];
    if (this.channels.slack) results.push(await this.sendToChannel('slack', payload));
    if (this.channels.telegram) results.push(await this.sendToChannel('telegram', payload));
    if (this.channels.email) results.push(await this.sendToChannel('email', payload));
    return results;
  }

  getQueueLength(): number {
    return this.queue.length;
  }
}
