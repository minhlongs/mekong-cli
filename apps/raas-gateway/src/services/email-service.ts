/**
 * EmailService — Resend API integration for transactional emails
 * Docs: https://resend.com/docs/api-reference/emails/send-email
 * Fire-and-forget pattern: never throws, logs and returns true when API key missing
 */

const FROM = 'Mekong RaaS <noreply@mekong.dev>';
const RESEND_ENDPOINT = 'https://api.resend.com/emails';

export class EmailService {
  private apiKey: string | undefined;

  constructor(env: { RESEND_API_KEY?: string }) {
    this.apiKey = env.RESEND_API_KEY;
  }

  /** Core send — POST to Resend HTTP API. Never throws. */
  async send(to: string, subject: string, html: string): Promise<boolean> {
    if (!this.apiKey) {
      console.log(`[Email] No RESEND_API_KEY — skipping email to ${to}: ${subject}`);
      return true;
    }
    try {
      const res = await fetch(RESEND_ENDPOINT, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ from: FROM, to: [to], subject, html }),
      });
      if (!res.ok) {
        const body = await res.text();
        console.error(`[Email] Resend error ${res.status}: ${body}`);
        return false;
      }
      return true;
    } catch (err) {
      console.error(`[Email] Failed to send to ${to}:`, err);
      return false;
    }
  }

  /** Welcome email with 10 free credits mention. Extra args accepted for backward compat. */
  async sendWelcome(email: string, name: string, _referralCode?: string, _credits?: number): Promise<boolean> {
    return this.send(
      email,
      `Welcome to Mekong RaaS, ${name}!`,
      `<div style="font-family:system-ui;max-width:600px;margin:0 auto;padding:20px">
        <h1 style="color:#06b6d4">Welcome to Mekong RaaS!</h1>
        <p>Hi ${name}, we've added <strong>10 free credits</strong> to your account to get you started.</p>
        <p>Submit your first mission and experience AI-driven automation at the edge.</p>
        <a href="https://app.agencyos.network/dashboard"
           style="display:inline-block;background:#06b6d4;color:#000;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold">
          Go to Dashboard &rarr;
        </a>
        <p style="color:#666;font-size:12px;margin-top:20px">Mekong RaaS</p>
      </div>`
    );
  }

  /** Mission completion notification */
  async sendMissionComplete(
    email: string,
    missionGoal: string,
    result: string
  ): Promise<boolean> {
    return this.send(
      email,
      `Mission Complete: ${missionGoal}`,
      `<div style="font-family:system-ui;max-width:600px;margin:0 auto;padding:20px">
        <h2 style="color:#06b6d4">Mission Accomplished</h2>
        <p><strong>Goal:</strong> ${missionGoal}</p>
        <p><strong>Result:</strong></p>
        <pre style="background:#f4f4f4;padding:12px;border-radius:4px;white-space:pre-wrap">${result}</pre>
        <p style="color:#666;font-size:12px;margin-top:20px">Mekong RaaS</p>
      </div>`
    );
  }

  /** Payment warning dunning email */
  async sendDunningWarning(email: string, daysLeft: number): Promise<boolean> {
    const dayLabel = daysLeft === 1 ? 'day' : 'days';
    return this.send(
      email,
      `Action Required: ${daysLeft} ${dayLabel} left on your plan`,
      `<div style="font-family:system-ui;max-width:600px;margin:0 auto;padding:20px">
        <h2 style="color:#f59e0b">Your plan is expiring soon</h2>
        <p>You have <strong>${daysLeft} ${dayLabel}</strong> remaining before your subscription ends.</p>
        <p>Renew now to avoid service interruption.</p>
        <a href="https://landing.agencyos.network#pricing"
           style="display:inline-block;background:#06b6d4;color:#000;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold">
          Manage Billing &rarr;
        </a>
        <p style="color:#666;font-size:12px;margin-top:20px">Mekong RaaS</p>
      </div>`
    );
  }

  /** Weekly digest with mission stats */
  async sendWeeklyDigest(
    email: string,
    stats: { missions: number; credits: number; topMission: string }
  ): Promise<boolean> {
    return this.send(
      email,
      'Your Weekly Mekong RaaS Digest',
      `<div style="font-family:system-ui;max-width:600px;margin:0 auto;padding:20px">
        <h2 style="color:#06b6d4">Weekly Summary</h2>
        <ul>
          <li>Missions run: <strong>${stats.missions}</strong></li>
          <li>Credits used: <strong>${stats.credits}</strong></li>
          <li>Top mission: <strong>${stats.topMission}</strong></li>
        </ul>
        <p>Keep building!</p>
        <p style="color:#666;font-size:12px;margin-top:20px">Mekong RaaS</p>
      </div>`
    );
  }

  /** Referral reward notification */
  async sendReferralBonus(
    email: string,
    referrerName: string,
    bonusCredits: number
  ): Promise<boolean> {
    return this.send(
      email,
      `You earned ${bonusCredits} credits from a referral!`,
      `<div style="font-family:system-ui;max-width:600px;margin:0 auto;padding:20px">
        <h2 style="color:#06b6d4">Referral Bonus Received</h2>
        <p><strong>${referrerName}</strong> joined Mekong RaaS using your referral link.</p>
        <p>You've been awarded <strong>${bonusCredits} credits</strong> — they're in your account now.</p>
        <p>Keep sharing and keep earning!</p>
        <p style="color:#666;font-size:12px;margin-top:20px">Mekong RaaS</p>
      </div>`
    );
  }
}
