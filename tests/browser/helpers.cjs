const { expect } = require('@playwright/test');

async function loginAsAdmin(page) {
  await page.goto('/accounts/login/');
  await page.locator('input[name="username"]').fill('admin_e2e');
  await page.locator('input[name="password"]').fill('SoloPruebasE2E!2026');
  await page.getByRole('button', { name: /iniciar sesión/i }).click();
  await expect(page).toHaveURL(/\/admin_gestion_users\//);
  await expect(page.locator('#users-table')).toBeVisible();
}

module.exports = { loginAsAdmin };
