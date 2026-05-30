import { test, expect } from '@playwright/test';

test.describe('Smoke', () => {
  test('GET /health returns {status: ok}', async ({ request }) => {
    const response = await request.get('/health');
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.status).toBe('ok');
  });

  test('root path responds with HTTP 200 or 303', async ({ request }) => {
    const response = await request.get('/', { maxRedirects: 0 });
    expect([200, 303]).toContain(response.status());
  });
});
