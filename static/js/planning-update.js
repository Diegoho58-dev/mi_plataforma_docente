(() => {
  "use strict";
  const selectionForm = document.querySelector("[data-selection-form]");
  const confirmationForm = document.querySelector("[data-confirmation-form]");
  if (selectionForm) {
    selectionForm.addEventListener("submit", (event) => {
      if (!selectionForm.querySelector('input[name="clase"]:checked')) {
        event.preventDefault();
        window.alert("Selecciona al menos una materia y un CLEI.");
      }
    });
  }
  if (confirmationForm) {
    confirmationForm.addEventListener("submit", (event) => {
      const checkbox = confirmationForm.querySelector('input[name="confirmar"]');
      if (!checkbox || !checkbox.checked) {
        event.preventDefault();
        window.alert("Debes confirmar que revisaste la propuesta.");
      }
    });
  }
})();
