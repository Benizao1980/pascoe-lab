#!/usr/bin/env python3
"""Refresh public Google Scholar metrics through SerpAPI.

Required environment variable: SERPAPI_KEY
Optional: SCHOLAR_AUTHOR_ID (defaults to Ben Pascoe's public profile)
"""
from __future__ import annotations
import json, os, sys, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'scholar-metrics.json'
KEY=os.environ.get('SERPAPI_KEY','').strip()
AUTHOR_ID=os.environ.get('SCHOLAR_AUTHOR_ID','UQrZ-fgAAAAJ').strip()
if not KEY:
    print('SERPAPI_KEY is not configured; leaving current metrics unchanged.')
    raise SystemExit(0)
params=urllib.parse.urlencode({'engine':'google_scholar_author','author_id':AUTHOR_ID,'hl':'en','api_key':KEY})
req=urllib.request.Request('https://serpapi.com/search.json?'+params,headers={'User-Agent':'PascoeLabMetrics/1.0'})
with urllib.request.urlopen(req,timeout=45) as response:
    data=json.load(response)
if data.get('error'):
    raise SystemExit('SerpAPI error: '+str(data['error']))
table=data.get('cited_by',{}).get('table',[])
def metric(name):
    for row in table:
        if name in row:
            value=row[name]
            return value.get('all') if isinstance(value,dict) else value
    return None
result={
    'source':'Google Scholar',
    'author_id':AUTHOR_ID,
    'profile_url':f'https://scholar.google.com/citations?user={AUTHOR_ID}&hl=en',
    'updated_at':datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    'citations':metric('citations'),
    'h_index':metric('h_index'),
    'i10_index':metric('i10_index'),
}
missing=[k for k in ('citations','h_index','i10_index') if result[k] is None]
if missing: raise SystemExit('Metrics missing from API response: '+', '.join(missing))
OUT.write_text(json.dumps(result,indent=2)+'\\n')
print(json.dumps(result,indent=2))
