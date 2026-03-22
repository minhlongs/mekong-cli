/**
 * Notifications Hub Templates Service — CRUD and seeding for notification_templates
 * Used by notifications-hub-service.ts for template-driven dispatch
 */

import type { D1Database } from '@cloudflare/workers-types';

// ── Types ──────────────────────────────────────────────────────────────────────

export interface NotificationTemplate {
  id: string;
  event_type: string;
  subject_template: string;
  body_template: string;
  channels: string; // JSON array string
  created_at: string;
}

// ── Queries ────────────────────────────────────────────────────────────────────

/** Get a single template by event_type */
export async function getTemplate(db: D1Database, eventType: string): Promise<NotificationTemplate | null> {
  return db
    .prepare('SELECT * FROM notification_templates WHERE event_type = ?')
    .bind(eventType)
    .first<NotificationTemplate>();
}

/** List all templates ordered alphabetically by event_type */
export async function listTemplates(db: D1Database): Promise<NotificationTemplate[]> {
  const rows = await db
    .prepare('SELECT * FROM notification_templates ORDER BY event_type ASC')
    .all<NotificationTemplate>();
  return rows.results;
}

/** Create or update a notification template (upsert on event_type) */
export async function upsertTemplate(
  db: D1Database,
  eventType: string,
  subject: string,
  body: string,
  channels: string[]
): Promise<NotificationTemplate> {
  const id = crypto.randomUUID();
  await db
    .prepare(
      `INSERT INTO notification_templates (id, event_type, subject_template, body_template, channels)
       VALUES (?, ?, ?, ?, ?)
       ON CONFLICT(event_type) DO UPDATE SET
         subject_template = excluded.subject_template,
         body_template    = excluded.body_template,
         channels         = excluded.channels`
    )
    .bind(id, eventType, subject, body, JSON.stringify(channels))
    .run();

  return (await getTemplate(db, eventType))!;
}

// ── Seed ───────────────────────────────────────────────────────────────────────

const DEFAULT_TEMPLATES: {
  event_type: string;
  subject: string;
  body: string;
  channels: string[];
}[] = [
  {
    event_type: 'mission_completed',
    subject: 'Mission "{{title}}" completed',
    body: 'Your mission "{{title}}" finished successfully. Result: {{result}}',
    channels: ['in_app', 'email'],
  },
  {
    event_type: 'budget_alert',
    subject: 'Budget alert: {{percent}}% used',
    body: 'You have used {{percent}}% of your {{period}} budget. Remaining: {{remaining}} credits.',
    channels: ['in_app', 'email'],
  },
  {
    event_type: 'team_invite',
    subject: '{{inviter}} invited you to {{team}}',
    body: '{{inviter}} has invited you to join the team "{{team}}". Click here to accept.',
    channels: ['in_app', 'email'],
  },
  {
    event_type: 'webhook_failure',
    subject: 'Webhook delivery failed for {{endpoint}}',
    body: 'Webhook to {{endpoint}} failed after {{attempts}} attempts. Error: {{error}}',
    channels: ['in_app'],
  },
  {
    event_type: 'credit_low',
    subject: 'Low credits: {{balance}} remaining',
    body: 'Your credit balance is low ({{balance}} credits). Top up to avoid service interruption.',
    channels: ['in_app', 'email'],
  },
];

/** Seed platform-default notification templates — idempotent via upsert */
export async function seedDefaultTemplates(db: D1Database): Promise<number> {
  let seeded = 0;
  for (const t of DEFAULT_TEMPLATES) {
    await upsertTemplate(db, t.event_type, t.subject, t.body, t.channels);
    seeded++;
  }
  return seeded;
}
