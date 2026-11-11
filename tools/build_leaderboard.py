"""Generate cohort-separated leaderboard data and source-bound JSON-LD."""
from pathlib import Path
import argparse
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'
SITE='https://paloframework.org/'
OVERVIEW=SITE+'PALO_BlueprintBench.html'
BOARD=SITE+'PALO_BlueprintBench_Leaderboard.html'
SOURCE_REVISION='c85624939bde546d67f3869c656cfb8b97b7ae00'
EVIDENCE='https://github.com/sev7enITA/PALO-BlueprintBench/tree/'+SOURCE_REVISION+'/internal_tests/2026-11-11-frontier'


def read(p):return json.loads(p.read_bytes().decode('utf-8'))


def dataset_graph(data,url):
    internal=data['internal'];historical=data['historical']
    person=SITE+'PALO_Community.html#creator'
    internal_id=OVERVIEW+'#internal-procurement-dataset'
    historical_id=OVERVIEW+'#historical-adapter-dataset'
    description=(f"Internal tests on {internal['cases']} short synthetic procurement cases from one maintainer-authored family. "
                 f"{len(internal['models'])} API configurations, {internal['repetitions']} repetitions, {internal['assigned_calls']} assigned requests: "
                 f"{internal['completed_calls']} complete responses and {internal['failed_calls']} provider failure. "
                 f"{internal['source_rules']} source rules and {internal['verification_probes']} seeded statements. "
                 "Agreement with assistant-draft labels; one contested label; failed assignments remain in the denominator. "
                 "No independently qualified results, model ranking or PALO Blueprint Index. Post-hoc sensitivity and scoring replay are explicitly labelled.")
    page_description=('Explore internal procurement tests and historical adapter diagnostics in separate cohorts. '
                      'Inspect configurations, source evidence, missing responses and disputed labels. No independently qualified ranking.')
    graph=[{'@type':'Person','@id':person,'name':'Fabrizio Degni','url':person},
           {'@type':'WebSite','@id':SITE+'#website','name':'PALO Framework','url':SITE,'publisher':{'@id':person}},
           {'@type':'CollectionPage','@id':url+'#webpage','url':url,'name':'PALO BlueprintBench Leaderboard' if url==BOARD else 'PALO BlueprintBench | Specification Fidelity',
            'description':page_description,'inLanguage':'en','dateModified':data['as_of'],'isAccessibleForFree':True,
            'isPartOf':{'@id':SITE+'#website'},'author':{'@id':person},'breadcrumb':{'@id':url+'#breadcrumb'},
            'mainEntity':[{'@id':internal_id},{'@id':historical_id}],
            'hasPart':[{'@id':internal_id},{'@id':historical_id}],
            'creativeWorkStatus':'Research programme; internal tests; independent validation pending'},
           {'@type':'BreadcrumbList','@id':url+'#breadcrumb','itemListElement':[
               {'@type':'ListItem','position':1,'name':'PALO Framework','item':SITE+'index.html'},
               {'@type':'ListItem','position':2,'name':'PALO BlueprintBench','item':OVERVIEW}]+([
               {'@type':'ListItem','position':3,'name':'Leaderboard','item':BOARD}] if url==BOARD else [])},
           {'@type':'Dataset','@id':internal_id,'name':'BlueprintBench internal procurement baseline tests, 11 November 2026',
            'identifier':internal['campaign_id'],'version':data['version'],'url':OVERVIEW+'#internal-tests','description':description,
            'creator':{'@id':person},'datePublished':data['as_of'],'dateModified':data['as_of'],'temporalCoverage':data['as_of'],
            'isAccessibleForFree':True,'creativeWorkStatus':'Internal tests; assistant-draft labels; not independently validated',
            'measurementTechnique':'Source-indexed translation and seeded-statement verification, three repetitions; fixed assigned denominators. Frozen primary labels and separate post-hoc sensitivity analysis. No confidence interval or model quality ordering.',
            'variableMeasured':['Agreement with assistant-draft labels over assigned statements','Missing and conflicting classifications','Request completion over assigned requests','Provider-reported inference charges, with unknown charges separate','Observed request latency in seconds; not a throughput comparison','Source-indexed draft translation coverage and verbatim-copy counts'],
            'about':[{'@type':'Thing','name':'Specification fidelity in synthetic procurement'}]+[{'@type':'Thing','name':m['name'],'identifier':m['id']} for m in internal['models']],
            'isBasedOn':EVIDENCE+'/manifest.json',
            'usageInfo':EVIDENCE+'/README.md',
            'distribution':[{'@type':'DataDownload','name':'Internal test counts, configurations and limitations','contentUrl':SITE+'downloads/blueprintbench/internal-tests-results.json','encodingFormat':'application/json'},
                            {'@type':'DataDownload','name':'Frozen design, public responses and post-hoc replay evidence','contentUrl':SITE+'downloads/blueprintbench/internal-tests-evidence.zip','encodingFormat':'application/zip'}]},
           {'@type':'Dataset','@id':historical_id,'name':'BlueprintBench historical adapter smoke tests, 10 November 2026',
            'identifier':'challenger-expanded-adapter-smoke-tests-20261110','version':historical['content_revision'],'url':OVERVIEW+'#explorer',
            'description':f"{len(historical['models'])} historical configurations assigned to three passages containing 4,994 UTF-8 bytes of document text. Structural PALO-contract diagnostics only, differing reasoning and quantisation, no repetitions or independent semantic gold. All 43 proposed relations failed checks; these observations are not a model capability ranking. Cost totals remain unreconciled.",
            'creator':{'@id':person},'dateModified':data['as_of'],'temporalCoverage':historical['measurement_date'],'isAccessibleForFree':True,
            'creativeWorkStatus':'Historical development diagnostics; unqualified',
            'measurementTechnique':historical['metric_notes']['structural_acceptance'],
            'variableMeasured':['Proposed and structurally accepted candidates by type','Assigned, completed and not-run adapter requests'],
            'distribution':[{'@type':'DataDownload','name':'Historical diagnostic records and limitations','contentUrl':SITE+'assets/blueprintbench/explorer-data.json','encodingFormat':'application/json'}]}]
    return {'@context':'https://schema.org','@graph':graph}


