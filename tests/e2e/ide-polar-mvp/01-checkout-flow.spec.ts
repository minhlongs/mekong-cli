import { test, expect } from "@playwright/test";

const PRICING_URL = process.env.PRICING_URL ?? "https://www.mekongmind.com/pricing";

test.describe("Checkout flow", () => {
  test("Growth tier checkout completes via Polar test card", async ({ page }) => {
    await page.goto(PRICING_URL);

    // Click the Growth tier CTA — selector intentionally loose; tighten when
    // the pricing page markup stabilises.
    const cta = page.getByRole("link", { name: /growth/i }).first();
    await expect(cta).toBeVisible();
    await cta.click();

    // Polar checkout opens in same tab (or new — handle both)
    await page.waitForURL(/polar\.sh|sandbox\.polar\.sh/);

    await page.fill('input[name="cardNumber"], input[autocomplete="cc-number"]', "4242424242424242");
    await page.fill('input[name="expiry"], input[autocomplete="cc-exp"]', "12/30");
    await page.fill('input[name="cvc"], input[autocomplete="cc-csc"]', "123");

    await page.getByRole("button", { name: /pay|subscribe/i }).click();

    await expect(page).toHaveURL(/success|complete/, { timeout: 30_000 });
  });
});
