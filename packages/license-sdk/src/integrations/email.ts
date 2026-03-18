import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import type { Brand, LicenseTier } from '../core/tiers.js';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface EmailOptions {
  to: string;
  brand: Brand;
  tier: LicenseTier;
  key: string;
  fromName?: string;
}

export interface EmailResult {
  sent: boolean;
  method: 'resend' | 'file-log';
  error?: string;
}

interface ResendPayload {
  from: string;
  to: string[];
  subject: string;
  html: string;
}

interface LogEntry extends EmailOptions {
  sentAt: string;
}

// ---------------------------------------------------------------------------
// HTML template
// ---------------------------------------------------------------------------

function buildHtmlEmail(opts: EmailOptions): string {
  const { brand, tier, key, fromName } = opts;
  const displayName = fromName ?? brand;
  const tierLabel = tier.charAt(0).toUpperCase() + tier.slice(1);

  return `<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Your ${brand} License Key</title></head>
<body style="font-family:sans-serif;background:#f9f9f9;padding:32px;margin:0">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:8px;padding:32px;box-shadow:0 2px 8px rgba(0,0,0,.08)">
    <h1 style="color:#1a1a1a;margin-top:0">Welcome to ${displayName} ${tierLabel}!</h1>
    <p style="color:#444">Thank you for your purchase. Here is your license key:</p>

    <div style="background:#f4f4f4;border:1px solid #ddd;border-radius:6px;padding:16px;margin:24px 0;text-align:center">
      <code style="font-size:18px;letter-spacing:2px;color:#1a1a1a;word-break:break-all">${key}</code>
    </div>

    <h2 style="color:#1a1a1a;font-size:16px">Activation Steps</h2>
    <ol style="color:#444;padding-left:20px;line-height:1.8">
      <li>Copy the license key above.</li>
      <li>Open your terminal and run:<br>
        <code style="background:#f4f4f4;padding:2px 6px;border-radius:4px">mekong license activate ${key}</code>
      </li>
      <li>Restart any running instances to apply your new tier.</li>
    </ol>

    <p style="color:#444">
      Need help? Visit our
      <a href="https://agencyos.network/support" style="color:#0070f3">support portal</a>
      or reply to this email.
    </p>

    <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
    <p style="color:#999;font-size:12px;margin:0">
      This key is personal and non-transferable. Keep it safe.<br>
      &copy; ${new Date().getFullYear()} ${displayName}
    </p>
  </div>
</body>
</html>`;
}

// ---------------------------------------------------------------------------
// File-log fallback
// ---------------------------------------------------------------------------

function logToFile(opts: EmailOptions): EmailResult {
  try {
    const dir = join(homedir(), '.openclaw');
    mkdirSync(dir, { recursive: true });

    const logPath = join(dir, 'email-log.json');
    let entries: LogEntry[] = [];

    try {
      entries = JSON.parse(readFileSync(logPath, 'utf8')) as LogEntry[];
    } catch {
      // file absent or malformed — start fresh
    }

    entries.push({ ...opts, sentAt: new Date().toISOString() });
    writeFileSync(logPath, JSON.stringify(entries, null, 2), 'utf8');

    return { sent: true, method: 'file-log' };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { sent: false, method: 'file-log', error: message };
  }
}

// ---------------------------------------------------------------------------
// Resend sender
// ---------------------------------------------------------------------------

async function sendViaResend(
  apiKey: string,
  opts: EmailOptions,
): Promise<EmailResult> {
  const fromName = opts.fromName ?? opts.brand;
  const subject  = `Your ${opts.brand} ${opts.tier} license key`;

  const payload: ResendPayload = {
    from:    `${fromName} <licenses@agencyos.network>`,
    to:      [opts.to],
    subject,
    html:    buildHtmlEmail(opts),
  };

  const response = await fetch('https://api.resend.com/emails', {
    method:  'POST',
    headers: {
      'Content-Type':  'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text().catch(() => response.statusText);
    return { sent: false, method: 'resend', error: `Resend API ${response.status}: ${text}` };
  }

  return { sent: true, method: 'resend' };
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Send a license key delivery email.
 * Uses Resend API when RESEND_API_KEY is set; falls back to ~/.openclaw/email-log.json.
 */
export async function sendLicenseKey(opts: EmailOptions): Promise<EmailResult> {
  const apiKey = process.env['RESEND_API_KEY'];

  if (!apiKey) {
    return logToFile(opts);
  }

  return sendViaResend(apiKey, opts);
}
