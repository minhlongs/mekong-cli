/**
 * OpenClaw Worker v3.0 - Full Mobile Coding Flow
 * Telegram ↔ Workers AI ↔ Bridge ↔ Antigravity/CC CLI
 */

interface TelegramUpdate {
  update_id: number;
  message?: {
    message_id: number;
    from: { id: number; username?: string; first_name: string };
    chat: { id: number; type: string };
    text?: string;
  };
}

interface Env {
  TELEGRAM_BOT_TOKEN: string;
  ALLOWED_USER_IDS: string;
  AI: Ai;
  BRIDGE_URL?: string; // Cloudflare Tunnel to local bridge
}

const MODELS = {
  llama: '@cf/meta/llama-3.1-8b-instruct',
} as const;

// Built-in commands  
const COMMANDS: Record<string, (args: string, env: Env, chatId: number) => Promise<string>> = {
  '/start': async () => `🤖 **OpenClaw Agent v3.0**
  
🧠 AI: Llama 3.1 (FREE)
🌉 Bridge: Connected to Antigravity

Commands:
/ai <prompt> - Quick AI response
/code <task> - Coding help
/delegate <task> - Send to Antigravity/CC CLI
/status - System status`,

  '/help': async (_, env) => `📚 **OpenClaw Commands**

🤖 AI (Workers AI - FREE):
/ai <prompt> - Llama 3.1 response
/code <task> - Coding assistant

🌉 Antigravity Bridge:
/delegate <task> - Send task to CC CLI
${env.BRIDGE_URL ? '✅ Bridge connected' : '⚠️ Bridge offline'}

📊 System:
/status, /ping`,

  '/status': async (_, env) => {
    const bridgeStatus = env.BRIDGE_URL ? '🟢 Connected' : '🔴 Offline';
    return `📊 **System Status**
    
🟢 Worker: Online (v3.0)
🟢 AI: Llama 3.1 Active
${bridgeStatus} Bridge: ${env.BRIDGE_URL?.slice(0, 40) || 'Not configured'}
⏰ ${new Date().toISOString()}`;
  },

  '/ping': async () => `🏓 Pong! ${Date.now() % 1000}ms`,

  '/ai': async (args, env, chatId) => {
    if (!args) return '❌ Usage: /ai <question>';

    try {
      await sendTelegramAction(env.TELEGRAM_BOT_TOKEN, chatId, 'typing');
      const response = await env.AI.run(MODELS.llama as any, {
        messages: [
          { role: 'system', content: 'Be concise and helpful.' },
          { role: 'user', content: args }
        ],
        max_tokens: 800,
      });
      const content = (response as { response?: string }).response || 'No response';
      return content.length > 4000 ? content.slice(0, 3900) + '...' : content;
    } catch (error) {
      return `❌ AI Error: ${error instanceof Error ? error.message : 'Unknown'}`;
    }
  },

  '/code': async (args, env, chatId) => {
    if (!args) return '❌ Usage: /code <task>';

    try {
      await sendTelegramAction(env.TELEGRAM_BOT_TOKEN, chatId, 'typing');
      const response = await env.AI.run(MODELS.llama as any, {
        messages: [
          { role: 'system', content: 'Expert programmer. Provide clean, commented code.' },
          { role: 'user', content: `Task: ${args}\n\nProvide solution with code.` }
        ],
        max_tokens: 1500,
      });
      const content = (response as { response?: string }).response || 'No response';
      return `✅ **Solution**\n\n${content.slice(0, 3800)}`;
    } catch (error) {
      return `❌ Error: ${error instanceof Error ? error.message : 'Unknown'}`;
    }
  },

  '/delegate': async (args, env, chatId) => {
    if (!args) {
      return `❌ Usage: /delegate <task for Antigravity>

Example:
/delegate fix the login bug in auth.ts
/delegate !ls -la (shell command)
/delegate create a new API endpoint`;
    }

    if (!env.BRIDGE_URL) {
      return `⚠️ Bridge not connected!

The local MacBook bridge server is offline.
Start it with: node bridge-server.js

Then create tunnel: ssh -R 80:localhost:8765 serveo.net`;
    }

    try {
      await sendTelegramAction(env.TELEGRAM_BOT_TOKEN, chatId, 'typing');

      const response = await fetch(`${env.BRIDGE_URL}/task`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: args, chatId, timestamp: new Date().toISOString() }),
      });

      if (!response.ok) {
        return `❌ Bridge error: ${response.status}`;
      }

      const result = await response.json() as { taskId?: string; status?: string };
      return `✅ Task sent to Antigravity!

🔑 ID: ${result.taskId}
📊 Status: ${result.status}

You'll receive updates via Telegram.`;

    } catch (error) {
      return `❌ Bridge connection failed: ${error instanceof Error ? error.message : 'Unknown'}

Is the bridge server running on MacBook?`;
    }
  },

  '/shell': async (args, env, chatId) => {
    if (!args) return '❌ Usage: /shell <command>';
    // Redirect to delegate with shell prefix
    return COMMANDS['/delegate'](`!${args}`, env, chatId);
  },
};

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === '/') {
      return new Response(JSON.stringify({
        status: 'ok',
        name: 'OpenClaw Worker',
        version: '3.0.0',
        features: ['telegram', 'workers-ai', 'bridge', 'delegate'],
        bridge: env.BRIDGE_URL ? 'connected' : 'offline',
        commands: Object.keys(COMMANDS),
        timestamp: new Date().toISOString(),
      }), { headers: { 'Content-Type': 'application/json' } });
    }

    if (url.pathname === '/telegram/webhook' && request.method === 'POST') {
      return handleTelegramWebhook(request, env);
    }

    return new Response('Not Found', { status: 404 });
  },
} satisfies ExportedHandler<Env>;

