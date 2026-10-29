"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("form-simulacro");
  const timer = document.getElementById("simulacro-timer");
  if (!form || !timer) return;

  const preguntas = [...form.querySelectorAll(".pregunta-simulacro")];
  const hoja = document.getElementById("hoja");
  const reloj = document.getElementById("reloj");
  const vence = Number(timer.dataset.vence) * 1000;
  let actual = 0;
  let enviado = false;

  function actualizarHoja() {
    hoja.replaceChildren();
    preguntas.forEach((pregunta, indice) => {
      const boton = document.createElement("button");
      boton.type = "button";
      boton.textContent = String(indice + 1);
      boton.className = `btn btn-sm ${
        pregunta.querySelector("input:checked")
          ? "btn-success"
          : indice === actual
            ? "btn-primary"
            : "btn-outline-secondary"
      }`;
      boton.setAttribute("aria-label", `Ir a pregunta ${indice + 1}`);
      boton.setAttribute("aria-current", indice === actual ? "step" : "false");
      boton.addEventListener("click", () => mostrarPregunta(indice));
      hoja.appendChild(boton);
    });
  }

  function mostrarPregunta(indice) {
    actual = Math.max(0, Math.min(indice, preguntas.length - 1));
    preguntas.forEach((pregunta, numero) => {
      pregunta.hidden = numero !== actual;
    });
    actualizarHoja();
  }

  function actualizarReloj() {
    const segundos = Math.max(0, Math.ceil((vence - Date.now()) / 1000));
    reloj.textContent = `${Math.floor(segundos / 60)}:${String(segundos % 60).padStart(2, "0")}`;
    if (segundos === 0 && !enviado) {
      enviado = true;
      form.requestSubmit();
    }
  }

  form.addEventListener("change", actualizarHoja);
  document.getElementById("anterior")?.addEventListener("click", () => {
    mostrarPregunta(actual - 1);
  });
  document.getElementById("siguiente")?.addEventListener("click", () => {
    mostrarPregunta(actual + 1);
  });

  mostrarPregunta(0);
  actualizarReloj();
  window.setInterval(actualizarReloj, 1000);
});
