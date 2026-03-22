/**
 * Admin Platform Backup routes — backup records and schedule management
 * All endpoints require X-Admin-Key header. Mount path: /admin/platform-backup
 */

import { Hono } from 'hono';
import { adminPlatformBackupService } from '../services/admin-platform-backup';

type Bindings = {
  DB: any;
  ADMIN_API_KEY: string;
};

const app = new Hono<{ Bindings: Bindings }>();

// Admin auth guard for ALL routes
app.use('*', async (c, next) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /backups — list all platform backups
app.get('/backups', async (c) => {
  try {
    const result = await adminPlatformBackupService.listBackups(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /backups — create a new platform backup
app.post('/backups', async (c) => {
  try {
    const body = await c.req.json() as {
      backup_name: string;
      backup_type?: string;
      size_bytes?: number;
      storage_path?: string;
    };
    if (!body.backup_name) return c.json({ error: 'backup_name is required' }, 400);
    const result = await adminPlatformBackupService.createBackup(c.env.DB, body);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /schedules — list all backup schedules
app.get('/schedules', async (c) => {
  try {
    const result = await adminPlatformBackupService.getSchedules(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — backup summary by status and type
app.get('/dashboard', async (c) => {
  try {
    const result = await adminPlatformBackupService.getDashboard(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as adminPlatformBackup };
