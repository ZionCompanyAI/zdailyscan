import { test, expect } from '@playwright/test';

test.describe('Contract', () => {
  test('/health JSON schema has status field', async ({ request }) => {
    const response = await request.get('/health');
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty('status');
    expect(typeof body.status).toBe('string');
  });
});
