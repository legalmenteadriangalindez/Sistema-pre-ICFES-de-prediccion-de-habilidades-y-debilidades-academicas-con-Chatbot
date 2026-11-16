"use strict";

document.addEventListener("click", (event) => {
  const toggle = event.target.closest("[data-password-toggle]");
  if (!toggle) return;

  const targetId = toggle.getAttribute("aria-controls");
  const input = targetId ? document.getElementById(targetId) : null;
  if (!input) return;

  const visible = input.type === "password";
  input.type = visible ? "text" : "password";
  toggle.setAttribute("aria-pressed", String(visible));

  const passwordName = toggle.dataset.passwordName || "la contraseña";
  toggle.setAttribute(
    "aria-label",
    (visible ? "Ocultar " : "Mostrar ") + passwordName
  );

  const icon = toggle.querySelector("i");
  if (icon) {
    icon.classList.toggle("fa-eye", !visible);
    icon.classList.toggle("fa-eye-slash", visible);
    icon.classList.toggle("far", !visible);
    icon.classList.toggle("fas", visible);
  }

  const label = toggle.querySelector("[data-password-toggle-label]");
  if (label) {
    label.textContent = visible ? "Ocultar contraseña" : "Mostrar contraseña";
  }
});
