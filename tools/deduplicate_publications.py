#!/usr/bin/env python3
"""Collapse preprint and journal versions into one publication record.

The journal or in-press version is retained. Curated metadata from the preprint
record is transferred to it, and the preprint DOI/URL are preserved as
`preprintDoi` and `preprintUrl`.

This runs after tools/update_publications.py so that Google Scholar and PubMed
can update independently without leaving duplicate versions on the website.
"""
from __future__ import annotations

import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLICATIONS = ROOT / "data" / "publications.json"

PREPRINT_DOI_PREFIXES = (
    "10.1101/",
    "10.21203/",
    "10.64898/",
)

PREPRINT_MARKERS = (
    "biorxiv",
    "medrxiv",
    "research square",
    "ssrn",
    "arxiv",
    "preprint server",
)

# Confirmed preprint → journal transitions. These explicit links also handle
# substantial title changes between versions.
KNOWN_VERSION_PAIRS = {
    "10.64898/2026.05.21.726754": "10.1186/s12864-026-13148-1",
    "10.64898/2026.02.06.704332": "10.4269/ajtmh.26-0268",
}


def norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def clean_doi(value: object) -> str:
    doi = str(value or "").strip().lower()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi)
    return doi.rstrip(" .")


def is_preprint_source(record: dict) -> bool:
    doi = clean_doi(record.get("doi"))
    source_text = norm(
        " ".join(
            str(record.get(field, ""))
            for field in ("journal", "citation", "url", "type")
        )
    )
    return doi.startswith(PREPRINT_DOI_PREFIXES) or any(
        marker in source_text for marker in PREPRINT_MARKERS
    )


def normalise_record_type(record: dict) -> None:
    """Correct records whose old preprint status survived PubMed enrichment."""
    if is_preprint_source(record):
        record["publicationType"] = "preprint"
        record["type"] = "preprint"
        record["status"] = "preprint"
        return

    record["publicationType"] = "journal"
    record["type"] = "publication"
    if record.get("status") == "preprint":
        record["status"] = "published"


def author_keys(record: dict) -> set[str]:
    keys: set[str] = set()
    for part in str(record.get("authors", "")).split(","):
        words = norm(part).split()
        if not words or words[0] in {"et", "consortium", "collaborators"}:
            continue
        # The first token is sufficient for overlap testing and is robust to
        # initials and inconsistent author formatting.
        keys.add(words[0])
    return keys


def title_scores(left: dict, right: dict) -> tuple[float, float]:
    a = norm(left.get("title"))
    b = norm(right.get("title"))
    if not a or not b:
        return 0.0, 0.0

    sequence = SequenceMatcher(None, a, b).ratio()
    at = set(a.split())
    bt = set(b.split())
    containment = len(at & bt) / max(1, min(len(at), len(bt)))
    return sequence, containment


def author_overlap(left: dict, right: dict) -> float:
    a = author_keys(left)
    b = author_keys(right)
    return len(a & b) / max(1, min(len(a), len(b)))


def likely_version_pair(preprint: dict, journal: dict) -> bool:
    preprint_doi = clean_doi(preprint.get("doi"))
    journal_doi = clean_doi(journal.get("doi"))

    if KNOWN_VERSION_PAIRS.get(preprint_doi) == journal_doi:
        return True

    years = {
        int(value)
        for value in (preprint.get("year"), journal.get("year"))
        if str(value or "").isdigit()
    }
    if len(years) == 2 and max(years) - min(years) > 2:
        return False

    sequence, containment = title_scores(preprint, journal)
    overlap = author_overlap(preprint, journal)

    first_preprint = next(iter(author_keys(preprint)), "")
    first_journal = next(iter(author_keys(journal)), "")
    first_author_matches = first_preprint and first_preprint == first_journal

    return bool(
        first_author_matches
        and overlap >= 0.60
        and (
            sequence >= 0.80
            or (containment >= 0.85 and sequence >= 0.68)
        )
    )


def merge_curated_metadata(journal: dict, preprint: dict) -> dict:
    result = dict(journal)

    for field in ("selected", "featuredHome"):
        result[field] = bool(result.get(field) or preprint.get(field))

    for field in ("summary", "themeId", "theme", "project"):
        if not result.get(field) and preprint.get(field):
            result[field] = preprint[field]

    for field in ("organisms", "topics", "projects", "geographies"):
        combined: list[str] = []
        for value in list(result.get(field) or []) + list(preprint.get(field) or []):
            if value and value not in combined:
                combined.append(value)
        if combined:
            result[field] = combined

    preprint_doi = clean_doi(preprint.get("doi"))
    if preprint_doi:
        result["preprintDoi"] = preprint_doi

    preprint_url = preprint.get("url")
    if not preprint_url and preprint_doi:
        preprint_url = f"https://doi.org/{preprint_doi}"
    if preprint_url:
        result["preprintUrl"] = preprint_url

    if preprint.get("title") and norm(preprint.get("title")) != norm(result.get("title")):
        result["preprintTitle"] = preprint["title"]

    return result


def quality_rank(record: dict) -> tuple[int, int, str]:
    status = str(record.get("status", "")).lower()
    status_rank = {"in press": 3, "published": 2, "preprint": 1}.get(status, 0)
    metadata = sum(
        bool(record.get(field))
        for field in ("doi", "pmid", "abstract", "journal", "publishedDate")
    )
    return status_rank, metadata, str(record.get("publishedDate", ""))


def collapse_exact_duplicates(records: list[dict]) -> list[dict]:
    kept: dict[str, dict] = {}
    order: list[str] = []

    for record in records:
        doi = clean_doi(record.get("doi"))
        key = f"doi:{doi}" if doi else f"title:{norm(record.get('title'))}"
        if key not in kept:
            kept[key] = record
            order.append(key)
        elif quality_rank(record) > quality_rank(kept[key]):
            kept[key] = record

    return [kept[key] for key in order]


def main() -> None:
    records = json.loads(PUBLICATIONS.read_text(encoding="utf-8"))
    for record in records:
        normalise_record_type(record)

    records = collapse_exact_duplicates(records)
    preprints = [record for record in records if is_preprint_source(record)]
    journals = [record for record in records if not is_preprint_source(record)]

    removed_ids: set[int] = set()
    replacements: dict[int, dict] = {}
    resolved: list[dict] = []

    for preprint in preprints:
        candidates = [
            journal
            for journal in journals
            if likely_version_pair(preprint, journal)
        ]
        if not candidates:
            continue

        journal = max(
            candidates,
            key=lambda candidate: (
                title_scores(preprint, candidate)[0],
                title_scores(preprint, candidate)[1],
                author_overlap(preprint, candidate),
                quality_rank(candidate),
            ),
        )
        merged = merge_curated_metadata(
            replacements.get(id(journal), journal),
            preprint,
        )
        replacements[id(journal)] = merged
        removed_ids.add(id(preprint))
        resolved.append(
            {
                "preprint": preprint.get("title"),
                "preprint_doi": clean_doi(preprint.get("doi")),
                "retained": journal.get("title"),
                "journal_doi": clean_doi(journal.get("doi")),
            }
        )

    cleaned: list[dict] = []
    for record in records:
        if id(record) in removed_ids:
            continue
        cleaned.append(replacements.get(id(record), record))

    cleaned.sort(
        key=lambda record: (
            str(record.get("publishedDate", "")),
            quality_rank(record),
            norm(record.get("title")),
        ),
        reverse=True,
    )

    PUBLICATIONS.write_text(
        json.dumps(cleaned, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "before": len(records),
                "after": len(cleaned),
                "version_pairs_collapsed": len(resolved),
                "resolved": resolved,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
