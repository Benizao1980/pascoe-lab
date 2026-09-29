# Content data

Structured content used by the site lives here.

- `publications.json` — synchronised site-facing publication records
- `manual-publications.json` — curated pending/in-press records and metadata that should survive sync
- `publication-sync.json` — records requiring publication-sync review
- `scholar-metrics.json` — Google Scholar citation metrics
- `projects.json` — project cards
- `people.json` — researcher profiles
- `stories.json` — story cards
- `themes.json` — four publication themes
- `tag-taxonomy.json` — controlled organism/topic/project/geography tags
- `site.json` — small site-wide metadata values

For ordinary publication updates, edit `manual-publications.json` rather than
`publications.json`; the weekly workflow rebuilds the latter from curated and indexed sources.

Run `python tools/validate_content.py` after editing JSON.
