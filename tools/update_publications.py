#!/usr/bin/env python3
"""Synchronise the Pascoe Lab publication list.

Identity source: Ben Pascoe's curated Google Scholar profile (SerpAPI).
Metadata enrichment: PubMed / NCBI E-utilities.

The updater is intentionally conservative:
- existing records are retained;
- new Google Scholar records are added automatically only when they match PubMed
  or are clearly hosted by a recognised preprint server;
- non-journal items are placed in data/publication-sync.json for review;
- themes, featured flags, summaries and project links from existing records persist.
"""
from __future__ import annotations
import json, os, re, sys, unicodedata, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PUB_FILE=ROOT/'data'/'publications.json'
METRIC_FILE=ROOT/'data'/'scholar-metrics.json'
SYNC_FILE=ROOT/'data'/'publication-sync.json'
KEY=os.environ.get('SERPAPI_KEY','').strip()
AUTHOR_ID=os.environ.get('SCHOLAR_AUTHOR_ID','UQrZ-fgAAAAJ').strip()
if not KEY:
    raise SystemExit('SERPAPI_KEY is required')

def fetch_json(base, params):
    url=base+'?'+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={'User-Agent':'PascoeLabPublicationSync/1.0 (https://pascoelab.com)'})
    with urllib.request.urlopen(req,timeout=90) as r:return json.load(r)

def fetch_text(base, params):
    url=base+'?'+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={'User-Agent':'PascoeLabPublicationSync/1.0 (https://pascoelab.com)'})
    with urllib.request.urlopen(req,timeout=90) as r:return r.read().decode('utf-8')

def norm(s):
    s=unicodedata.normalize('NFKD',s or '').encode('ascii','ignore').decode().lower()
    s=re.sub(r'<[^>]+>',' ',s)
    s=re.sub(r'[^a-z0-9]+',' ',s)
    return ' '.join(s.split())

def clean_doi(s):
    if not s:return ''
    s=re.sub(r'^https?://(?:dx\.)?doi\.org/','',str(s).strip(),flags=re.I)
    return s.rstrip(' .').lower()

def xml_text(node):
    return ''.join(node.itertext()).strip() if node is not None else ''

def month_num(value):
    if not value:return '01'
    value=value.strip()
    months={'jan':'01','feb':'02','mar':'03','apr':'04','may':'05','jun':'06','jul':'07','aug':'08','sep':'09','oct':'10','nov':'11','dec':'12'}
    if value.isdigit():return f'{int(value):02d}'
    return months.get(value[:3].lower(),'01')

def scholar_pages():
    articles=[]; cited_by=None; start=0
    while True:
        data=fetch_json('https://serpapi.com/search.json',{
            'engine':'google_scholar_author','author_id':AUTHOR_ID,'hl':'en',
            'sort':'pubdate','num':100,'start':start,'api_key':KEY,'no_cache':'true'
        })
        if data.get('error'):raise RuntimeError('SerpAPI: '+str(data['error']))
        batch=data.get('articles',[])
        if cited_by is None:cited_by=data.get('cited_by',{})
        articles.extend(batch)
        if len(batch)<100:break
        start+=100
        if start>=500:break
    return articles,cited_by or {}

