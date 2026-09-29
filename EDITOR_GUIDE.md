# Updating the Pascoe Lab website

This site is intentionally simple: static HTML/CSS/JavaScript plus structured JSON in `data/`.
The safest rule is to edit structured content where possible and avoid duplicating the same
information across pages.

## Publications

### New pending or in-press paper

Add a curated record to `data/manual-publications.json`.

Use:

- `publicationType: "pending"` and `status: "pending"` for a submitted paper/preprint that is
  not yet public;
- `publicationType: "preprint"` and `status: "preprint"` once a public preprint is available;
- `publicationType: "journal"` and `status: "in press"` for an accepted paper without final
  publication details;
- `publicationType: "journal"` and `status: "published"` for a final journal article.

Include an `id`, `year`, `title`, `authors`, `citation`, `themeId` and the structured tag arrays
(`organisms`, `topics`, `projects`, `geographies`). Use names from `data/tag-taxonomy.json`.

### Automatic publication sync

The workflow `.github/workflows/update-scholar-metrics.yml` runs each Monday and can also be
started manually. It:

1. merges `data/manual-publications.json` into the working publication list;
2. retrieves the curated Google Scholar profile through SerpAPI;
3. uses PubMed to enrich journal metadata where the title match is sufficiently strong;
4. collapses preprint and journal versions into a single record;
5. updates `data/publications.json`, `data/publication-sync.json` and
   `data/scholar-metrics.json`.

For normal updates, do **not** hand-edit `data/publications.json` unless repairing a specific
record. Curated metadata belongs in `manual-publications.json`; the synchronised file is the
site-facing output.

The publication browser defaults to **in press → published → preprint**, then newest date first.
Pending records are displayed separately and do not count as public outputs.

## Stories

1. Copy `stories/template.html`.
2. Give the page a lower-case hyphenated filename.
3. Update its title, description, canonical URL, hero content and body.
4. Add a matching card to `data/stories.json`.
5. Add the canonical story URL to `sitemap.xml`.

Use the existing story/card classes before adding page-specific CSS. Permanent local story pages
are preferable to relying on social-media embeds alone.

## Projects

Project cards live in `data/projects.json`; detailed project pages remain normal HTML files.
When adding a new canonical project page, also add it to `sitemap.xml`.

## People

Current researcher profiles are stored in `data/people.json`. Opportunities are part of
`people.html`; `join.html` is retained only as a redirect.

## Images and logos

- Put photographs in `assets/photos/`.
- Put diagrams/illustrations in `assets/illustrations/`.
- Prefer WebP or a compact SVG for images used on many pages.
- Aim for roughly 1,400–2,000 px on the long edge for photographs and keep files comfortably
  below 700 KB when practical.
- Always provide meaningful `alt` text for content images. Decorative images may use `alt=""`.
- Keep filenames lower-case and hyphenated.

The high-resolution PNG logo is retained as a downloadable asset; site chrome should prefer the
small SVG logo where practical.

## Checks before committing

Run:

```bash
python tools/validate_content.py
python tools/validate_site.py
node --check script.js
node --check content.js
```

GitHub Actions runs the same checks on relevant pushes and pull requests.

The validators are deliberately conservative: they catch broken local links, malformed JSON,
duplicate publication identifiers, missing page metadata and sitemap drift without attempting to
rewrite scientific content automatically.

## Legacy routes

Small redirect pages such as `all-publications.html`, `latest-work.html`, `news.html`,
`lab-guides.html`, `join.html` and their directory variants are intentionally retained to protect
old bookmarks and external links. Do not add redirect URLs to the sitemap.
