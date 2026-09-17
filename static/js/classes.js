(() => {
  "use strict";

  const source = [
    ...document.querySelectorAll(".class-source")
  ].map((element, id) => ({
    id,
    date: element.dataset.date,
    ...element.dataset
  }));

  const grid = document.getElementById("calendarGrid");
  const title = document.getElementById("calendarTitle");
  const status = document.getElementById("calendarStatus");

  if (!grid || !title) {
    return;
  }

  const monthNames = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre"
  ];

  /*
   * La fecha actual se obtiene del navegador.
   * El calendario siempre comienza en el mes actual.
   */
  const today = new Date();

  let current = new Date(
    today.getFullYear(),
    today.getMonth(),
    1
  );

  function iso(date) {
    const year = date.getFullYear();

    const month = String(
      date.getMonth() + 1
    ).padStart(2, "0");

    const day = String(
      date.getDate()
    ).padStart(2, "0");

    return `${year}-${month}-${day}`;
  }

  function isCurrentMonth() {
    return (
      current.getFullYear() === today.getFullYear() &&
      current.getMonth() === today.getMonth()
    );
  }

  function renderCalendar() {
    grid.innerHTML = "";

    title.textContent =
      `${monthNames[current.getMonth()]} ${current.getFullYear()}`;

    const firstDay = new Date(
      current.getFullYear(),
      current.getMonth(),
      1
    );

    const firstDayPosition =
      (firstDay.getDay() + 6) % 7;

    const lastDay = new Date(
      current.getFullYear(),
      current.getMonth() + 1,
      0
    );

    const totalDays =
      Math.ceil(
        (firstDayPosition + lastDay.getDate()) / 7
      ) * 7;

    let visibleEvents = 0;

    for (let index = 0; index < totalDays; index += 1) {
      const date = new Date(
        current.getFullYear(),
        current.getMonth(),
        index - firstDayPosition + 1
      );

      const dateIso = iso(date);

      const dayEvents = source.filter(
        event => event.date === dateIso
      );

      visibleEvents += dayEvents.length;

      const cell = document.createElement("div");

      cell.className =
        "calendar-day" +
        (
          date.getMonth() !== current.getMonth()
            ? " other-month"
            : ""
        ) +
        (
          dateIso === iso(today)
            ? " today"
            : ""
        );

      const dayNumber = document.createElement("div");

      dayNumber.className = "day-number";

      const number = document.createElement("span");

      number.textContent = date.getDate();

      dayNumber.appendChild(number);

      if (dayEvents.length > 0) {
        const counter = document.createElement("b");

        counter.className = "day-count";

        counter.textContent =
          `${dayEvents.length} clase${
            dayEvents.length > 1 ? "s" : ""
          }`;

        dayNumber.appendChild(counter);
      }

      cell.appendChild(dayNumber);

      dayEvents.forEach(event => {
        const button = document.createElement("button");

        button.type = "button";
        button.className = `event ${event.contextClass}`;

        const subject = document.createElement("span");

        subject.className = "event-subject";
        subject.textContent = event.subject;

        const group = document.createElement("span");

        group.className = "event-group";
        group.textContent = event.group;

        button.appendChild(subject);
        button.appendChild(group);

        button.addEventListener("click", () => {
          openDetail(event);
        });

        cell.appendChild(button);
      });

      grid.appendChild(cell);
    }

    updateCalendarStatus(visibleEvents);
  }

  function updateCalendarStatus(visibleEvents) {
    if (!status) {
      return;
    }

    if (visibleEvents > 0) {
      status.textContent =
        `${visibleEvents} clase${
          visibleEvents > 1 ? "s" : ""
        } en ${
          monthNames[current.getMonth()].toLowerCase()
        }.`;

      status.className =
        "calendar-status has-events";

      return;
    }

    if (isCurrentMonth()) {
      status.textContent =
        "No hay clases registradas para el mes actual. " +
        "Puedes navegar a otro mes o ajustar los filtros.";
    } else {
      status.textContent =
        "No hay clases registradas para este mes. " +
        "Usa las flechas o vuelve a Hoy.";
    }

    status.className =
      "calendar-status is-empty";
  }

  function openDetail(event) {
    const detailBackdrop =
      document.getElementById("detailsBackdrop");

    const detailKicker =
      document.getElementById("detailKicker");

    const detailTitle =
      document.getElementById("detailTitle");

    const detailTheme =
      document.getElementById("detailTheme");

    const detailContext =
      document.getElementById("detailContext");

    const detailGroup =
      document.getElementById("detailGroup");

    const detailCycle =
      document.getElementById("detailCycle");

    const detailStatus =
      document.getElementById("detailStatus");

    const detailObservations =
      document.getElementById("detailObservations");

    const detailSource =
      document.getElementById("detailSource");

    const detailLink =
      document.getElementById("detailLink");

    if (!detailBackdrop) {
      return;
    }

    detailKicker.textContent =
      new Date(
        `${event.date}T12:00:00`
      ).toLocaleDateString(
        "es-CO",
        {
          weekday: "long",
          day: "numeric",
          month: "long",
          year: "numeric"
        }
      );

    detailTitle.textContent =
      `${event.subject} · ${event.group}`;

    detailTheme.textContent =
      `Tema: ${
        event.theme || "Sin tema registrado"
      }`;

    detailContext.textContent =
      event.context || "Sin contexto";

    detailGroup.textContent =
      event.group || "Sin grupo";

    detailCycle.textContent =
      event.cycle || "Sin ciclo asignado";

    detailStatus.textContent =
      event.status || "Sin estado";

    detailObservations.textContent =
      event.observations ||
      "Sin observaciones registradas";

    detailSource.textContent =
      `Hoja ${event.source || "No especificada"}`;

    if (event.link) {
      detailLink.href = event.link;
      detailLink.style.display = "inline-block";
    } else {
      detailLink.removeAttribute("href");
      detailLink.style.display = "none";
    }

    detailBackdrop.classList.add("open");
  }

  function closeDetail() {
    const detailBackdrop =
      document.getElementById("detailsBackdrop");

    if (detailBackdrop) {
      detailBackdrop.classList.remove("open");
    }
  }

  const previousButton =
    document.getElementById("prevMonth");

  if (previousButton) {
    previousButton.addEventListener("click", () => {
      current.setMonth(
        current.getMonth() - 1
      );

      renderCalendar();
    });
  }

  const nextButton =
    document.getElementById("nextMonth");

  if (nextButton) {
    nextButton.addEventListener("click", () => {
      current.setMonth(
        current.getMonth() + 1
      );

      renderCalendar();
    });
  }

  const todayButton =
    document.getElementById("todayBtn");

  if (todayButton) {
    todayButton.addEventListener("click", () => {
      current = new Date(
        today.getFullYear(),
        today.getMonth(),
        1
      );

      renderCalendar();
    });
  }

  const closeButton =
    document.getElementById("closeDetails");

  if (closeButton) {
    closeButton.addEventListener(
      "click",
      closeDetail
    );
  }

  const backdrop =
    document.getElementById("detailsBackdrop");

  if (backdrop) {
    backdrop.addEventListener("click", event => {
      if (event.target === backdrop) {
        closeDetail();
      }
    });
  }

  document.addEventListener("keydown", event => {
    if (event.key === "Escape") {
      closeDetail();
    }
  });

  renderCalendar();
})();
