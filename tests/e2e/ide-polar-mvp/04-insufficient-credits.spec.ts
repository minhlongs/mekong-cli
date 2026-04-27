import { test, expect } from "@playwright/test";

const IDE_BASE_URL = process.env.IDE_BASE_URL ?? "https://ide.mekongmind.com";
const DRAINED_LICENSE_KEY = process.env.DRAINED_LICENSE_KEY ?? "";

test.describe("Insufficient credits", () => {
  test.skip(!DRAINED_LICENSE_KEY, "DRAINED_LICENSE_KEY not set");

  test("zero balance triggers 402 toast with recharge link", async ({ page }) => {
    await page.goto(`${IDE_BASE_URL}/login`);
    await page.getByPlaceholder(/lic_/i).fill(DRAINED_LICENSE_KEY);
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL(/\/app/);

    await page.getByPlaceholder(/scout/i).fill("simple test");
    await page.keyboard.press("Enter");

    const error = page.locator("pre", { hasText: /Out of credits/i });
    await expect(error).toBeVisible({ timeout: 10_000 });
    await expect(error).toContainText(/billing|recharge/i);
  });
});