def pubmed_records():
    search=fetch_json('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',{
        'db':'pubmed','term':'pascoe b[au]','retmode':'json','retmax':500,'sort':'pub_date'
    })
    ids=search.get('esearchresult',{}).get('idlist',[])
    if not ids:return []
    xml=fetch_text('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi',{
        'db':'pubmed','id':','.join(ids),'retmode':'xml'
    })
    root=ET.fromstring(xml); out=[]
    for art in root.findall('.//PubmedArticle'):
        med=art.find('./MedlineCitation'); article=med.find('./Article') if med is not None else None
        if article is None:continue
        title=xml_text(article.find('./ArticleTitle'))
        pmid=xml_text(med.find('./PMID'))
        authors=[]; aff=[]
        for a in article.findall('./AuthorList/Author'):
            collective=xml_text(a.find('./CollectiveName'))
            if collective:authors.append(collective)
            else:
                name=' '.join(x for x in [xml_text(a.find('./LastName')),xml_text(a.find('./Initials'))] if x)
                if name:authors.append(name)
            aff.extend(xml_text(x) for x in a.findall('./AffiliationInfo/Affiliation') if xml_text(x))
        journal=xml_text(article.find('./Journal/Title')) or xml_text(article.find('./Journal/ISOAbbreviation'))
        volume=xml_text(article.find('./Journal/JournalIssue/Volume'))
        issue=xml_text(article.find('./Journal/JournalIssue/Issue'))
        pages=xml_text(article.find('./Pagination/MedlinePgn'))
        if not pages:
            pages=xml_text(article.find('./ELocationID'))
        ad=article.find('./ArticleDate')
        pd=article.find('./Journal/JournalIssue/PubDate')
        year=xml_text(ad.find('./Year')) if ad is not None else ''
        month=xml_text(ad.find('./Month')) if ad is not None else ''
        day=xml_text(ad.find('./Day')) if ad is not None else ''
        if not year and pd is not None:
            year=xml_text(pd.find('./Year'))
            month=xml_text(pd.find('./Month'))
            day=xml_text(pd.find('./Day'))
            if not year:
                medline=xml_text(pd.find('./MedlineDate'))
                m=re.search(r'(19|20)\d{2}',medline); year=m.group(0) if m else ''
        date=f"{year or '1900'}-{month_num(month)}-{int(day or 1):02d}"
        doi=''
        for aid in art.findall('./PubmedData/ArticleIdList/ArticleId'):
            if aid.attrib.get('IdType')=='doi':doi=clean_doi(xml_text(aid));break
        types=[xml_text(x) for x in article.findall('./PublicationTypeList/PublicationType')]
        out.append({'title':title,'title_norm':norm(title),'pmid':pmid,'doi':doi,'authors':', '.join(authors),
                    'journal':journal,'volume':volume,'issue':issue,'pages':pages,'publishedDate':date,
                    'year':int(year) if year.isdigit() else None,'affiliations':' | '.join(aff),'publication_types':types})
    return out

def best_pubmed(title, records):
    n=norm(title)
    exact=[r for r in records if r['title_norm']==n]
    if exact:return exact[0]
    best=None;score=0
    for r in records:
        s=SequenceMatcher(None,n,r['title_norm']).ratio()
        if s>score:score=s;best=r
    return best if score>=0.94 else None

def is_preprint(article):
    text=(article.get('publication','')+' '+article.get('title','')).lower()
    return any(x in text for x in ('biorxiv','medrxiv','research square','ssrn','arxiv','preprint'))

def theme_for(title, old=None):
    if old and old.get('themeId'):return old['themeId']
    t=title.lower()
    if any(x in t for x in ('predict','machine learning','association study','gwas','source attribution')):return 'prediction'
    if any(x in t for x in ('protocol','surveillance','typing','lin code','nomenclature','workflow','genome data')):return 'tools'
    if any(x in t for x in ('transmission','outbreak','epidemiology','spread','carriage','source')):return 'transmission'
    return 'evolution'

THEMES={'transmission':'Transmission across One Health systems','evolution':'Evolution and host adaptation',
        'tools':'Open genomic tools and surveillance','prediction':'Genomics, AI and disease prediction'}


# Controlled publication tags. Existing manually curated tags are retained and
# inferred tags are added from titles, citations and explicit project fields.
def ordered_unique(items):
    seen=set(); result=[]
    for item in items:
        if item and item not in seen:
            seen.add(item); result.append(item)
    return result

ORGANISM_RULES=[
 ('Campylobacter',('campylobacter','c jejuni','c coli','c concisus')),
 ('Salmonella',('salmonella',)),('Acinetobacter',('acinetobacter',)),
 ('Staphylococcus',('staphylococcus','methicillin resistant staphylococcus','methicillin sensitive staphylococcus')),
 ('Helicobacter',('helicobacter','h pylori')),('Shigella',('shigella',)),
 ('Escherichia coli',('escherichia coli','avian escherichia','mcr 1 genes and plasmids')),
 ('Mycoplasma',('mycoplasma',)),('Yersinia',('yersinia',)),('Streptococcus',('streptococcus',)),
 ('Listeria',('listeria',)),('Bacillus',('bacillus',)),('Pseudomonas',('pseudomonas',)),
 ('Enterobacter',('enterobacter species',)),('Renibacterium',('renibacterium',)),
 ('Streptomyces',('streptomyces',)),('Klebsiella',('klebsiella',)),('Oropouche virus',('oropouche',))]
