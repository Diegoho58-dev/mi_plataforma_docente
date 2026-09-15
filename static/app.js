/* Comportamiento compartido de AulaCol/Panel docente: no contiene lógica de datos. */
(function () {
  'use strict';
  const ready = (fn) => document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', fn) : fn();
  ready(function () {
    const clock = document.getElementById('liveClock');
    const updateClock = () => { if (clock) clock.textContent = new Date().toLocaleTimeString('es-CO', {hour:'2-digit', minute:'2-digit'}); };
    updateClock();
    if (clock) setInterval(updateClock, 30000);

    const greeting = document.getElementById('greeting');
    if (greeting) {
      const hour = new Date().getHours();
      greeting.textContent = (hour < 12 ? 'Buenos días' : hour < 18 ? 'Buenas tardes' : 'Buenas noches') + ', Diego';
    }

    const currentPath = window.location.pathname;
    document.querySelectorAll('.menu-item').forEach((item) => {
      const href = item.getAttribute('href') || '';
      if (href.startsWith('/') && href !== '/' && currentPath.startsWith(href)) item.classList.add('active');
    });

    document.querySelectorAll('.mobile-menu').forEach((button) => {
      button.addEventListener('click', () => document.querySelector('.sidebar')?.classList.toggle('mobile-open'));
    });
    document.querySelectorAll('.sidebar .menu-item').forEach((item) => item.addEventListener('click', () => document.querySelector('.sidebar')?.classList.remove('mobile-open')));

    document.querySelectorAll('.panel, .stat-card, .quick-card, .context-card, .insight-card, .class-card').forEach((element, index) => {
      element.classList.add('shared-reveal');
      element.style.setProperty('--reveal-delay', `${Math.min(index * 35, 280)}ms`);
    });

    document.querySelectorAll('[data-toggle]').forEach((button) => {
      button.addEventListener('click', () => {
        const target = document.querySelector(button.dataset.toggle);
        if (!target) return;
        const open = target.classList.toggle('is-open');
        button.setAttribute('aria-expanded', String(open));
      });
    });
  });
})();

