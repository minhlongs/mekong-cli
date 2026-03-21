/**
 * Cloud auth commands: signup, login, logout, whoami
 * Connects to RaaS Gateway for account management and credential storage
 */

import type { Command } from 'commander';
import type { SignupResponse } from '@mekong/raas-sdk';
import { success, error as showError, info } from '../ui/output.js';
import {
  saveCredentials,
  clearCredentials,
  loadCredentials,
  getCloudClient,
} from '../../core/raas-client.js';

const GATEWAY = 'https://raas.agencyos.network';

export function registerCloudAuthCommand(program: Command): void {
  program
    .command('signup')
    .description('Create a new RaaS account')
    .requiredOption('-n, --name <name>', 'Your name')
    .requiredOption('-e, --email <email>', 'Your email')
    .action(async (opts: { name: string; email: string }) => {
      try {
        const res = await fetch(`${GATEWAY}/v1/tenants/signup`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: opts.name, email: opts.email }),
        });
        const data = await res.json() as SignupResponse;
        if (!res.ok) {
          showError((data as unknown as { error?: string }).error ?? 'Signup failed');
          return;
        }
        saveCredentials({
          jwt: data.token,
          email: data.tenant.email,
          tenantId: data.tenant.id,
          baseUrl: GATEWAY,
        });
        success(`Account created! ${data.credits} free MCU credits.`);
        info(`Tenant ID: ${data.tenant.id}`);
        info(`Credentials saved to ~/.mekong/credentials.json`);
      } catch (err) {
        showError(err instanceof Error ? err.message : 'Network error');
      }
    });

  program
    .command('login')
    .description('Login with API key or JWT')
    .option('-k, --api-key <key>', 'API key')
    .option('-t, --token <jwt>', 'JWT token')
    .action(async (opts: { apiKey?: string; token?: string }) => {
      if (!opts.apiKey && !opts.token) {
        showError('Provide --api-key or --token');
        return;
      }
      const creds = { apiKey: opts.apiKey, jwt: opts.token, baseUrl: GATEWAY };
      saveCredentials(creds);
      // Verify credentials by fetching profile
      try {
        const client = getCloudClient();
        if (!client) { showError('Failed to create client'); return; }
        const profile = await client.tenants.getProfile();
        saveCredentials({ ...creds, email: profile.email, tenantId: profile.id });
        success(`Logged in as ${profile.id} (${profile.tier})`);
      } catch {
        clearCredentials();
        showError('Invalid credentials');
      }
    });

  program
    .command('logout')
    .description('Clear stored credentials')
    .action(() => {
      clearCredentials();
      success('Logged out. Credentials cleared.');
    });

  program
    .command('whoami')
    .description('Show current identity and account details')
    .action(async () => {
      const creds = loadCredentials();
      if (!creds.jwt && !creds.apiKey) {
        info('Not logged in. Run: mekong signup or mekong login');
        return;
      }
      try {
        const client = getCloudClient();
        if (!client) { showError('No client available'); return; }
        const profile = await client.tenants.getProfile();
        info(`Tenant: ${profile.id}`);
        info(`Name:   ${profile.name}`);
        info(`Email:  ${profile.email}`);
        info(`Tier:   ${profile.tier}`);
        info(`Credits: ${profile.credits}`);
      } catch {
        showError('Session expired. Run: mekong login');
      }
    });
}
