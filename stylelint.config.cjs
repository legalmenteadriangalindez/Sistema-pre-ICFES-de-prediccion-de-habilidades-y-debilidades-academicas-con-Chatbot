/* Primera etapa: detectar CSS inválido en todas las hojas sin aplicar cambios visuales. */
module.exports = {
  extends: ['stylelint-config-recommended'],
  ignoreFiles: ['node_modules/**', 'playwright-report/**', 'test-results/**'],
  rules: {
    // El CSS histórico aún tiene capas de compatibilidad; depurar duplicados
    // por módulos requiere una fase separada con inspección en navegador.
    'no-duplicate-selectors': null,
  },
};
