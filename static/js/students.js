(() => {
  "use strict";

  const modal = document.getElementById("studentModal");
  const content = document.getElementById("studentModalContent");
  if (!modal || !content) return;

  const escapeHtml = (value) => String(value ?? "—")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

  const metric = (label, value, tone = "") => `<div class="student-detail-metric ${tone}"><strong>${escapeHtml(value)}</strong><span>${escapeHtml(label)}</span></div>`;

  const sessionRow = (item) => `<tr><td>${escapeHtml(item.date)}</td><td>${escapeHtml(item.math_attendance)}</td><td>${escapeHtml(item.math_grade)}</td><td>${escapeHtml(item.science_attendance)}</td><td>${escapeHtml(item.science_grade)}</td><td>${escapeHtml(item.observation)}</td></tr>`;

  function renderStudent(student) {
    const observations = student.observations?.length
      ? `<div class="student-detail-block"><h3>Observaciones registradas</h3><ul class="student-observations">${student.observations.map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div>`
      : `<div class="student-detail-block"><h3>Observaciones registradas</h3><p class="student-muted">No hay observaciones registradas en la planilla.</p></div>`;
    const sessions = student.sessions_detail?.length
      ? `<div class="student-detail-block"><h3>Historial por fecha</h3><div class="student-history"><table><thead><tr><th>Fecha</th><th>Matemáticas</th><th>Nota</th><th>Ciencias</th><th>Nota</th><th>Observación</th></tr></thead><tbody>${student.sessions_detail.map(sessionRow).join("")}</tbody></table></div></div>`
      : `<div class="student-detail-block"><h3>Historial por fecha</h3><p class="student-muted">No hay fechas válidas para mostrar.</p></div>`;

    content.innerHTML = `<div class="student-detail-header"><p class="chart-kicker">FICHA INDIVIDUAL</p><h2 id="studentModalTitle">${escapeHtml(student.name)}</h2><p>${escapeHtml(student.context)} · ${escapeHtml(student.group)} · ${escapeHtml(student.clei)}</p></div><div class="student-detail-grid"><div><span>Documento / cédula</span><strong>${escapeHtml(student.identification)}</strong></div><div><span>Número de patio</span><strong>${escapeHtml(student.patio)}</strong></div><div><span>Grupo</span><strong>${escapeHtml(student.group)}</strong></div><div><span>Contexto educativo</span><strong>${escapeHtml(student.context)}</strong></div></div><div class="student-detail-metrics">${metric("Asistencia global", `${student.attendance_rate}%`, "good")}${metric("Sesiones", student.sessions)}${metric("Asistencias", student.total_present, "good")}${metric("Inasistencias", student.total_absent, "risk")}${metric("Matemáticas", `${student.math_present} / ${student.math_absent}`)}${metric("Ciencias", `${student.science_present} / ${student.science_absent}`)}${metric("Promedio Matemáticas", student.math_average ?? "—")}${metric("Promedio Ciencias", student.science_average ?? "—")}</div>${observations}${sessions}`;
  }

  function closeModal() {
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("modal-open");
  }

  document.querySelectorAll(".student-detail-trigger").forEach((button) => {
    button.addEventListener("click", async () => {
      modal.classList.add("is-open");
      modal.setAttribute("aria-hidden", "false");
      document.body.classList.add("modal-open");
      content.innerHTML = '<div class="student-modal-loading">Cargando información real desde Google Drive…</div>';
      const params = new URLSearchParams({ nombre: button.dataset.name || "", identificacion: button.dataset.identification || "", grupo: button.dataset.group || "" });
      try {
        const response = await fetch(`${button.dataset.detailUrl}?${params.toString()}`, { credentials: "same-origin", headers: { Accept: "application/json" } });
        const contentType = response.headers.get("content-type") || "";
        if (!contentType.includes("application/json")) {
          throw new Error(response.redirected ? "La sesión expiró. Vuelve a iniciar sesión." : `El servidor respondió con ${response.status}.`);
        }
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || "No se pudo cargar el detalle.");
        renderStudent(payload.student);
      } catch (error) {
        content.innerHTML = `<div class="student-modal-error">${escapeHtml(error.message)}</div>`;
      }
    });
  });

  document.querySelectorAll("[data-close-student-modal]").forEach((element) => element.addEventListener("click", closeModal));
  document.addEventListener("keydown", (event) => { if (event.key === "Escape" && modal.classList.contains("is-open")) closeModal(); });
})();

