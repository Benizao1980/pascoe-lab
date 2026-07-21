#!/usr/bin/env python3
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
errors=[]

def load(name):
    path=ROOT/"data"/name
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        errors.append(f"{path}: {exc}")
        return []

def unique(items,field,label):
    seen=set()
    for item in items:
        value=str(item.get(field,"")).strip().lower()
        if not value:
            errors.append(f"{label}: missing {field}")
        elif value in seen:
            errors.append(f"{label}: duplicate {field}: {value}")
        seen.add(value)

projects=load("projects.json")
people=load("people.json")
publications=load("publications.json")
stories=load("stories.json")

unique(projects,"id","projects")
unique(people,"id","people")
unique(publications,"id","publications")
unique(stories,"id","stories")
unique([p for p in publications if p.get("doi")],"doi","publications")

for p in projects:
    for field in ("id","code","title","summary","image","imageAlt","url"):
        if not p.get(field): errors.append(f"projects/{p.get('id','?')}: missing {field}")

for p in people:
    for field in ("id","name","role","supervision","summary","url"):
        if not p.get(field): errors.append(f"people/{p.get('id','?')}: missing {field}")

for p in publications:
    for field in ("id","year","citation","type","status"):
        if not p.get(field): errors.append(f"publications/{p.get('id','?')}: missing {field}")
    if p.get("status")!="published":
        errors.append(f"publications/{p.get('id','?')}: non-published status is not allowed")

for s in stories:
    for field in ("id","title","format","date","summary","image","imageAlt","url"):
        if not s.get(field): errors.append(f"stories/{s.get('id','?')}: missing {field}")

for item in projects+stories:
    for field in ("image","url"):
        value=item.get(field,"")
        if value and not value.startswith(("http://","https://")) and not (ROOT/value).exists():
            errors.append(f"{item.get('id')}: missing local {field}: {value}")

if errors:
    print("\n".join("ERROR: "+e for e in errors))
    sys.exit(1)

print(f"OK: {len(projects)} projects, {len(people)} people, {len(publications)} completed outputs, {len(stories)} stories")
