(() => {
const esc=v=>String(v??"").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[ch]));
async function loadJson(path){const r=await fetch(path,{cache:"no-store"});if(!r.ok)throw new Error(`${path}: ${r.status}`);return r.json();}
async function loadLiveJson(path){
  const raw=`https://raw.githubusercontent.com/Benizao1980/pascoe-lab/main/${path}?v=${Date.now()}`;
  try{return await loadJson(raw);}catch(e){console.warn(`Raw GitHub fallback for ${path}:`,e);return loadJson(path);}
}
async function loadPublications(){return loadLiveJson("data/publications.json");}
async function loadScholarMetrics(){return loadLiveJson("data/scholar-metrics.json");}
function publicationTime(p){const d=Date.parse(p.publishedDate||`${p.year||0}-01-01`);return Number.isFinite(d)?d:0;}
function external(url,label){return `<a href="${esc(url)}" target="_blank" rel="noopener">${label}</a>`;}
function publicationHref(p){
  if(p.doi)return `https://doi.org/${p.doi}`;
  if(p.url)return p.url;
  return `https://scholar.google.com/scholar?q=${encodeURIComponent('"'+p.title+'"')}`;
}
function publicationLabel(p){return p.status==="in press"?"In press":p.publicationType==="preprint"?"Preprint":"Paper";}
function projectCard(p){const pos=p.imagePosition?` style="object-position:${esc(p.imagePosition)}"`:"";return `<article class="project-card accent-${esc(p.accent||"rose")}"><img class="project-image" src="${esc(p.image)}" alt="${esc(p.imageAlt)}"${pos}><div class="project-body"><h3>${esc(p.title)}</h3><p>${esc(p.summary)}</p><a href="${esc(p.url)}">Project overview →</a></div></article>`;}
function storyCard(s,compact=false){return compact?`<article class="card compact-feature"><div><p class="meta">${esc(s.format)}</p><h3>${esc(s.title)}</h3><a class="pill" href="${esc(s.url)}">Read story</a></div></article>`:`<article class="card story-card"><img class="story-cover" src="${esc(s.image)}" alt="${esc(s.imageAlt)}"><div class="story-body"><span class="story-format">${esc(s.format)}</span><h3>${esc(s.title)}</h3><p>${esc(s.summary)}</p><a href="${esc(s.url)}">Read →</a></div></article>`;}
function publicationFeature(p,compact=false){const href=publicationHref(p),label=publicationLabel(p);return compact?`<article class="card compact-feature"><div><p class="meta">${esc(p.journal||(p.status==="in press"?"In press":p.publicationType==="preprint"?"Preprint":"Journal article"))} · ${esc(p.year)}</p><h3>${esc(p.title)}</h3><a class="pill" href="${esc(href)}" target="_blank" rel="noopener">${label}</a></div></article>`:`<article class="card publication-card"><div><p class="meta">${esc(p.theme||"Publication")}</p><h3>${esc(p.title)}</h3><p class="journal">${esc(p.journal||(p.status==="in press"?"In press":p.publicationType==="preprint"?"Preprint":"Journal article"))} · ${esc(p.year)}</p>${p.summary?`<p>${esc(p.summary)}</p>`:""}<div class="pub-links"><a class="pill" href="${esc(href)}" target="_blank" rel="noopener">${label}</a></div></div></article>`;}
async function renderProjects(){const nodes=document.querySelectorAll('[data-content="projects"]');if(!nodes.length)return;const data=(await loadJson("data/projects.json")).sort((a,b)=>(a.order||99)-(b.order||99));nodes.forEach(n=>n.innerHTML=data.slice(0,Number(n.dataset.limit||999)).map(projectCard).join(""));}
async function renderStories(){const nodes=document.querySelectorAll('[data-content="stories"]');if(!nodes.length)return;const data=(await loadJson("data/stories.json")).sort((a,b)=>String(b.date).localeCompare(String(a.date)));nodes.forEach(n=>{const compact=n.dataset.compact==="true";n.innerHTML=data.slice(0,Number(n.dataset.limit||999)).map(s=>storyCard(s,compact)).join("");});}
async function renderFeatured(){const nodes=document.querySelectorAll('[data-content="publications"]');if(!nodes.length)return;const data=await loadPublications();nodes.forEach(n=>{const s=data.filter(p=>n.dataset.featured==="home"?p.featuredHome:p.selected).sort((a,b)=>(publicationTime(b)-publicationTime(a))||String(a.title).localeCompare(String(b.title))).slice(0,Number(n.dataset.limit||999));n.innerHTML=s.map(p=>publicationFeature(p,n.dataset.compact==="true")).join("");});}
async function renderMetrics(){
  const nodes=document.querySelectorAll("[data-metric]");if(!nodes.length)return;
  const pubs=await loadPublications();
  let scholar;
  const rawScholar=`https://raw.githubusercontent.com/Benizao1980/pascoe-lab/main/data/scholar-metrics.json?v=${Date.now()}`;
  try{scholar=await loadJson(rawScholar);}
  catch(e1){
    try{scholar=await loadJson(`data/scholar-metrics.json?v=${Date.now()}`);}
    catch(e2){scholar=await loadJson("data/site.json");}
  }
  const values={journal:pubs.filter(p=>p.publicationType==="journal").length,preprint:pubs.filter(p=>p.publicationType==="preprint").length,"h-index":scholar.h_index??"—",citations:Number.isFinite(Number(scholar.citations))?Number(scholar.citations).toLocaleString("en-GB"):"—"};
  nodes.forEach(n=>{n.textContent=values[n.dataset.metric]??"—";});
}
function refreshAltmetric(context){if(typeof window._altmetric_embed_init==="function")window._altmetric_embed_init(context||document);}
async function renderBrowser(){
  const list=document.getElementById("publication-list");if(!list)return;
  const [pubs,themes]=await Promise.all([loadPublications(),loadJson("data/themes.json")]);
  const tmap=Object.fromEntries(themes.map(t=>[t.id,t]));
  const search=document.getElementById("pub-search"),type=document.getElementById("pub-type"),
    organism=document.getElementById("pub-organism"),project=document.getElementById("pub-project"),
    group=document.getElementById("pub-group"),count=document.getElementById("pub-count");
  let active="all";

  function uniqueValues(field){return [...new Set(pubs.flatMap(p=>Array.isArray(p[field])?p[field]:[]).filter(Boolean))].sort((a,b)=>a.localeCompare(b));}
  function fillSelect(node,values){values.forEach(value=>{const option=document.createElement("option");option.value=value;option.textContent=value;node.appendChild(option);});}
  fillSelect(organism,uniqueValues("organisms"));fillSelect(project,uniqueValues("projects"));

  function statusRank(p){return p.status==="in press"?0:p.publicationType==="preprint"?2:1;}
  function comparePublications(a,b){
    const yearDiff=Number(b.year||0)-Number(a.year||0);if(yearDiff)return yearDiff;
    const statusDiff=statusRank(a)-statusRank(b);if(statusDiff)return statusDiff;
    const dateDiff=publicationTime(b)-publicationTime(a);if(dateDiff)return dateDiff;
    return String(a.title).localeCompare(String(b.title));
  }
  function tagHref(kind,value){
    const params=new URLSearchParams();
    if(kind==="organism")params.set("organism",value);
    else if(kind==="project")params.set("project",value);
    else params.set("q",value);
    return `publications.html?${params.toString()}`;
  }
  function displayTags(p){
    const tags=[];
    const push=(kind,value)=>{if(value&&!tags.some(t=>t.value===value))tags.push({kind,value});};
    (p.organisms||[]).slice(0,1).forEach(v=>push("organism",v));
    (p.topics||[]).slice(0,1).forEach(v=>push("topic",v));
    (p.projects||[]).slice(0,1).forEach(v=>push("project",v));
    if(tags.length<3)(p.geographies||[]).slice(0,1).forEach(v=>push("geography",v));
    return tags.slice(0,3).map(t=>`<a class="publication-tag tag-${esc(t.kind)}" href="${esc(tagHref(t.kind,t.value))}" data-tag-kind="${esc(t.kind)}" data-tag-value="${esc(t.value)}">${esc(t.value)}</a>`).join("");
  }
  function conciseSummary(p){
    const source=String(p.summary||p.abstract||"").replace(/\s+/g," ").trim();
    if(!source)return "";
    if(p.summary)return source;
    const sentences=source.match(/[^.!?]+[.!?]+/g)||[];
    const text=(sentences.slice(0,2).join(" ")||source).trim();
    return text.length>360?text.slice(0,357).replace(/\s+\S*$/,"")+"…":text;
  }
  function item(p){
    const t=tmap[p.themeId]||themes[0],typeLabel=p.status==="in press"?"In press":p.publicationType==="preprint"?"Preprint":"Journal article",typeClass=p.status==="in press"?"in-press":p.publicationType,href=publicationHref(p);
    const badge=p.doi?`<div class="publication-altmetric" aria-label="Altmetric attention"><div class="altmetric-embed" data-badge-type="donut" data-badge-popover="right" data-doi="${esc(p.doi)}"></div></div>`:`<div class="publication-altmetric publication-altmetric-empty" aria-hidden="true"></div>`;
    const tags=displayTags(p),summary=conciseSummary(p),journal=p.journal||"";
    const details=[p.publishedDate||p.year,journal].filter(Boolean).map(esc).join(" · ");
    return `<article class="publication-row"><div class="publication-theme-mark"><img src="${esc(t.icon)}" alt=""><span>${esc(t.short)}</span></div><div class="publication-details"><div class="publication-meta"><span class="type-badge ${esc(typeClass)}">${typeLabel}</span><span>${details}</span></div><h3><a href="${esc(href)}" target="_blank" rel="noopener">${esc(p.title)}</a></h3>${tags?`<div class="publication-tags" aria-label="Filter using publication tags">${tags}</div>`:""}<p class="publication-authors">${esc(p.authors||"")}</p>${summary?`<p class="publication-summary">${esc(summary)}</p>`:""}</div>${badge}</article>`;
  }
  function render(){
    const q=search.value.trim().toLowerCase(),tv=type.value,ov=organism.value,pv=project.value;
    let data=pubs.filter(p=>{
      const tagText=[...(p.organisms||[]),...(p.topics||[]),...(p.projects||[]),...(p.geographies||[])];
      const h=[p.title,p.authors,p.citation,p.year,p.publishedDate,p.theme,p.doi,p.url,p.status,...tagText].join(" ").toLowerCase();
      return(!q||h.includes(q))&&(tv==="all"||p.publicationType===tv)&&(ov==="all"||(p.organisms||[]).includes(ov))&&(pv==="all"||(p.projects||[]).includes(pv))&&(active==="all"||p.themeId===active);
    });
    data.sort(comparePublications);
    count.textContent=`${data.length} output${data.length===1?"":"s"}`;
    const grouped={};
    if(group.value==="theme"){
      themes.forEach(t=>grouped[t.id]=[]);data.forEach(p=>(grouped[p.themeId]||=[]).push(p));
      list.innerHTML=themes.map(t=>grouped[t.id].length?`<section class="publication-group"><div class="publication-group-title"><img src="${esc(t.icon)}" alt=""><div><p class="kicker">${esc(t.short)}</p><h2>${esc(t.label)}</h2></div><span>${grouped[t.id].length}</span></div><div class="publication-group-list">${grouped[t.id].map(item).join("")}</div></section>`:"").join("");
    }else{
      data.forEach(p=>(grouped[p.year]||=[]).push(p));
      list.innerHTML=Object.keys(grouped).sort((a,b)=>b-a).map(y=>`<section class="publication-group"><div class="publication-group-title year"><h2>${esc(y)}</h2><span>${grouped[y].length}</span></div><div class="publication-group-list">${grouped[y].map(item).join("")}</div></section>`).join("");
    }
    window.setTimeout(()=>refreshAltmetric(list),0);
  }
  const initial=new URLSearchParams(window.location.search);
  if(initial.get("q"))search.value=initial.get("q");
  if(initial.get("organism")&&[...organism.options].some(o=>o.value===initial.get("organism")))organism.value=initial.get("organism");
  if(initial.get("project")&&[...project.options].some(o=>o.value===initial.get("project")))project.value=initial.get("project");
  if(initial.get("type")&&[...type.options].some(o=>o.value===initial.get("type")))type.value=initial.get("type");
  if(initial.get("group")&&[...group.options].some(o=>o.value===initial.get("group")))group.value=initial.get("group");
  if(initial.get("theme"))active=initial.get("theme");
  document.querySelectorAll(".theme-filter").forEach(b=>{
    b.classList.toggle("active",b.dataset.theme===active);
    b.addEventListener("click",()=>{active=b.dataset.theme;document.querySelectorAll(".theme-filter").forEach(x=>x.classList.toggle("active",x===b));render();});
  });
  list.addEventListener("click",event=>{
    const tag=event.target.closest(".publication-tag");if(!tag)return;
    event.preventDefault();
    const kind=tag.dataset.tagKind,value=tag.dataset.tagValue;
    if(kind==="organism"&&[...organism.options].some(o=>o.value===value)){organism.value=value;search.value="";}
    else if(kind==="project"&&[...project.options].some(o=>o.value===value)){project.value=value;search.value="";}
    else search.value=value;
    render();
    document.querySelector(".publication-controls")?.scrollIntoView({behavior:"smooth",block:"start"});
  });
  search.addEventListener("input",render);type.addEventListener("change",render);organism.addEventListener("change",render);project.addEventListener("change",render);group.addEventListener("change",render);render();
}
Promise.allSettled([renderProjects(),renderStories(),renderFeatured(),renderMetrics(),renderBrowser()]).then(rs=>rs.filter(r=>r.status==="rejected").forEach(r=>console.error(r.reason)));
})();
