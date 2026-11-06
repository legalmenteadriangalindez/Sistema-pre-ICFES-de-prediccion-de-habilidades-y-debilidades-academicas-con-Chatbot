/* Navegación responsive. No depende de módulos de otras pantallas. */
'use strict';
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('app-menu-toggle');
  const sidebar = document.getElementById('app-sidebar');
  if (!toggle || !sidebar) return;

  const setOpen = (open) => {
    sidebar.classList.toggle('open', open);
    toggle.setAttribute('aria-expanded', String(open));
  };

  toggle.addEventListener('click', () => {
    setOpen(!sidebar.classList.contains('open'));
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') setOpen(false);
  });
  sidebar.addEventListener('click', (event) => {
    if (event.target.closest('a')) setOpen(false);
  });
});
