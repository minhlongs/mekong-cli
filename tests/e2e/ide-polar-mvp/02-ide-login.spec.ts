import { test, expect } from "@playwright/test";

const IDE_BASE_URL = process.env.IDE_BASE_URL ?? "https://ide.mekongmind.com";
const TEST_LICENSE_KEY = process.env.TEST_LICENSE_KEY ?? "";

test.describe("IDE login", () => {
  test.skip(!TEST_LICENSE_KEY, "TEST_LICENSE_KEY not set");

  test("license key signs the user in and lands on /app", async ({ page }) => {
    await page.goto(`${IDE_BASE_URL}/login`);

    await page.getByPlaceholder(/lic_/i).fill(TEST_LICENSE_KEY);
    await page.getByRole("button", { name: /sign in/i }).click();

    await page.waitForURL(/\/app/, { timeout: 10_000 });

    // Header should expose MCU balance and a tier badge.
    await expect(page.getByText(/MCU:/i)).toBeVisible();
  });

  test("invalid license shows error", async ({ page }) => {
    await page.goto(`${IDE_BASE_URL}/login`);
    await page.getByPlaceholder(/lic_/i).fill("lic_definitely_bad_99");
    await page.getByRole("button", { name: /sign in/i }).click();

    await expect(page.getByRole("alert")).toBeVisible();
  });
});
