/* Guardado por pregunta, navegación y tiempo visual. Servidor valida tiempos y permisos. */
(() => {
  const root = document.getElementById('examen-persistente');
  const clock = document.getElementById('tiempo-restante');
  if (clock) {
    const deadline = Number(clock.dataset.vence || 0) * 1000;
    const initial = Number(clock.dataset.restante || 0);
    const running = clock.dataset.activo === '1';
    const tick = () => {
      const seconds = running ? Math.max(0, Math.floor((deadline - Date.now()) / 1000)) : initial;
      const minutes = Math.floor(seconds / 60);
      clock.textContent = `${minutes} min ${String(seconds % 60).padStart(2, '0')} s`;
      if (seconds === 0 && running) {
        clock.textContent += ' · tiempo agotado, recarga para continuar';
        root?.querySelectorAll('input[type="radio"]').forEach((input) => {
          input.disabled = true;
        });
      }
    };
    tick();
    if (running) window.setInterval(tick, 1000);
  }
  if (!root) return;
  const questions = [...root.querySelectorAll('.cierre-pregunta')];
  const nav = document.getElementById('navegador-preguntas');
  const feedback = document.getElementById('estado-guardado');
  const csrf = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
  let current = 0;
  let pending = Promise.resolve();

  const update = () => {
    questions.forEach((question, i) => {
      question.hidden = i !== current;
    });
    if (nav) {
      [...nav.children].forEach((button, i) => {
        button.classList.toggle('is-current', i === current);
        button.classList.toggle(
          'is-answered',
          Boolean(questions[i].querySelector('input[type="radio"]:checked'))
        );
        button.setAttribute('aria-current', i === current ? 'step' : 'false');
      });
    }
    const previous = document.getElementById('pregunta-anterior');
    const next = document.getElementById('pregunta-siguiente');
    if (previous) previous.disabled = current === 0;
    if (next) next.disabled = current === questions.length - 1;
  };

  questions.forEach((question, i) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'cierre-numero';
    button.textContent = String(i + 1);
    button.setAttribute('aria-label', `Ir a la pregunta ${i + 1}`);
    button.addEventListener('click', () => {
      current = i;
      update();
    });
    nav?.appendChild(button);
    question.querySelectorAll('input[type="radio"]').forEach((input) => {
      input.addEventListener('change', () => {
        feedback.textContent = 'Guardando respuesta...';
        const payload = new FormData();
        payload.append('csrfmiddlewaretoken', csrf || '');
        payload.append('accion', 'guardar');
        payload.append('indice', question.dataset.idx);
        payload.append('valor', input.value);
        pending = pending.catch(() => {}).then(async () => {
          const response = await fetch(root.dataset.guardarUrl, {
            method: 'POST', body: payload, credentials: 'same-origin',
          });
          if (!response.ok) throw new Error('No se pudo guardar la respuesta');
          return response.json();
        }).then(() => {
          feedback.textContent = 'Respuesta guardada en el servidor.';
          update();
        }).catch(() => {
          feedback.textContent = 'Error al guardar. No finalices sin comprobar la conexión.';
        });
      });
    });
  });
  document.getElementById('pregunta-anterior')?.addEventListener('click', () => {
    current = Math.max(0, current - 1);
    update();
  });
  document.getElementById('pregunta-siguiente')?.addEventListener('click', () => {
    current = Math.min(questions.length - 1, current + 1);
    update();
  });

  // Garantizar que una pausa/finalización no adelante el último guardado AJAX.
  document.querySelectorAll('form').forEach((form) => {
    if (!form.querySelector('input[name="accion"][value="pausar"], input[name="accion"][value="siguiente_bloque"], input[name="accion"][value="finalizar"]')) return;
    form.addEventListener('submit', async (event) => {
      if (form.dataset.readyToSubmit === '1') return;
      event.preventDefault();
      await pending;
      form.dataset.readyToSubmit = '1';
      form.submit();
    });
  });
  update();
})();
