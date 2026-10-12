(() => {
  "use strict";
  const modal = document.getElementById("studentDetailModal");
  if (!modal) return;
  const title = document.getElementById("studentModalTitle");
  const summary = document.getElementById("studentDetailSummary");
  const subjectsList = document.getElementById("studentSubjectsList");
  const recordsList = document.getElementById("studentRecordsList");
  let lastTrigger = null;
  const value = (item) => item === null || item === undefined || item === "" ? "—" : String(item);
  const node = (tag, text, className) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    element.textContent = value(text);
    return element;
  };
  const close = () => {
    modal.hidden = true;
    document.body.classList.remove("modal-open");
    if (lastTrigger) lastTrigger.focus();
  };
  const open = (student, trigger) => {
    lastTrigger = trigger;
    title.textContent = value(student.name || "Estudiante sin nombre");
    summary.replaceChildren();
    [["Identificación", student.identification], ["Contexto", student.context], ["Grupo", student.group], ["Nivel", student.clei === "Multigrado" ? "Multigrado" : `CLEI ${value(student.clei)}`], ["Asistencia general", `${value(student.overall_rate)}%`], ["Fechas registradas", student.date_count], ["Promedio general", student.overall_average == null ? "—" : Number(student.overall_average).toFixed(2)]].forEach(([label, text]) => {
      const box = document.createElement("div");
      box.appendChild(node("span", label));
      box.appendChild(node("strong", text));
      summary.appendChild(box);
    });
    subjectsList.replaceChildren();
    (student.subjects || []).forEach((subject) => {
      const card = document.createElement("article");
      card.className = "student-subject-card";
      card.appendChild(node("strong", subject.subject));
      const details = document.createElement("div");
      details.className = "student-subject-details";
      details.appendChild(node("span", `${subject.rate}% asistencia · ${subject.sessions} sesiones`));
      details.appendChild(node("span", `${subject.present} asistencias · ${subject.absent} inasistencias`));
      details.appendChild(node("span", subject.average == null ? "Promedio: —" : `Promedio: ${Number(subject.average).toFixed(2)}`));
      details.appendChild(node("small", `Fuente: ${value(subject.source)}`));
      card.appendChild(details);
      subjectsList.appendChild(card);
    });
    if (!(student.subjects || []).length) subjectsList.appendChild(node("p", "No hay materias con evidencia registrada.", "empty-state"));
    recordsList.replaceChildren();
    (student.records || []).slice(0, 30).forEach((record) => {
      const article = document.createElement("article");
      article.className = "student-record";
      article.appendChild(node("strong", `${value(record.date)} · ${value(record.subject)}`));
      article.appendChild(node("p", `${value(record.attendance)} · Nota: ${value(record.grade)}`));
      if (record.observation) article.appendChild(node("p", `Observación: ${record.observation}`, "record-observation"));
      recordsList.appendChild(article);
    });
    if (!(student.records || []).length) recordsList.appendChild(node("p", "No hay registros académicos disponibles.", "empty-state"));
    modal.hidden = false;
    document.body.classList.add("modal-open");
    modal.querySelector(".modal-close").focus();
  };
  document.querySelectorAll(".detail-button").forEach((button) => button.addEventListener("click", () => {
    try { open(JSON.parse(button.dataset.student), button); } catch (error) { console.error("No se pudo abrir la ficha", error); }
  }));
  modal.addEventListener("click", (event) => { if (event.target.hasAttribute("data-close-student-modal")) close(); });
  document.addEventListener("keydown", (event) => { if (!modal.hidden && event.key === "Escape") close(); });
})();
