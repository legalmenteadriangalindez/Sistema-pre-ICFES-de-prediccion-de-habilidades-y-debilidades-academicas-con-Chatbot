"use strict";

// Mejora visual solamente: la calificación y las respuestas correctas viven en Django.
document.addEventListener("change", (event) => {
  if (!event.target.matches('.pregunta-cuestionario input[type="radio"]')) return;

  const fieldset = event.target.closest(".pregunta-cuestionario");
  fieldset.querySelectorAll(".opcion").forEach((opcion) => {
    opcion.classList.toggle(
      "opcion-seleccionada",
      opcion.querySelector("input").checked,
    );
  });
});