def outputs():
    base=ROOT/'internal_tests/2026-11-11-frontier'
    internal=read(WEB/'downloads/blueprintbench/internal-tests-results.json')
    assert internal['qualified'] is False and internal['status']=='internal_tests'
    internal['configurations']=read(base/'models.json')
    internal['records']=[read(p) for p in sorted((base/'runs').glob('*/record.json'))]
    examples=[]
    for p in sorted((base/'contract-replay').glob('*/*/blueprint.json')):
        b=read(p)
        for r in b['rules']:
            examples.append(dict(model=b['model'],case=b['case'],repetition=b['repetition'],source_id=r['id'],
                source_text=r['source_text'],proposed_specification=r['proposed_specification'],verbatim=r['source_text']==r['proposed_specification'],
                evidence_path=p.relative_to(base).as_posix()))
    assert len(examples)==324
    internal['translation_examples']=examples
    data={'version':'2026-11-11.1','as_of':'2026-11-11','qualified_count':0,'internal':internal,
          'historical':read(WEB/'assets/blueprintbench/explorer-data.json'),'evidence_base':EVIDENCE,
          'qualification_gates':[{'name':n,'state':'pending'} for n in ['Named independent custodian','Independent domain annotations and adjudication','Validated severity and error-detection measure','Independent reproduction']]}
    out={WEB/'downloads/blueprintbench/leaderboard-data.json':(json.dumps(data,indent=2)+'\n').encode()}
    for name,url in [('PALO_BlueprintBench.html',OVERVIEW),('PALO_BlueprintBench_Leaderboard.html',BOARD)]:
        path=WEB/name
        if not path.exists():continue
        html=path.read_text(encoding='utf-8')
        encoded=json.dumps(dataset_graph(data,url),separators=(',',':'),ensure_ascii=False).replace('<','\\u003c')
        pattern=r'<script[^>]*type="application/ld\+json"[^>]*>.*?</script>'
        assert len(re.findall(pattern,html,re.S))==1,name
        html=re.sub(pattern,lambda _: '<script type="application/ld+json">'+encoded+'</script>',html,flags=re.S)
        out[path]=html.encode()
    return out


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    changes=[]
    for p,body in outputs().items():
        if args.check:
            if not p.exists() or p.read_bytes()!=body:changes.append(str(p.relative_to(ROOT)))
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
    if changes:raise SystemExit('Leaderboard data/schema drift: '+', '.join(changes))
    print('Leaderboard data and JSON-LD '+('verified' if args.check else 'built'))
