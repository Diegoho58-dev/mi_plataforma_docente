(() => {
  "use strict";

  const form = document.querySelector("[data-selection-form]");
  if (!form) return;

  const syncSubject = (subjectCard) => {
    const subjectCheck = subjectCard.querySelector("[data-subject-check]");
    const controls = subjectCard.querySelectorAll("[data-clei-check], [data-topic-select], [data-ai-field]");
    controls.forEach((control) => {
      control.disabled = !subjectCheck.checked;
    });
  };

  document.querySelectorAll(".planning-subject").forEach((subjectCard) => {
    const subjectCheck = subjectCard.querySelector("[data-subject-check]");
    const cleiChecks = subjectCard.querySelectorAll("[data-clei-check]");
    const topicSelects = subjectCard.querySelectorAll("[data-topic-select]");
    const aiFields = subjectCard.querySelectorAll("[data-ai-field]");

    subjectCheck.addEventListener("change", () => syncSubject(subjectCard));
    cleiChecks.forEach((check, index) => {
      check.addEventListener("change", () => {
        if (topicSelects[index]) {
          topicSelects[index].disabled = !subjectCheck.checked || !check.checked;
          if (!check.checked) topicSelects[index].value = "";
          aiFields.forEach((field) => {
            const row = field.closest(".clei-row");
            if (row && row.querySelector("[data-clei-check]") === check && !check.checked) {
              field.value = "";
            }
          });
        }
      });
    });
    syncSubject(subjectCard);
  });

  form.addEventListener("submit", (event) => {
    const selectedSubjects = [...form.querySelectorAll('input[name="materia"]:checked')];
    if (!selectedSubjects.length) {
      event.preventDefault();
      window.alert("Selecciona al menos una materia para actualizar.");
      return;
    }

    let missingTopic = false;
    const isGenerating = event.submitter && event.submitter.value === "generar_ia";
    document.querySelectorAll(".planning-subject").forEach((subjectCard) => {
      const subjectCheck = subjectCard.querySelector("[data-subject-check]");
      if (!subjectCheck.checked) return;
      subjectCard.querySelectorAll(".clei-row").forEach((row) => {
        const cleiCheck = row.querySelector("[data-clei-check]");
        const topicSelect = row.querySelector("[data-topic-select]");
        if (cleiCheck.checked && (!topicSelect || !topicSelect.value)) {
          missingTopic = true;
        }
      });
    });

    if (missingTopic) {
      event.preventDefault();
      window.alert(isGenerating ? "Cada CLEI marcado debe tener un tema antes de generar la propuesta." : "Cada CLEI marcado debe tener un tema seleccionado de la malla curricular.");
    }
  });
})();
