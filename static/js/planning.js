(() => {
  "use strict";

  const board = document.getElementById("excelBoard");
  const cards = document.getElementById("cardsView");

  const boardButton = document.getElementById("boardBtn");
  const cardsButton = document.getElementById("cardsBtn");

  const openAllButton = document.getElementById("openAll");
  const closeAllButton = document.getElementById("closeAll");

  const backdrop = document.getElementById("detailBackdrop");
  const closeDetailButton = document.getElementById("closeDetail");

  if (!board || !cards) {
    return;
  }

  function showView(mode) {
    const isBoard = mode === "board";

    board.classList.toggle("hidden", !isBoard);

    cards.classList.toggle("hidden", isBoard);
    cards.classList.toggle("grid-on", !isBoard);

    if (boardButton) {
      boardButton.classList.toggle("active", isBoard);
    }

    if (cardsButton) {
      cardsButton.classList.toggle("active", !isBoard);
    }

    localStorage.setItem("planeacionView", mode);
  }

  if (boardButton) {
    boardButton.addEventListener("click", () => {
      showView("board");
    });
  }

  if (cardsButton) {
    cardsButton.addEventListener("click", () => {
      showView("cards");
    });
  }

  /*
   * Estos botones se conservan por compatibilidad.
   * Actualmente las tarjetas usan un modal individual.
   */
  if (openAllButton) {
    openAllButton.addEventListener("click", () => {
      document
        .querySelectorAll(".detail-trigger")
        .forEach(card => {
          card.classList.add("card-highlight");
        });

      setTimeout(() => {
        document
          .querySelectorAll(".detail-trigger")
          .forEach(card => {
            card.classList.remove("card-highlight");
          });
      }, 900);
    });
  }

  if (closeAllButton) {
    closeAllButton.addEventListener("click", () => {
      document
        .querySelectorAll(".detail-trigger")
        .forEach(card => {
          card.classList.remove("card-highlight");
        });
    });
  }

  function openDetail(card) {
    if (!backdrop) {
      return;
    }

    const detailSubject =
      document.getElementById("detailSubject");

    const detailTitle =
      document.getElementById("detailTitle");

    const detailWeek =
      document.getElementById("detailWeek");

    const detailTheme =
      document.getElementById("detailTheme");

    const detailObjective =
      document.getElementById("detailObjective");

    const detailActivity =
      document.getElementById("detailActivity");

    const detailStatus =
      document.getElementById("detailStatus");

    const detailSource =
      document.getElementById("detailSource");

    const detailLink =
      document.getElementById("detailLink");

    detailSubject.textContent =
      card.dataset.subject || "Sin materia";

    detailTitle.textContent =
      card.dataset.group || "Sin grupo";

    detailWeek.textContent =
      `${card.dataset.week || "Semana sin definir"} · ${
        card.dataset.date || "Fecha por definir"
      }`;

    detailTheme.textContent =
      card.dataset.theme || "Sin tema registrado";

    detailObjective.textContent =
      card.dataset.objective || "No registrado";

    detailActivity.textContent =
      card.dataset.activity || "No registrada";

    detailStatus.textContent =
      card.dataset.status || "Sin estado";

    detailSource.textContent =
      card.dataset.source || "Planeación";

    if (card.dataset.link) {
      detailLink.href = card.dataset.link;
      detailLink.style.display = "inline-block";
    } else {
      detailLink.removeAttribute("href");
      detailLink.style.display = "none";
    }

    backdrop.classList.add("open");
    document.body.classList.add("modal-open");
  }

  function closeDetail() {
    if (!backdrop) {
      return;
    }

    backdrop.classList.remove("open");
    document.body.classList.remove("modal-open");
  }

  document
    .querySelectorAll(".detail-trigger")
    .forEach(card => {
      card.addEventListener("click", () => {
        openDetail(card);
      });
    });

  if (closeDetailButton) {
    closeDetailButton.addEventListener(
      "click",
      closeDetail
    );
  }

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

  const savedView =
    localStorage.getItem("planeacionView") || "board";

  showView(savedView);
})();

