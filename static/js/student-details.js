(() => {
  "use strict";
  const modal = document.getElementById("studentDetailModal");
  if (!modal) return;
  const title = document.getElementById("studentModalTitle");
  const summary = document.getElementById("studentDetailSummary");
  const recordsList = document.getElementById("studentRecordsList");
  let lastTrigger = null;
  const text = (value) => value || "—";
  const close = () => {
    modal.hidden = true;
    document.body.classList.remove("modal-open");
    if (lastTrigger) lastTrigger.focus();
  };
  const open = (student, trigger) => {
    lastTrigger = trigger;
    title.textContent = student.name || "Estudiante sin nombre";
    summary.innerHTML = `<div><span>Identificación</span><strong>${text(student.identification)}</strong></div><div><span>Contexto</span><strong>${text(student.context)}</strong></div><div><span>Grupo</span><strong>${text(student.group)}</strong></div><div><span>Nivel</span><strong>${student.clei === "Multigrado" ? "Multigrado" : `CLEI ${text(student.clei)}`}</strong></div><div><span>Fechas registradas</span><strong>${student.date_count}</strong></div><div><span>Promedio Matemáticas</span><strong>${student.math_average == null ? "—" : Number(student.math_average).toFixed(2)}</strong></div><div><span>Promedio Ciencias Naturales</span><strong>${student.science_average == null ? "—" : Number(student.science_average).toFixed(2)}</strong></div>`;
    recordsList.innerHTML = (student.records || []).map((record) => `<article class="student-record"><strong>${text(record.date)}</strong><p><b>Matemáticas:</b> ${text(record.math_attendance)} · Nota: ${text(record.math_grade)}</p><p><b>Ciencias Naturales:</b> ${text(record.science_attendance)} · Nota: ${text(record.science_grade)}</p>${record.observation ? `<p class="record-observation"><b>Observación:</b> ${record.observation}</p>` : ""}</article>`).join("") || '<p class="empty-state">No hay registros académicos disponibles.</p>';
    modal.hidden = false;
    document.body.classList.add("modal-open");
    modal.querySelector(".modal-close").focus();
  };
  document.querySelectorAll(".detail-button").forEach((button) => button.addEventListener("click", () => open(JSON.parse(button.dataset.student), button)));
  modal.addEventListener("click", (event) => { if (event.target.hasAttribute("data-close-student-modal")) close(); });
  document.addEventListener("keydown", (event) => { if (!modal.hidden && event.key === "Escape") close(); });
})();
