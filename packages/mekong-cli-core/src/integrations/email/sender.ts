/** SMTP email sender using nodemailer with rate limiting and template rendering */
import nodemailer from 'nodemailer';
import type { Transporter } from 'nodemailer';
import type { Integration, IntegrationCredentials } from '../types.js';
import { EmailTemplateEngine } from './templates.js';
import { ok, err } from '../../types/common.js';
import type { Result } from '../../types/common.js';

export interface EmailMessage {
  to: string | string[];
  cc?: string | string[];
  bcc?: string | string[];
  subject?: string;
  text?: string;
  html?: string;
  templateName?: string;
  templateData?: Record<string, unknown>;
  attachments?: Array<{ filename: string; path?: string; content?: string; contentType?: string }>;
  replyTo?: string;
  from?: string;
}

export interface SendResult {
  messageId: string;
  accepted: string[];
  rejected: string[];
}

const RATE_LIMIT_PER_HOUR = 20;

export class EmailIntegration implements Integration {
  readonly name = 'email';
  connected = false;
  private transporter: Transporter | null = null;
  private from = '';
  private templates = new EmailTemplateEngine();
  private sentThisHour: number[] = []; // timestamps in ms

  async connect(credentials: IntegrationCredentials): Promise<Result<void>> {
    if (credentials.type !== 'smtp') {
      return err(new Error('Email integration requires smtp credentials'));
    }
    try {
      this.transporter = nodemailer.createTransport({
        host: credentials.host,
        port: credentials.port,
        secure: credentials.secure,
        auth: { user: credentials.user, pass: credentials.pass },
      });
      await this.transporter.verify();
      this.from = credentials.user;
      this.connected = true;
      return ok(undefined);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async disconnect(): Promise<void> {
    this.transporter?.close();
    this.transporter = null;
    this.connected = false;
  }

  async healthCheck(): Promise<boolean> {
    if (!this.transporter) return false;
    try {
      await this.transporter.verify();
      return true;
    } catch {
      return false;
    }
  }

  async send(message: EmailMessage): Promise<Result<SendResult>> {
    if (!this.transporter) return err(new Error('Not connected'));

    if (!this.checkRateLimit()) {
      return err(new Error(`Rate limit exceeded: max ${RATE_LIMIT_PER_HOUR} emails/hour`));
    }

    let subject = message.subject ?? '';
    let html = message.html;
    let text = message.text;

    if (message.templateName) {
      try {
        const rendered = this.templates.render(
          message.templateName,
          message.templateData ?? {},
        );
        subject = rendered.subject;
        text = rendered.body;
      } catch (e) {
        return err(e instanceof Error ? e : new Error(String(e)));
      }
    }

    try {
      const info = await this.transporter.sendMail({
        from: message.from ?? this.from,
        to: message.to,
        cc: message.cc,
        bcc: message.bcc,
        replyTo: message.replyTo,
        subject,
        text,
        html,
        attachments: message.attachments,
      });

      this.recordSent();

      return ok({
        messageId: info.messageId as string,
        accepted: (info.accepted as string[]) ?? [],
        rejected: (info.rejected as string[]) ?? [],
      });
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  private checkRateLimit(): boolean {
    const now = Date.now();
    const oneHourAgo = now - 3600_000;
    this.sentThisHour = this.sentThisHour.filter(t => t > oneHourAgo);
    return this.sentThisHour.length < RATE_LIMIT_PER_HOUR;
  }

  private recordSent(): void {
    this.sentThisHour.push(Date.now());
  }

  getTemplateEngine(): EmailTemplateEngine {
    return this.templates;
  }
}
