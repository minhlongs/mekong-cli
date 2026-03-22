/**
 * Tenant backup & restore routes — export/import point-in-time snapshots
 */
import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import {
  createBackup,
  listBackups,
  getBackup,
  downloadBackup,
  deleteBackup,
  restoreBackup,
  getRestoreLogs,
  cleanExpiredBackups,
  getBackupStats,
  scheduleAutoBackup,
} from '../services/tenant-backup-service';

const app = new Hono<{ Bindings: Env }>();

app.use('/*', auth());

function isAdmin(c: any): boolean {
  return !!(c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY);
}

/** GET /v1/backup/backups — list all backups for tenant */
app.get('/backups', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const backups = await listBackups(c.env.DB, tenantId);
    return c.json({ success: true, data: backups });
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

/** POST /v1/backup/backups — create a new backup */
app.post('/backups', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const body = await c.req.json().catch(() => ({}));
    const backup = await createBackup(c.env.DB, tenantId, body.backup_type, body.tables);
    return c.json({ success: true, data: backup }, 201);
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

/** GET /v1/backup/stats — aggregate stats (MUST be before /:id) */
app.get('/stats', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const stats = await getBackupStats(c.env.DB, tenantId);
    return c.json({ success: true, data: stats });
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

/** GET /v1/backup/restore-logs — restore history */
app.get('/restore-logs', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const logs = await getRestoreLogs(c.env.DB, tenantId);
    return c.json({ success: true, data: logs });
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

/** GET /v1/backup/backups/:id — get backup metadata */
app.get('/backups/:id', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const backup = await getBackup(c.env.DB, c.req.param('id'), tenantId);
    if (!backup) return c.json({ error: 'Backup not found' }, 404);
    return c.json({ success: true, data: backup });
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

/** GET /v1/backup/backups/:id/download — download full backup data */
app.get('/backups/:id/download', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const data = await downloadBackup(c.env.DB, c.req.param('id'), tenantId);
    if (!data) return c.json({ error: 'Backup not found or not completed' }, 404);
    return new Response(JSON.stringify(data, null, 2), {
      headers: {
        'Content-Type': 'application/json',
        'Content-Disposition': `attachment; filename="backup-${c.req.param('id')}.json"`,
      },
    });
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

/** DELETE /v1/backup/backups/:id — remove a backup */
app.delete('/backups/:id', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const deleted = await deleteBackup(c.env.DB, c.req.param('id'), tenantId);
    if (!deleted) return c.json({ error: 'Backup not found' }, 404);
    return c.json({ success: true });
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

/** POST /v1/backup/backups/:id/restore — restore from backup */
app.post('/backups/:id/restore', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const result = await restoreBackup(c.env.DB, c.req.param('id'), tenantId);
    return c.json({ success: true, data: result });
  } catch (err: any) {
    return c.json({ error: err.message }, 400);
  }
});

/** POST /v1/backup/schedule — schedule auto backup for cron pickup */
app.post('/schedule', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const result = await scheduleAutoBackup(c.env.DB, tenantId);
    return c.json({ success: true, data: result }, 201);
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

/** POST /v1/backup/admin/cleanup — delete expired backups (admin only) */
app.post('/admin/cleanup', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Unauthorized' }, 401);
  try {
    const deleted = await cleanExpiredBackups(c.env.DB);
    return c.json({ success: true, data: { deleted } });
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

export { app as tenantBackup };