TOPIC_RULES=[
 ('AMR',('antimicrobial resistance','antibiotic resistance','drug resistance','multidrug resistant','multidrug resistance','resistant determinants','resistance genes','resistance to','mcr 1','esbl','colistin','ciprofloxacin','azithromycin','clarithromycin','erythromycin','chloramphenicol','methicillin resistant','methicillin sensitive')),
 ('One Health',('one health','farm to fork','livestock','poultry','pig farms','swine','wild bird','wildlife','animal and human','pork production','broiler farms','slaughterhouses','multi host')),
 ('Transmission',('transmission','spread','outbreak','zooanthroponosis','host switching','land sea transfer','farm to fork','gene pool transmission')),
 ('Source attribution',('source attribution','tracing human infections','host segregating','isolation source','source of campylobacter','predict colonisation')),
 ('Surveillance',('surveillance','monitoring','genomic epidemiology','molecular epidemiology','typing','genome project','geographical distribution')),
 ('Evolution',('evolution','adaptation','selection','domestication','introgression','diversification','allopatry','co evolution','pathoadaptive','fitness costs')),
 ('Recombination',('recombination','horizontal gene transfer','gene sharing','allele sharing')),
 ('Population genomics',('population genomics','comparative genomics','population structure','genome wide','genomic analysis','genomic insights','pan genome','pangenome','core genome')),
 ('Machine learning',('machine learning','probabilistic inference','bayesian identification','bayesian belief network')),
 ('Metagenomics',('metagenomics','microbiome','sweep metagenomics')),('Vaccines',('vaccine','vaccines')),
 ('Biofilms',('biofilm','biofilms')),('Diagnostics',('assay','detection','qpcr','serotyping','primer probe','diagnostic')),
 ('Virulence and disease',('virulence','pathogenicity','disease association','patient outcome','poor patient outcomes','irritable bowel syndrome','gastric cancer risk','diarrheal manifestation')),
 ('Environmental microbiology',('water cycle','wastewater','environmental bacteria','sewage','environmental risk'))]
GEO_RULES=[('The Gambia',('the gambia','gambia')),('Peru',('peru','peruvian','iquitos','amazon')),
 ('Thailand',('thailand','thai','chiang mai')),('Egypt',('egypt','egyptian')),('India',('india','indian')),
 ('United States',('united states','american black bear')),('United Kingdom',('united kingdom',)),
 ('China',('china','chinese')),('Brazil',('brazil',)),('Chile',('chile','chilean')),
 ('Africa',('across africa','out of africa','africa')),('Americas',('americas',)),('Global',('global','worldwide'))]
PROJECT_FIELD_MAP={'enteric disease in africa':['GETcampy-Africa','Campylobacter Control Campaign'],
 'peru':['Peru'],'peru and childhood enteric disease':['Peru'],'hu rizon':['HU-RIZON'],
 'thailand and poultry systems':['Thailand']}
PROJECT_TITLE_RULES=[
 ('GETcampy-Africa',('protocols for genomic epidemiology and source attribution of enteric bacteria causing diarrhoeal disease across africa',)),
 ('Campylobacter Control Campaign',('protocols for genomic epidemiology and source attribution of enteric bacteria causing diarrhoeal disease across africa','using a bayesian belief network to explore public health interventions in the gambia')),
 ('Peru',('peruvian amazon','iquitos peru','in peru','paediatric infection in the peruvian amazon','childhood growth','diarrheal manifestation')),
 ('Thailand',('thailand','thai pork','northern thailand','chiang mai')),
 ('HU-RIZON',('proximity to humans is associated with antimicrobial resistant enteric pathogens in wild bird microbiomes',)),
 ('CRAB Eastern Europe',('carbapenem resistance phenotypes are heterogeneous','eastern europe'))]

def apply_tags(p):
    text=norm(' '.join(str(p.get(k,'')) for k in ('title','citation','summary','journal','project')))
    organisms=list(p.get('organisms') or [])
    for label,terms in ORGANISM_RULES:
        if any(norm(term) in text for term in terms):organisms.append(label)
    if 'protocols for genomic epidemiology and source attribution of enteric bacteria causing diarrhoeal disease across africa' in text:
        organisms += ['Campylobacter','Salmonella','Shigella','Escherichia coli']
    topics=list(p.get('topics') or [])
    for label,terms in TOPIC_RULES:
        if any(norm(term) in text for term in terms):topics.append(label)
    if not topics:topics.append('Population genomics')
    projects=list(p.get('projects') or [])
    projects += PROJECT_FIELD_MAP.get(norm(p.get('project','')),[])
    for label,terms in PROJECT_TITLE_RULES:
        if any(norm(term) in text for term in terms):projects.append(label)
    geographies=list(p.get('geographies') or [])
    for label,terms in GEO_RULES:
        if any(norm(term) in text for term in terms):geographies.append(label)
    p['organisms']=ordered_unique(organisms);p['topics']=ordered_unique(topics)
    p['projects']=ordered_unique(projects);p['geographies']=ordered_unique(geographies)
    return p
