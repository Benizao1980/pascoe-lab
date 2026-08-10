#!/usr/bin/env python3
"""Merge manually curated in-press records into data/publications.json.

Use data/manual-publications.json for accepted papers that are not yet reliably
present in Google Scholar/PubMed. The normal publication synchronisation then
enriches the main list when indexed metadata becomes available.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLICATIONS = ROOT / "data" / "publications.json"
MANUAL = ROOT / "data" / "manual-publications.json"


def norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def clean_doi(value: object) -> str:
    doi = str(value or "").strip().lower()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi)
    return doi.rstrip(" .")


def main() -> None:
    pubs = json.loads(PUBLICATIONS.read_text(encoding="utf-8"))
    manual = json.loads(MANUAL.read_text(encoding="utf-8")) if MANUAL.exists() else []

    doi_index = {clean_doi(p.get("doi")) for p in pubs if clean_doi(p.get("doi"))}
    title_index = {norm(p.get("title")) for p in pubs if norm(p.get("title"))}

    added = 0
    refreshed = 0

    for record in manual:
        doi = clean_doi(record.get("doi"))
        title = norm(record.get("title"))

        # If the exact manual record already exists, refresh its curated fields
        # without creating a duplicate.
        existing = next(
            (
                p for p in pubs
                if (doi and clean_doi(p.get("doi")) == doi)
                or (title and norm(p.get("title")) == title and not clean_doi(p.get("doi")))
            ),
            None,
        )
        if existing is not None:
            for key, value in record.items():
                if value not in ("", None, [], {}):
                    existing[key] = value
            refreshed += 1
            continue

        # A DOI-bearing published version with the same title takes precedence.
        if title in title_index:
            continue

        pubs.append(record)
        if doi:
            doi_index.add(doi)
        if title:
            title_index.add(title)
        added += 1

    PUBLICATIONS.write_text(
        json.dumps(pubs, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"manual_added": added, "manual_refreshed": refreshed, "site_records": len(pubs)}))


if __name__ == "__main__":
    main()
