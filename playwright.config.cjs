const { defineConfig, devices } = require('@playwright/test');

const port = 8765;
const baseURL = `http://127.0.0.1:${port}`;

module.exports = defineConfig({
  testDir: './tests/browser',
  testMatch: '**/*.spec.cjs',
  timeout: 45_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1, // SQLite efímera: sin carreras entre pruebas.
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    actionTimeout: 10_000,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: `python manage.py runserver 127.0.0.1:${port} --noreload`,
    url: `${baseURL}/accounts/login/`,
    timeout: 150_000,
    reuseExistingServer: !process.env.CI,
    env: {
      DJANGO_ENV: 'development',
      DJANGO_DEBUG: 'true',
      DJANGO_DB_PATH: 'ci-browser.sqlite3',
      DJANGO_ALLOWED_HOSTS: '127.0.0.1,localhost',
      OLLAMA_BASE_URL: 'http://127.0.0.1:11434',
    },
  },
});
