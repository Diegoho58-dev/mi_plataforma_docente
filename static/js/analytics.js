(() => {
  "use strict";

  const colors = {
    teal: "#078f91",
    green: "#52aa82",
    navy: "#0c526b",
    red: "#c85b58",
    grid: "rgba(24, 48, 71, .10)"
  };

  function showEmpty(id, empty) {
    const canvas = document.getElementById(id);
    const message = document.querySelector(`[data-empty-for="${id}"]`);
    if (canvas) canvas.style.display = empty ? "none" : "block";
    if (message) message.hidden = !empty;
  }

  function total(values) {
    return values.reduce((sum, value) => sum + Number(value || 0), 0);
  }

  function chart(id, config, hasData) {
    const canvas = document.getElementById(id);
    if (!canvas) return;
    if (!hasData || typeof window.Chart !== "function") {
      showEmpty(id, true);
      return;
    }
    showEmpty(id, false);
    new window.Chart(canvas, config);
  }

  function render(data) {
    const followup = data.followup || {};
    const clei = Array.isArray(followup.clei) ? followup.clei : [];
    const subjects = Array.isArray(followup.subjects) ? followup.subjects : [];
    const padrino = Array.isArray(followup.padrino) ? followup.padrino : [];

    chart("followupCleiChart", {
      type: "bar",
      data: {
        labels: clei.map(item => item.label),
        datasets: [
          { label: "Matemáticas %", data: clei.map(item => item.math || 0), backgroundColor: colors.teal, borderRadius: 5 },
          { label: "Ciencias Naturales %", data: clei.map(item => item.science || 0), backgroundColor: colors.green, borderRadius: 5 }
        ]
      },
      options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, max: 100, ticks: { callback: value => `${value}%` }, grid: { color: colors.grid } } }, plugins: { legend: { position: "bottom" } } }
    }, clei.length > 0 && total(clei.map(item => item.math || 0)) + total(clei.map(item => item.science || 0)) > 0);

    chart("followupSubjectsChart", {
      type: "bar",
      data: {
        labels: subjects.map(item => item.label),
        datasets: [
          { label: "Sesiones", data: subjects.map(item => item.sessions || 0), backgroundColor: colors.navy, borderRadius: 5 },
          { label: "Inasistencias", data: subjects.map(item => item.absent || 0), backgroundColor: colors.red, borderRadius: 5 }
        ]
      },
      options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: colors.grid } } }, plugins: { legend: { position: "bottom" } } }
    }, subjects.length > 0 && total(subjects.map(item => item.sessions || 0)) > 0);

    chart("followupPadrinoChart", {
      type: "bar",
      data: {
        labels: padrino.map(item => item.label),
        datasets: [
          { label: "Asistencias", data: padrino.map(item => item.present || 0), backgroundColor: colors.green, borderRadius: 5 },
          { label: "Inasistencias", data: padrino.map(item => item.absent || 0), backgroundColor: colors.red, borderRadius: 5 }
        ]
      },
      options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: colors.grid } } }, plugins: { legend: { position: "bottom" } } }
    }, padrino.length > 0 && total(padrino.map(item => item.present || 0)) + total(padrino.map(item => item.absent || 0)) > 0);
  }

  let data = {};
  try {
    const element = document.getElementById("analytics-data");
    data = element ? JSON.parse(element.textContent) : {};
  } catch (error) {
    console.error("No se pudieron interpretar los datos del informe integral", error);
  }
  document.addEventListener("DOMContentLoaded", () => render(data));
})();
