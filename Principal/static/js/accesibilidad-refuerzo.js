/* Preferencias visuales locales, sin enviar información al servidor. */
(() => {
  const name = 'preicfes-visual-preferences';
  const apply = (state) => {
    document.body.classList.toggle('accessible-text', Boolean(state.texto));
    document.body.classList.toggle('accessible-contrast', Boolean(state.contraste));
    document.querySelectorAll('[data-accessibility-toggle]').forEach((button) => {
      const key = button.dataset.accessibilityToggle;
      button.setAttribute('aria-pressed', state[key] ? 'true' : 'false');
    });
  };
  let state = { texto: false, contraste: false };
  try {
    const stored = JSON.parse(localStorage.getItem(name) || '{}');
    state = { texto: Boolean(stored.texto), contraste: Boolean(stored.contraste) };
  } catch {
    /* El sitio funciona incluso si el navegador bloquea almacenamiento local. */
  }
  apply(state);
  document.querySelectorAll('[data-accessibility-toggle]').forEach((button) => {
    button.addEventListener('click', () => {
      const key = button.dataset.accessibilityToggle;
      if (!['texto', 'contraste'].includes(key)) return;
      state[key] = !state[key];
      apply(state);
      try {
        localStorage.setItem(name, JSON.stringify(state));
      } catch {
        /* Los controles siguen funcionando en esta sesión. */
      }
    });
  });
})();
