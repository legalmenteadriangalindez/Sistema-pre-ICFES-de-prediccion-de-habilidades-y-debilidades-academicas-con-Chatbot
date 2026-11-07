/* Preferencias de accesibilidad y apariencia: fuente única, estado existente v2. */
'use strict';
(() => {
  const KEY = 'preicfes.ui.v2';
  const DEFAULTS = { dark: false, textSize: 100, reduceMotion: false };
  let options = { ...DEFAULTS };

  // Almacenamiento de navegador puede estar prohibido (p. ej. modo privado).
  try {
    const saved = localStorage.getItem(KEY);
    if (saved) {
      const data = JSON.parse(saved);
      if (data && typeof data === 'object' && !Array.isArray(data)) {
        options = { ...options, ...data };
      }
    } else {
      // Únicamente al migrar, conservar la preferencia del script heredado.
      const oldDark = localStorage.getItem('modoOscuro');
      if (oldDark === 'true') options.dark = true;
    }
  } catch {
    // La interfaz sigue funcionando sin persistencia local.
  }

  options.dark = options.dark === true;
  options.reduceMotion = options.reduceMotion === true;
  options.textSize = Math.max(90, Math.min(120, Number(options.textSize) || 100));

  const apply = () => {
    if (!document.body) return;
    document.body.classList.toggle('theme-dark', options.dark);
    document.body.classList.toggle('reduce-motion', options.reduceMotion);
    document.body.style.setProperty('--pc-text-scale', String(options.textSize / 100));
  };

  const save = () => {
    apply();
    try {
      localStorage.setItem(KEY, JSON.stringify(options));
    } catch {
      // Sin almacenamiento, las preferencias continúan activas durante la sesión.
    }
  };

  apply();
  document.addEventListener('DOMContentLoaded', () => {
    apply();
    const dark = document.querySelector('[data-ui-preference="dark"]');
    const size = document.querySelector('[data-ui-preference="text-size"]');
    const motion = document.querySelector('[data-ui-preference="reduce-motion"]');
    const output = document.getElementById('pref-text-size-output');

    if (dark) dark.checked = options.dark;
    if (motion) motion.checked = options.reduceMotion;
    if (size) size.value = String(options.textSize);
    if (output) output.textContent = options.textSize + ' %';

    dark?.addEventListener('change', () => {
      options.dark = dark.checked;
      save();
    });
    motion?.addEventListener('change', () => {
      options.reduceMotion = motion.checked;
      save();
    });
    size?.addEventListener('input', () => {
      options.textSize = Math.max(90, Math.min(120, Number(size.value) || 100));
      if (output) output.textContent = options.textSize + ' %';
      save();
    });
  });
})();
