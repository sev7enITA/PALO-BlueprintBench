"""Generate cohort-separated leaderboard data and source-bound JSON-LD."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import build_expansion

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'
SITE='https://paloframework.org/'
OVERVIEW=SITE+'PALO_BlueprintBench.html'
BOARD=SITE+'PALO_BlueprintBench_Leaderboard.html'
SOURCE_REVISION='c85624939bde546d67f3869c656cfb8b97b7ae00'
EVIDENCE='https://github.com/sev7enITA/PALO-BlueprintBench/tree/'+SOURCE_REVISION+'/internal_tests/2026-11-11-frontier'
EXPANSION_REVISION='2b054692baea4ca1a892e3d39453a76097a64f74'


def read(p):return json.loads(p.read_bytes().decode('utf-8'))


def internal_report(data):
    d=data['internal']
    report=f'''# Internal procurement tests and model catalogue

Revision {data['version']}. Internal tests; independent qualification pending.

Both the [launch page]({OVERVIEW}) and [leaderboard]({BOARD}) use this evidence dataset. The internal view contains **{len(d['models'])} distinct model IDs**, with the original ten historical identities preserved in a separate adapter-diagnostics view. A model with two evidence cohorts has two configuration rows; they are not two different models.

## Execution scope

Three short synthetic procurement cases, one maintainer-authored family, 36 source rules, 108 seeded statements, two tasks and three repetitions. Source, prompt and draft expected-label bytes are unchanged across all campaigns. **{d['assigned_calls']} assigned task slots; {d['attempted_calls']} dispatched requests; {d['completed_calls']} complete responses; {d['failed_calls']} failed or incomplete responses; {d['not_run']} unrun assignments**, including {d['precall_blocked_assignments']} compatibility blocks. Failures and missing assignments remain in the fixed denominator.

| Configuration | Complete / assigned calls | Draft-label matches / assigned | Missing classifications | Known inference USD | Unknown charges | Unrun assignments |
|---|---:|---:|---:|---:|---:|---:|
'''
    for m in sorted(d['models'],key=lambda m:m['name']):
        report+=f"| {m['name']} | {m['completed_calls']}/{m['assigned_calls']} | {m['verification_correct']}/324 | {m['verification_missing']} | {m['provider_reported_cost_usd']:.7f} | {m['unknown_cost_calls']} | {m['not_run']} |\n"
    report+='''
These counts measure agreement with assistant-draft labels and delivery under each serving configuration. They are not independently adjudicated accuracy or a qualified model ranking. The primary label for invoice P002 remains contested; the optional post-hoc sensitivity excludes it uniformly across every model and repetition. Missing classifications are not assumed wrong semantic judgments.

## Compatibility and configuration

Sakana Fugu Max is catalogued with no supported max_tokens or response_format controls. Under the frozen strict-parameter, bounded-output policy its supplement assignments are blocked before dispatch. Zero request charge is explicitly not_incurred; latency and semantic output are unavailable. Its original historical transport failures remain preserved. This does not establish model incapability.

Schematron Small and Turbo use an advertised 8,192-token output cap and have no reasoning control. Other runnable configurations use 32,768. Supported high reasoning is used where offered, xhigh for Bonsai27B where high is unavailable, and enabled reasoning for endpoints without effort enums. Provider/quantisation/reasoning differences are retained in the metadata. High effort is not equal compute. Temperature is provider default and seed omitted. Endpoint fallback and inference retries are disabled.

The original baseline ran serially. The later extensions use up to four concurrent requests. Observed request duration includes network and provider scheduling; it is not a controlled speed comparison. The extensions were selected after baseline outcomes were known and retain separate campaign identities.

## Source-indexed translations

The original three-model baseline has 27 assistant-reviewed draft exports. The new extensions preserve source-indexed raw outputs as unreviewed model drafts; no prior review, business approval or blueprint-export result is inherited. Exact source-copy counts and source/output inspection are descriptive. A wording change is not automatically an improvement.

## Cost and limits

'''
    report+=f"Known provider-reported charges in the internal dataset total USD {sum(m['provider_reported_cost_usd'] for m in d['models']):.7f}. There are {d['unknown_cost_calls']} unknown-charge records carrying USD {d['unknown_cost_reserved_usd']:.7f} in conservative reservations. Reservations are not charges. The overall user-authorised ceiling remains USD40 including prior work and advisory reviews; this dataset's inference cost is not the full key spend. No paid retrieval, embeddings, tools or search were requested. Engineering, review, electricity and hosting costs are not measured.\n\n"
    report+='''One synthetic authoring family, assistant-draft labels, unreviewed new translations and differing serving configurations limit interpretation. No independent custodian, blind domain annotation or independent reproduction is claimed. No PALO Blueprint Index is assigned. Detailed limitations remain in the research interface and method document.

## Reproduce and inspect

Run `python tools/build_leaderboard.py --check` and `python -m unittest discover -s tools -p test_leaderboard_schema.py` after installing evaluator requirements. These are offline checks; they do not make paid model calls. The raw successful responses, exact outputs, frozen inputs and request hashes are in the campaign archives. Public error bodies with account identifiers are explicitly redacted with original/public hashes. Hash consistency is not independent custody.

'''
    for c in d['campaigns']:
        report+=f"- [{c['id']}]({c['evidence_base']}): {c['models']} models, {c['assigned_calls']} assigned tasks; {c['design']}.\n"
    return report


def dataset_graph(data,url):
    internal=data['internal'];historical=data['historical']
    person=SITE+'PALO_Community.html#creator'
    internal_id=OVERVIEW+'#internal-procurement-dataset'
    historical_id=OVERVIEW+'#historical-adapter-dataset'
    description=(f"Internal tests on {internal['cases']} short synthetic procurement cases from one maintainer-authored family. "
                 f"{len(internal['models'])} API configurations, {internal['repetitions']} repetitions, {internal['assigned_calls']} assigned requests: "
                 f"{internal['completed_calls']} complete responses, {internal['failed_calls']} failed requests and {internal['not_run']} unrun assignments. "
                 f"{internal['source_rules']} source rules and {internal['verification_probes']} seeded statements. "
                 "Agreement with assistant-draft labels; one contested label; failed assignments remain in the denominator. "
                 "The original baseline and later extensions retain their campaign identities. No independently qualified results or PALO Blueprint Index. Post-hoc sensitivity is explicitly labelled; translations remain assistant-draft outputs; a selected sample has separate internal model reviews.")
    page_description=('Explore internal procurement tests and historical adapter diagnostics in separate cohorts. '
                      'Explore metric-specific internal-test ranks, developer-country filters and sortable KPIs in the leaderboard, with filtered CSV and JSON exports. Inspect configurations, source evidence, missing responses and disputed labels. No independently qualified ranking.')
    graph=[{'@type':'Person','@id':person,'name':'Fabrizio Degni','url':person},
           {'@type':'WebSite','@id':SITE+'#website','name':'PALO Framework','url':SITE,'publisher':{'@id':person}},
           {'@type':'CollectionPage','@id':url+'#webpage','url':url,'name':'PALO BlueprintBench Leaderboard' if url==BOARD else 'PALO BlueprintBench | Results and Method',
            'image':{'@id':OVERVIEW+'#benchmark-logo'},'description':page_description,'inLanguage':'en','dateModified':data['as_of'],'isAccessibleForFree':True,
            'isPartOf':{'@id':SITE+'#website'},'author':{'@id':person},'breadcrumb':{'@id':url+'#breadcrumb'},
            'mainEntity':[{'@id':internal_id},{'@id':historical_id}],
            'hasPart':[{'@id':internal_id},{'@id':historical_id}],
            'creativeWorkStatus':'Research programme; internal tests; independent validation pending'},
           {'@type':'BreadcrumbList','@id':url+'#breadcrumb','itemListElement':[
               {'@type':'ListItem','position':1,'name':'PALO Framework','item':SITE+'index.html'},
               {'@type':'ListItem','position':2,'name':'PALO BlueprintBench','item':OVERVIEW}]+([
               {'@type':'ListItem','position':3,'name':'Leaderboard','item':BOARD}] if url==BOARD else [])},
           {'@type':'Dataset','@id':internal_id,'name':'BlueprintBench internal procurement tests and extensions, 11 November 2026',
            'identifier':internal['campaign_id'],'version':data['version'],'url':BOARD+'?cohort=internal','description':description,
            'creator':{'@id':person},'datePublished':data['as_of'],'dateModified':data['as_of'],'temporalCoverage':data['as_of'],
            'isAccessibleForFree':True,'creativeWorkStatus':'Internal tests; assistant-draft labels; not independently validated',
            'measurementTechnique':'Source-indexed translation and seeded-statement verification, three repetitions; fixed assigned denominators. Frozen primary labels and separate post-hoc sensitivity analysis. Metric-specific exploratory ranks use unrounded values and competition ties within the eligible internal cohort; visibility filters do not renumber them. No confidence interval or qualified model quality ranking.',
            'variableMeasured':['Agreement with assistant-draft labels over assigned statements','Missing and conflicting classifications','Request completion over assigned requests','Provider-reported inference charges, with unknown charges separate','Observed request latency in seconds; not a throughput comparison','Source-indexed draft translation coverage and verbatim-copy counts','Recorded verification-request start times in UTC; collection order, not model release or longitudinal progress'],
            'about':[{'@type':'Thing','name':'Specification fidelity in synthetic procurement'}]+[{'@type':'Thing','name':m['name'],'identifier':m['id']} for m in internal['models']],
            'isBasedOn':[c['evidence_base']+'/manifest.json' for c in internal['campaigns']],
            'usageInfo':EVIDENCE+'/README.md',
            'distribution':[{'@type':'DataDownload','name':'All internal counts, configurations and limitations','contentUrl':SITE+'downloads/blueprintbench/leaderboard-data.json','encodingFormat':'application/json'},
                            {'@type':'DataDownload','name':'Original baseline evidence and post-hoc replay','contentUrl':SITE+'downloads/blueprintbench/internal-tests-evidence.zip','encodingFormat':'application/zip'},
                            {'@type':'DataDownload','name':'Additional model campaign evidence','contentUrl':SITE+'downloads/blueprintbench/internal-expansion-evidence.zip','encodingFormat':'application/zip'}]},
           {'@type':'Dataset','@id':historical_id,'name':'BlueprintBench historical adapter smoke tests, 10 November 2026',
            'identifier':'challenger-expanded-adapter-smoke-tests-20261110','version':historical['content_revision'],'url':OVERVIEW+'#explorer',
            'description':f"{len(historical['models'])} historical configurations assigned to three passages containing 4,994 UTF-8 bytes of document text. Structural PALO-contract diagnostics only, differing reasoning and quantisation, no repetitions or independent semantic gold. All 43 proposed relations failed checks; these observations are not a model capability ranking. Cost totals remain unreconciled.",
            'creator':{'@id':person},'dateModified':data['as_of'],'temporalCoverage':historical['measurement_date'],'isAccessibleForFree':True,
            'creativeWorkStatus':'Historical development diagnostics; unqualified',
            'measurementTechnique':historical['metric_notes']['structural_acceptance'],
            'variableMeasured':['Proposed and structurally accepted candidates by type','Assigned, completed and not-run adapter requests'],
            'distribution':[{'@type':'DataDownload','name':'Historical diagnostic records and limitations','contentUrl':SITE+'assets/blueprintbench/explorer-data.json','encodingFormat':'application/json'}]}]
    adversarial_path=WEB/'downloads/blueprintbench/adversarial-tests.json'
    if adversarial_path.exists():
        review=read(adversarial_path);summary=review['summary'];review_id=OVERVIEW+'#adversarial-dataset'
        graph[2]['mainEntity'].append({'@id':review_id});graph[2]['hasPart'].append({'@id':review_id})
        graph.append({'@type':'Dataset','@id':review_id,'name':'BlueprintBench internal adversarial cross-model review',
            'identifier':review['version'],'version':review['version'],'url':BOARD+'#adversarial-review',
            'description':f"Internal purposive countertest: {summary['items']} selected items, {summary['assigned_review_records']} assigned judgments, {summary['valid_review_records']} usable record-level judgments and {summary['missing_review_records']} missing. {summary['unanimous']} items with three-way agreement, {summary['divergent']} decisive three-way divergences, {summary['uncertain']} uncertain and {summary['incomplete']} incomplete. GLM, Gemini and local Qwen are automated reviewers with model-family overlap. Qwen requires a disclosed structural projection on 36 records; its raw envelope passes 0 of 3 batches. Primary scores are unchanged. Not independent validation.",
            'creator':{'@id':person},'datePublished':data['as_of'],'dateModified':data['as_of'],'isAccessibleForFree':True,
            'creativeWorkStatus':'Internal tests; not independently validated',
            'measurementTechnique':'Frozen purposive sample, authors and prior labels withheld from reviewers. One pass per case, missing responses retained. Agreement is not correctness; post-hoc format projection is reported separately.',
            'variableMeasured':['Reviewer agreement, divergence, uncertainty and missing judgments','Raw response-envelope compliance','Selected-probe replay against each reviewer, with 54 assigned slots per original model'],
            'isBasedOn':review['protocol_url'],
            'distribution':[{'@type':'DataDownload','name':'Internal cross-model judgments and evidence links','contentUrl':SITE+'downloads/blueprintbench/adversarial-tests.json','encodingFormat':'application/json'}]})
    # Country provenance is a dated metadata overlay, not a measurement result.
    origins = read(WEB/'downloads/blueprintbench/model-origins.json')
    country_id = OVERVIEW+'#developer-country-metadata'
    workspace_id = BOARD+'#results-workspace'
    kpis = [
        ('matches', 'Draft-label agreement', 'ratio', 'Matched statements divided by all assigned statements in the selected case, dimension and label lens. Missing assignments remain in the denominator; agreement is not independent semantic accuracy.'),
        ('coverage', 'Classification coverage', 'ratio', 'Classified statements divided by assigned statements in the selected semantic scope.'),
        ('disagreements', 'Draft-label disagreements', 'statements', 'Classified statements disagreeing with the draft label. Ranking minimises their assigned-denominator ratio and requires complete classification in the selected scope.'),
        ('missing', 'Missing classifications', 'statements', 'Assigned statements without a classification, including unrun assignments. Ranking minimises the assigned-denominator ratio.'),
        ('calls', 'Call completion', 'ratio', 'Complete calls divided by all assigned calls across both tasks and all cases, independently of semantic filters.'),
        ('cost', 'Provider-reported charges', 'USD', 'Recorded provider charges across both tasks and all cases. Unknown charges remain separate. Charge ranking requires all assigned calls to complete and complete accounting.'),
        ('time', 'Median request time', 'seconds', 'Observed median request duration across both tasks and all cases. Time ranking requires all assigned calls to complete; this is not a controlled throughput comparison.'),
        ('costpercall', 'Cost per complete call', 'USD per call', 'Provider-reported charges divided by completed calls, available only when all assigned calls complete and accounting is complete.'),
        ('input', 'Input tokens', 'tokens', 'Reported prompt-token total across dispatched calls in both tasks and all cases; unavailable if any dispatched call lacks the value.'),
        ('output', 'Completion tokens including reasoning', 'tokens', 'Reported completion-token total, including reasoning where reported in that total, across dispatched calls in both tasks and all cases; unavailable if any value is missing.'),
        ('rank', 'Exploratory metric rank', 'ordinal position', 'Derived within the eligible internal cohort for the selected metric and semantic scope. Unrounded values and competition ties (1, 1, 3); visibility filters do not renumber positions. Blocked configurations are unranked. No PALO Blueprint Index or independent qualification.')
    ]
    measured = next(n for n in graph if n.get('@id') == internal_id)
    measured['variableMeasured'] = [
        {'@type':'PropertyValue','propertyID':key,'name':name,'description':description,'unitText':unit}
        for key,name,unit,description in kpis
    ] + measured['variableMeasured'][5:]
    measured['usageInfo'] = [EVIDENCE+'/README.md', BOARD+'#workspace', BOARD+'#limitations']
    graph.append({
        '@type':'Dataset','@id':country_id,'name':'BlueprintBench developer-organisation country source register',
        'identifier':origins['version'],'version':origins['version'],'dateModified':origins['as_of'],
        'url':BOARD+'#workspace','creator':{'@id':person},'isAccessibleForFree':True,
        'description':origins['definition'],
        'creativeWorkStatus':'Dated source metadata; internal tests not independently validated',
        'measurementTechnique':'Official-source review with per-organisation attribution basis and retrieval date. Unknown attribution has no country assertion. This overlay does not change frozen campaign evidence.',
        'variableMeasured':['Documented developer business-base country','Country attribution status and source provenance'],
        'about':[
            dict({'@type':'Organization','name':m['name'],'identifier':m['id'],'description':m['basis'],
                  'subjectOf':[{'@type':'WebPage','url':source['url'],'name':source['title']} for source in m['sources']]},
                 **({'location':[{'@type':'Country','identifier':c['code'],'name':c['name']} for c in m['countries']]} if m['status']=='verified' else {}))
            for m in origins['makers']
        ],
        'distribution':[{'@type':'DataDownload','name':'Developer-country source register','contentUrl':SITE+'downloads/blueprintbench/model-origins.json','encodingFormat':'application/json'}]
    })
    graph.append({
        '@type':'WebPageElement','@id':workspace_id,'name':'BlueprintBench results workspace','url':BOARD+'#workspace',
        'description':'Interactive internal-test ranking with selectable metrics, competition ties, developer-country and serving-provider filters, sortable quality and operational KPIs, and configuration comparison. Export CSV or JSON for the visible ordered rows with rank eligibility, filters, scope, denominators, data revision and country sources. Filtered downloads are generated in the browser, not permanent file endpoints. Historical diagnostics stay separate; no independently validated ranking or PALO Blueprint Index.',
        'about':[{'@id':internal_id},{'@id':historical_id},{'@id':country_id}]
    })
    graph[2]['mentions'] = [{'@id':country_id},{'@id':workspace_id}]
    if url == BOARD:
        graph[2]['hasPart'].append({'@id':workspace_id})
    else:
        graph[2]['relatedLink'] = BOARD+'#workspace'
    if url == OVERVIEW:
        references = read(ROOT/'docs/benchmark-references.json')
        selected = [r for r in references['entries'] if r.get('review_group') == 'visibility-expansion-20261111']
        reference_id = OVERVIEW+'#benchmark-reference-review'
        graph.append({'@type':'WebPageElement','@id':reference_id,'url':OVERVIEW+'#references',
                      'name':'BlueprintBench benchmark reference comparison',
                      'description':f"{len(references['entries'])} methodological references, including {len(selected)} added high-visibility benchmark families. Selection uses sourced launch references, leaderboards, competitions and dated repository signals. Visibility is not benchmark validity. PALO transfer priorities are maintainer assessments; external suites were not executed and do not validate PALO.",
                      'dateModified':references['checked_on'],
                      'citation':[r['source_url'] for r in selected]})
        graph[2]['hasPart'].append({'@id':reference_id})
    graph.extend([
        {'@type':'ImageObject','@id':OVERVIEW+'#benchmark-logo','name':'PALO BlueprintBench identity',
         'contentUrl':SITE+'assets/blueprintbench/brand/blueprintbench-logo.png','encodingFormat':'image/png',
         'caption':'PALO BlueprintBench identity. A project mark, not certification or independent validation.'},
        {'@type':'ImageObject','@id':OVERVIEW+'#testing-badge','name':'PALO BlueprintBench internal testing badge',
         'contentUrl':SITE+'assets/blueprintbench/brand/internal-testing-badge.png','encodingFormat':'image/png',
         'caption':'Internal testing badge; requires a linked evidence record. Not a certification or qualified PALO Blueprint Index.'},
        {'@type':'ImageObject','@id':SITE+'#palo-logo','name':'PALO Framework logo',
         'contentUrl':SITE+'assets/blueprintbench/brand/palo-framework-logo.png','encodingFormat':'image/png'}])
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
    internal['campaigns']=[dict(id=internal['campaign_id'],models=len(internal['models']),assigned_calls=54,evidence_base=EVIDENCE,design='original baseline')]
    for group in ['models','records','configurations','translation_examples']:
        for item in internal[group]:
            item['evidence_base']=EVIDENCE
            item['campaign_id']=internal['campaign_id']
    for item in internal['translation_examples']:item['review_status']='assistant_draft'
    derived_paths=[WEB/'downloads/blueprintbench/internal-expansion-evidence.zip']
    derived_paths += [folder/name for folder in build_expansion.EXPANSIONS if folder.exists()
                     for name in ['analysis.json','translation-review-queue.json']]
    before={path:path.read_bytes() if path.exists() else None for path in derived_paths}
    try:
        additions=build_expansion.extensions()
        build_expansion.archive(additions)
        generated={path:path.read_bytes() for path in derived_paths}
    finally:
        # A --check must detect drift, not silently repair an archive before comparison.
        for path,body in before.items():
            if body is None:path.unlink(missing_ok=True)
            else:path.write_bytes(body)
    for folder,extension in additions:
        evidence='https://github.com/sev7enITA/PALO-BlueprintBench/tree/'+EXPANSION_REVISION+'/internal_tests/'+folder.name
        internal['campaigns'].append(dict(id=extension['campaign_id'],models=len(extension['models']),assigned_calls=extension['assigned_calls'],evidence_base=evidence,design='extension after original baseline observations'))
        for key in ['assigned_calls','recorded_calls','completed_calls','failed_calls','not_run','unknown_cost_calls','unknown_cost_reserved_usd']:
            internal[key]+=extension[key]
        for key in ['models','configurations','records','verification_rows','sensitivity','translations','translation_examples']:
            for item in extension[key]:
                item['campaign_id']=extension['campaign_id']
                item['evidence_base']=evidence
            internal[key].extend(extension[key])
    internal['campaign_id']='internal-procurement-baseline-and-extensions-20261111'
    internal['attempted_calls']=sum(r['state']!='not_run' for r in internal['records'])
    internal['precall_blocked_assignments']=sum(r['state']=='not_run' for r in internal['records'])
    internal['label_challenge']['resolution']='Preserve frozen primary labels. Post-hoc sensitivity excludes invoice P002 for every model and repetition. No independent adjudication.'
    internal['limitations']+=['Later extensions were selected after baseline outcomes were known; identities remain visible.', 'Supported reasoning settings, endpoint quantisation and output caps differ; high effort is not equal compute.', 'New translation outputs have not received the original baseline assistant review or draft-evaluator export.']
    data={'version':'2026-11-11.2','as_of':'2026-11-11','qualified_count':0,'internal':internal,
          'historical':read(WEB/'assets/blueprintbench/explorer-data.json'),'evidence_base':EVIDENCE,
          'qualification_gates':[{'name':n,'state':'pending'} for n in ['Named independent custodian','Independent domain annotations and adjudication','Validated severity and error-detection measure','Independent reproduction']]}
    out=dict(generated)
    out[WEB/'downloads/blueprintbench/leaderboard-data.json']=(json.dumps(data,indent=2)+'\n').encode()
    out[WEB/'downloads/blueprintbench/internal-cohort-report.md']=internal_report(data).encode()
    for name,url in [('PALO_BlueprintBench.html',OVERVIEW),('PALO_BlueprintBench_Leaderboard.html',BOARD)]:
        path=WEB/name
        if not path.exists():continue
        html=path.read_text(encoding='utf-8')
        encoded=json.dumps(dataset_graph(data,url),separators=(',',':'),ensure_ascii=False).replace('<','\\u003c')
        pattern=r'<script[^>]*type="application/ld\+json"[^>]*>.*?</script>'
        assert len(re.findall(pattern,html,re.S))==1,name
        html=re.sub(pattern,lambda _: '<script type="application/ld+json">'+encoded+'</script>',html,flags=re.S)
        metadata=(f"Explore {len(internal['models'])} model configurations in internal procurement tests, "
                  f"{internal['assigned_calls']} assigned tasks and separate historical diagnostics. "
                  "Inspect sources, settings and missing results. Independent validation pending.")
        for attribute in ['name="description"','property="og:description"','name="twitter:description"']:
            html=re.sub(r'<meta '+attribute+r' content="[^"]*">',lambda _: '<meta '+attribute+' content="'+metadata+'">',html)
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
