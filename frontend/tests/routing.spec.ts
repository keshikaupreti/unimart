import { test, expect } from '@playwright/test';

test('API forwarding preserves POST data and the Django trailing slash', async ({ request }) => {
  const response = await request.post('/api/auth/login/', { data: { username: 'routing-check', password: 'fixture-only' }, maxRedirects: 0 });
  expect(response.status()).toBe(200);
  const forwarded = await response.json();
  expect(forwarded.path).toBe('/api/auth/login/');
  expect(forwarded.method).toBe('POST');
  expect(JSON.parse(forwarded.body)).toEqual({ username: 'routing-check', password: 'fixture-only' });
});

test('media forwarding preserves file paths', async ({ request }) => {
  const response = await request.get('/media/listings/example.png', { maxRedirects: 0 });
  expect(response.status()).toBe(200);
  expect((await response.json()).path).toBe('/media/listings/example.png');
});
