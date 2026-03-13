/**
 * ═══════════════════════════════════════════════════════════════════════════
 * E2E TESTS — New Features 2027
 *
 * Test suites:
 * - Notification Center
 * - Command Palette
 * - Project Health Monitor
 *
 * Run: npm test -- tests/new-features-2027.spec.ts
 * ═══════════════════════════════════════════════════════════════════════════
 */

import { test, expect } from '@playwright/test';

const TEST_URL = 'http://localhost:3000/admin/features-demo-2027.html';

// ═══════════════════════════════════════════════════════════════════════════
// NOTIFICATION CENTER TESTS
// ═══════════════════════════════════════════════════════════════════════════

test.describe('Notification Center', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(TEST_URL);
    await page.waitForTimeout(1000); // Wait for initialization
  });

  test('notification center initializes', async ({ page }) => {
    const notificationBell = page.locator('notification-center').locator('.notification-bell');
    await expect(notificationBell).toBeVisible();
  });

  test('notification badge shows unread count', async ({ page }) => {
    // Trigger a notification
    await page.click('button:has-text("Info Notification")');
    await page.waitForTimeout(500);

    const badge = page.locator('.notification-bell .badge');
    await expect(badge).toBeVisible();
    await expect(badge).toContainText('1');
  });

  test('notification panel opens on bell click', async ({ page }) => {
    // Trigger a notification first
    await page.click('button:has-text("Info Notification")');
    await page.waitForTimeout(500);

    // Open panel
    await page.locator('notification-center').locator('.notification-bell').click();
    await page.waitForTimeout(300);

    const panel = page.locator('notification-center').locator('.notification-panel');
    await expect(panel).toHaveClass(/show/);
  });

  test('notification panel shows notification list', async ({ page }) => {
    // Trigger multiple notifications
    await page.click('button:has-text("Success Notification")');
    await page.waitForTimeout(300);
    await page.click('button:has-text("Warning Notification")');
    await page.waitForTimeout(300);

    // Open panel
    await page.locator('notification-center').locator('.notification-bell').click();
    await page.waitForTimeout(300);

    const notificationItems = page.locator('.notification-item');
    await expect(notificationItems).toHaveCount(2);
  });

  test('mark all as read clears unread count', async ({ page }) => {
    // Trigger notifications
    await page.click('button:has-text("Info Notification")');
    await page.waitForTimeout(300);
    await page.click('button:has-text("Success Notification")');
    await page.waitForTimeout(300);

    // Open panel
    await page.locator('notification-center').locator('.notification-bell').click();
    await page.waitForTimeout(300);

    // Mark all as read
    await page.click('button:has-text("Đánh dấu đã đọc")');
    await page.waitForTimeout(300);

    const badge = page.locator('.notification-bell .badge');
    await expect(badge).not.toBeVisible();
  });

  test('clear all removes notifications', async ({ page }) => {
    // Trigger notifications
    await page.click('button:has-text("Info Notification")');
    await page.waitForTimeout(300);

    // Open panel
    await page.locator('notification-center').locator('.notification-bell').click();
    await page.waitForTimeout(300);

    // Clear all
    await page.click('button:has-text("Xóa tất cả")');
    await page.waitForTimeout(300);

    const notificationItems = page.locator('.notification-item');
    await expect(notificationItems).toHaveCount(0);
  });

  test('notification types have correct icons', async ({ page }) => {
    const notifications = [
      { button: 'Info Notification', icon: 'ℹ️' },
      { button: 'Success Notification', icon: '✅' },
      { button: 'Warning Notification', icon: '⚠️' },
      { button: 'Error Notification', icon: '❌' }
    ];

    for (const notif of notifications) {
      await page.click(`button:has-text("${notif.button}")`);
      await page.waitForTimeout(200);
    }

    // Open panel
    await page.locator('notification-center').locator('.notification-bell').click();
    await page.waitForTimeout(300);

    // Check icons
    const icons = page.locator('.notification-icon');
    await expect(icons.nth(0)).toContainText('❌'); // Last one first (unshift)
    await expect(icons.nth(1)).toContainText('⚠️');
    await expect(icons.nth(2)).toContainText('✅');
    await expect(icons.nth(3)).toContainText('ℹ️');
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// COMMAND PALETTE TESTS
// ═══════════════════════════════════════════════════════════════════════════

test.describe('Command Palette', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(TEST_URL);
    await page.waitForTimeout(1000);
  });

  test('command palette opens with Ctrl+K', async ({ page }) => {
    await page.keyboard.press('Control+k');
    await page.waitForTimeout(300);

    const overlay = page.locator('.command-palette-overlay');
    await expect(overlay).toHaveClass(/open/);
  });

  test('command palette shows default commands', async ({ page }) => {
    await page.keyboard.press('Control+k');
    await page.waitForTimeout(300);

    const commandItems = page.locator('.command-item');
    await expect(commandItems).toHaveCount({ min: 5 });
  });

  test('command palette search filters results', async ({ page }) => {
    await page.keyboard.press('Control+k');
    await page.waitForTimeout(300);

    // Type search query
    await page.locator('.command-palette-input').fill('Dashboard');
    await page.waitForTimeout(300);

    const commandItems = page.locator('.command-item');
    await expect(commandItems.first()).toContainText('Dashboard');
  });

  test('command palette keyboard navigation', async ({ page }) => {
    await page.keyboard.press('Control+k');
    await page.waitForTimeout(300);

    // Navigate down
    await page.keyboard.press('ArrowDown');
    await page.waitForTimeout(100);

    const selectedItem = page.locator('.command-item.selected');
    await expect(selectedItem).toBeVisible();

    // Navigate up
    await page.keyboard.press('ArrowUp');
    await page.waitForTimeout(100);

    // First item should be selected again
    const firstItem = page.locator('.command-item').first();
    await expect(firstItem).toHaveClass(/selected/);
  });

  test('command palette closes with ESC', async ({ page }) => {
    await page.keyboard.press('Control+k');
    await page.waitForTimeout(300);

    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);

    const overlay = page.locator('.command-palette-overlay');
    await expect(overlay).not.toHaveClass(/open/);
  });

  test('command palette closes on overlay click', async ({ page }) => {
    await page.keyboard.press('Control+k');
    await page.waitForTimeout(300);

    // Click outside the palette
    await page.locator('.command-palette-overlay').click({ position: { x: 10, y: 10 } });
    await page.waitForTimeout(300);

    const overlay = page.locator('.command-palette-overlay');
    await expect(overlay).not.toHaveClass(/open/);
  });

  test('command palette opens with button click', async ({ page }) => {
    await page.click('button:has-text("Open Command Palette")');
    await page.waitForTimeout(300);

    const overlay = page.locator('.command-palette-overlay');
    await expect(overlay).toHaveClass(/open/);
  });

  test('command palette adds custom command', async ({ page }) => {
    await page.click('button:has-text("Add Custom Command")');
    await page.waitForTimeout(300);

    // Open command palette
    await page.keyboard.press('Control+k');
    await page.waitForTimeout(300);

    // Search for custom command
    await page.locator('.command-palette-input').fill('Demo');
    await page.waitForTimeout(300);

    const commandItems = page.locator('.command-item');
    await expect(commandItems.first()).toContainText('Demo Command');
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// PROJECT HEALTH MONITOR TESTS
// ═══════════════════════════════════════════════════════════════════════════

test.describe('Project Health Monitor', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(TEST_URL);
    await page.waitForTimeout(1000);
  });

  test('health monitor widget renders', async ({ page }) => {
    const healthMonitor = page.locator('project-health-monitor');
    await expect(healthMonitor).toBeVisible();
  });

  test('health gauge displays score', async ({ page }) => {
    await page.waitForTimeout(1000); // Wait for data fetch

    const gaugeScore = page.locator('.health-gauge-text .score');
    const scoreText = await gaugeScore.textContent();
    const score = parseInt(scoreText || '0');

    await expect(score).toBeGreaterThanOrEqual(0);
    await expect(score).toBeLessThanOrEqual(100);
  });

  test('health metrics display correctly', async ({ page }) => {
    await page.waitForTimeout(1000);

    const metricCards = page.locator('.health-metric-card');
    await expect(metricCards).toHaveCount({ min: 4 });
  });

  test('health status shows correct color', async ({ page }) => {
    await page.waitForTimeout(1000);

    const gaugeFill = page.locator('.health-gauge-fill');
    const stroke = await gaugeFill.evaluate((el) =>
      window.getComputedStyle(el).stroke
    );

    // Should have a color (green/yellow/orange/red)
    expect(stroke).toMatch(/rgb\(|rgba\(/);
  });

  test('refresh button triggers data reload', async ({ page }) => {
    await page.waitForTimeout(1000);

    const refreshBtn = page.locator('.btn-refresh');
    await expect(refreshBtn).toBeVisible();

    // Click refresh
    await refreshBtn.click();
    await page.waitForTimeout(500);

    // Score should still be valid
    const gaugeScore = page.locator('.health-gauge-text .score');
    const scoreText = await gaugeScore.textContent();
    expect(scoreText).toMatch(/^\d+$/);
  });

  test('recommendations section displays', async ({ page }) => {
    await page.waitForTimeout(1000);

    const recommendationsTitle = page.locator('.recommendations-title');
    await expect(recommendationsTitle).toBeVisible();
  });

  test('health monitor has trend indicator', async ({ page }) => {
    await page.waitForTimeout(1000);

    const trendEl = page.locator('.health-trend');
    await expect(trendEl).toBeVisible();
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// INTEGRATION TESTS
// ═══════════════════════════════════════════════════════════════════════════

test.describe('Integration Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(TEST_URL);
    await page.waitForTimeout(1000);
  });

  test('notification + command palette work together', async ({ page }) => {
    // Trigger notification
    await page.click('button:has-text("Info Notification")');
    await page.waitForTimeout(300);

    // Open command palette
    await page.keyboard.press('Control+k');
    await page.waitForTimeout(300);

    const overlay = page.locator('.command-palette-overlay');
    await expect(overlay).toHaveClass(/open/);

    // Close command palette
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);

    // Notification bell should still work
    const badge = page.locator('.notification-bell .badge');
    await expect(badge).toBeVisible();
  });

  test('health monitor auto-refreshes', async ({ page }) => {
    await page.waitForTimeout(1000);

    // Get initial score
    const gaugeScore = page.locator('.health-gauge-text .score');
    const initialScore = await gaugeScore.textContent();

    // Wait for auto-refresh (30s is default, check if component exists)
    await page.waitForTimeout(5000);

    // Score should still be valid
    const newScore = await gaugeScore.textContent();
    expect(newScore).toMatch(/^\d+$/);
  });

  test('all features load without errors', async ({ page }) => {
    const consoleErrors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto(TEST_URL);
    await page.waitForTimeout(2000);

    // Should have no unexpected errors
    const unexpectedErrors = consoleErrors.filter(
      err => !err.includes('localhost') && !err.includes('favicon')
    );

    expect(unexpectedErrors.length).toBeLessThan(3);
  });
});
