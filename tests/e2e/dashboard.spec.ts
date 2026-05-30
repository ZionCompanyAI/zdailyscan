import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/login");
  await page.fill('input[name="username"]', process.env.DASHBOARD_USERNAME || "admin");
  await page.fill('input[name="password"]', process.env.DASHBOARD_PASSWORD || "");
  await page.click('button[type="submit"]');
});

test('botão "Iniciar Scan" existe e está habilitado', async ({ page }) => {
  await page.goto("/dashboard/scanner");
  const btn = page.getByRole("button", { name: "Iniciar Scan" });
  await expect(btn).toBeVisible();
  await expect(btn).toBeEnabled();
});

test("página scanner carrega", async ({ page }) => {
  await page.goto("/dashboard/scanner");
  await expect(page).toHaveURL(/dashboard\/scanner/);
});
