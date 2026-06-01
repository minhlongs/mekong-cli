import { test, expect } from '@playwright/test';

const BASE = 'https://ide.mekongmind.com';

test.describe('Founder dry-run', () => {
  test('root page loads, has title + content + CTA + footer', async ({ page }) => {
    await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 30_000 });
    const title = await page.title();
    console.log('title:', title);
    expect(title).toContain('Mekong');

    const body = await page.textContent('body');
    expect(body!.length).toBeGreaterThan(100);

    const cta = page.getByRole('link', { name: /get started|sign in|login/i }).first();
    await expect(cta).toBeVisible();

    const footer = page.locator('footer, [data-testid="footer"], nav').first();
    await expect(footer).toBeVisible();
  });

  test('navigate to /dashboard via SPA', async ({ page }) => {
    await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 30_000 });
    await page.goto(`${BASE}/dashboard`, { waitUntil: 'domcontentloaded', timeout: 30_000 });
    const dashTitle = await page.title();
    console.log('/dashboard title:', dashTitle);
    expect(dashTitle).toContain('Mekong');

    const body = await page.textContent('body');
    expect(body!.length).toBeGreaterThan(100);
  });
});
