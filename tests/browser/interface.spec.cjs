const { test, expect } = require('@playwright/test');
const { loginAsAdmin } = require('./helpers.cjs');

test('apariencia persiste después de recargar la página', async ({ page }) => {
  await loginAsAdmin(page);
  await page.goto('/configuraciones/');
  const dark = page.locator('[data-ui-preference="dark"]');
  await expect(dark).toHaveCount(1);
  await dark.check({ force: true });
  await expect(page.locator('body')).toHaveClass(/theme-dark/);

  await page.locator('[data-ui-preference="text-size"]').evaluate((element) => {
    element.value = '115';
    element.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await expect(page.locator('#pref-text-size-output')).toHaveText('115 %');
  await page.reload();
  await expect(dark).toBeChecked();
  await expect(page.locator('body')).toHaveClass(/theme-dark/);
  await expect(page.locator('#pref-text-size-output')).toHaveText('115 %');
});

test('mensajes dinámicos son accesibles y no interpretan HTML', async ({ page }) => {
  await loginAsAdmin(page);
  await page.evaluate(() => {
    window.PreICFES.notify('<img src=x onerror=alert(1)>', 'warning');
  });
  const notice = page.locator('#app-notifications [data-notice]');
  await expect(notice).toHaveCount(1);
  await expect(notice).toHaveAttribute('role', 'alert');
  await expect(notice).toContainText('<img src=x onerror=alert(1)>');
  await expect(notice.locator('img')).toHaveCount(0);
  await notice.getByRole('button', { name: 'Cerrar notificación' }).click();
  await expect(notice).toHaveCount(0);
});

test('menú responsive funciona en pantalla móvil', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await loginAsAdmin(page);
  const toggle = page.locator('#app-menu-toggle');
  await expect(toggle).toBeVisible();
  await toggle.click();
  await expect(toggle).toHaveAttribute('aria-expanded', 'true');
  await expect(page.locator('#app-sidebar')).toHaveClass(/open/);
  await page.keyboard.press('Escape');
  await expect(toggle).toHaveAttribute('aria-expanded', 'false');
});

test('pantallas principales no arrojan errores JavaScript', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/accounts/login/');
  await page.goto('/registro/');
  await loginAsAdmin(page);
  await page.goto('/configuraciones/');
  await page.goto('/admin_gestion_academica/');
  expect(errors, errors.join('\n')).toEqual([]);
});
