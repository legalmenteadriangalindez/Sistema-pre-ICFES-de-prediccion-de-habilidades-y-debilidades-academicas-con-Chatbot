const { test, expect } = require('@playwright/test');

async function entrar(page, username) {
  await page.goto('/accounts/login/');
  await page.locator('input[name="username"]').fill(username);
  await page.locator('input[name="password"]').fill('SoloPruebasE2E!2026');
  await page.getByRole('button', { name: /iniciar sesión/i }).click();
  await expect(page).not.toHaveURL(/\/accounts\/login\//);
}

test('docente crea, segundo docente aprueba y estudiante practica sin exposición de claves', async ({ page, context }) => {
  await entrar(page, 'docente_e2e');
  await page.goto('/banco-preguntas/');
  await expect(page.getByRole('heading', { name: 'Banco de preguntas y revisión docente' })).toBeVisible();

  const form = page.locator('form.bank-form');
  await form.locator('select[name="materia"]').selectOption('Matemáticas');
  await form.locator('input[name="competencia"]').fill('Sustracción');
  await form.locator('select[name="dificultad"]').selectOption('BASICA');
  await form.locator('textarea[name="enunciado"]').fill('¿Cuál es el resultado de 10 menos 6?');
  await form.locator('input[name="opcion_a"]').fill('Dos');
  await form.locator('input[name="opcion_b"]').fill('Cuatro');
  await form.locator('input[name="opcion_c"]').fill('Ocho');
  await form.locator('input[name="opcion_d"]').fill('Diez');
  await form.locator('select[name="respuesta_correcta"]').selectOption('B');
  await form.locator('textarea[name="explicacion"]').fill('La resta de diez menos seis da cuatro.');
  await form.getByRole('button', { name: 'Guardar borrador' }).click();

  let fila = page.locator('.bank-row').filter({ hasText: '¿Cuál es el resultado de 10 menos 6?' });
  await expect(fila).toBeVisible();
  await fila.getByRole('button', { name: 'Enviar a revisión' }).click();
  await expect(page.getByText('Pregunta enviada a revisión docente.')).toBeVisible();

  await context.clearCookies();
  await entrar(page, 'revisor_e2e');
  await page.goto('/banco-preguntas/');
  fila = page.locator('.bank-row').filter({ hasText: '¿Cuál es el resultado de 10 menos 6?' });
  await fila.getByRole('link', { name: 'Revisar contenido' }).click();
  await expect(page.getByText('La resta de diez menos seis da cuatro.')).toBeVisible();
  await page.locator('textarea[name="observacion"]').fill('Pregunta y respuesta verificadas manualmente.');
  await page.getByRole('button', { name: 'Aprobar publicación' }).click();
  await expect(page.getByText('Revisión guardada. Solo las aprobadas se publican.')).toBeVisible();

  await context.clearCookies();
  await entrar(page, 'estudiante_e2e');
  const forbidden = await page.goto('/banco-preguntas/');
  expect(forbidden.status()).toBe(403);
  await page.goto('/practica-adaptativa/');
  await page.getByRole('button', { name: 'Preparar mis preguntas' }).click();
  await expect(page.getByText('¿Cuál es el resultado de 10 menos 6?')).toBeVisible();
  await expect(page.getByText('La resta de diez menos seis da cuatro.')).toHaveCount(0);
  await expect(page.locator('input[name="respuesta_0"]')).toHaveCount(4);
  await page.locator('input[name="respuesta_0"][value="B"]').check();
  await page.getByRole('button', { name: 'Calificar y guardar respuestas' }).click();
  await expect(page.getByRole('heading', { name: 'Resultado del refuerzo' })).toBeVisible();
  await expect(page.getByText('La resta de diez menos seis da cuatro.')).toBeVisible();
  await page.goto('/historial-academico/');
  await expect(page.getByRole('heading', { name: 'Práctica adaptativa' })).toBeVisible();
});
