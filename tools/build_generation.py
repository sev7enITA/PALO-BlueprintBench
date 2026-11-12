"""Publish real-document observations separately from prior synthetic tests."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, sys
import build_site_architecture as site
import research_publication

ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/'internal_tests/2026-11-11-real-procurement'
PAGE='PALO_BlueprintBench_Generation.html'
URL=site.SITE+PAGE

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def capture_provenance(row, accounting, capture=None):
    """Presentation overlay only; retained assessment and receipt values stay intact."""
    payload=accounting.get('data') or {}
    statuses=sorted({r['status'] for r in payload.get('provider_responses', [])
                     if isinstance(r.get('status'), int)})
    failures=[status for status in statuses if status>=400]
    row['upstream_statuses']=statuses
    row['collection_failure']=('Upstream error '+', '.join(map(str, failures))+'; incomplete capture') if failures else None
    if capture and capture.get('isError'):
        error_text='\n'.join(item.get('text','') for item in capture.get('content',[]) if item.get('type')=='text')
        row['capture_tool_error']=error_text
        if not row['collection_failure']:
            row['collection_failure']='MCP timeout; no complete capture' if 'timed out' in error_text.lower() else 'MCP collection error; no complete capture'
    row['cost_zero_reason']=('Provider accounting reports a zero charge for the upstream error; this is not a successful zero-cost generation.') if failures and payload.get('total_cost')==0 and row.get('cost_usd')==0 else row.get('cost_zero_reason')
    if row.get('state')=='not_run' and row.get('cost_usd')==0:
        row['cost_zero_reason']='No request was dispatched.'
    native=[(row.get('usage') or {}).get(k) for k in ['native_prompt_tokens','native_completion_tokens','native_reasoning_tokens','native_cached_tokens']]
    row['native_usage_available']=any(v is not None for v in native) and not (failures and all(v in (None,0) for v in native))
    return row

def data():
    analysis_name=next(name for name in ['analysis-corrected.json','analysis.json'] if (STUDY/name).exists())
    blueprint_directory='blueprints' if analysis_name=='analysis.json' else 'blueprints-corrected'
    analysis=load(STUDY/analysis_name)
    assessment={'analysis_path':analysis_name,'blueprints_directory':blueprint_directory,
      'checker_revision':analysis.get('checker_revision','quote-normalisation-v1.0'),
      'correction_status':analysis.get('correction_status'),'correction_note':analysis.get('correction_note'),
      'original_analysis_path':'analysis.json','original_replay_path':'corrections/analysis-v1.0-replayed.json' if analysis_name!='analysis.json' else None}
    packets=load(STUDY/'source-packets.json')
    models=load(STUDY/'models.json')
    supplement=STUDY/'supplemental-google-ai-studio'
    if analysis_name=='analysis-combined.json':models+=load(supplement/'models.json')
    configurations=[]
    for m in models:
        config_id=m['id']+'@'+m['provider']
        configurations.append({'id':config_id,'model_id':m['id'],'name':m['name']+' · '+m['provider'],
          'access_channel':m.get('access_channel') or ('OpenRouter MCP Batch API' if analysis_name=='analysis-combined.json' and m['provider']=='google-ai-studio' else 'OpenRouter MCP'),'execution_mode':'Cloud API inference','provider_pin':m['provider'],
          'advertised_endpoint':m['endpoint']['name'],'advertised_context_tokens':m['endpoint']['context_length'],
          'quantization':m['endpoint']['quantization'],'reasoning_effort':'high',
          'maximum_generated_tokens_including_reasoning':32768,'temperature':'not exposed by MCP tool; provider default',
          'seed':'not exposed by MCP tool; provider default','fallbacks':False,'price_snapshot':m['endpoint']['pricing']})
    for row in analysis['rows']:
        prefix=Path('supplemental-google-ai-studio') if row.get('cohort')=='transport_supplement' else Path('.')
        run_path=prefix/'runs'/row['id']
        record_path=Path(row.get('record_json_path') or run_path/'record.json')
        rec=load(STUDY/record_path) if (STUDY/record_path).exists() else {}
        provider=row.get('pinned_provider') or row.get('provider') or next(m['provider'] for m in models if m['id']==row['model'])
        row.setdefault('configuration_id',row['model']+'@'+provider)
        row['access_channel']=next(m['access_channel'] for m in configurations if m['id']==row['configuration_id'])
        is_batch='Batch' in row['access_channel']
        row['display_elapsed_seconds']=None if is_batch else row.get('elapsed_seconds')
        row['duration_basis']='Not comparable: asynchronous batch queue' if is_batch else 'MCP call wall time'
        row['usage']=rec.get('usage') or {}
        row['returned_model']=rec.get('returned_model')
        row['recorded_at']=rec.get('finished_at')
        accounting_path=STUDY/run_path/'get_generation.json'
        capture_path=STUDY/run_path/'mcp-response.json'
        capture_provenance(row, load(accounting_path) if accounting_path.exists() else {},load(capture_path) if capture_path.exists() else None)
        output_path=Path(row.get('output_txt_path') or run_path/'output.txt')
        row['raw_output']=(STUDY/output_path).read_bytes().decode('utf-8') if rec and (STUDY/output_path).exists() else None
        row['capture_record_path']=record_path.as_posix()
        row['capture_output_path']=output_path.as_posix()
        p=Path(row.get('blueprint_path') or prefix/blueprint_directory/(row['id']+'.json'))
        row['blueprint']=load(STUDY/p) if (STUDY/p).exists() else None
        row['capture_blueprint_path']=p.as_posix() if row['blueprint'] is not None else None
    for group in analysis.get('by_configuration',analysis.get('by_model',[])):
        if not group.get('configuration_id'):
            group['configuration_id']=next(m['id'] for m in configurations if m['model_id']==group['model'])
    return {'revision':'2026-11-11.6','title':'Specification Generation','evidence_status':'Closed incomplete; internal tests; assistant-draft reference outcomes; no independent validation',
      'analysis':analysis,'assessment':assessment,
      'transport_amendment':load(STUDY/'transport-amendment.json') if (STUDY/'transport-amendment.json').exists() else None,
      'supplement_manifest':load(supplement/'manifest.json') if analysis_name=='analysis-combined.json' else None,
      'advisory_review':load(STUDY/'review/post-output-disagreements-r1.json') if (STUDY/'review/post-output-disagreements-r1.json').exists() else None,
      'models':configurations,'sources':[{k:v for k,v in p.items() if k!='pages'} for p in packets],
      'budget':load(STUDY/'budget-final.json') if (STUDY/'budget-final.json').exists() else load(STUDY/'budget-before.json'),
      'design':load(STUDY/'design/task-design.json'),'preparation_commit':'a530a70050d5f06a5e2504d2ef81e2a6b4af3222',
      'manifest_sha256':hashlib.sha256((STUDY/'manifest.json').read_bytes()).hexdigest()}

def schema(d):
    s=d['analysis']['summary'];url=URL
    dataset={'@type':'Dataset','@id':url+'#dataset','name':'Procurement document-to-specification generation observations','description':f"Three public procurement documents, 200 supplied pages, {len(d['models'])} serving configurations and three assigned repetitions. Generated requirements, workflow drafts and decision rules; executable outcomes compared with pre-output assistant-draft expectations. Internal tests, not independent semantic validation.",
      'url':url,'version':d.get('assessment',{}).get('checker_revision','quote-normalisation-v1.0'),'identifier':'real-procurement-generation-1.0.0','creator':{'@type':'Person','name':'Fabrizio Degni'},'creativeWorkStatus':'Closed incomplete; internal tests; independent validation pending','datePublished':'2026-11-11','isAccessibleForFree':True,
      'measurementTechnique':'Full supplied source text; scoped specification generation; fixed-provider cloud inference through OpenRouter MCP; high reasoning and maximum 32768 generated tokens; three assigned repetitions. Original serial collection and supplementary batch collection are distinguished; provider and transport changes are not isolated causal effects. Local JSON, provenance and decision-tree checks. Missing and unassessed outcomes remain distinct. No quality rank or PALO Blueprint Index.',
      'citation':[p['source_url'] for p in d['sources']],
      'isBasedOn':{'@type':'CreativeWork','name':'Pre-output task and assessment disclosure','url':site.GIT+'/tree/'+d['preparation_commit']+'/internal_tests/2026-11-11-real-procurement'},
      'variableMeasured':[{'@type':'PropertyValue','propertyID':k,'name':k.replace('_',' '),'value':s[k]} for k in ['assigned_calls','completed_calls','structurally_valid_calls','assigned_decisions','matched_decisions','disagreed_decisions','missing_decisions','unassessed_decisions','known_cost_usd']],
      'distribution':[{'@type':'DataDownload','name':'Generation observations and model drafts','encodingFormat':'application/json','contentUrl':site.SITE+'downloads/blueprintbench/generation-results.json'},{'@type':'DataDownload','name':'Frozen inputs, tool receipts and draft exports','encodingFormat':'application/zip','contentUrl':site.SITE+'downloads/blueprintbench/generation-evidence.zip'}]}
    if d.get('assessment',{}).get('correction_note'):
        dataset['correction']={'@type':'CreativeWork','name':'PDF hyphen-linewrap quote-check correction v1.1','url':site.GIT+'/blob/main/internal_tests/2026-11-11-real-procurement/corrections/correction-note.md'}
    return {'@context':'https://schema.org','@graph':[{'@type':'WebPage','@id':url+'#webpage','url':url,'name':'Specification Generation | BlueprintBench','description':dataset['description'],'version':research_publication.PRESENTATION_REVISION,'dateModified':'2026-11-11','inLanguage':'en','mainEntity':{'@id':url+'#dataset'},'image':site.SITE+'assets/blueprintbench/brand/blueprintbench-logo.png'},dataset]}

def render(d):
    s=d['analysis']['summary'];g=json.dumps(schema(d),ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
    scope=site.scope([('Input','3 published documents · 200 supplied pages'),('Task','Generate requirements, workflow and decision rules'),('Models',str(len({m['model_id'] for m in d['models']}))+' model IDs · '+str(len(d['models']))+' serving configurations'),('Repetitions','3 per document and configuration · '+str(s['assigned_calls'])+' assigned calls'),('Execution','OpenRouter MCP · '+('serial original / batch supplement' if d.get('supplement_manifest') else 'serial pinned cloud providers'))])
    amendment='''<details class="gen-status" id="transport-amendment"><summary>Serving configuration and transport amendment</summary><p>The original 27 assignments remain in the record, including Google Vertex failures and stopped requests. A separately frozen Google AI Studio supplement adds 9 assignments under its own serving configuration. Provider results are not merged. The supplement also changes serial collection to the OpenRouter MCP Batch API, so these observations do not isolate a provider effect. <a href="'''+site.GIT+'''/blob/main/internal_tests/2026-11-11-real-procurement/transport-amendment.json">Transport amendment</a> · <a href="'''+site.GIT+'''/tree/main/internal_tests/2026-11-11-real-procurement/supplemental-google-ai-studio">Supplement freeze and receipts</a></p></details>''' if d.get('supplement_manifest') else ''
    correction='''<details class="gen-status"><summary>Quote-check correction v1.1</summary><p>Quote checker v1.1 corrects PDF hyphen-linewrap matching while retaining the hyphen. Source documents, model answers and draft decision labels are unchanged. <a href="'''+site.GIT+'''/blob/main/internal_tests/2026-11-11-real-procurement/corrections/correction-note.md">Correction record</a> · <a href="'''+site.GIT+'''/blob/main/internal_tests/2026-11-11-real-procurement/analysis.json">Original v1.0 analysis</a> · <a href="'''+site.GIT+'''/blob/main/internal_tests/2026-11-11-real-procurement/corrections/analysis-v1.0-replayed.json">v1.0 replay on the same receipts</a></p></details>''' if d.get('assessment',{}).get('correction_note') else ''
    advisory='''<details class="gen-status" id="draft-key-review"><summary>FEMA draft-key review, first repetition.</summary><p> '''+str(d['advisory_review']['summary']['observed_disagreements'])+''' disagreements in the reviewed first-repetition outputs share an ambiguous other contract category. This is one candidate input/key ambiguity, not an established model error. Frozen counts are retained; human adjudication is pending. <a href="'''+site.GIT+'''/blob/main/internal_tests/2026-11-11-real-procurement/review/post-output-disagreements-r1.md">Review scope and competing interpretations</a></p></details>''' if d.get('advisory_review') else ''
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'"><title>Specification Generation | BlueprintBench</title><meta name="description" content="Source-linked specifications generated from three real procurement documents. Compare model outputs, execution conditions and repeated decision-rule tests."><link rel="canonical" href="'''+URL+'''"><link rel="stylesheet" href="assets/blueprintbench/site-architecture.css?v=20261111-6"><link rel="stylesheet" href="assets/blueprintbench/generation.css?v=20261111-6"><script src="assets/blueprintbench/generation.js?v=20261111-6" defer></script><script type="application/ld+json">'''+g+'''</script></head><body class="bench-architecture"><a class="gen-skip" href="#main">Skip to results</a>'''+site.navigation(PAGE)+'''<main id="main" class="bench-shell"><section class="bench-hero"><p class="bench-kicker">Document-to-specification evaluation</p><h1>Specification Generation</h1><p class="bench-lead">Generated specifications from published procurement documents.</p><p>Models read the supplied document text and generate atomic requirements, process steps and executable decision rules. The comparison separates completed requests, accepted output contracts and agreement with pre-output reference decisions.</p>'''+scope+'''<p class="gen-status">Closed incomplete · 14 complete, 5 incomplete and 8 not dispatched · Reference decisions are assistant drafts · <a href="#limits">Assessment scope and limitations</a></p></section><section class="gen-stats" aria-label="Recorded execution"><div><strong>'''+str(s['completed_calls'])+'/'+str(s['assigned_calls'])+'''</strong><span>Requests completed</span></div><div><strong>200</strong><span>Supplied PDF pages</span></div><div><strong>'''+str(s['structurally_valid_calls'])+'/'+str(s['assigned_calls'])+'''</strong><span>Contract and citation checks passed</span></div><div><strong>$'''+f"{s['known_cost_usd']:.4f}"+'''</strong><span>Known study charge</span></div></section><section class="bench-section" id="results"><h2>Execution of generated rules</h2><p>Counts refer to a fixed set of draft reference decisions. A citation match or a matching test outcome does not establish full semantic correctness. Missing output and rejected contracts remain in the assigned denominator.</p>'''+advisory+'''<div id="generation-chart" aria-label="Decision outcomes by model"></div><div class="gen-legend"><span class="match">Matches draft</span><span class="diverge">Diverges</span><span class="unassessed">Unassessed</span><span class="missing">Missing</span></div></section><section class="bench-section" id="runs"><h2>Recorded executions</h2><div class="gen-controls"><label>Document<select id="document-filter"><option value="all">All three documents</option></select></label><label>Serving configuration<select id="model-filter"><option value="all">All serving configurations</option></select></label><label>Repetition<select id="repetition-filter"><option value="all">All three repetitions</option><option>1</option><option>2</option><option>3</option></select></label><label>Order<select id="order-filter"><option value="identity">Model and document</option><option value="cost">Known charge</option><option value="duration">Observed duration</option><option value="matches">Draft matches</option></select></label><button id="export-csv" disabled>Export filtered CSV</button><button id="export-json" disabled>Export filtered JSON</button></div><p id="selection-summary" role="status"></p><div class="table-scroll"><table class="gen-table"><caption>Access channel, serving provider, repeated outcomes and accounting for each request. Sorting is descriptive; no rank is assigned.</caption><thead><tr><th>Model / execution</th><th>Document / repetition</th><th>Contract</th><th>Matches / assigned</th><th>Diverges</th><th>Unassessed / missing</th><th>Known USD</th><th>Duration</th><th>Native provider tokens input / output</th><th>Evidence</th></tr></thead><tbody id="run-table"></tbody></table></div><section id="run-detail" tabindex="-1" aria-live="polite"></section></section><section class="bench-section" id="documents"><h2>Documents and generation tasks</h2><div id="document-cards" class="bench-three"></div><p><a href="PALO_BlueprintBench_Corpus.html">Complete corpus register</a> · <a href="'''+site.GIT+'/tree/'+d['preparation_commit']+'''/internal_tests/2026-11-11-real-procurement">Frozen pre-output preparation</a></p></section><section class="bench-section" id="configuration"><h2>Serving configurations</h2><div id="configuration-cards" class="bench-three"></div><p>All calls use cloud inference through OpenRouter. Configuration cards distinguish original serial MCP access from supplementary batch access. No local inference, browser chat or model-assisted reviewer output is included in this comparison. Each model and pinned provider is a distinct configuration. Full source text is supplied directly; no RAG, embeddings or retrieval are used. Observed tokens are recorded per request and differ from the advertised context limit.</p></section><section class="bench-section" id="limits"><h2>Method and limitations</h2><p><a href="https://github.com/sev7enITA/PALO-BlueprintBench/blob/main/docs/study-closure-2026-11-12.md">Study closure and assigned calls</a> · <a href="https://github.com/sev7enITA/PALO-BlueprintBench/blob/main/docs/workflow-connectivity-diagnostic.json">Workflow connectivity diagnostic</a> · <a href="https://github.com/sev7enITA/PALO-BlueprintBench/blob/main/docs/source-silence-rubric-draft.md">Draft source-silence rubric</a></p>'''+amendment+correction+'''<details><summary>Assessment boundaries and reproducibility</summary><ul id="limitations"></ul><p>There are three document inputs and three assigned repetitions per configuration, not additional independent document families. A transport supplement is a separate configuration, not a replacement for original failed assignments. The 36 private-to-prompt test situations contain 132 component decisions per model repetition. Labels were prepared by an assistant before collection and require independent human adjudication. No confidence interval or quality ordering is inferred from these observations.</p><p>Tasks cover a defined process within each source. Full semantic coverage of every requirement in the 200 pages has not been measured. Provider defaults for temperature and seed are not controlled by the MCP interface. Exact tool arguments and returned tool envelopes are retained; original HTTP response bytes are unavailable.</p></details><details><summary>Costs and authorised budget</summary><div id="budget-details"></div><p>Reported charges include whatever input, output, reasoning and cache usage the serving provider billed. Native provider counts and router-reported counts can use different tokenisers. Reasoning and cache counters may overlap the reported totals; they must not be added again. A reported cache adjustment can be negative and is not interpreted as measured savings. Token subcategories are displayed when returned; missing accounting is not replaced by zero. Source acquisition and deterministic local processing have no billed model calls. The USD 40 ceiling applies cumulatively, including preceding tests and unresolved-cost reserves.</p></details><p><a href="PALO_BlueprintBench_Method.html">Research method</a> · <a href="downloads/blueprintbench/generation-evidence.zip">Download reproducibility archive</a> · <a href="'''+site.GIT+'''/tree/main/internal_tests/2026-11-11-real-procurement">Source code and complete records</a></p></section></main>'''+site.footer()+'''</body></html>'''

def outputs():
    d=data()
    from build_public import archive
    files={p.relative_to(STUDY).as_posix():p.read_bytes() for p in STUDY.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    return {ROOT/'web'/PAGE:render(d).encode(),ROOT/'web/downloads/blueprintbench/generation-results.json':(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode(),ROOT/'web/downloads/blueprintbench/generation-evidence.zip':archive(files)}

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();bad=[]
    for path,body in outputs().items():
        if args.check:
            if not path.exists() or path.read_bytes()!=body:bad.append(str(path.relative_to(ROOT)))
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(body)
    if bad:raise SystemExit('Generation artifact drift: '+', '.join(bad))
    print('Generation publication '+('verified' if args.check else 'built'))
if __name__=='__main__':main()
