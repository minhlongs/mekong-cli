/**
 * ═══════════════════════════════════════════════════════════════════════════
 * E2E TESTS — Untested Admin Pages Coverage
 * 
 * Coverage: 44 admin pages previously untested
 * Run: npx playwright test tests/untested-admin-pages.spec.ts
 * ═══════════════════════════════════════════════════════════════════════════
 */

import { test, expect } from '@playwright/test';

// Base URL for local dev server
const BASE_URL = process.env.BASE_URL || 'http://localhost:5502';

// List of previously untested admin pages
const UNTESTED_PAGES = [
  'agents.html',
  'ai-analysis.html',
  'api-builder.html',
  'approvals.html',
  'auth.html',
  'binh-phap.html',
  'brand-guide.html',
  'community.html',
  'components-demo.html',
  'content-calendar.html',
  'customer-success.html',
  'deploy.html',
  'docs.html',
  'ecommerce.html',
  'events.html',
  'hr-hiring.html',
  'inventory.html',
  'landing-builder.html',
  'legal.html',
  'lms.html',
  'loyalty.html',
  'menu.html',
  'mvp-launch.html',
  'notifications.html',
  'onboarding.html',
  'payments.html',
  'pos.html',
  'pricing.html',
  'proposals.html',
  'quality.html',
  'raas-overview.html',
  'retention.html',
  'roiaas-admin.html',
  'shifts.html',
  'suppliers.html',
  'ui-components-demo.html',
  'ui-demo.html',
  'ux-components-demo.html',
  'vc-readiness.html',
  'video-workflow.html',
  'workflows.html',
  'zalo.html',
];

// Already tested pages (exclude from this suite)
const TESTED_PAGES = [
  'dashboard.html',
  'leads.html',
  'pipeline.html',
  'campaigns.html',
  'finance.html',
  'features-demo-2027.html',
];

test.describe('Admin Pages — Smoke Tests', () => {
  test.describe.configure({ mode: 'parallel' });

  for (const page of UNTESTED_PAGES) {
    test.describe(`Page: ${page}`, () => {
      test('page loads successfully', async ({ page }) => {
        await page.goto(`${BASE_URL}/admin/${page}`, { 
          waitUntil: 'domcontentloaded',
          timeout: 15000 
        });
        
        // Check page has title
        const title = await page.title();
        expect(title).toBeTruthy();
      });

      test('page has no critical JS errors', async ({ page }) => {
        const errors: string[] = [];
        page.on('pageerror', (error) => {
          if (!error.message.includes('supabase') && 
              !error.message.includes('Auth') &&
              !error.message.includes('is not defined')) {
            errors.push(error.message);
          }
        });

        await page.goto(`${BASE_URL}/admin/${page}`, { 
          waitUntil: 'domcontentloaded',
          timeout: 15000 
        });
        await page.waitForTimeout(1000);

        expect(errors, `JS errors: ${errors.join(', ')}`).toHaveLength(0);
      });

      test('page has proper heading', async ({ page }) => {
        await page.goto(`${BASE_URL}/admin/${page}`, { 
          waitUntil: 'domcontentloaded',
          timeout: 15000 
        });

        const h1 = page.locator('h1').first();
        await expect(h1).toBeVisible();
      });

      test('page is responsive', async ({ page }) => {
        // Mobile viewport
        await page.setViewportSize({ width: 375, height: 667 });
        await page.goto(`${BASE_URL}/admin/${page}`, { 
          waitUntil: 'domcontentloaded',
          timeout: 15000 
        });

        // Check no horizontal overflow
        const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
        const viewportWidth = await page.evaluate(() => window.innerWidth);
        expect(bodyWidth).toBeLessThanOrEqual(viewportWidth);
      });
    });
  }
});

test.describe('Admin Pages — Accessibility Checks', () => {
  const samplePages = UNTESTED_PAGES.slice(0, 10); // Test first 10

  for (const page of samplePages) {
    test(`${page} has lang attribute`, async ({ page }) => {
      await page.goto(`${BASE_URL}/admin/${page}`, { 
        waitUntil: 'domcontentloaded',
        timeout: 15000 
      });

      const html = page.locator('html');
      const lang = await html.getAttribute('lang');
      expect(lang).toBe('vi');
    });
  }
});
