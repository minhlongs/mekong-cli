/**
 * Compliance Reports routes — SOC2/GDPR/HIPAA/PCI report generation and checks
 * Mount: /v1/compliance
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import type { D1Database } from '@cloudflare/workers-types';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  generateReport,
  getReports,
  getReport,
  deleteReport,
  runComplianceChecks,
  getComplianceScore,
  getCheckHistory,
  getComplianceSummary,
  exportReport,
  getFrameworks,
} from '../services/compliance-report-service';

const app = new Hono<{ Bindings: Env }>();

app.use('/*', auth());

/**
 * GET /frameworks — supported compliance frameworks + check descriptions
 */
app.get('/frameworks', (c) => {
  return json(getFrameworks());
});

/**
 * GET /summary — cross-category compliance score summary
 */
app.get('/summary', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const summary = await getComplianceSummary(c.env.DB, tenantId);
    return json({ summary });
  } catch (err) {
    return json({ error: 'Failed to fetch compliance summary' }, { status: 500 });
  }
});

/**
 * GET /score — compliance score for a category (?category=soc2)
 */
app.get('/score', async (c) => {
  const { tenantId } = getTenant(c);
  const category = c.req.query('category') ?? 'soc2';
  try {
    const score = await getComplianceScore(c.env.DB, tenantId, category);
    return json(score);
  } catch (err) {
    return json({ error: 'Failed to calculate compliance score' }, { status: 500 });
  }
});

/**
 * GET /checks — run live compliance checks (?category=soc2)
 * Also supports GET /checks/history?category=soc2
 */
app.get('/checks/history', async (c) => {
  const { tenantId } = getTenant(c);
  const category = c.req.query('category') ?? 'soc2';
  try {
    const history = await getCheckHistory(c.env.DB, tenantId, category);
    return json({ history });
  } catch (err) {
    return json({ error: 'Failed to fetch check history' }, { status: 500 });
  }
});

app.get('/checks', async (c) => {
  const { tenantId } = getTenant(c);
  const category = c.req.query('category') ?? 'soc2';
  try {
    const checks = await runComplianceChecks(c.env.DB, tenantId, category);
    return json({ category, checks });
  } catch (err) {
    return json({ error: 'Failed to run compliance checks' }, { status: 500 });
  }
});

/**
 * GET /reports — list reports (?type=soc2)
 */
app.get('/reports', async (c) => {
  const { tenantId } = getTenant(c);
  const type = c.req.query('type');
  try {
    const reports = await getReports(c.env.DB, tenantId, type);
    return json({ reports });
  } catch (err) {
    return json({ error: 'Failed to list compliance reports' }, { status: 500 });
  }
});

/**
 * POST /reports/generate — generate a new compliance report
 * Body: { report_type, coverage_start, coverage_end }
 */
app.post('/reports/generate', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const body = await c.req.json<{
      report_type: string;
      coverage_start: string;
      coverage_end: string;
    }>();

    if (!body.report_type || !body.coverage_start || !body.coverage_end) {
      return json({ error: 'report_type, coverage_start, coverage_end are required' }, { status: 400 });
    }

    const valid = ['soc2', 'gdpr', 'hipaa', 'pci', 'custom'];
    if (!valid.includes(body.report_type)) {
      return json({ error: `report_type must be one of: ${valid.join(', ')}` }, { status: 400 });
    }

    const result = await generateReport(
      c.env.DB,
      tenantId,
      body.report_type,
      body.coverage_start,
      body.coverage_end
    );
    return json(result, { status: 201 });
  } catch (err) {
    return json({ error: 'Failed to generate compliance report' }, { status: 500 });
  }
});

/**
 * POST /reports/:id/export — export report as JSON
 */
app.post('/reports/:id/export', async (c) => {
  const { tenantId } = getTenant(c);
  const reportId = c.req.param('id');
  try {
    const exported = await exportReport(c.env.DB, tenantId, reportId);
    if (!exported) {
      return json({ error: 'Report not found' }, { status: 404 });
    }
    return json(exported);
  } catch (err) {
    return json({ error: 'Failed to export report' }, { status: 500 });
  }
});

/**
 * GET /reports/:id — get report detail
 */
app.get('/reports/:id', async (c) => {
  const { tenantId } = getTenant(c);
  const reportId = c.req.param('id');
  try {
    const report = await getReport(c.env.DB, tenantId, reportId);
    if (!report) {
      return json({ error: 'Report not found' }, { status: 404 });
    }
    return json(report);
  } catch (err) {
    return json({ error: 'Failed to fetch report' }, { status: 500 });
  }
});

/**
 * DELETE /reports/:id — delete a report
 */
app.delete('/reports/:id', async (c) => {
  const { tenantId } = getTenant(c);
  const reportId = c.req.param('id');
  try {
    const deleted = await deleteReport(c.env.DB, tenantId, reportId);
    if (!deleted) {
      return json({ error: 'Report not found' }, { status: 404 });
    }
    return json({ deleted: true });
  } catch (err) {
    return json({ error: 'Failed to delete report' }, { status: 500 });
  }
});

export const complianceReports = app;
