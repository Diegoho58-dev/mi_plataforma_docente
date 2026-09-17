(() => {
  "use strict";

  const colors = {
    teal: "#078f91",
    green: "#52aa82",
    gold: "#d49e2b",
    navy: "#0c526b",
    red: "#c85b58",
    purple: "#80539c",
    grid: "rgba(24, 48, 71, .10)"
  };

  function showEmpty(canvasId, show, text) {
    const message = document.querySelector(
      `[data-empty-for="${canvasId}"]`
    );

    const canvas = document.getElementById(canvasId);

    if (message) {
      message.hidden = !show;

      if (text) {
        message.textContent = text;
      }
    }

    if (canvas) {
      canvas.style.display = show ? "none" : "block";
    }
  }

  function sum(values) {
    return values.reduce(
      (total, value) => total + Number(value || 0),
      0
    );
  }

  function makeChart(canvasId, config, hasData) {
    const canvas = document.getElementById(canvasId);

    if (!canvas) {
      return;
    }

    if (!hasData) {
      showEmpty(canvasId, true);
      return;
    }

    if (typeof window.Chart !== "function") {
      showEmpty(
        canvasId,
        true,
        "No se pudo cargar el motor de gráficas. Revisa la conexión a internet."
      );

      return;
    }

    showEmpty(canvasId, false);

    new window.Chart(canvas, config);
  }

  function render(data) {
    const dates = Array.isArray(data.dates)
      ? data.dates
      : [];

    const math = Array.isArray(data.math)
      ? data.math
      : [];

    const science = Array.isArray(data.science)
      ? data.science
      : [];

    const contexts = Array.isArray(data.contexts)
      ? data.contexts
      : [];

    const risks = Array.isArray(data.risks)
      ? data.risks
      : [];

    const attendanceSummary =
      data.attendance_summary || {
        present: 0,
        absent: 0
      };

    const totalAttendance =
      sum(math.map(item => item.present)) +
      sum(science.map(item => item.present)) +
      sum(math.map(item => item.absent)) +
      sum(science.map(item => item.absent));

    const hasAttendance =
      dates.length > 0 &&
      totalAttendance > 0;

    makeChart(
      "attendanceChart",
      {
        type: "line",

        data: {
          labels: dates,

          datasets: [
            {
              label: "Matemáticas: asistencias",
              data: math.map(item => item.present || 0),
              borderColor: colors.teal,
              backgroundColor: "rgba(7,143,145,.12)",
              fill: true,
              tension: 0.3
            },

            {
              label: "Ciencias: asistencias",
              data: science.map(item => item.present || 0),
              borderColor: colors.green,
              backgroundColor: "rgba(82,170,130,.10)",
              fill: true,
              tension: 0.3
            },

            {
              label: "Inasistencias totales",
              data: dates.map((_, index) => {
                const mathAbsent =
                  math[index]?.absent || 0;

                const scienceAbsent =
                  science[index]?.absent || 0;

                return mathAbsent + scienceAbsent;
              }),
              borderColor: colors.red,
              borderDash: [5, 5],
              tension: 0.3
            }
          ]
        },

        options: {
          responsive: true,
          maintainAspectRatio: false,

          interaction: {
            mode: "index",
            intersect: false
          },

          plugins: {
            legend: {
              position: "bottom"
            }
          },

          scales: {
            x: {
              grid: {
                display: false
              }
            },

            y: {
              beginAtZero: true,

              ticks: {
                precision: 0
              },

              grid: {
                color: colors.grid
              }
            }
          }
        }
      },
      hasAttendance
    );

    makeChart(
      "subjectChart",
      {
        type: "bar",

        data: {
          labels: [
            "Matemáticas",
            "Ciencias Naturales"
          ],

          datasets: [
            {
              label: "Asistencias",

              data: [
                sum(math.map(item => item.present)),
                sum(science.map(item => item.present))
              ],

              backgroundColor: colors.green,
              borderRadius: 6
            },

            {
              label: "Inasistencias",

              data: [
                sum(math.map(item => item.absent)),
                sum(science.map(item => item.absent))
              ],

              backgroundColor: colors.red,
              borderRadius: 6
            }
          ]
        },

        options: {
          responsive: true,
          maintainAspectRatio: false,

          plugins: {
            legend: {
              position: "bottom"
            }
          },

          scales: {
            y: {
              beginAtZero: true,

              ticks: {
                precision: 0
              },

              grid: {
                color: colors.grid
              }
            }
          }
        }
      },
      totalAttendance > 0
    );

    const balanceTotal =
      Number(attendanceSummary.present || 0) +
      Number(attendanceSummary.absent || 0);

    makeChart(
      "attendanceBalanceChart",
      {
        type: "doughnut",

        data: {
          labels: [
            "Asistencias",
            "Inasistencias"
          ],

          datasets: [
            {
              data: [
                attendanceSummary.present || 0,
                attendanceSummary.absent || 0
              ],

              backgroundColor: [
                colors.green,
                colors.red
              ],

              borderWidth: 3,
              borderColor: "#fff"
            }
          ]
        },

        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: "62%",

          plugins: {
            legend: {
              position: "bottom"
            },

            tooltip: {
              callbacks: {
                label: item => {
                  const percentage = balanceTotal
                    ? (
                        (item.raw / balanceTotal) *
                        100
                      ).toFixed(1)
                    : 0;

                  return `${item.label}: ${item.raw} (${percentage}%)`;
                }
              }
            }
          }
        }
      },
      balanceTotal > 0
    );

    makeChart(
      "contextChart",
      {
        type: "doughnut",

        data: {
          labels: contexts.map(item => item.label),

          datasets: [
            {
              data: contexts.map(item => item.value),

              backgroundColor: [
                colors.navy,
                colors.gold,
                colors.teal,
                colors.purple
              ],

              borderWidth: 3,
              borderColor: "#fff"
            }
          ]
        },

        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: "58%",

          plugins: {
            legend: {
              position: "bottom"
            }
          }
        }
      },
      contexts.length > 0 &&
      sum(contexts.map(item => item.value)) > 0
    );

    makeChart(
      "riskChart",
      {
        type: "bar",

        data: {
          labels: risks.map(item => item.label),

          datasets: [
            {
              label: "Inasistencias",
              data: risks.map(item => item.value),
              backgroundColor: colors.red,
              borderRadius: 6
            }
          ]
        },

        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,

          plugins: {
            legend: {
              display: false
            }
          },

          scales: {
            x: {
              beginAtZero: true,

              ticks: {
                precision: 0
              },

              grid: {
                color: colors.grid
              }
            },

            y: {
              grid: {
                display: false
              }
            }
          }
        }
      },
      risks.length > 0 &&
      sum(risks.map(item => item.value)) > 0
    );
  }

  let data = {};

  try {
    const dataElement =
      document.getElementById("analytics-data");

    data = dataElement
      ? JSON.parse(dataElement.textContent)
      : {};
  } catch (error) {
    console.error(
      "No se pudieron interpretar los datos de seguimiento",
      error
    );
  }

  document.addEventListener(
    "DOMContentLoaded",
    () => render(data)
  );
})();
