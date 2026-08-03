# v6.12 Google Scholar metrics fix

The Publications page now retrieves `data/scholar-metrics.json` from the GitHub Contents API first. This bypasses GitHub Pages deployment caching.

The page also displays the date of the Scholar data beneath the metrics, making it clear which file was loaded.

Important: upload the files **inside** this folder to the repository root. In particular, `publications.html` must replace the root file and must contain `content.js?v=6.12`.
