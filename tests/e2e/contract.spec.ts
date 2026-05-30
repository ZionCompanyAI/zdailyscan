import { test, expect } from "@playwright/test";

test("GET /health retorna status code 200", async ({ request }) => {
  const response = await request.get("/health");
  expect(response.status()).toBe(200);
});

test("GET /health JSON schema válido", async ({ request }) => {
  const response = await request.get("/health");
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(typeof body.status).toBe("string");
  expect(body.status).toBeTruthy();
});
