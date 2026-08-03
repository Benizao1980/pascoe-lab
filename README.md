# Pascoe Lab website

Public website for the Pascoe Lab at the University of Oxford and the Ineos Oxford Institute for Antimicrobial Research.

**Live site:** https://pascoelab.com

## Main pages

- `index.html` — homepage and overview of the lab
- `research.html` — research themes and representative papers
- `projects.html` — overview of current research programmes
- `project-africa.html` — enteric disease research in Africa
- `project-peru.html` — child health and enteric disease research in Peru
- `project-thailand.html` — One Health collaborations in Thailand
- `project-hurizon.html` — wildlife, urbanisation and antimicrobial resistance
- `publications.html` — searchable and filterable publication list
- `publication-overview.html` — publication summaries and visualisations
- `stories.html` — research stories, threads and behind-the-paper content
- `people.html` — lab members and supervision
- `join.html` — opportunities to work with the lab
- `network.html` — collaborators and research locations
- `resources.html` — software, protocols and open resources
- `logo.html` — downloadable Pascoe Lab logo files

## Site content

Structured content is stored in `data/`:

- `publications.json` — publication records, tags and links
- `scholar-metrics.json` — Google Scholar citation metrics
- `projects.json` — project cards and summaries
- `people.json` — researcher profiles
- `stories.json` — stories and social-media threads
- `themes.json` and `tag-taxonomy.json` — publication themes and controlled tags

Images, logos and icons are stored in `assets/`.

## Publication updates

GitHub Actions and the scripts in `tools/` update Google Scholar metrics and help synchronise publication records with Google Scholar and PubMed. Publication themes, project links and selected homepage content remain manually curated.

## Technical notes

The website is a static HTML, CSS and JavaScript site hosted with GitHub Pages. Legacy redirect pages are retained so older links continue to reach the current content.
