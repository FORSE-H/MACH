// Playwright config for MACH's static-site end-to-end tests.
// The site is plain files, so we serve the repo root over HTTP (a simple Python
// server) and point the tests at it. Semantic search hits a live API, so those
// tests stub the /search response — the local-filter tests (python, licence,
// filter-reset) need no network and are the ones that guard today's bug class.

const { defineConfig, devices } = require('@playwright/test');

const PORT = 8000;

module.exports = defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,   // a stray test.only fails CI
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['list']] : 'list',
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  // Serve the repo root before the tests run.
  webServer: {
    command: `python -m http.server ${PORT}`,
    url: `http://127.0.0.1:${PORT}/index.html`,
    reuseExistingServer: !process.env.CI,
    timeout: 60 * 1000,
  },
});
