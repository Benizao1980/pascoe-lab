#!/usr/bin/env python3
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []

def load(name):
    path = ROOT / "data" / name
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        errors.append(f"{path}: {exc}")
        return []

def check_unique(items, field, label):
    seen = set()
    for item in items:
        value = str(item.get(field, "")).strip().lower()
        if not value:
            errors.append(f"{label}: missing {field}")
        elif value in seen:
            errors.append(f"{label}: duplicate {field} {value}")
        seen.add(value)

projects = load("projects.json")
publications = load("publications.json")
stories = load("stories.json")

check_unique(projects, "id", "projects")
check_unique(publications, "id", "publications")
check_unique(stories, "id", "stories")
check_unique([p for p in publications if p.get("doi")], "doi", "publications")

required = {
    "projects": (projects, ["id","code","title","summary","image","imageAlt","url"]),
    "publications": (publications, ["id","title","authors","journal","year","doi","theme","summary"]),
    "stories": (stories, ["id","title","format","date","summary","image","imageAlt","url"])
}
for label, (items, fields) in required.items():
    for item in items:
        for field in fields:
            if item.get(field) in (None, ""):
                errors.append(f"{label}/{item.get('id','?')}: missing {field}")

for item in projects + stories:
    for field in ("image","url"):
        value = item.get(field, "")
        if value and not value.startswith(("http://","https://")):
            if not (ROOT / value).exists():
                errors.append(f"{item.get('id')}: missing local {field} {value}")

if errors:
    print("\n".join(f"ERROR: {e}" for e in errors))
    sys.exit(1)

print(f"OK: {len(projects)} projects, {len(publications)} publications, {len(stories)} stories")
