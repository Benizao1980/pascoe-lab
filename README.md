# Pascoe Lab website

Public website for the Pascoe Lab at the University of Oxford and the Ineos Oxford Institute for Antimicrobial Research.

**Live site:** https://pascoelab.com

## Main pages

- `index.html` — homepage
- `research.html` — research themes and representative papers
- `projects.html` — overview of current research programmes
- `publications.html` — searchable publication record
- `publication-overview.html` — publication summaries and visualisations
- `stories.html` — behind-the-paper pieces, explainers and field notes
- `people.html` — researchers, supervision and opportunities
- `network.html` — collaborators and research locations
- `resources.html` — software, protocols and open resources
- `logo.html` — Pascoe Lab logo files

Project pages include `project-africa.html`, `project-getcampy.html`, `project-ccc.html`,
`project-peru.html`, `project-thailand.html` and `project-hurizon.html`.

`join.html` and several older paths are retained as redirects so existing links continue to work.

## Structured content

Most repeatable content is stored in `data/`:

- `publications.json` — synchronised publication records used by the site
- `manual-publications.json` — curated pending and in-press records that may not yet be indexed
- `publication-sync.json` — publication-sync review output
- `scholar-metrics.json` — Google Scholar citation metrics
- `projects.json` — project cards
- `people.json` — researcher profiles
- `stories.json` — story cards
- `themes.json` and `tag-taxonomy.json` — publication themes and controlled tags
- `site.json` — small site-wide metadata values

Images, illustrations, logos and icons live in `assets/`.

## Automation

Two GitHub Actions workflows keep the site healthy:

- **Update publications and Google Scholar metrics** runs weekly and on demand. It merges
  curated records with Google Scholar and PubMed data, removes preprint/journal duplicates,
  and updates Scholar metrics.
- **Validate site** runs on relevant pushes and pull requests. It checks structured content,
  HTML metadata, local links, sitemap coverage and JavaScript syntax.

The publication updater depends on the repository secret `SERPAPI_KEY`.

## Editing

See [`EDITOR_GUIDE.md`](EDITOR_GUIDE.md) for the current editing workflow.

The site is deliberately a small static HTML/CSS/JavaScript project hosted with GitHub Pages.
Legacy redirect pages are kept for link stability rather than used as canonical pages.
