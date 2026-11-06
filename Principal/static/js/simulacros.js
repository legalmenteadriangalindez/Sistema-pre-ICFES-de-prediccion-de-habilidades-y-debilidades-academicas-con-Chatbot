'use strict';

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('form-simulacro');
  const timer = document.getElementById('simulacro-timer');
  if (!form || !timer) return;

  const preguntas = [...form.querySelectorAll('.pregunta-simulacro')];
  const hoja = document.getElementById('hoja');
  const reloj = document.getElementById('reloj');
  const vence = Number(timer.dataset.vence) * 1000;
  const progresoTitulo = document.getElementById('progreso-titulo');
  const progresoBarra = document.getElementById('exam-progress-fill');
  const areaActual = document.getElementById('area-actual');
  const indiceChip = document.getElementById('question-index-chip');
  const respondidas = document.getElementById('respondidas');
  const pendientes = document.getElementById('pendientes');
  const anterior = document.getElementById('anterior');
  const siguiente = document.getElementById('siguiente');
  let actual = 0;
  let enviado = false;
  if (!preguntas.length || !hoja || !reloj || !Number.isFinite(vence)) return;

  function estado() {
    const totalRespondidas = preguntas.filter(p => Boolean(p.querySelector('input:checked'))).length;
    if (respondidas) respondidas.textContent = String(totalRespondidas);
    if (pendientes) pendientes.textContent = String(preguntas.length - totalRespondidas);
    if (progresoTitulo) progresoTitulo.textContent = `Pregunta ${actual + 1} de ${preguntas.length}`;
    if (progresoBarra) progresoBarra.style.width = `${(actual + 1) / preguntas.length * 100}%`;
    if (indiceChip) indiceChip.textContent = `${actual + 1} / ${preguntas.length}`;
    if (areaActual) areaActual.textContent = preguntas[actual].dataset.materia || 'Simulacro';
    anterior.disabled = actual === 0;
    siguiente.disabled = actual === preguntas.length - 1;
    hoja.replaceChildren();
    preguntas.forEach((p, i) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = p.querySelector('input:checked') ? 'answered' : 'unanswered';
      btn.textContent = String(i + 1);
      btn.setAttribute('aria-label', `Ir a pregunta ${i + 1}`);
      btn.setAttribute('aria-current', i === actual ? 'step' : 'false');
      btn.addEventListener('click', () => mostrar(i));
      hoja.appendChild(btn);
    });
  }
  function mostrar(i) {
    actual = Math.max(0, Math.min(i, preguntas.length - 1));
    preguntas.forEach((p, j) => { p.hidden = j !== actual; });
    estado();
  }
  function actualizarReloj() {
    const segundos = Math.max(0, Math.ceil((vence - Date.now()) / 1000));
    const h = Math.floor(segundos / 3600);
    const m = Math.floor((segundos % 3600) / 60);
    const s = segundos % 60;
    reloj.textContent = `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
    timer.classList.toggle('timer-warning', segundos > 0 && segundos <= 300);
    if (segundos === 0 && !enviado) {
      enviado = true;
      form.requestSubmit();
    }
  }
  form.addEventListener('change', estado);
  anterior?.addEventListener('click', () => mostrar(actual - 1));
  siguiente?.addEventListener('click', () => mostrar(actual + 1));
  form.addEventListener('submit', event => {
    if (enviado) return;
    if (event.submitter?.dataset.confirmFinalizar === 'true') {
      const respondidas = preguntas.filter(p => p.querySelector('input:checked')).length;
      const faltantes = preguntas.length - respondidas;
      const pregunta = faltantes ? `Faltan ${faltantes} preguntas. ¿Deseas finalizar y calificar?` : '¿Finalizar el simulacro y calificar tus respuestas?';
      if (!window.confirm(pregunta)) { event.preventDefault(); return; }
    }
    enviado = true;
  });
  mostrar(0);
  actualizarReloj();
  window.setInterval(actualizarReloj, 1000);
});
