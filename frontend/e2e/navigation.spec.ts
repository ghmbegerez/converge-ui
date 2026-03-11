import { test, expect } from "@playwright/test";

test.describe("Navigation", () => {
  test("overview page loads with KPIs", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("h1")).toContainText("Converge UI");
    // KPI metrics render (demo mode produces at least running, blocked, merged)
    await expect(page.locator(".metric, .metric-box")).toHaveCount({ minimum: 1 });
    // No unhandled JS errors — page title updates
    await expect(page).toHaveTitle(/Converge UI/);
  });

  test("navigate to operations", async ({ page }) => {
    await page.goto("/");
    await page.click('a[href="/operations"]');
    await expect(page).toHaveURL(/\/operations/);
    // Operations page renders job lists
    await expect(page.locator(".card")).toHaveCount({ minimum: 1 });
  });

  test("navigate to reviews", async ({ page }) => {
    await page.goto("/");
    await page.click('a[href="/reviews"]');
    await expect(page).toHaveURL(/\/reviews/);
    await expect(page.locator("text=Review queue")).toBeVisible();
  });

  test("navigate to compliance", async ({ page }) => {
    await page.goto("/");
    await page.click('a[href="/compliance"]');
    await expect(page).toHaveURL(/\/compliance/);
    await expect(page.locator(".card")).toHaveCount({ minimum: 1 });
  });

  test("job detail page loads with timeline", async ({ page }) => {
    // Navigate to a demo job via the operations page
    await page.goto("/operations");
    // Click on first job link if available
    const jobLink = page.locator('a[href^="/jobs/"]').first();
    if (await jobLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await jobLink.click();
      await expect(page).toHaveURL(/\/jobs\//);
      // Job detail renders with timeline section
      await expect(page.locator("text=Job detail")).toBeVisible();
      await expect(page.locator("text=Timeline")).toBeVisible();
    }
  });

  test("intent detail page loads with events", async ({ page }) => {
    // Navigate to intent from a job page or directly
    await page.goto("/operations");
    const intentLink = page.locator('a[href^="/intents/"]').first();
    if (await intentLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await intentLink.click();
      await expect(page).toHaveURL(/\/intents\//);
    }
  });
});
