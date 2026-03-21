/**
 * Cloud RaaS client — singleton that reads credentials from ~/.mekong/credentials.json
 * Provides MekongClient for CLI commands to call gateway API
 */

import { MekongClient } from '@mekong/raas-sdk';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';

const CREDS_DIR = join(homedir(), '.mekong');
const CREDS_FILE = join(CREDS_DIR, 'credentials.json');
const DEFAULT_BASE_URL = 'https://raas.agencyos.network';

export interface Credentials {
  jwt?: string;
  apiKey?: string;
  baseUrl?: string;
  email?: string;
  tenantId?: string;
}

let _client: MekongClient | null = null;

export function loadCredentials(): Credentials {
  try {
    if (existsSync(CREDS_FILE)) {
      return JSON.parse(readFileSync(CREDS_FILE, 'utf-8')) as Credentials;
    }
  } catch { /* ignore parse errors */ }
  return {};
}

export function saveCredentials(creds: Credentials): void {
  mkdirSync(CREDS_DIR, { recursive: true });
  writeFileSync(CREDS_FILE, JSON.stringify(creds, null, 2), { mode: 0o600 });
}

export function clearCredentials(): void {
  if (existsSync(CREDS_FILE)) {
    writeFileSync(CREDS_FILE, '{}', { mode: 0o600 });
  }
  _client = null;
}

export function isAuthenticated(): boolean {
  const creds = loadCredentials();
  return !!(creds.jwt || creds.apiKey);
}

export function getCloudClient(): MekongClient | null {
  if (_client) return _client;
  const creds = loadCredentials();
  if (!creds.jwt && !creds.apiKey) return null;
  _client = new MekongClient({
    baseUrl: creds.baseUrl ?? DEFAULT_BASE_URL,
    jwt: creds.jwt,
    apiKey: creds.apiKey,
  });
  return _client;
}

export function requireCloudClient(): MekongClient {
  const client = getCloudClient();
  if (!client) {
    throw new Error('Not logged in. Run: mekong login');
  }
  return client;
}
