/**
 * Email service using Resend API
 * Docs: https://resend.com/docs/api-reference/emails/send-email
 * Fire-and-forget — never blocks API responses
 */

interface D1Database {
  prepare(query: string): { bind(...values: unknown[]): { run(): Promise<unknown> } };
}

export class EmailService {
  private apiKey: string;
  private db: D1Database | null;
  private fromEmail = 'Mekong RaaS <noreply@agencyos.network>';

  constructor(env: { RESEND_API_KEY?: string; DB?: D1Database }) {
    this.apiKey = env.RESEND_API_KEY || '';
    this.db = env.DB ?? null;
  }

  /**
   * Core send — returns false if not configured or on error (never throws)
   */
  private async send(to: string, subject: string, html: string): Promise<boolean> {
    if (!this.apiKey) return false;
    try {
      const res = await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ from: this.fromEmail, to: [to], subject, html }),
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  /**
   * Welcome email sent after successful signup
   */
  async sendWelcome(
    email: string,
    name: string,
    referralCode: string,
    credits: number
  ): Promise<boolean> {
    return this.send(
      email,
      `Welcome to Mekong RaaS, ${name}!`,
      `
      <div style="font-family:system-ui;max-width:600px;margin:0 auto;padding:20px">
        <h1 style="color:#06b6d4">Welcome to Mekong RaaS!</h1>
        <p>Hi ${name}, you have <strong>${credits} MCU</strong> credits to start.</p>
        <h3>Quick Start:</h3>
        <ol>
          <li>Submit your first mission via <a href="https://raas.agencyos.network">API</a> or <a href="https://app.agencyos.network/dashboard">Dashboard</a></li>
          <li>Check results in seconds</li>
          <li>Share your referral code: <code>${referralCode}</code> for +5 MCU each</li>
        </ol>
        <a href="https://app.agencyos.network/dashboard" style="display:inline-block;background:#06b6d4;color:#000;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold">Go to Dashboard &rarr;</a>
        <p style="color:#666;margin-top:20px;font-size:12px">Mekong RaaS by AgencyOS</p>
      </div>
      `
    );
  }

  /**
   * Low credits alert — sent when balance drops below threshold
   */
  async sendLowCredits(email: string, name: string, balance: number): Promise<boolean> {
    return this.send(
      email,
      `\u26A1 Low Credits: ${balance} MCU remaining`,
      `
      <div style="font-family:system-ui;max-width:600px;margin:0 auto;padding:20px">
        <h2 style="color:#f59e0b">\u26A1 Credits Running Low</h2>
        <p>Hi ${name}, you have <strong>${balance} MCU</strong> remaining.</p>
        <p>Top up to keep your missions running:</p>
        <a href="https://landing.agencyos.network#pricing" style="display:inline-block;background:#06b6d4;color:#000;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold">Buy Credits &rarr;</a>
        <p style="color:#666;margin-top:20px;font-size:12px">Mekong RaaS by AgencyOS</p>
      </div>
      `
    );
  }

  /**
   * Win-back email — records attempt in DB then sends offer to churned tenant
   */
  async sendWinBackEmail(tenantId: string, email: string, offerCode: string): Promise<boolean> {
    if (this.db) {
      const id = crypto.randomUUID();
      await this.db
        .prepare(
          `INSERT INTO win_back_emails (id, tenant_id, email, offer_code, status, sent_at)
           VALUES (?, ?, ?, ?, 'sent', datetime('now'))`
        )
        .bind(id, tenantId, email, offerCode)
        .run();
    }
    return this.send(
      email,
      "We miss you! Here's a special offer to come back",
      `
      <div style="font-family:system-ui;max-width:600px;margin:0 auto;padding:20px">
        <h2 style="color:#06b6d4">We miss you!</h2>
        <p>We noticed you cancelled your Mekong subscription. We'd love to have you back!</p>
        <p>Use code <strong>${offerCode}</strong> to get 20% off your next month.</p>
        <a href="https://landing.agencyos.network#pricing" style="display:inline-block;background:#06b6d4;color:#000;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold">Come Back &rarr;</a>
        <p style="color:#666;margin-top:20px;font-size:12px">Mekong RaaS by AgencyOS</p>
      </div>
      `
    );
  }

  /**
   * Weekly mission digest — summarises completed missions and credit usage
   */
  async sendMissionDigest(
    _tenantId: string,
    email: string,
    stats: { completed: number; totalCredits: number; topGoals: string[]; period: string }
  ): Promise<boolean> {
    const goalsList = stats.topGoals.map((g) => `<li>${g}</li>`).join('');
    return this.send(
      email,
      `Your Mekong Weekly Digest — ${stats.completed} missions completed`,
      `
      <div style="font-family:system-ui;max-width:600px;margin:0 auto;padding:20px">
        <h2 style="color:#06b6d4">Weekly Summary (${stats.period})</h2>
        <p>Missions completed: <strong>${stats.completed}</strong></p>
        <p>Credits used: <strong>${stats.totalCredits} MCU</strong></p>
        <h3>Top missions:</h3>
        <ul>${goalsList}</ul>
        <p>Keep building!</p>
        <p style="color:#666;margin-top:20px;font-size:12px">Mekong RaaS by AgencyOS</p>
      </div>
      `
    );
  }
}
