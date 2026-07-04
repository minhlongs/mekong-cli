import { test, expect } from "@playwright/test";

const IDE_BASE_URL = process.env.IDE_BASE_URL ?? "https://ide.mekongmind.com";
const TEST_LICENSE_KEY = process.env.TEST_LICENSE_KEY ?? "";

test.describe("Mission flow", () => {
  test.skip(!TEST_LICENSE_KEY, "TEST_LICENSE_KEY not set");

  test("submit a goal and stream output, balance decrements", async ({ page }) => {
    await page.goto(`${IDE_BASE_URL}/login`);
    await page.getByPlaceholder(/lic_/i).fill(TEST_LICENSE_KEY);
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL(/\/app/);

    const balanceBefore = await readBalance(page);
    expect(balanceBefore).not.toBeNull();
    expect(balanceBefore!).toBeGreaterThan(0);

    await page.getByPlaceholder(/scout/i).fill("scout user model");
    await page.keyboard.press("Enter");

    // Wait for at least one output line beyond the system prompt.
    await expect(page.locator("pre", { hasText: /mission/i })).toBeVisible({
      timeout: 15_000,
    });

    // Allow background MCU deduction to land before re-reading.
    await page.waitForTimeout(2_000);
    const balanceAfter = await readBalance(page);
    expect(balanceAfter).not.toBeNull();
    expect(balanceAfter!).toBeLessThan(balanceBefore!);
  });
});

async function readBalance(page: import("@playwright/test").Page): Promise<number | null> {
  const text = await page.getByText(/MCU:/i).textContent();
  const match = text?.match(/MCU:\s*(\d+)/);
  return match ? Number(match[1]) : null;
}
