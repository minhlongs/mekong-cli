/**
 * Telegram bot webhook handler
 * Commands: /start, /submit, /credits, /missions, /help
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { AuthService } from '../services/auth-service';
import { CreditService } from '../services/credit-service';
import { MissionService } from '../services/mission-service';

export const telegram = new Hono<{ Bindings: Env }>();

interface TelegramUpdate {
  message?: {
    chat: { id: number };
    from?: { id: number; first_name?: string; username?: string };
    text?: string;
  };
}

/**
 * POST /webhook/telegram — Handle Telegram bot updates
 */
telegram.post('/', async (c) => {
  const botToken = (c.env as any).TELEGRAM_BOT_TOKEN;
  if (!botToken) {
    return c.json({ ok: false, error: 'Bot not configured' }, 503);
  }

  const update: TelegramUpdate = await c.req.json();
  const msg = update.message;
  if (!msg?.text || !msg.chat) return c.json({ ok: true });

  const chatId = msg.chat.id;
  const text = msg.text.trim();
  const telegramId = msg.from?.id?.toString() || chatId.toString();

  const send = (reply: string) => sendMessage(botToken, chatId, reply);

  try {
    // Parse command
    const [cmd, ...args] = text.split(/\s+/);
    const arg = args.join(' ');

    let reply = '';

    switch (cmd.toLowerCase()) {
      case '/start':
        await handleStart(c.env, telegramId, msg.from?.first_name || 'User', send);
        break;
      case '/submit':
        if (!arg) { await send('Usage: /submit <your goal>\nExample: /submit Build a REST API'); break; }
        await handleSubmit(c.env, telegramId, arg, send);
        break;
      case '/credits':
        await handleCredits(c.env, telegramId, send);
        break;
      case '/missions':
        await handleMissions(c.env, telegramId, send);
        break;
      case '/marketplace': {
        const featured = await c.env.DB.prepare(
          `SELECT goal, complexity FROM missions WHERE is_public = 1 AND status = 'completed' ORDER BY completed_at DESC LIMIT 5`
        ).all();
        const items = featured.results.map((m: any, i: number) => `${i+1}. [${m.complexity}] ${m.goal.slice(0, 60)}`).join('\n');
        reply = items ? `🏪 *Featured Missions:*\n${items}` : 'No public missions yet.';
        await send(reply);
        break;
      }
      case '/buy':
        reply = `💰 *Credit Packs:*\n\n` +
          `• 10 MCU — $5\n• 50 MCU — $20\n• 100 MCU — $35\n• 500 MCU — $150\n\n` +
          `Visit dashboard to purchase: https://app.agencyos.network/dashboard`;
        await send(reply);
        break;
      case '/help':
        await send(
          'Mekong CLI Bot\n\n' +
          '/start — Create account\n' +
          '/submit <goal> — Submit mission\n' +
          '/credits — Check balance\n' +
          '/missions — List missions\n' +
          '/marketplace — Browse featured missions\n' +
          '/buy — View credit packs\n' +
          '/help — Show this help'
        );
        break;
      default:
        await send('Unknown command. Type /help for available commands.');
    }
  } catch (error) {
    console.error('[Telegram] Error:', error);
    await send('Something went wrong. Try again later.');
  }

  return c.json({ ok: true });
});

// --- Command handlers ---

async function handleStart(
  env: Env, telegramId: string, name: string,
  send: (msg: string) => Promise<void>
) {
  // Check if already registered
  const existing = await env.DB.prepare(
    "SELECT id, balance FROM tenants WHERE email = ?"
  ).bind(`tg_${telegramId}@mekong.bot`).first<{ id: string; balance: number }>();

  if (existing) {
    // Update chat_id if not set
    await env.DB.prepare('UPDATE tenants SET telegram_chat_id = ? WHERE id = ? AND telegram_chat_id IS NULL')
      .bind(telegramId, existing.id).run();
    await send(`Welcome back! Balance: ${existing.balance} MCU\nType /submit <goal> to start.`);
    return;
  }

  // Create tenant with chat_id for result delivery
  const tenantId = crypto.randomUUID();
  const email = `tg_${telegramId}@mekong.bot`;
  const refCode = tenantId.slice(0, 8);

  await env.DB.prepare(
    `INSERT INTO tenants (id, name, email, tier, active, balance, total_earned, total_spent, telegram_chat_id, referral_code, created_at, updated_at)
     VALUES (?, ?, ?, 'free', 1, 10, 10, 0, ?, ?, datetime('now'), datetime('now'))`
  ).bind(tenantId, name, email, telegramId, refCode).run();

  // Record credits
  await env.DB.prepare(
    `INSERT INTO credit_transactions (id, tenant_id, amount, type, description, metadata, created_at)
     VALUES (?, ?, 10, 'adjustment', 'Telegram welcome bonus', '{}', datetime('now'))`
  ).bind(crypto.randomUUID(), tenantId).run();

  await send(
    `Welcome to Mekong CLI, ${name}!\n\n` +
    `You have 10 free credits (MCU).\n` +
    `Costs: simple=1, standard=3, complex=5 MCU\n\n` +
    `Try: /submit Build a landing page`
  );
}

async function handleSubmit(
  env: Env, telegramId: string, goal: string,
  send: (msg: string) => Promise<void>
) {
  const tenant = await getTenantByTelegram(env, telegramId);
  if (!tenant) { await send('Please /start first to create your account.'); return; }

  const missionService = new MissionService(env);
  const result = await missionService.submit(tenant.id, goal, 'standard');

  if (!result.success) {
    await send(`Cannot submit: ${result.error}`);
    return;
  }

  await send(
    `Mission submitted!\n` +
    `ID: ${result.mission!.id.slice(0, 8)}...\n` +
    `Cost: ${result.mission!.creditsCost} MCU\n` +
    `Status: queued`
  );
}

async function handleCredits(
  env: Env, telegramId: string,
  send: (msg: string) => Promise<void>
) {
  const tenant = await getTenantByTelegram(env, telegramId);
  if (!tenant) { await send('Please /start first.'); return; }

  const creditService = new CreditService(env);
  const balance = await creditService.getBalance(tenant.id);

  await send(`Balance: ${balance} MCU\nTier: ${tenant.tier}`);
}

async function handleMissions(
  env: Env, telegramId: string,
  send: (msg: string) => Promise<void>
) {
  const tenant = await getTenantByTelegram(env, telegramId);
  if (!tenant) { await send('Please /start first.'); return; }

  const missionService = new MissionService(env);
  const { missions, total } = await missionService.list(tenant.id, { limit: 5 });

  if (missions.length === 0) {
    await send('No missions yet. Try: /submit <your goal>');
    return;
  }

  const lines = missions.map(m =>
    `${m.id.slice(0, 8)} | ${m.status} | ${m.creditsCost}MCU | ${m.goal.slice(0, 40)}`
  );
  await send(`Missions (${total} total):\n\n${lines.join('\n')}`);
}

// --- Helpers ---

async function getTenantByTelegram(env: Env, telegramId: string) {
  return env.DB.prepare(
    'SELECT id, tier, balance FROM tenants WHERE email = ? AND active = 1'
  ).bind(`tg_${telegramId}@mekong.bot`).first<{ id: string; tier: string; balance: number }>();
}

async function sendMessage(botToken: string, chatId: number, text: string): Promise<void> {
  await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: chatId, text, parse_mode: 'Markdown' }),
  });
}
