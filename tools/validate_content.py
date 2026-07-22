#!/usr/bin/env python3
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];errors=[]
def load(n):
    try:return json.loads((ROOT/"data"/n).read_text())
    except Exception as e:errors.append(f"{n}: {e}");return[]
pubs=load("publications.json");themes=load("themes.json");ids={t.get("id") for t in themes};seen=set()
for p in pubs:
    for f in ("id","year","citation","title","publicationType","themeId"):
        if not p.get(f):errors.append(f"{p.get('id','?')}: missing {f}")
    if p.get("publicationType") not in {"journal","preprint"}:errors.append(f"{p.get('id')}: invalid type")
    if p.get("themeId") not in ids:errors.append(f"{p.get('id')}: invalid theme")
    d=str(p.get("doi","")).lower()
    if d:
        if d in seen:errors.append(f"duplicate DOI: {d}")
        seen.add(d)
if errors:print("\n".join("ERROR: "+e for e in errors));sys.exit(1)
print(f"OK: {len(pubs)} journal articles/preprints across {len(themes)} themes")