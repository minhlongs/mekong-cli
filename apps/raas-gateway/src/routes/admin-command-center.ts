/**
 * Admin Command Center routes — execute, audit, schedule admin commands
 * All endpoints require X-Admin-Key header
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';
import {
  executeCommand,
  listCommands,
  getCommand,
  getAvailableCommands,
  createScheduledCommand,
  listScheduledCommands,
  updateScheduledCommand,
  deleteScheduledCommand,
  getCommandStats,
  getDashboardSummary,
} from '../services/admin-command-center-service';

export const adminCommandCenter = new Hono<{ Bindings: Env }>();

// Admin auth guard
adminCommandCenter.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (key !== c.env.ADMIN_API_KEY) return c.json({ error: 'Unauthorized' }, 401);
  await next();
});

// POST /execute — execute a command immediately
adminCommandCenter.post('/execute', async (c) => {
  try {
    const body = await c.req.json<{
      commandType: string;
      commandName: string;
      parameters?: Record<string, unknown>;
      executedBy?: string;
      targetTenantId?: string;
    }>();

    if (!body.commandType || !body.commandName) {
      return json({ error: 'commandType and commandName are required' }, { status: 400 });
    }

    const result = await executeCommand(
      c.env.DB,
      body.commandType,
      body.commandName,
      body.parameters ?? {},
      body.executedBy ?? 'admin',
      body.targetTenantId
    );
    return json(result);
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// GET /history — list executed commands
adminCommandCenter.get('/history', async (c) => {
  try {
    const status = c.req.query('status');
    const commandType = c.req.query('commandType');
    const limit = parseInt(c.req.query('limit') ?? '50', 10);
    const commands = await listCommands(c.env.DB, { status, commandType, limit });
    return json({ commands, count: (commands as unknown[]).length });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// GET /history/:commandId — command detail
adminCommandCenter.get('/history/:commandId', async (c) => {
  try {
    const command = await getCommand(c.env.DB, c.req.param('commandId'));
    if (!command) return json({ error: 'Command not found' }, { status: 404 });
    return json(command);
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// GET /available — list available command types
adminCommandCenter.get('/available', async (c) => {
  try {
    return json({ commands: getAvailableCommands() });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// POST /scheduled — create scheduled command
adminCommandCenter.post('/scheduled', async (c) => {
  try {
    const body = await c.req.json<{
      commandType: string;
      commandName: string;
      parameters?: Record<string, unknown>;
      cronExpression?: string;
      nextRunAt?: string;
    }>();

    if (!body.commandType || !body.commandName) {
      return json({ error: 'commandType and commandName are required' }, { status: 400 });
    }

    const scheduled = await createScheduledCommand(c.env.DB, body);
    return json(scheduled, { status: 201 });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// GET /scheduled — list all scheduled commands
adminCommandCenter.get('/scheduled', async (c) => {
  try {
    const commands = await listScheduledCommands(c.env.DB);
    return json({ commands, count: (commands as unknown[]).length });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// PUT /scheduled/:id — update scheduled command
adminCommandCenter.put('/scheduled/:id', async (c) => {
  try {
    const updates = await c.req.json<Record<string, unknown>>();
    const updated = await updateScheduledCommand(c.env.DB, c.req.param('id'), updates);
    if (!updated) return json({ error: 'Scheduled command not found' }, { status: 404 });
    return json(updated);
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// DELETE /scheduled/:id — delete scheduled command
adminCommandCenter.delete('/scheduled/:id', async (c) => {
  try {
    const deleted = await deleteScheduledCommand(c.env.DB, c.req.param('id'));
    if (!deleted) return json({ error: 'Scheduled command not found' }, { status: 404 });
    return json({ deleted: true });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// GET /stats — command execution stats
adminCommandCenter.get('/stats', async (c) => {
  try {
    const days = parseInt(c.req.query('days') ?? '7', 10);
    const stats = await getCommandStats(c.env.DB, days);
    return json(stats);
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// GET /dashboard — combined admin summary
adminCommandCenter.get('/dashboard', async (c) => {
  try {
    const summary = await getDashboardSummary(c.env.DB);
    return json(summary);
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});
