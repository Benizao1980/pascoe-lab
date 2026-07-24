#!/usr/bin/env python3
"""Find conservative Crossref DOI candidates for publication records.

Default: writes DOI_REVIEW.csv only. Pass --write to add only very high-confidence
matches (title similarity >= 0.97 and publication year within one year).
"""
from __future__ import annotations
import argparse, csv, json, os, re, time, unicodedata, urllib.parse, urllib.request
from difflib import SequenceMatcher
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PUBS=ROOT/'data'/'publications.json'; REPORT=ROOT/'DOI_REVIEW.csv'
def norm(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+',' ',s).strip()
def year_of(item):
    for key in ('published-print','published-online','issued','created'):
        parts=item.get(key,{}).get('date-parts',[])
        if parts and parts[0]: return int(parts[0][0])
    return None
def search(p,mailto):
    params={'query.bibliographic':f"{p.get('title','')} {p.get('authors','')} {p.get('year','')}",'rows':5,'select':'DOI,title,author,published-print,published-online,issued,created,container-title,type,score','mailto':mailto}
    url='https://api.crossref.org/works?'+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={'User-Agent':f'PascoeLabDOIAudit/1.0 (mailto:{mailto})'})
    with urllib.request.urlopen(req,timeout=45) as r: return json.load(r)['message']['items']
parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');args=parser.parse_args()
mailto=os.environ.get('CROSSREF_MAILTO','ben.pascoe@ndm.ox.ac.uk')
pubs=json.loads(PUBS.read_text()); rows=[]; changed=0
for p in pubs:
    if p.get('doi'): continue
    try: items=search(p,mailto)
    except Exception as e:
        rows.append({'id':p.get('id'),'title':p.get('title'),'year':p.get('year'),'candidate_doi':'','candidate_title':'','candidate_year':'','similarity':'','decision':f'error: {e}' });continue
    best=None
    for item in items:
        title=' '.join(item.get('title') or [])
        sim=SequenceMatcher(None,norm(p.get('title','')),norm(title)).ratio()
        y=year_of(item); yd=abs(int(p.get('year') or 0)-y) if y else 99
        score=(sim,-yd,float(item.get('score') or 0))
        if best is None or score>best[0]: best=(score,item,title,sim,y,yd)
    if best:
        _,item,title,sim,y,yd=best; doi=item.get('DOI','')
        decision='auto-add' if doi and sim>=0.97 and yd<=1 else 'review'
        rows.append({'id':p.get('id'),'title':p.get('title'),'year':p.get('year'),'candidate_doi':doi,'candidate_title':title,'candidate_year':y or '','similarity':f'{sim:.3f}','decision':decision})
        if args.write and decision=='auto-add': p['doi']=doi; changed+=1
    time.sleep(0.12)
with REPORT.open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['id','title','year','candidate_doi','candidate_title','candidate_year','similarity','decision']);w.writeheader();w.writerows(rows)
if args.write and changed: PUBS.write_text(json.dumps(pubs,indent=2,ensure_ascii=False)+'\\n')
print(f'Wrote {REPORT}; {changed} DOI(s) added.')
