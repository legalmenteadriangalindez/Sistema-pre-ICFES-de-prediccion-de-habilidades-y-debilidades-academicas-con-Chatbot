/* Confirmaciones de formularios por delegación, sin onclick/onsubmit en HTML. */
'use strict';
document.addEventListener('submit', (event) => {
  const form = event.target?.closest?.('form[data-confirm]');
  if (!form) return;
  const message = form.getAttribute('data-confirm');
  if (message && !window.confirm(message)) {
    event.preventDefault();
  }
});
