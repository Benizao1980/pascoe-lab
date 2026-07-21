
(() => {
  const esc = value => String(value ?? "").replace(/[&<>"']/g, ch => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[ch]));

  async function loadJson(path) {
    const response = await fetch(path, {cache:"no-store"});
    if (!response.ok) throw new Error(`${path}: ${response.status}`);
    return response.json();
  }

  function projectCard(p) {
    const pos = p.imagePosition ? ` style="object-position:${esc(p.imagePosition)}"` : "";
    return `<article class="project-card accent-${esc(p.accent || "rose")}">
      <img class="project-image" src="${esc(p.image)}" alt="${esc(p.imageAlt)}"${pos}>
      <div class="project-body">
        <span class="project-code">${esc(p.code)}</span>
        <h3>${esc(p.title)}</h3>
        <p>${esc(p.summary)}</p>
        <a href="${esc(p.url)}">Project overview →</a>
      </div>
    </article>`;
  }

  function personCard(p) {
    return `<article class="person-card accent-${esc(p.accent || "rose")}">
      <div class="person-monogram">${esc(p.initials)}</div>
      <div>
        <p class="meta">${esc(p.role)}</p>
        <h3>${esc(p.name)}</h3>
        <p class="person-supervision">${esc(p.supervision)}</p>
        <p>${esc(p.summary)}</p>
        <a href="${esc(p.url)}">Profile →</a>
      </div>
    </article>`;
  }

  function publicationCard(p) {
    const links = [];
    if (p.doi) links.push(`<a class="pill" href="https://doi.org/${esc(p.doi)}">Paper</a>`);
    if (p.story) links.push(`<a class="pill" href="${esc(p.story)}">Behind the paper</a>`);
    return `<article class="card publication-card">
      <div>
        <p class="meta">${esc(p.theme || p.type || "Publication")}</p>
        <h3>${esc(p.title)}</h3>
        <p class="journal">${esc(p.journal || "")} · ${esc(p.year)}</p>
        ${p.summary ? `<p>${esc(p.summary)}</p>` : ""}
        <div class="pub-links">${links.join("")}</div>
      </div>
      ${p.doi ? `<div class="altmetric-embed" data-badge-type="donut" data-doi="${esc(p.doi)}"></div>` : ""}
    </article>`;
  }

  function storyCard(s) {
    return `<article class="card story-card">
      <img class="story-cover" src="${esc(s.image)}" alt="${esc(s.imageAlt)}">
      <div class="story-body">
        <span class="story-format">${esc(s.format)}</span>
        <h3>${esc(s.title)}</h3>
        <p>${esc(s.summary)}</p>
        <a href="${esc(s.url)}">Read →</a>
      </div>
    </article>`;
  }

  async function renderProjects() {
    const nodes = document.querySelectorAll('[data-content="projects"]');
    if (!nodes.length) return;
    const data = (await loadJson("data/projects.json")).sort((a,b)=>(a.order||99)-(b.order||99));
    nodes.forEach(node => node.innerHTML = data.slice(0,Number(node.dataset.limit||999)).map(projectCard).join(""));
  }

  async function renderPeople() {
    const nodes = document.querySelectorAll('[data-content="people"]');
    if (!nodes.length) return;
    const data = await loadJson("data/people.json");
    nodes.forEach(node => node.innerHTML = data.map(personCard).join(""));
  }

  async function renderPublications() {
    const nodes = document.querySelectorAll('[data-content="publications"]');
    if (!nodes.length) return;
    const data = await loadJson("data/publications.json");
    nodes.forEach(node => {
      const home = node.dataset.featured === "home";
      const selected = data.filter(p => home ? p.featuredHome : p.selected)
        .sort((a,b)=>(b.year-a.year)||String(a.title).localeCompare(String(b.title)))
        .slice(0,Number(node.dataset.limit||999));
      node.innerHTML = selected.map(publicationCard).join("");
    });
    if (typeof window._altmetric_embed_init === "function") window._altmetric_embed_init();
  }

  async function renderStories() {
    const nodes = document.querySelectorAll('[data-content="stories"]');
    if (!nodes.length) return;
    const data = await loadJson("data/stories.json");
    nodes.forEach(node => node.innerHTML = data
      .sort((a,b)=>String(b.date).localeCompare(String(a.date)))
      .slice(0,Number(node.dataset.limit||999)).map(storyCard).join(""));
  }

  async function renderAllPublications() {
    const list = document.getElementById("publication-list");
    if (!list) return;
    const data = await loadJson("data/publications.json");
    const search = document.getElementById("pub-search");
    const yearSelect = document.getElementById("pub-year");
    const count = document.getElementById("pub-count");
    const status = document.getElementById("publication-status");
    const years = [...new Set(data.map(p=>p.year).filter(Boolean))].sort((a,b)=>b-a);
    yearSelect.innerHTML = '<option value="">All years</option>' +
      years.map(y=>`<option value="${y}">${y}</option>`).join("");

    function render() {
      const q = search.value.trim().toLowerCase();
      const y = yearSelect.value;
      const filtered = data.filter(p => {
        const text = [p.citation,p.title,p.authors,p.year,p.doi,p.type].join(" ").toLowerCase();
        return (!q || text.includes(q)) && (!y || String(p.year)===y);
      });
      count.textContent = `${filtered.length} completed output${filtered.length===1?"":"s"}`;
      list.innerHTML = "";
      let current = null;
      filtered.forEach(p => {
        if (p.year !== current) {
          list.insertAdjacentHTML("beforeend", `<h2 class="year-heading">${esc(p.year)}</h2>`);
          current = p.year;
        }
        const link = p.doi ? `<p class="small"><a href="https://doi.org/${esc(p.doi)}">DOI: ${esc(p.doi)}</a></p>` : "";
        list.insertAdjacentHTML("beforeend", `<article class="pub-entry">
          <p class="meta">${esc(p.type || "Publication")}</p>
          <p class="citation-text">${esc(p.citation)}</p>${link}
        </article>`);
      });
      status.hidden = true;
      list.hidden = false;
    }
    render();
    search.addEventListener("input", render);
    yearSelect.addEventListener("change", render);
  }

  Promise.allSettled([
    renderProjects(),renderPeople(),renderPublications(),renderStories(),renderAllPublications()
  ]).then(results => results.filter(r=>r.status==="rejected").forEach(r=>console.error(r.reason)));
})();
