/** Integration registry — manages all integration instances and credentials */
import { promises as fs } from 'fs';
import { homedir } from 'os';
import { join } from 'path';
import type { Integration, IntegrationCredentials, IntegrationEntry } from './types.js';
import { ok, err } from '../types/common.js';
import type { Result } from '../types/common.js';

const CREDENTIALS_PATH = join(homedir(), '.mekong', 'credentials.json');

export class IntegrationRegistry {
  private registry = new Map<string, IntegrationEntry>();

  register(name: string, integration: Integration): void {
    this.registry.set(name, { integration, enabled: true });
  }

  async connect(name: string, credentials: IntegrationCredentials): Promise<Result<void>> {
    const entry = this.registry.get(name);
    if (!entry) return err(new Error(`Integration '${name}' not registered`));
    try {
      const result = await entry.integration.connect(credentials);
      if (result.ok) {
        entry.credentials = credentials;
        await this.saveCredentials(name, credentials);
      }
      return result;
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  get(name: string): Integration | undefined {
    return this.registry.get(name)?.integration;
  }

  async isHealthy(name: string): Promise<boolean> {
    const entry = this.registry.get(name);
    if (!entry || !entry.enabled) return false;
    try {
      const healthy = await entry.integration.healthCheck();
      entry.lastHealthCheck = new Date().toISOString();
      return healthy;
    } catch {
      return false;
    }
  }

  list(): Array<{ name: string; connected: boolean; enabled: boolean; lastHealthCheck?: string }> {
    return Array.from(this.registry.entries()).map(([name, entry]) => ({
      name,
      connected: entry.integration.connected,
      enabled: entry.enabled,
      lastHealthCheck: entry.lastHealthCheck,
    }));
  }

  private async saveCredentials(name: string, credentials: IntegrationCredentials): Promise<void> {
    const dir = join(homedir(), '.mekong');
    await fs.mkdir(dir, { recursive: true });
    let existing: Record<string, unknown> = {};
    try {
      const raw = await fs.readFile(CREDENTIALS_PATH, 'utf-8');
      existing = JSON.parse(raw) as Record<string, unknown>;
    } catch { /* file may not exist yet */ }
    existing[name] = credentials;
    const tmp = CREDENTIALS_PATH + '.tmp';
    await fs.writeFile(tmp, JSON.stringify(existing, null, 2), 'utf-8');
    await fs.rename(tmp, CREDENTIALS_PATH);
  }

  async loadCredentials(name: string): Promise<IntegrationCredentials | undefined> {
    try {
      const raw = await fs.readFile(CREDENTIALS_PATH, 'utf-8');
      const all = JSON.parse(raw) as Record<string, unknown>;
      return all[name] as IntegrationCredentials | undefined;
    } catch {
      return undefined;
    }
  }
}

export { StripeIntegration } from './stripe/client.js';
export { EmailIntegration } from './email/sender.js';
export { EmailTemplateEngine } from './email/templates.js';
export { GoogleCalendarIntegration } from './calendar/google.js';
export { SlackNotifier } from './notifications/slack.js';
export { TelegramNotifier } from './notifications/telegram.js';
export { NotificationDispatcher } from './notifications/dispatcher.js';
export type { Integration, IntegrationCredentials, IntegrationEntry, NotificationPayload } from './types.js';
