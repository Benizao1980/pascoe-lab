# Updating the Pascoe Lab website

The repeatable content now lives in three JSON files:

- `data/publications.json`
- `data/stories.json`
- `data/projects.json`

The website reads those files in the visitor's browser through `content.js`.
A publication, story card or project card therefore only needs to be entered once.

## Add a paper

Open `data/publications.json` and copy an existing record.

Required fields:

```json
{
  "id": "short-unique-id",
  "title": "Full title",
  "authors": "Author A, Author B, Pascoe B, et al.",
  "journal": "Journal name",
  "year": 2026,
  "doi": "10.xxxx/xxxxx",
  "theme": "Campylobacter · AMR",
  "summary": "One sentence explaining why it matters.",
  "project": "Peru",
  "selected": true,
  "featuredHome": false,
  "status": "published"
}
```

- `selected: true` places it on Selected Publications.
- `featuredHome: true` places it on the homepage.
- `story` is optional and should be a relative link such as
  `stories/my-story.html`.

The full publication page merges this local file with Crossref results from
the ORCID record and removes DOI duplicates.

## Add a blog, Behind-the-Paper page or thread

1. Copy `stories/template.html`.
2. Rename the copy with lower-case words and hyphens:
   `stories/peru-coli-emergence.html`.
3. Edit its title, introduction, text, image and links.
4. Add one record to `data/stories.json`.

Example:

```json
{
  "id": "peru-coli-emergence",
  "title": "How an emerging C. coli lineage spread in the Peruvian Amazon",
  "format": "Behind the paper",
  "date": "2026-08-01",
  "summary": "One short sentence for the story card.",
  "image": "assets/photos/peru-coli-tree.webp",
  "imageAlt": "Phylogeny of C. coli isolates from Peru",
  "url": "stories/peru-coli-emergence.html",
  "tags": ["Peru", "Campylobacter", "AMR"],
  "featuredHome": true
}
```

Use `Bluesky thread`, `Field note`, `Behind the paper`, `Project update` or
`Research explainer` consistently in the `format` field.

For a quick social-post link, the `url` field may point directly to a public
Bluesky or X post. For a permanent archive, create a local story page from the
template and link to the original thread from that page.

## Add or change a project

Project cards are stored in `data/projects.json`.

Each project still has its own normal HTML page. Add the page first, then add
the JSON record. `featuredHome` controls whether it appears on the homepage.

## Add an image

Upload it to `assets/photos/`.

Recommended:
- WebP or JPEG
- 1,400-2,000 pixels on the long edge
- under about 700 KB
- lower-case filename with hyphens
- meaningful alt text

Pages inside `stories/` refer to images as:

```html
../assets/photos/image-name.webp
```

The JSON files use:

```text
assets/photos/image-name.webp
```

## Check before committing

Run locally when Python is available:

```bash
python tools/validate_content.py
```

GitHub also runs this check automatically after each push.


# Version 5 additions

## Publication source

The full published-output list was imported from:

`BenPascoe_CV.full_NOV2025(1).docx`

The site currently contains **102 completed outputs**. The import deliberately
omits manuscripts in preparation, papers under review, preprints, and items still
marked "In press" in the CV.

To add a newly published paper, append one record to `data/publications.json`.

```json
{
  "id": "year-short-title",
  "year": 2026,
  "citation": "Full completed citation",
  "authors": "Authors",
  "title": "Paper title",
  "doi": "10.xxxx/xxxxx",
  "type": "publication",
  "status": "published",
  "selected": false,
  "featuredHome": false
}
```

Only set `selected` or `featuredHome` to true when the paper has a final
publication record.

## People

Current doctoral researchers are stored in `data/people.json`. Add a person once
and the homepage and People page update together.

## Projects

The four current project cards are:

1. Enteric disease in Africa
2. Peru child health
3. Thailand One Health
4. HU-RIZON wildlife and AMR

They are maintained in `data/projects.json`.
