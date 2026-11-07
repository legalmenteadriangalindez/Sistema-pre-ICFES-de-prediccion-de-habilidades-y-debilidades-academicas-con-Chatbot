const { test, expect } = require('@playwright/test');
const { loginAsAdmin } = require('./helpers.cjs');

test('los diez componentes CSS heredados cargan sin errores en el navegador', async ({ page }) => {
  const loaded = new Map();
  page.on('response', (response) => {
    const path = new URL(response.url()).pathname;
    if (path.includes('/static/css/legacy/') && path.endsWith('.css')) {
      loaded.set(path, response.status());
    }
  });
  await loginAsAdmin(page);
  await expect.poll(() => loaded.size).toBe(10);
  for (const [path, status] of loaded) {
    expect(status, path).toBe(200);
  }
  await expect(page.locator('#users-table')).toBeVisible();
});
