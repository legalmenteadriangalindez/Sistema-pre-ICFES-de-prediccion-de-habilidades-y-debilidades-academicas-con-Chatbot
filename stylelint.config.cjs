/* Adopción gradual: errores CSS en todas las hojas, excepciones legacy acotadas. */
module.exports = {
  extends: ['stylelint-config-recommended'],
  ignoreFiles: ['node_modules/**', 'playwright-report/**', 'test-results/**'],
  rules: {
    // Capas y pseudoclases deliberadas: reordenarlas rompe la cascada existente.
    'no-descending-specificity': null,
    'no-duplicate-selectors': null,
  },
  overrides: [
    {
      files: ['**/configuraciones.css', '**/perfile.css'],
      rules: {
        // Estas dos hojas antiguas definen dos border-radius en la misma regla.
        'declaration-block-no-duplicate-properties': null,
      },
    },
    {
      files: ['**/ui-polish-administracion.css'],
      rules: {
        // word-break:break-word todavía se requiere para diseño de tablas heredadas.
        'declaration-property-value-keyword-no-deprecated': null,
      },
    },
  ],
};