existing=json.loads(PUB_FILE.read_text())
by_doi={clean_doi(p.get('doi')):p for p in existing if clean_doi(p.get('doi'))}
by_title={norm(p.get('title')):p for p in existing}
scholar,cited_by=scholar_pages(); pubmed=pubmed_records()
merged=[];seen=set();review=[]
for a in scholar:
    title=(a.get('title') or '').strip()
    if not title:continue
    pm=best_pubmed(title,pubmed)
    old=by_title.get(norm(title))
    if not old and pm and pm.get('doi'):old=by_doi.get(pm['doi'])
    pre=is_preprint(a) or (old and old.get('publicationType')=='preprint')
    if not old and not pm and not pre:
        review.append({'title':title,'authors':a.get('authors'),'publication':a.get('publication'),
                       'year':a.get('year'),'reason':'Not matched to PubMed and not clearly a preprint'})
        continue
    p=dict(old or {})
    p['title']=pm['title'] if pm else title
    p['authors']=pm['authors'] if pm and pm.get('authors') else a.get('authors','')
    p['year']=pm.get('year') if pm and pm.get('year') else int(a.get('year') or p.get('year') or 0)
    p['publishedDate']=pm.get('publishedDate') if pm else p.get('publishedDate',f"{p['year']:04d}-01-01")
    p['doi']=pm.get('doi') if pm and pm.get('doi') else clean_doi(p.get('doi'))
    p['pmid']=pm.get('pmid') if pm else p.get('pmid','')
    p['journal']=pm.get('journal') if pm and pm.get('journal') else p.get('journal') or a.get('publication','')
    p['scholarCitationId']=a.get('citation_id','')
    p['scholarUrl']=a.get('link','')
    p['publicationType']='preprint' if pre else 'journal'
    p['status']=p.get('status') if p.get('status')=='in press' else ('preprint' if pre else 'published')
    p['type']='preprint' if pre else 'publication'
    p.setdefault('selected',False);p.setdefault('featuredHome',False)
    tid=theme_for(p['title'],old);p['themeId']=tid;p['theme']=THEMES[tid]
    p.setdefault('summary','')
    if not p.get('id'):
        p['id']=str(p['year'])+'-'+re.sub(r'[^a-z0-9]+','-',norm(p['title'])).strip('-')[:80]
    if pm:
        vol=pm.get('volume','');iss=pm.get('issue','');pages=pm.get('pages','')
        vi=vol+(f'({iss})' if iss else '')
        tail=' '.join(x for x in [pm.get('journal',''),vi,(':'+pages if pages and vi else pages)] if x).replace(' :',':')
        p['citation']=f"{p['authors']} ({p['year']}) {p['title']}. {tail}."+(f" doi: {p['doi']}" if p.get('doi') else '')
    else:
        p.setdefault('citation',f"{p['authors']} ({p['year']}) {p['title']}. {a.get('publication','')}")
    key=p.get('doi') or norm(p['title'])
    if key in seen:continue
    seen.add(key);merged.append(p)
# Retain manually curated records not returned by Scholar (e.g. in press), without duplicating.
for p in existing:
    key=clean_doi(p.get('doi')) or norm(p.get('title'))
    if key not in seen:
        p.setdefault('publishedDate',f"{int(p.get('year',1900)):04d}-01-01")
        merged.append(p);seen.add(key)
for p in merged:apply_tags(p)
merged.sort(key=lambda p:(p.get('publishedDate',''),p.get('title','').lower()),reverse=True)
PUB_FILE.write_text(json.dumps(merged,ensure_ascii=False,indent=2)+'\n')

def metric(name):
    for row in cited_by.get('table',[]):
        if name in row:
            value=row[name];return value.get('all') if isinstance(value,dict) else value
    return None
metrics={'source':'Google Scholar','author_id':AUTHOR_ID,
         'profile_url':f'https://scholar.google.com/citations?user={AUTHOR_ID}&hl=en',
         'updated_at':datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
         'citations':metric('citations'),'h_index':metric('h_index'),'i10_index':metric('i10_index')}
METRIC_FILE.write_text(json.dumps(metrics,indent=2)+'\n')
SYNC_FILE.write_text(json.dumps({'updated_at':metrics['updated_at'],'scholar_records':len(scholar),
     'pubmed_records_examined':len(pubmed),'site_records':len(merged),'review':review},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'site_records':len(merged),'review':len(review),**metrics},indent=2))
