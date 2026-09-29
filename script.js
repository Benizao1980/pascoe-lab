// Load the current visual/accessibility polish across every page, including
// legacy project and story URLs that still use the shared script.
const polishStylesheet = document.createElement('link');
polishStylesheet.rel = 'stylesheet';
polishStylesheet.href = '/polish.css?v=6.18';
document.head.appendChild(polishStylesheet);

const menuButton = document.querySelector('.menu-button');
const siteNav = document.querySelector('.site-nav');
const navLinks = siteNav ? [...siteNav.querySelectorAll('a')] : [];

// Keep the active navigation state tied to the current section rather than
// relying on duplicated page markup. Subpages inherit their parent section.
if (navLinks.length) {
  const pathname = window.location.pathname;
  const currentPage = pathname.split('/').pop() || 'index.html';
  let navPage = currentPage;

  if (/^project-/.test(currentPage)) navPage = 'projects.html';
  else if (currentPage === 'publication-overview.html' || currentPage === 'all-publications.html') navPage = 'publications.html';
  else if (pathname.includes('/stories/') && currentPage !== 'stories.html') navPage = 'stories.html';
  else if (currentPage === 'logo.html' || currentPage === 'lab-guides.html') navPage = 'resources.html';

  navLinks.forEach(link => {
    const target = new URL(link.href, window.location.href).pathname.split('/').pop() || 'index.html';
    const active = target === navPage;
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });
}

if (menuButton && siteNav) {
  menuButton.setAttribute('aria-label', 'Open navigation');

  const closeMenu = ({ returnFocus = false } = {}) => {
    siteNav.classList.remove('open');
    menuButton.setAttribute('aria-expanded', 'false');
    menuButton.setAttribute('aria-label', 'Open navigation');
    if (returnFocus) menuButton.focus();
  };

  menuButton.addEventListener('click', () => {
    const open = siteNav.classList.toggle('open');
    menuButton.setAttribute('aria-expanded', open ? 'true' : 'false');
    menuButton.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
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

// Theme filters act like a single-choice control. content.js owns the filtering;
// this shared layer keeps the state exposed to assistive technology.
const themeFilterButtons = [...document.querySelectorAll('.theme-filter')];
if (themeFilterButtons.length) {
  const syncThemeFilterState = () => {
    themeFilterButtons.forEach(button => {
      button.setAttribute('aria-pressed', button.classList.contains('active') ? 'true' : 'false');
    });
  };
  syncThemeFilterState();
  themeFilterButtons.forEach(button => {
    button.addEventListener('click', () => requestAnimationFrame(syncThemeFilterState));
  });
}

// Keep the footer identical across old and new pages. The static HTML remains
// a useful no-JavaScript fallback; this removes drift between duplicated shells.
const siteFooter = document.querySelector('.site-footer');
if (siteFooter) {
  siteFooter.innerHTML = `
    <div class="wrap footer-grid">
      <div>
        <div class="footer-brand">Pascoe Lab</div>
        <p>Pathogen genomics, evolution and One Health research at the University of Oxford and across an international collaborative network.</p>
      </div>
      <div>
        <h2>Profiles</h2>
        <p><a href="https://orcid.org/0000-0001-6376-5121">ORCID</a><br>
        <a href="https://scholar.google.co.uk/citations?hl=en&user=UQrZ-fgAAAAJ">Google Scholar</a><br>
        <a href="https://github.com/Benizao1980">GitHub</a></p>
      </div>
      <div>
        <h2>Connect</h2>
        <p><a href="https://bsky.app/profile/benizao.bsky.social">Bluesky</a><br>
        <a href="https://www.linkedin.com/in/benpascoe">LinkedIn</a><br>
        <a href="https://campylobacter-control-campaign.github.io/website/">CCC website</a></p>
      </div>
    </div>
    <div class="wrap footer-bottom">
      <span>© 2026 Pascoe Lab</span>
      <span>Open, version-controlled research communication.</span>
    </div>`;
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
