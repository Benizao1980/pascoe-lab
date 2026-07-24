# Pascoe Lab website — v6.5

Main changes:

- New bacterium mascot logo and horizontal lock-up
- Moderated homepage heading sizes and corrected the malformed hero markup
- Increased small text, metadata, navigation and caption sizes
- Publications limited to journal articles and public preprints
- Reports, book chapters, unfinished manuscripts and non-public submissions excluded
- Searchable publication browser with four theme filters and theme icons
- Publications can be grouped by research theme or year
- Thailand collaboration photographs added to the Thailand project page

Publication browser: 97 journal articles and 7 preprints.

- Re-exported with the illustrated bacterium logo generated from the supplied artwork.

- Fixed header/site logo path and replaced with the supplied final logo artwork.
- Updated Thailand project cards to use the attached collaboration photo.

- Removed the homepage hero headline and retained the concise mission statement.
- Shortened all four homepage research questions.
- Reduced project cards to a title and one short line.
- Simplified recent publication and story cards.
- Removed decorative page, section and project numbering throughout the site.

- Publication counts now update automatically from data/publications.json.
- H-index and citation totals load from data/site.json.
- In-press journal articles are supported and labelled.

## v6.5 publication upgrades

- Publications are grouped by year by default, newest first.
- Altmetric donuts are inserted for records with a DOI.
- Journal/preprint counts are calculated from `data/publications.json`.
- Google Scholar metrics load from `data/scholar-metrics.json`.
- A weekly GitHub Action can refresh Scholar metrics after adding a `SERPAPI_KEY` repository secret.
- Missing publication links fall back to an exact-title Google Scholar search.
- `tools/enrich_publications.py` provides a conservative Crossref DOI review workflow.
