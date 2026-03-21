/**
 * Notification Service — shared types and row mapper utilities
 */

export type NotificationChannel = 'in_app' | 'email' | 'push' | 'webhook';
export type NotificationStatus = 'pending' | 'sent' | 'delivered' | 'failed' | 'read';

export interface Notification {
  id: string;
  tenantId: string;
  templateId: string | null;
  channel: NotificationChannel;
  recipient: string;
  subject: string | null;
  body: string;
  status: NotificationStatus;
  metadata: Record<string, unknown>;
  createdAt: string;
  readAt: string | null;
}

export interface NotificationTemplate {
  id: string;
  tenantId: string;
  name: string;
  channel: NotificationChannel;
  subject: string | null;
  bodyTemplate: string;
  variables: string[];
  createdAt: string;
  updatedAt: string;
}

export interface NotificationPreference {
  id: string;
  tenantId: string;
  channel: NotificationChannel;
  enabled: boolean;
  quietHoursStart: string | null;
  quietHoursEnd: string | null;
  updatedAt: string;
}

export interface SendNotificationInput {
  channel: NotificationChannel;
  recipient: string;
  subject?: string;
  body: string;
  templateId?: string;
  metadata?: Record<string, unknown>;
}

export interface ListNotificationsOptions {
  status?: NotificationStatus;
  limit?: number;
  offset?: number;
}

export interface CreateTemplateInput {
  name: string;
  channel: NotificationChannel;
  subject?: string;
  bodyTemplate: string;
  variables?: string[];
}

export interface SendFromTemplateInput {
  templateId: string;
  recipient: string;
  variables?: Record<string, string>;
}

export interface UpdatePreferenceInput {
  enabled: boolean;
  quietHoursStart?: string;
  quietHoursEnd?: string;
}

// --- Row mappers ---

export function mapNotification(row: Record<string, unknown>): Notification {
  return {
    id: row.id as string,
    tenantId: row.tenant_id as string,
    templateId: (row.template_id as string | null) ?? null,
    channel: row.channel as NotificationChannel,
    recipient: row.recipient as string,
    subject: (row.subject as string | null) ?? null,
    body: row.body as string,
    status: row.status as NotificationStatus,
    metadata: JSON.parse((row.metadata as string) || '{}'),
    createdAt: row.created_at as string,
    readAt: (row.read_at as string | null) ?? null,
  };
}

export function mapTemplate(row: Record<string, unknown>): NotificationTemplate {
  return {
    id: row.id as string,
    tenantId: row.tenant_id as string,
    name: row.name as string,
    channel: row.channel as NotificationChannel,
    subject: (row.subject as string | null) ?? null,
    bodyTemplate: row.body_template as string,
    variables: JSON.parse((row.variables as string) || '[]'),
    createdAt: row.created_at as string,
    updatedAt: row.updated_at as string,
  };
}

export function mapPreference(row: Record<string, unknown>): NotificationPreference {
  return {
    id: row.id as string,
    tenantId: row.tenant_id as string,
    channel: row.channel as NotificationChannel,
    enabled: Boolean(row.enabled),
    quietHoursStart: (row.quiet_hours_start as string | null) ?? null,
    quietHoursEnd: (row.quiet_hours_end as string | null) ?? null,
    updatedAt: row.updated_at as string,
  };
}
