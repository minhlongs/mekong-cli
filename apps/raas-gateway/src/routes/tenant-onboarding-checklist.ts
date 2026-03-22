/**
 * Tenant Onboarding Checklist routes — guided setup with steps, progress, milestone rewards
 * Mount at: /v1/onboarding-checklist
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  getChecklist,
  initializeChecklist,
  completeStep,
  claimReward,
  getProgress,
  getMilestones,
  achieveMilestone,
  resetChecklist,
  getAdminOverview,
} from '../services/tenant-onboarding-checklist-service';

type Env = {
  Bindings: {
    DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any;
    JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string;
    TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string;
    LOG_LEVEL: string; ADMIN_API_KEY: string;
  };
};

const app = new Hono<Env>();

/** GET / — get my checklist */
app.get('/', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const checklist = await getChecklist(c.env.DB, tenantId);
    if (!checklist) return json({ error: 'Checklist not initialized' }, { status: 404 });
    return json({ checklist });
  } catch {
    return json({ error: 'Failed to fetch checklist' }, { status: 500 });
  }
});

/** POST /init — initialize checklist for tenant */
app.post('/init', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const checklist = await initializeChecklist(c.env.DB, tenantId);
    return json({ checklist }, { status: 201 });
  } catch {
    return json({ error: 'Failed to initialize checklist' }, { status: 500 });
  }
});

/** POST /steps/:stepKey/complete — mark a step as completed */
app.post('/steps/:stepKey/complete', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const stepKey = c.req.param('stepKey');
  try {
    const result = await completeStep(c.env.DB, tenantId, stepKey) as any;
    if (result?.error) return json({ error: result.error }, { status: 404 });
    return json({ step: result });
  } catch {
    return json({ error: 'Failed to complete step' }, { status: 500 });
  }
});

/** POST /steps/:stepKey/claim — claim reward for a completed step */
app.post('/steps/:stepKey/claim', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const stepKey = c.req.param('stepKey');
  try {
    const result = await claimReward(c.env.DB, tenantId, stepKey) as any;
    if (result?.error) return json({ error: result.error }, { status: 400 });
    return json(result);
  } catch {
    return json({ error: 'Failed to claim reward' }, { status: 500 });
  }
});

/** GET /progress — get progress summary */
app.get('/progress', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const progress = await getProgress(c.env.DB, tenantId);
    if (!progress) return json({ error: 'Checklist not initialized' }, { status: 404 });
    return json({ progress });
  } catch {
    return json({ error: 'Failed to fetch progress' }, { status: 500 });
  }
});

/** GET /milestones — list milestones */
app.get('/milestones', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const milestones = await getMilestones(c.env.DB, tenantId);
    return json({ milestones });
  } catch {
    return json({ error: 'Failed to fetch milestones' }, { status: 500 });
  }
});

/** POST /milestones/:key/achieve — achieve a milestone */
app.post('/milestones/:key/achieve', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const milestoneKey = c.req.param('key');
  try {
    const result = await achieveMilestone(c.env.DB, tenantId, milestoneKey) as any;
    if (result?.error) return json({ error: result.error }, { status: 400 });
    return json({ milestone: result });
  } catch {
    return json({ error: 'Failed to achieve milestone' }, { status: 500 });
  }
});

/** POST /reset — reset checklist to initial state */
app.post('/reset', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const checklist = await resetChecklist(c.env.DB, tenantId);
    return json({ checklist });
  } catch {
    return json({ error: 'Failed to reset checklist' }, { status: 500 });
  }
});

/** GET /admin/overview — admin aggregate stats (X-Admin-Key required) */
app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (key !== c.env.ADMIN_API_KEY) return json({ error: 'Unauthorized' }, { status: 401 });
  try {
    const overview = await getAdminOverview(c.env.DB);
    return json({ overview });
  } catch {
    return json({ error: 'Failed to fetch admin overview' }, { status: 500 });
  }
});

export { app as tenantOnboardingChecklist };
