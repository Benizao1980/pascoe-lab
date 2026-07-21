
(() => {
  const esc = value => String(value ?? "").replace(/[&<>"']/g, ch => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[ch]));

  async function loadJson(path) {
    const response = await fetch(path, {cache: "no-store"});
    if (!response.ok) throw new Error(`${path}: ${response.status}`);
    return response.json();
  }

  function projectCard(project) {
    const pos = project.imagePosition ? ` style="object-position:${esc(project.imagePosition)}"` : "";
    return `<article class="project-card accent-${esc(project.accent || "rose")}">
      <img class="project-image" src="${esc(project.image)}" alt="${esc(project.imageAlt)}"${pos}>
      <div class="project-body">
        <span class="project-code">${esc(project.code)}</span>
        <h3>${esc(project.title)}</h3>
        <p>${esc(project.summary)}</p>
        <a href="${esc(project.url)}">Project overview →</a>
      </div>
    </article>`;
  }

  function publicationCard(pub) {
    const links = [`<a class="pill" href="https://doi.org/${esc(pub.doi)}">Paper</a>`];
    if (pub.story) links.push(`<a class="pill" href="${esc(pub.story)}">Behind the paper</a>`);
    return `<article class="card publication-card">
      <div>
        <p class="meta">${esc(pub.theme)}</p>
        <h3>${esc(pub.title)}</h3>
        <p class="journal">${esc(pub.journal)} · ${esc(pub.year)}</p>
        <p>${esc(pub.summary)}</p>
        <div class="pub-links">${links.join("")}</div>
      </div>
      ${pub.doi ? `<div class="altmetric-embed" data-badge-type="donut" data-doi="${esc(pub.doi)}"></div>` : ""}
    </article>`;
  }

  function storyCard(story) {
    return `<article class="card story-card">
      <img class="story-cover" src="${esc(story.image)}" alt="${esc(story.imageAlt)}">
      <div class="story-body">
        <span class="story-format">${esc(story.format)}</span>
        <h3>${esc(story.title)}</h3>
        <p>${esc(story.summary)}</p>
        <a href="${esc(story.url)}">Read →</a>
      </div>
    </article>`;
  }

  async function renderProjects() {
    const nodes = document.querySelectorAll('[data-content="projects"]');
    if (!nodes.length) return;
    const projects = (await loadJson("data/projects.json")).sort((a,b) => (a.order || 99) - (b.order || 99));
    nodes.forEach(node => {
      const homeOnly = node.dataset.featured === "home";
      const limit = Number(node.dataset.limit || 999);
      const selected = projects.filter(p => !homeOnly || p.featuredHome).slice(0, limit);
      node.innerHTML = selected.map(projectCard).join("");
    });
  }

  async function renderSelectedPublications() {
    const nodes = document.querySelectorAll('[data-content="publications"]');
    if (!nodes.length) return;
    const publications = await loadJson("data/publications.json");
    nodes.forEach(node => {
      const homeOnly = node.dataset.featured === "home";
      const limit = Number(node.dataset.limit || 999);
      const selected = publications
        .filter(p => homeOnly ? p.featuredHome : p.selected)
        .sort((a,b) => (b.year - a.year) || a.title.localeCompare(b.title))
        .slice(0, limit);
      node.innerHTML = selected.map(publicationCard).join("");
    });
    if (typeof window._altmetric_embed_init === "function") window._altmetric_embed_init();
  }

  async function renderStories() {
    const nodes = document.querySelectorAll('[data-content="stories"]');
    if (!nodes.length) return;
    const stories = await loadJson("data/stories.json");
    nodes.forEach(node => {
      const homeOnly = node.dataset.featured === "home";
      const limit = Number(node.dataset.limit || 999);
      const selected = stories
        .filter(s => !homeOnly || s.featuredHome)
        .sort((a,b) => String(b.date).localeCompare(String(a.date)))
        .slice(0, limit);
      node.innerHTML = selected.map(storyCard).join("");
    });
  }

  function yearOf(item) {
    const parts = item.published?.["date-parts"] || item.issued?.["date-parts"];
    return parts?.[0]?.[0] || item.year || "Undated";
  }

  function authorsOf(item) {
    if (item.authors) return item.authors;
    return (item.author || []).map(a => [a.given, a.family].filter(Boolean).join(" ")).join(", ");
  }

  async function renderAllPublications() {
    const list = document.getElementById("publication-list");
    if (!list) return;

    const status = document.getElementById("publication-status");
    const search = document.getElementById("pub-search");
    const yearSelect = document.getElementById("pub-year");
    const count = document.getElementById("pub-count");

    let local = await loadJson("data/publications.json");
    let records = local.map(p => ({
      DOI:p.doi, title:[p.title], authors:p.authors, "container-title":[p.journal],
      year:p.year, status:p.status, summary:p.summary, theme:p.theme, local:true
    }));

    try {
      const endpoint = "https://api.crossref.org/works?filter=orcid:0000-0001-6376-5121&rows=1000&sort=published&order=desc&select=DOI,title,author,container-title,published,issued,type,is-referenced-by-count,URL";
      const response = await fetch(endpoint);
      if (!response.ok) throw new Error(`Crossref returned ${response.status}`);
      const crossref = (await response.json()).message.items || [];
      const localDois = new Set(records.map(r => String(r.DOI || "").toLowerCase()));
      records = records.concat(crossref.filter(r => !localDois.has(String(r.DOI || "").toLowerCase())));
      status.hidden = true;
    } catch (error) {
      status.innerHTML = `<strong>Showing the locally maintained publication record.</strong><br>${esc(error.message)}. Google Scholar and ORCID remain linked above.`;
    }

    records.sort((a,b) => {
      const yearDiff = Number(yearOf(b)) - Number(yearOf(a));
      return yearDiff || String(a.title?.[0] || "").localeCompare(String(b.title?.[0] || ""));
    });

    const years = [...new Set(records.map(yearOf).filter(y => y !== "Undated"))].sort((a,b) => b-a);
    yearSelect.innerHTML = '<option value="">All years</option>' + years.map(y => `<option value="${y}">${y}</option>`).join("");

    function render() {
      const q = search.value.trim().toLowerCase();
      const y = yearSelect.value;
      const filtered = records.filter(item => {
        const text = [item.title?.[0], authorsOf(item), item["container-title"]?.[0], yearOf(item), item.DOI, item.theme].join(" ").toLowerCase();
        return (!q || text.includes(q)) && (!y || String(yearOf(item)) === y);
      });
      count.textContent = `${filtered.length} record${filtered.length === 1 ? "" : "s"}`;
      list.innerHTML = "";
      let currentYear = null;
      filtered.forEach(item => {
        const year = yearOf(item);
        if (year !== currentYear) {
          list.insertAdjacentHTML("beforeend", `<h2 class="year-heading">${esc(year)}</h2>`);
          currentYear = year;
        }
        const title = item.title?.[0] || "Untitled publication";
        const journal = item["container-title"]?.[0] || item.type || "";
        const statusText = item.status ? ` · ${esc(item.status)}` : "";
        const citationText = Number.isFinite(item["is-referenced-by-count"]) ? ` · ${item["is-referenced-by-count"]} Crossref citations` : "";
        list.insertAdjacentHTML("beforeend", `<article class="pub-entry">
          <p class="meta">${esc(year)} · ${esc(journal)}${statusText}</p>
          <h3><a href="https://doi.org/${esc(item.DOI)}">${esc(title)}</a></h3>
          <p class="pub-meta">${esc(authorsOf(item))}</p>
          <p class="small">DOI: ${esc(item.DOI)}${citationText}</p>
        </article>`);
      });
    }

    list.hidden = false;
    render();
    search.addEventListener("input", render);
    yearSelect.addEventListener("change", render);
  }

  Promise.allSettled([
    renderProjects(),
    renderSelectedPublications(),
    renderStories(),
    renderAllPublications()
  ]).then(results => {
    results.filter(r => r.status === "rejected").forEach(r => console.error(r.reason));
  });
})();
