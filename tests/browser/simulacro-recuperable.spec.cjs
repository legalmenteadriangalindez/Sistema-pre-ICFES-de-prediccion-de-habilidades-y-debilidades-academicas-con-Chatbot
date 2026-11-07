const { test, expect } = require('@playwright/test');

test('simulacro de dos bloques recupera las respuestas tras pausa y recarga', async ({ page }) => {
  await page.goto('/accounts/login/');
  await page.locator('input[name="username"]').fill('estudiante_e2e');
  await page.locator('input[name="password"]').fill('SoloPruebasE2E!2026');
  await page.getByRole('button', { name: /iniciar sesión/i }).click({ noWaitAfter: true });
  await expect(page).not.toHaveURL(/\/accounts\/login\//, { timeout: 30000 });
  await page.goto('/simulacros/avanzado/');
  await expect(page.getByRole('heading', { name: 'Simulacro recuperable' })).toBeVisible();
  await page.getByRole('button', { name: 'Iniciar 50 preguntas' }).click();
  await expect(page.getByText('Bloque 1 de 2')).toBeVisible();
  await page.locator('.cierre-pregunta').first().locator('input[type="radio"][value="A"]').check();
  await expect(page.locator('#estado-guardado')).toContainText('guardada', { timeout: 15000 });
  await page.getByRole('button', { name: 'Pausar y guardar' }).click();
  await expect(page.getByRole('button', { name: 'Reanudar bloque 1' })).toBeVisible();
  await page.reload();
  await page.getByRole('button', { name: 'Reanudar bloque 1' }).click();
  await expect(page.locator('.cierre-pregunta').first().locator('input[type="radio"][value="A"]')).toBeChecked();
  await page.getByRole('button', { name: 'Pausar y guardar' }).click();
  await page.getByRole('button', { name: 'Cerrar bloque 1 y preparar bloque 2' }).click();
  await expect(page.getByRole('button', { name: 'Reanudar bloque 2' })).toBeVisible();
  await page.getByRole('button', { name: 'Reanudar bloque 2' }).click();
  await expect(page.getByText('Bloque 2 de 2')).toBeVisible();
  await page.getByRole('button', { name: 'Finalizar y calificar' }).click();
  await expect(page.getByRole('heading', { name: 'Tu simulacro de práctica' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Resultados por materia y competencia' })).toBeVisible();
});
