import { defineConfig, devices } from "@playwright/test";

/**
 * E2E tests run against the FastAPI server in demo mode.
 *
 * Start the backend before running:
 *   CONVERGE_UI_DATA_MODE=demo CONVERGE_UI_AUTH_REQUIRED=0 \
 *     python -m converge_ui --port 9988
 *
 * Or use `webServer` below to auto-start.
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? "github" : "list",
  timeout: 15_000,
  use: {
    baseURL: process.env.BASE_URL || "http://127.0.0.1:9988",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: process.env.BASE_URL
    ? undefined
    : {
        command:
          "CONVERGE_UI_DATA_MODE=demo CONVERGE_UI_AUTH_REQUIRED=0 CONVERGE_UI_ENV=test python -m converge_ui",
        url: "http://127.0.0.1:9988/health/live",
        reuseExistingServer: !process.env.CI,
        timeout: 30_000,
        cwd: "..",
      },
});
