(() => {
  "use strict";

  const form = document.querySelector("[data-selection-form]");
  if (!form) return;

  form.addEventListener("submit", (event) => {
    const selected = form.querySelectorAll('input[name="materia"]:checked');
    if (!selected.length) {
      event.preventDefault();
      window.alert("Selecciona al menos una materia para crear la estructura.");
    }
  });
})();
