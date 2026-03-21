/**
 * Conversion Analytics Routes
 * Public: POST /conversion/track
 * Admin:  GET  /conversion/funnel | /rates | /cohorts | /sources
 */

import { Hono } from 'hono';
import type { Context, Next } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';
import {
  FUNNEL_STAGES,
  trackEvent,
  getFunnel,
  getConversionRates,
  getCohortAnalysis,
  getTopSources,
  type FunnelStage,
} from '../services/conversion-analytics-service';

export const conversionAnalytics = new Hono<{ Bindings: Env }>();

// ── Admin auth middleware (applied to /funnel, /rates, /cohorts, /sources) ──
const requireAdmin = async (c: Context<{ Bindings: Env }>, next: Next) => {
  const key = c.req.header('X-Admin-Key');
  const expected = c.env.ADMIN_API_KEY;
  if (!expected || key !== expected) {
    return json({ error: 'Unauthorized' }, { status: 401 });
  }
  await next();
};

// ── Public: track a conversion event ──────────────────────────────────────

/**
 * POST /conversion/track
 * Body: { event_type, tenant_id?, session_id?, source?, event_data? }
 */
conversionAnalytics.post('/track', async (c) => {
  let body: Record<string, unknown>;
  try {
    body = await c.req.json<Record<string, unknown>>();
  } catch {
    return json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const { event_type, tenant_id, session_id, source, event_data } = body as {
    event_type?: string;
    tenant_id?: string;
    session_id?: string;
    source?: string;
    event_data?: Record<string, unknown>;
  };

  if (!event_type || !(FUNNEL_STAGES as readonly string[]).includes(event_type)) {
    return json(
      { error: 'Invalid event_type', valid: FUNNEL_STAGES },
      { status: 400 }
    );
  }

  try {
    await trackEvent(c.env.DB, {
      event_type: event_type as FunnelStage,
      tenant_id: typeof tenant_id === 'string' ? tenant_id : undefined,
      session_id: typeof session_id === 'string' ? session_id : undefined,
      source: typeof source === 'string' ? source : undefined,
      event_data: event_data && typeof event_data === 'object' ? event_data : undefined,
    });
    return json({ success: true, data: { tracked: event_type } });
  } catch (err) {
    console.error('[conversion/track]', err);
    return json({ error: 'Failed to track event' }, { status: 500 });
  }
});

// ── Admin: funnel visualization ────────────────────────────────────────────

/**
 * GET /conversion/funnel?days=30&source=google
 */
conversionAnalytics.get('/funnel', requireAdmin, async (c) => {
  const days = Math.min(parseInt(c.req.query('days') ?? '30', 10) || 30, 365);
  const source = c.req.query('source');

  try {
    const data = await getFunnel(c.env.DB, { days, source });
    return json({ success: true, data });
  } catch (err) {
    console.error('[conversion/funnel]', err);
    return json({ error: 'Failed to fetch funnel' }, { status: 500 });
  }
});

// ── Admin: conversion rates ────────────────────────────────────────────────

/**
 * GET /conversion/rates?days=30&source=google
 */
conversionAnalytics.get('/rates', requireAdmin, async (c) => {
  const days = Math.min(parseInt(c.req.query('days') ?? '30', 10) || 30, 365);
  const source = c.req.query('source');

  try {
    const data = await getConversionRates(c.env.DB, { days, source });
    return json({ success: true, data });
  } catch (err) {
    console.error('[conversion/rates]', err);
    return json({ error: 'Failed to fetch conversion rates' }, { status: 500 });
  }
});

// ── Admin: cohort retention ────────────────────────────────────────────────

/**
 * GET /conversion/cohorts?period=month&cohorts=6
 */
conversionAnalytics.get('/cohorts', requireAdmin, async (c) => {
  const rawPeriod = c.req.query('period') ?? 'month';
  const period = rawPeriod === 'week' ? 'week' : 'month';
  const cohorts = Math.min(parseInt(c.req.query('cohorts') ?? '6', 10) || 6, 24);

  try {
    const data = await getCohortAnalysis(c.env.DB, { period, cohorts });
    return json({ success: true, data });
  } catch (err) {
    console.error('[conversion/cohorts]', err);
    return json({ error: 'Failed to fetch cohort data' }, { status: 500 });
  }
});

// ── Admin: top acquisition sources ────────────────────────────────────────

/**
 * GET /conversion/sources?days=30&limit=10
 */
conversionAnalytics.get('/sources', requireAdmin, async (c) => {
  const days = Math.min(parseInt(c.req.query('days') ?? '30', 10) || 30, 365);
  const limit = Math.min(parseInt(c.req.query('limit') ?? '10', 10) || 10, 50);

  try {
    const data = await getTopSources(c.env.DB, { days, limit });
    return json({ success: true, data });
  } catch (err) {
    console.error('[conversion/sources]', err);
    return json({ error: 'Failed to fetch sources' }, { status: 500 });
  }
});
