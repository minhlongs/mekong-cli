/** Telegram Bot API sender — uses fetch, no SDK */
import type { Result } from '../../types/common.js';
import { ok, err } from '../../types/common.js';

const TELEGRAM_API = 'https://api.telegram.org';

export type TelegramParseMode = 'HTML' | 'Markdown' | 'MarkdownV2';

export interface TelegramSendOptions {
  parseMode?: TelegramParseMode;
  disableNotification?: boolean;
  disableWebPagePreview?: boolean;
}

interface TelegramApiResponse {
  ok: boolean;
  result?: { message_id: number };
  description?: string;
}

export class TelegramNotifier {
  async send(
    botToken: string,
    chatId: string | number,
    message: string,
    options?: TelegramSendOptions,
  ): Promise<Result<number>> {
    const url = `${TELEGRAM_API}/bot${botToken}/sendMessage`;
    const body: Record<string, unknown> = {
      chat_id: chatId,
      text: message,
    };
    if (options?.parseMode) body['parse_mode'] = options.parseMode;
    if (options?.disableNotification) body['disable_notification'] = true;
    if (options?.disableWebPagePreview) body['disable_web_page_preview'] = true;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      const data = await response.json() as TelegramApiResponse;

      if (!data.ok) {
        return err(new Error(`Telegram API error: ${data.description ?? 'unknown'}`));
      }

      return ok(data.result?.message_id ?? 0);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async sendMarkdown(botToken: string, chatId: string | number, markdown: string): Promise<Result<number>> {
    return this.send(botToken, chatId, markdown, { parseMode: 'Markdown' });
  }

  async sendHtml(botToken: string, chatId: string | number, html: string): Promise<Result<number>> {
    return this.send(botToken, chatId, html, { parseMode: 'HTML' });
  }
}
