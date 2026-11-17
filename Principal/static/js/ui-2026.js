/* Navegación responsive. No depende de módulos de otras pantallas. */
'use strict';
(() => {
  const controls = () => ({
    toggle: document.getElementById('app-menu-toggle'),
    sidebar: document.getElementById('app-sidebar'),
  });

  const setOpen = (open) => {
    const { toggle, sidebar } = controls();
    if (!toggle || !sidebar) return;
    sidebar.classList.toggle('open', open);
    toggle.setAttribute('aria-expanded', String(open));
  };

  const markHandled = (event) => {
    if (event.__preicfesMenuHandled) return true;
    event.__preicfesMenuHandled = true;
    return false;
  };

  const bindControls = () => {
    const { toggle, sidebar } = controls();
    if (!toggle || !sidebar || toggle.dataset?.preicfesMenuBound) return;
    if (toggle.dataset) toggle.dataset.preicfesMenuBound = 'true';
    toggle.addEventListener('click', (event) => {
      if (markHandled(event)) return;
      setOpen(!sidebar.classList.contains('open'));
    });
    sidebar.addEventListener('click', (event) => {
      if (!markHandled(event) && event.target?.closest?.('a')) setOpen(false);
    });
  };

  // Delegación inmediata: el usuario puede abrir el menú incluso mientras
  // el resto del documento todavía termina de cargar.
  document.addEventListener('click', (event) => {
    const toggle = event.target?.closest?.('#app-menu-toggle');
    if (toggle && !markHandled(event)) {
      const { sidebar } = controls();
      setOpen(!sidebar?.classList.contains('open'));
      return;
    }

    const { sidebar } = controls();
    if (sidebar && event.target?.closest?.('#app-sidebar a')) setOpen(false);
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') setOpen(false);
  });

  bindControls();
  document.addEventListener('DOMContentLoaded', bindControls, { once: true });
})();
