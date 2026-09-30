const menuButton = document.querySelector('.menu-button');
const siteNav = document.querySelector('.site-nav');

// The first NCTC story assets were malformed WebP blobs. Keep a narrow
// compatibility shim for those files only. Do not rewrite unrelated story
// images that already render correctly.
const storyAssetReplacements = new Map([
  ['nctc11168-meme.webp', 'nctc11168-meme.svg'],
  ['nctc11168-fig2.webp', 'nctc11168-fig2.svg']
]);

document.querySelectorAll('img[src]').forEach(img => {
  const current = img.getAttribute('src');
  if (!current) return;
  const filename = current.split('/').pop();
  const replacement = storyAssetReplacements.get(filename);
  if (replacement) img.setAttribute('src', current.replace(filename, replacement));
});

// The article meme is intentionally rendered from a full-resolution public
// template with the paper-specific captions overlaid in HTML. This avoids
// upscaling the small compatibility SVG used by cards and cached markup.
if (window.location.pathname.endsWith('/stories/nctc11168.html')) {
  const memeImg = [...document.querySelectorAll('figure img')].find(img =>
    (img.getAttribute('src') || '').includes('nctc11168-meme')
  );

  if (memeImg) {
    const meme = document.createElement('div');
    meme.setAttribute('role', 'img');
    meme.setAttribute('aria-label', 'Meme asking whether two laboratories with NCTC 11168 are really working on the same strain');
    meme.style.cssText = [
      'position:relative',
      'width:100%',
      'max-width:760px',
      'aspect-ratio:1/1',
      'background-image:url(https://i.imgflip.com/4/5c7lwq.jpg)',
      'background-size:cover',
      'background-position:center',
      'border:2px solid var(--ink)',
      'overflow:hidden'
    ].join(';');

    const captionStyle = [
      'position:absolute',
      'color:#fff',
      'font-family:Impact, Haettenschweiler, Arial Narrow Bold, sans-serif',
      'font-weight:700',
      'line-height:1.05',
      'text-align:center',
      'text-transform:uppercase',
      'text-shadow:-2px -2px 0 #000,2px -2px 0 #000,-2px 2px 0 #000,2px 2px 0 #000,0 3px 0 #000',
      'letter-spacing:.01em'
    ].join(';');

    const addCaption = (text, extraStyle) => {
      const span = document.createElement('span');
      span.textContent = text;
      span.style.cssText = `${captionStyle};${extraStyle}`;
      meme.appendChild(span);
    };

    addCaption('I HAVE NCTC 11168', 'left:1.5%;bottom:51%;width:47%;font-size:clamp(22px,4.6vw,49px)');
    addCaption("I ALSO HAVE NCTC 11168. SO, WE'RE WORKING ON THE SAME STRAIN, RIGHT?", 'right:1.5%;top:2.5%;width:47%;font-size:clamp(16px,3.1vw,34px)');
    addCaption('RIGHT??', 'right:2%;bottom:2.5%;width:46%;font-size:clamp(28px,6vw,62px)');

    memeImg.replaceWith(meme);
  }
}

// Keep the primary navigation deliberately compact. Join is folded into People,
// while the network map remains available as a secondary link from Projects.
if (siteNav) {
  const secondaryNavTargets = new Set(['join.html', 'network.html']);
  [...siteNav.querySelectorAll('a')].forEach(link => {
    const target = new URL(link.href, window.location.href).pathname.split('/').pop() || 'index.html';
    if (secondaryNavTargets.has(target)) link.remove();
  });
}

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
