import type { Result } from '../types/common.js';

/** Base interface for all integrations */
export interface Integration {
  name: string;
  connected: boolean;
  connect(credentials: IntegrationCredentials): Promise<Result<void>>;
  disconnect(): Promise<void>;
  healthCheck(): Promise<boolean>;
}

/** Credential types per integration */
export type IntegrationCredentials =
  | { type: 'api_key'; key: string }
  | { type: 'oauth'; clientId: string; clientSecret: string; refreshToken: string }
  | { type: 'smtp'; host: string; port: number; user: string; pass: string; secure: boolean }
  | { type: 'webhook'; url: string; secret?: string };

/** Integration registry entry */
export interface IntegrationEntry {
  integration: Integration;
  credentials?: IntegrationCredentials;
  lastHealthCheck?: string;
  enabled: boolean;
}

/** Notification payload — unified across channels */
export interface NotificationPayload {
  channel: 'slack' | 'telegram' | 'email';
  to: string;                     // channel ID, chat ID, or email
  subject?: string;               // email only
  message: string;                // plain text or markdown
  priority: 'low' | 'normal' | 'high' | 'critical';
  metadata?: Record<string, unknown>;
}
