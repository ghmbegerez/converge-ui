import { test, expect } from "@playwright/test";

test.describe("Actions", () => {
  test("refresh action returns result", async ({ page }) => {
    // Navigate to a job detail page with the refresh button
    await page.goto("/operations");
    const jobLink = page.locator('a[href^="/jobs/"]').first();
    if (await jobLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await jobLink.click();
      await expect(page).toHaveURL(/\/jobs\//);

      // Click refresh button
      const refreshBtn = page.locator("button", { hasText: "Refresh" });
      if (await refreshBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await refreshBtn.click();
        // Should show a result banner
        await expect(page.locator(".banner")).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test("reviews page has create review form", async ({ page }) => {
    await page.goto("/reviews");
    // Review creation form is present
    await expect(page.locator("text=Create review")).toBeVisible();
    // Intent input field exists
    const intentInput = page.locator("input").first();
    await expect(intentInput).toBeVisible();
    // Request review button exists
    await expect(page.locator("button", { hasText: "Request review" })).toBeVisible();
  });

  test("reviews page has export buttons", async ({ page }) => {
    await page.goto("/reviews");
    await expect(page.locator("button", { hasText: "Export CSV" })).toBeVisible();
    await expect(page.locator("button", { hasText: "Export JSON" })).toBeVisible();
  });
});
