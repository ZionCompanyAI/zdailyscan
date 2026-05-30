import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: "html",
  use: {
    baseURL: process.env.BASE_URL || "https://zdailyscan.zioncompanyai.com.br",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
});
