import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  use: { baseURL: 'http://127.0.0.1:3100', ...(process.env.PLAYWRIGHT_CHANNEL ? { channel: process.env.PLAYWRIGHT_CHANNEL } : {}) },
  webServer: [
    { command: 'node tests/api-fixture.cjs', url: 'http://127.0.0.1:8101', reuseExistingServer: false },
    {
      command: 'npm run dev -- --hostname 127.0.0.1 --port 3100 --webpack',
      url: 'http://127.0.0.1:3100',
      env: { BACKEND_URL: 'http://127.0.0.1:8101' },
      reuseExistingServer: false,
      timeout: 120000,
    },
  ],
});
