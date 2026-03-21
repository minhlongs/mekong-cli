/**
 * Notification Template Service — create, list, and send from templates
 * Handles variable substitution with {{variable}} syntax
 */

import type { D1Database } from '@cloudflare/workers-types';
import { mapTemplate } from './notification-types';
import { sendNotification } from './notification-service';
import type {
  Notification,
  NotificationTemplate,
  CreateTemplateInput,
  SendFromTemplateInput,
} from './notification-types';

/** Create a reusable notification template */
export async function createTemplate(
  db: D1Database,
  tenantId: string,
  input: CreateTemplateInput
): Promise<NotificationTemplate> {
  const id = crypto.randomUUID();
  const variables = JSON.stringify(input.variables ?? []);

  await db
    .prepare(
      `INSERT INTO notification_templates (id, tenant_id, name, channel, subject, body_template, variables)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    )
    .bind(id, tenantId, input.name, input.channel, input.subject ?? null, input.bodyTemplate, variables)
    .run();

  const row = await db
    .prepare('SELECT * FROM notification_templates WHERE id = ?')
    .bind(id)
    .first<Record<string, unknown>>();

  return mapTemplate(row!);
}

/** List all templates for a tenant */
export async function getTemplates(db: D1Database, tenantId: string): Promise<NotificationTemplate[]> {
  const rows = await db
    .prepare('SELECT * FROM notification_templates WHERE tenant_id = ? ORDER BY created_at DESC')
    .bind(tenantId)
    .all<Record<string, unknown>>();

  return rows.results.map(mapTemplate);
}

/** Resolve {{variable}} placeholders and send notification */
export async function sendFromTemplate(
  db: D1Database,
  tenantId: string,
  input: SendFromTemplateInput
): Promise<Notification> {
  const row = await db
    .prepare('SELECT * FROM notification_templates WHERE id = ? AND tenant_id = ?')
    .bind(input.templateId, tenantId)
    .first<Record<string, unknown>>();

  if (!row) throw new Error('Template not found');

  const template = mapTemplate(row);
  const vars = input.variables ?? {};

  const resolveVars = (str: string) =>
    str.replace(/\{\{(\w+)\}\}/g, (_, key: string) => vars[key] ?? `{{${key}}}`);

  return sendNotification(db, tenantId, {
    channel: template.channel,
    recipient: input.recipient,
    subject: template.subject ? resolveVars(template.subject) : undefined,
    body: resolveVars(template.bodyTemplate),
    templateId: template.id,
  });
}
