/* Avisos reutilizables y accesibles. Solo textContent, nunca innerHTML. */
'use strict';
(() => {
  const TYPES = new Set(['success', 'warning', 'info']);
  const container = () => document.getElementById('app-notifications');

  function dismiss(target) {
    const notice = target?.closest?.('[data-notice]');
    if (notice) notice.remove();
  }

  document.addEventListener('click', (event) => {
    const button = event.target?.closest?.('[data-notice-dismiss]');
    if (button) dismiss(button);
  });

  // API compartida para los módulos futuros sin introducir dependencias.
  window.PreICFES = window.PreICFES || {};
  window.PreICFES.notify = (message, tone = 'info') => {
    const host = container();
    if (!host) return null;

    const safeTone = TYPES.has(tone) ? tone : 'info';
    const notice = document.createElement('div');
    notice.className = 'app-notice app-notice--' + safeTone;
    notice.setAttribute('data-notice', '');
    notice.setAttribute('role', safeTone === 'warning' ? 'alert' : 'status');

    const text = document.createElement('span');
    text.className = 'app-notice__text';
    text.textContent = String(message ?? '');

    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'app-notice__close';
    close.setAttribute('data-notice-dismiss', '');
    close.setAttribute('aria-label', 'Cerrar notificación');
    close.textContent = '×';

    notice.append(text, close);
    host.appendChild(notice);
    return notice;
  };
})();
