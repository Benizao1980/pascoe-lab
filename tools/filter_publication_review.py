#!/usr/bin/env python3
"""Remove obvious non-publication noise from the Scholar review queue.

The publication updater is intentionally conservative: unmatched Scholar records are
sent to data/publication-sync.json rather than automatically added to the website.
This post-processing step keeps that review queue useful by dropping records that
are clearly not Ben Pascoe publications (namesakes/coauthor-profile leakage) or
are routine protocols, SOPs, theses and conference-only material.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNC_FILE = ROOT / "data" / "publication-sync.json"


def norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def is_ben_author(authors: object) -> bool:
    text = norm(authors)
    return bool(re.search(r"\b(?:b|ben|benjamin)\s+pascoe\b|\bpascoe\s+(?:b|ben|benjamin)\b", text))


def is_obvious_non_publication(item: dict) -> bool:
    title = norm(item.get("title"))
    publication = norm(item.get("publication"))
    combined = f"{title} {publication}"

    title_prefixes = (
        "c sop ",
        "getcampy laboratory procedures",
        "getcampy sequencing protocols",
        "dna extraction campylobacter",
    )
    if title.startswith(title_prefixes):
        return True

    markers = (
        "annual meeting",
        "conference abstract",
        "conference proceedings",
        "poster presentation",
        "oral presentation",
        "doctoral thesis",
        "phd thesis",
        "master s thesis",
    )
    if any(marker in combined for marker in markers):
        return True

    # Scholar sometimes labels theses and repository records with a university
    # name or '(No Title)' rather than a journal. They are useful elsewhere but
    # should not repeatedly appear in the publication-review queue.
    if publication in {"no title", "(no title)"}:
        return True
    if publication.startswith("university of ") and not re.search(r"journal|press", publication):
        return True

    # Access Microbiology supplement records in the profile are conference
    # abstracts rather than full research articles.
    if publication.startswith("access microbiology 1"):
        return True

    return False


def main() -> None:
    data = json.loads(SYNC_FILE.read_text())
    review = data.get("review", [])
    kept = [item for item in review if is_ben_author(item.get("authors")) and not is_obvious_non_publication(item)]
    data["review"] = kept
    data["review_filter"] = {
        "before": len(review),
        "after": len(kept),
        "rule": "Ben Pascoe author match; exclude obvious protocols/SOPs/theses/conference-only records",
    }
    SYNC_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"Publication review queue: {len(review)} -> {len(kept)}")


if __name__ == "__main__":
    main()
