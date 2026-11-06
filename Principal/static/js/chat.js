/* Composición del chat: solo carga en Inicio. No controla micrófono ni preferencias. */
'use strict';
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('tutor-form');
  const prompt = document.getElementById('chat-prompt');
  const send = document.getElementById('generar');
  if (!form || !prompt || !send) return;

  const pdf = form.querySelector('input[name="archivo"]');
  const audio = form.querySelector('input[name="audio"]');
  const attachmentName = document.getElementById('attachment-name');

  const synchronize = () => {
    prompt.style.height = 'auto';
    prompt.style.height = Math.min(prompt.scrollHeight, 180) + 'px';
    const hasAttachment = Boolean(pdf?.files?.length || audio?.files?.length);
    send.disabled = !prompt.value.trim() && !hasAttachment;
    if (attachmentName) {
      attachmentName.textContent = pdf?.files?.[0]?.name || audio?.files?.[0]?.name || '';
    }
  };

  prompt.addEventListener('input', synchronize);
  prompt.addEventListener('keydown', (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter' && !send.disabled) {
      event.preventDefault();
      form.requestSubmit(send);
    }
  });
  document.querySelectorAll('[data-chat-suggestion]').forEach((chip) => {
    chip.addEventListener('click', () => {
      prompt.value = chip.dataset.chatSuggestion || '';
      synchronize();
      prompt.focus();
    });
  });
  pdf?.addEventListener('change', synchronize);
  audio?.addEventListener('change', synchronize);
  form.addEventListener('submit', () => {
    send.disabled = true;
    send.setAttribute('aria-busy', 'true');
  });

  const history = document.getElementById('respuesta');
  if (history?.querySelector('.chat-row')) history.scrollTop = history.scrollHeight;
  synchronize();
});
