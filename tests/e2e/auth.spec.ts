import { test, expect } from "@playwright/test";

test("login com credenciais válidas redireciona para /dashboard", async ({ page }) => {
  await page.goto("/login");
  await page.fill('input[name="username"]', process.env.DASHBOARD_USERNAME || "admin");
  await page.fill('input[name="password"]', process.env.DASHBOARD_PASSWORD || "");
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/dashboard/);
});