async function handleTelegramWebhook(request: Request, env: Env): Promise<Response> {
  try {
    const update: TelegramUpdate = await request.json();
    if (!update.message?.text) return new Response('OK');

    const userId = update.message.from.id;
    const chatId = update.message.chat.id;
    const text = update.message.text;
    const firstName = update.message.from.first_name;

    // Security
    const allowedIds = env.ALLOWED_USER_IDS.split(',').map(id => parseInt(id.trim()));
    if (!allowedIds.includes(userId)) {
      await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, chatId, '⛔ Unauthorized');
      return new Response('OK');
    }

    if (text.startsWith('/')) {
      const [command, ...args] = text.split(' ');
      const handler = COMMANDS[command];
      if (handler) {
        const response = await handler(args.join(' '), env, chatId);
        await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, chatId, response);
      } else {
        await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, chatId, `❓ Unknown: ${command}`);
      }
    } else {
      // Auto AI for regular messages
      await sendTelegramAction(env.TELEGRAM_BOT_TOKEN, chatId, 'typing');
      try {
        const response = await env.AI.run(MODELS.llama as any, {
          messages: [
            { role: 'system', content: 'Be helpful and concise.' },
            { role: 'user', content: text }
          ],
          max_tokens: 500,
        });
        await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, chatId,
          (response as { response?: string }).response || `Hi ${firstName}! Use /help`);
      } catch {
        await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, chatId, `👋 Hi ${firstName}! Use /help`);
      }
    }

    return new Response('OK');
  } catch (error) {
    console.error('Webhook error:', error);
    return new Response('Error', { status: 500 });
  }
}

async function sendTelegramMessage(token: string, chatId: number, text: string): Promise<void> {
  await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: chatId, text, parse_mode: 'Markdown' }),
  });
}

async function sendTelegramAction(token: string, chatId: number, action: string): Promise<void> {
  await fetch(`https://api.telegram.org/bot${token}/sendChatAction`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: chatId, action }),
  });
}
