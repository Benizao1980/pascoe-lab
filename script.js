const menuButton = document.querySelector('.menu-button');
const siteNav = document.querySelector('.site-nav');
const navLinks = siteNav ? [...siteNav.querySelectorAll('a')] : [];

// Keep the active navigation state tied to the current page rather than relying
// on duplicated page markup. This also adds an accessible current-page marker.
if (navLinks.length) {
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';
  navLinks.forEach(link => {
    const target = new URL(link.href, window.location.href).pathname.split('/').pop() || 'index.html';
    const active = target === currentPage;
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });
}

if (menuButton && siteNav) {
  const closeMenu = ({ returnFocus = false } = {}) => {
    siteNav.classList.remove('open');
    menuButton.setAttribute('aria-expanded', 'false');
    if (returnFocus) menuButton.focus();
  };

  menuButton.addEventListener('click', () => {
    const open = siteNav.classList.toggle('open');
    menuButton.setAttribute('aria-expanded', open ? 'true' : 'false');
  });

  siteNav.addEventListener('click', event => {
    if (event.target.closest('a')) closeMenu();
  });

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && siteNav.classList.contains('open')) {
      closeMenu({ returnFocus: true });
    }
  });

  document.addEventListener('click', event => {
    if (!siteNav.classList.contains('open')) return;
    if (siteNav.contains(event.target) || menuButton.contains(event.target)) return;
    closeMenu();
  });
}

document.querySelectorAll('a[href^="http"]').forEach(a => {
  if (!a.hasAttribute('target')) {
    a.setAttribute('target', '_blank');
    a.setAttribute('rel', 'noopener');
  }
});

const countEls = document.querySelectorAll('[data-count]');
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const el = entry.target;
      const target = Number(el.dataset.count);
      const duration = 850;
      const start = performance.now();
      function tick(now) {
        const progress = Math.min((now - start) / duration, 1);
        el.textContent = Math.floor(progress * target).toLocaleString();
        if (progress < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
      observer.unobserve(el);
    });
  }, { threshold: .5 });
  countEls.forEach(el => observer.observe(el));
} else {
  countEls.forEach(el => {
    el.textContent = Number(el.dataset.count).toLocaleString();
  });
}
