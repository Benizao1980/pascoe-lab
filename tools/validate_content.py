#!/usr/bin/env python3
import json,re,sys,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];errors=[];warnings=[]
def load(n):
    try:return json.loads((ROOT/'data'/n).read_text())
    except Exception as e:errors.append(f'{n}: {e}');return []
def norm(s):
    s=unicodedata.normalize('NFKD',s or '').encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+',' ',s).strip()
pubs=load('publications.json');themes=load('themes.json');ids={t.get('id') for t in themes};dois=set();titles=set()
for p in pubs:
    for f in ('id','year','citation','title','publicationType','themeId'):
        if not p.get(f):errors.append(f"{p.get('id','?')}: missing {f}")
    if p.get('publicationType') not in {'journal','preprint'}:errors.append(f"{p.get('id')}: invalid publicationType")
    if p.get('themeId') not in ids:errors.append(f"{p.get('id')}: invalid themeId")
    d=str(p.get('doi','')).lower().strip();t=norm(p.get('title'))
    if d:
        if d in dois:errors.append('duplicate DOI: '+d)
        if d=='tbc' or not d.startswith('10.'):errors.append(f"{p.get('id')}: invalid DOI {d}")
        dois.add(d)
    if t in titles:errors.append('duplicate title: '+p.get('title',''))
    titles.add(t)
    date=p.get('publishedDate','')
    if date and not re.fullmatch(r'\d{4}-\d{2}-\d{2}',date):errors.append(f"{p.get('id')}: invalid publishedDate")
    if re.search(r'\bdoi\s*:',p.get('title',''),re.I):warnings.append(f"{p.get('id')}: title may contain citation text")
if errors:
    print('\n'.join('ERROR: '+e for e in errors));sys.exit(1)
print(f"OK: {len(pubs)} publication records; {len(dois)} DOIs; {len(warnings)} title warnings")
for w in warnings[:20]:print('WARNING:',w)
