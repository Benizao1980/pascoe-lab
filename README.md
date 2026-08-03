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


## Version 6.6

- Burgundy masthead across the site.
- Shortened homepage and page introductions.
- Research themes now use visuals and representative papers; visible numbering removed.
- Added Ben Pascoe portrait to the People page.
- Resources now lists SourceRunnerML, BAMPS-ML, PANOPTICON, LINwalker and ICassigner separately.
- Scholar metric fallback updated to the successful 24 July 2026 refresh.


## v6.7 Scholar metrics reliability fix

- The publications page reads the latest Scholar metrics directly from the repository raw file.
- The Scholar workflow explicitly requests a GitHub Pages rebuild after updating metrics.
- GitHub Actions dependencies upgraded to Node 24-compatible releases.
- `content.js` is cache-busted on the publications page.


## v6.11 publication synchronisation

- Google Scholar profile is the curated identity source.
- PubMed enriches matching records with DOI, PMID, journal and exact publication date.
- New unmatched non-preprint records are placed in `data/publication-sync.json` for review.
- Themes and homepage selections remain manually curated.
- The browser fetches publication data directly from the main GitHub branch, with the deployed local file as fallback.
- Publications are sorted by `publishedDate`, not alphabetically within each year.


## v6.11 publication tags

- Added controlled organism, topic, project and geography tags.
- Added organism and project dropdown filters.
- Search includes all tag fields.
- Publication cards show up to three compact tags.
- Default year grouping orders each year as: in press, published, preprint; each status is then newest first.


## v6.11 publication cards

- Publication tags are clickable filters.
- The duplicate full citation block has been removed from cards.
- Cards show authors once and a two-line summary or abstract excerpt.
- PubMed abstracts and publication status are stored during synchronisation.
- PMID 42532029 is explicitly imported even if Google Scholar indexing lags.


## v6.11 publication updates

- cache-busted publication CSS and JavaScript to prevent an older browser bundle reappearing after a Pages rebuild
- added compact Dimensions citation badges beside Altmetric badges
- added a separate, automatically generated publication-overview page with output-by-year, theme, organism and project charts
