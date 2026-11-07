const { test, expect } = require('@playwright/test');

const { loginAsAdmin } = require('./helpers.cjs');

test('login y registro conservan los campos públicos', async ({ page }) => {
  await page.goto('/accounts/login/');
  await expect(page.getByRole('heading', { name: /iniciar sesión/i })).toBeVisible();
  await expect(page.locator('input[name="username"]')).toBeVisible();
  await expect(page.locator('input[name="password"]')).toBeVisible();

  await page.goto('/registro/');
  await expect(page.getByRole('heading', { name: 'Registro' })).toBeVisible();
  await expect(page.locator('input[name="username"]')).toBeVisible();
  await expect(page.locator('input[name="email"]')).toBeVisible();
});

test('gestión administrativa exige sesión', async ({ page }) => {
  await page.goto('/admin_gestion_users/');
  await expect(page).toHaveURL(/\/accounts\/login\//);
  await expect(page.locator('#users-table')).toHaveCount(0);
});

test('administrador inicia sesión y filtra usuarios reales', async ({ page }) => {
  await loginAsAdmin(page);
  const row = page.locator('#users-table tbody tr').filter({ hasText: 'estudiante_e2e' });
  await expect(row).toBeVisible();
  await page.locator('#user-search').fill('estudiante_e2e');
  await expect(row).toBeVisible();
  await expect(page.locator('#table-count')).toContainText('Mostrando 1 de');
  await page.locator('#user-search').fill('sin-coincidencias-123456');
  await expect(row).toBeHidden();
});

test('cancelar eliminación mantiene el registro y la sesión', async ({ page }) => {
  await loginAsAdmin(page);
  const row = page.locator('#users-table tbody tr').filter({ hasText: 'estudiante_e2e' });
  await expect(row).toBeVisible();
  page.once('dialog', async (dialog) => {
    expect(dialog.type()).toBe('confirm');
    await dialog.dismiss();
  });
  await row.getByRole('button', { name: /eliminar usuario/i }).click();
  await expect(row).toBeVisible();
  await expect(page).toHaveURL(/\/admin_gestion_users\//);
});
