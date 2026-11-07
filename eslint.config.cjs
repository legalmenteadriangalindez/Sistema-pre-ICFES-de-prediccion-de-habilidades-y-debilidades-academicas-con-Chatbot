/* ESLint flat config: módulos del navegador y pruebas E2E Node. */
const js = require('@eslint/js');
const globals = require('globals');

module.exports = [
  {
    ignores: ['node_modules/**', 'test-results/**', 'playwright-report/**'],
  },
  {
    files: ['Principal/static/js/**/*.js', 'tests/browser/**/*.cjs'],
    ...js.configs.recommended,
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'script',
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    rules: {
      'no-undef': 'error',
      'no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      'no-debugger': 'error',
      'no-eval': 'error',
    },
  },
];
