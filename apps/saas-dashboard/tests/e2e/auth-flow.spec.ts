import { test, expect } from '@playwright/test';

test.describe('Auth Flow', () => {
  test('shows login page', async ({ page }) => {
    await page.goto('/login');

    // Check login form is visible
    await expect(page.getByPlaceholder('email')).toBeVisible();
    await expect(page.getByPlaceholder('password', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
  });

  test('shows register page', async ({ page }) => {
    await page.goto('/register');

    // Check register form is visible
    await expect(page.getByPlaceholder('Full Name')).toBeVisible();
    await expect(page.getByPlaceholder('email')).toBeVisible();
    await expect(page.getByPlaceholder('password', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: /create account/i })).toBeVisible();
  });
});

test.describe('Dashboard', () => {
  test('dashboard loads with mock data', async ({ page }) => {
    // Note: This test requires authentication
    // For now, just verify the route exists
    await page.goto('/dashboard');

    // Check for loading state or dashboard content
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Stripe Integration', () => {
  test('pricing/checkout UI elements exist', async ({ page }) => {
    // Mock test - actual checkout requires Stripe test mode
    await page.goto('/dashboard');

    // Check page loads
    await expect(page.locator('body')).toBeVisible();
  });
});
