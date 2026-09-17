(() => {
  "use strict";
  const sidebar = document.getElementById("mainSidebar");
  const menuButton = document.querySelector(".mobile-menu");
  if (sidebar && menuButton) {
    const setMenu = (open) => {
      sidebar.classList.toggle("is-open", open);
      menuButton.setAttribute("aria-expanded", String(open));
    };
    menuButton.addEventListener("click", () => setMenu(!sidebar.classList.contains("is-open")));
    sidebar.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => setMenu(false)));
  }
  const clock = document.getElementById("liveClock");
  if (clock) {
    const updateClock = () => { clock.textContent = new Date().toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" }); };
    updateClock(); window.setInterval(updateClock, 30000);
  }
})();
