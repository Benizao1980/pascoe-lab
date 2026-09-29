#!/usr/bin/env python3
"""Validate structured JSON used by the Pascoe Lab website."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
errors: list[str] = []
warnings: list[str] = []


def load(name: str, expected: type | tuple[type, ...] | None = None) -> Any:
    path = DATA / name
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{name}: {exc}")
        return [] if expected is list else {}
    if expected is not None and not isinstance(value, expected):
        errors.append(f"{name}: expected {expected}, found {type(value).__name__}")
    return value


def norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def valid_date(value: object) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value or "")))


themes = load("themes.json", list)
taxonomy = load("tag-taxonomy.json", dict)
publications = load("publications.json", list)
manual_publications = load("manual-publications.json", list)
projects = load("projects.json", list)
people = load("people.json", list)
stories = load("stories.json", list)
site = load("site.json", dict)
metrics = load("scholar-metrics.json", dict)
load("publication-sync.json")

theme_ids = {item.get("id") for item in themes if isinstance(item, dict) and item.get("id")}
allowed_types = {"journal", "preprint", "pending"}
allowed_statuses = {"published", "in press", "preprint", "pending", "accepted"}
tag_fields = ("organisms", "topics", "projects", "geographies")


def validate_record(record: dict[str, Any], source: str) -> None:
    rid = record.get("id") or "?"
    for field in ("id", "year", "citation", "title", "publicationType", "themeId"):
        if not record.get(field):
            errors.append(f"{source}:{rid}: missing {field}")

    publication_type = record.get("publicationType")
    if publication_type not in allowed_types:
        errors.append(f"{source}:{rid}: invalid publicationType {publication_type!r}")

    status = str(record.get("status") or "").lower()
    if status and status not in allowed_statuses:
        errors.append(f"{source}:{rid}: invalid status {record.get('status')!r}")

    if record.get("themeId") not in theme_ids:
        errors.append(f"{source}:{rid}: invalid themeId {record.get('themeId')!r}")

    for field in tag_fields:
        values = record.get(field, [])
        if not isinstance(values, list):
            errors.append(f"{source}:{rid}: {field} must be a list")
            continue
        allowed = set(taxonomy.get(field, [])) if isinstance(taxonomy, dict) else set()
        for value in values:
            if allowed and value not in allowed:
                warnings.append(f"{source}:{rid}: {field} tag outside taxonomy: {value!r}")

    doi = str(record.get("doi") or "").strip().lower()
    if doi and (doi == "tbc" or not doi.startswith("10.")):
        errors.append(f"{source}:{rid}: invalid DOI {doi}")

    for field in ("publishedDate", "acceptedDate", "submittedDate", "postedDate"):
        value = record.get(field)
        if value and not valid_date(value):
            errors.append(f"{source}:{rid}: invalid {field}: {value!r}")

    if re.search(r"\bdoi\s*:", str(record.get("title") or ""), re.I):
        warnings.append(f"{source}:{rid}: title may contain citation text")


def validate_publication_collection(records: list[Any], source: str, check_duplicates: bool) -> None:
    ids: set[str] = set()
    dois: set[str] = set()
    titles: set[str] = set()

    for raw in records:
        if not isinstance(raw, dict):
            errors.append(f"{source}: publication record is not an object")
            continue
        validate_record(raw, source)

        rid = str(raw.get("id") or "")
        if rid:
            if rid in ids:
                errors.append(f"{source}: duplicate id: {rid}")
            ids.add(rid)

        if not check_duplicates:
            continue

        doi = str(raw.get("doi") or "").strip().lower()
        title = norm(raw.get("title"))
        if doi:
            if doi in dois:
                errors.append(f"{source}: duplicate DOI: {doi}")
            dois.add(doi)
        if title:
            if title in titles:
                errors.append(f"{source}: duplicate title: {raw.get('title', '')}")
            titles.add(title)


validate_publication_collection(publications, "publications.json", check_duplicates=True)
validate_publication_collection(manual_publications, "manual-publications.json", check_duplicates=False)

for name, records in (("projects.json", projects), ("people.json", people), ("stories.json", stories)):
    seen: set[str] = set()
    for raw in records:
        if not isinstance(raw, dict):
            errors.append(f"{name}: record is not an object")
            continue
        rid = str(raw.get("id") or "")
        if not rid:
            warnings.append(f"{name}: record without id")
        elif rid in seen:
            errors.append(f"{name}: duplicate id: {rid}")
        else:
            seen.add(rid)

for field in ("citations", "h_index", "i10_index"):
    if field in metrics and not isinstance(metrics[field], int):
        errors.append(f"scholar-metrics.json: {field} must be an integer")

if errors:
    print("\n".join("ERROR: " + item for item in errors))
    if warnings:
        print("\n".join("WARNING: " + item for item in warnings[:30]))
    sys.exit(1)

doi_count = len({str(p.get("doi") or "").lower() for p in publications if isinstance(p, dict) and p.get("doi")})
print(
    f"OK: {len(publications)} publication records; "
    f"{len(manual_publications)} manual records; {doi_count} DOIs; "
    f"{len(warnings)} warning(s)"
)
for warning in warnings[:30]:
    print("WARNING:", warning)
