/**
 * Admin Platform Backup routes — backup and restore point management
 * All endpoints require X-Admin-Key header. Mount path: /admin/platform-backup
 */

import { Hono } from 'hono';
import { Env } from '../index';
import { adminPlatformBackupService } from '../services/admin-platform-backup-service';

const app = new Hono<{ Bindings: Env }>();

// Admin auth guard for ALL routes
app.use('*', async (c, next) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /backups — list all backups, optional ?status= filter
app.get('/backups', async (c) => {
  try {
    const status = c.req.query('status');
    const backups = await adminPlatformBackupService.listBackups(c.env.DB, status);
    return c.json({ backups, count: backups.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /backups — create a new platform backup
app.post('/backups', async (c) => {
  try {
    const body = await c.req.json() as {
      backup_type?: string;
      storage_location: string;
      size_bytes?: number;
      initiated_by?: string;
    };
    if (!body.storage_location) return c.json({ error: 'storage_location is required' }, 400);
    const backup = await adminPlatformBackupService.createBackup(c.env.DB, body);
    return c.json(backup, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /restore-points — list restore points, optional ?backup_id= filter
app.get('/restore-points', async (c) => {
  try {
    const backupId = c.req.query('backup_id');
    const points = await adminPlatformBackupService.getRestorePoints(c.env.DB, backupId);
    return c.json({ restore_points: points, count: points.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — summary counts by status/type, recent restores
app.get('/dashboard', async (c) => {
  try {
    const dashboard = await adminPlatformBackupService.getDashboard(c.env.DB);
    return c.json(dashboard);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as adminPlatformBackup };
