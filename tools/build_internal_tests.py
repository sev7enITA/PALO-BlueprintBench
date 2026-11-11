"""Build the internal baseline report and a deterministic public evidence archive."""
import collections
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'internal_tests/2026-11-11-frontier'
DL = ROOT/'web/downloads/blueprintbench'


def build():
    spec=importlib.util.spec_from_file_location('internal_analysis',BASE/'analyse.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    data=module.analyse()
    corpus=module.load(BASE/'corpus.json')
    records=[module.load(p) for p in sorted((BASE/'runs').glob('*/record.json'))]
    bank=module.load(BASE/'translation-assessments.json')
    data['completed_calls']=sum(r['state']=='completed' for r in records)
    data['failed_calls']=sum(r['state']!='completed' for r in records)
    data['unknown_cost_calls']=sum(r['cost_status']=='unknown' for r in records)
    data['unknown_cost_reserved_usd']=sum(r['reserved_usd'] for r in records if r['cost_status']=='unknown')
    data['case_metadata']=[dict(id=c['id'],name=c['id'].replace('-',' ').title(),dimensions=dict(collections.Counter(p['dimension'] for p in c['probes']))) for c in corpus]
    data['label_challenge']=module.load(BASE/'label-challenge.json')
    data['sensitivity']=[]
    data['translations']=[]
    for m in data['models']:
        rows=[r for r in data['verification_rows'] if r['model']==m['id']]
        judgments=[j for r in rows for j in r['judgments'] if not (r['case']=='invoice-matching' and j['id']=='P002')]
        data['sensitivity'].append(dict(model=m['id'],assigned=321,classified=len(judgments),correct=sum(j['correct'] for j in judgments),posthoc=True))
        own=[r for r in records if r['model']==m['id'] and r['track']=='translation']
        translated,verbatim,reviewed=0,0,0
        for r in own:
            raw=BASE/'runs'/r['id']/'output.txt'
            if not raw.exists(): continue
            claims,_=module.translation_claims(raw.read_bytes().decode('utf-8'))
            source={x['id']:x['text'] for c in corpus if c['id']==r['case'] for x in c['source']}
            for claim in claims:
                translated+=1
                key=r['case']+':'+claim['text_sha256']
                reviewed+=int(key in bank['claims'])
                verbatim+=int(claim['text'].split(' :: ',1)[-1]==source.get(claim['source_id']))
        data['translations'].append(dict(model=m['id'],assigned_source_rules=108,emitted_lines=translated,internally_reviewed_lines=reviewed,verbatim_source_lines=verbatim,review_type='assistant_draft',business_approved=False))
    total=sum(m['provider_reported_cost_usd'] for m in data['models'])
    text='''# Internal procurement baseline tests: OpenAI, Claude and Gemini

Status: **internal tests**, 11 November 2026. **Zero independently qualified results.**

This campaign exercises real model calls against short, original synthetic policies. It adds recognisable OpenAI, Anthropic and Google baselines to the research programme, separately from the historical challenger adapter diagnostics. It does not validate the benchmark as an independent measure.

## What was measured

Three synthetic procurement cases: purchase approval, supplier onboarding and invoice matching. Each has 12 numbered source rules and 36 seeded statements. All cases belong to one maintainer-authored family. Three repetitions, two tracks, three API models: **54 assigned calls**, 27 source-indexed translations and 27 verification calls. Verification has 324 assigned classifications per model. Expected labels and source propositions are assistant drafts.

Frozen input commits: `cd128a2` and `bca269c`, published before inference. Providers were pinned with fallback disabled, reasoning set to supported `high`, total output cap 32,768 tokens, no tools. Temperature and seed use provider defaults. High effort is not equal compute. No inference retries. This is not a 100 MB test or a Workbench application qualification.

## Recorded outcomes

'''
    text+=f"{data['recorded_calls']} requests recorded; {data['completed_calls']} complete responses; {data['failed_calls']} failed; {data['not_run']} not run. Failures remain in the assigned denominator.\n\n"
    text+='| API configuration | Complete calls | Agreement with frozen labels / assigned | Classified statements | Known provider charges, USD | Unknown-charge calls | Median request time |\n|---|---:|---:|---:|---:|---:|---:|\n'
    for m in sorted(data['models'],key=lambda x:x['name']):
        text+=f"| {m['name']} | {m['completed_calls']}/18 | {m['verification_correct']}/324 | {m['verification_classified']}/324 | {m['provider_reported_cost_usd']:.7f} | {m['unknown_cost_calls']} | {m['latency_median_seconds']:.2f} s |\n"
    text+='''
These are descriptive counts in alphabetical order, not a leaderboard. Agreement with draft labels is not independently adjudicated semantic accuracy. Model latency includes network and service time, with serial calls and no cache controls. It mixes translation and verification tasks; it is not a matched throughput comparison.

## A useful failure in our labels

On invoice matching, candidate P002 says: “The tolerance is increased by 5 percent for overseas suppliers.” Its frozen label is `not_established`. Source R03 categorically blocks automatic payment above EUR 10. Claude classified this statement as `contradicted` in repetitions 2 and 3. That interpretation is defensible: increasing the tolerance can contradict the explicit threshold. This is an ambiguity in the control design, not an adjudicated model mistake.

We preserve all original labels and primary counts. An explicitly **post-hoc sensitivity check**, excluding this one candidate from every model and repetition, gives:

| Model | Agreement / remaining assigned | Classified / remaining assigned |
|---|---:|---:|
'''
    for m in sorted(data['sensitivity'],key=lambda x:x['model']):text+=f"| {m['model']} | {m['correct']}/321 | {m['classified']}/321 |\n"
    text+='''
The remaining controls are near the ceiling for these configurations. The suite is too small and easy to support a comparative quality claim. We need harder independent cases, an explicit contradiction/absence rubric and independent label adjudication before ranking models. Repetitions of one authored family are not independent companies; no confidence interval is offered.

## Translation, review and draft export

Every distinct emitted line is read beside its numbered source rule by the coding assistant. Repeated identical text reuses that internal assessment. Model identity was visible; this review is not blind or independent. It is not a human correction-time study. A close restatement or verbatim copy is permitted by this track, which is therefore much easier than unconstrained document interpretation.

| Model | Emitted lines / source opportunities | Internally reviewed lines | Exact source copies |
|---|---:|---:|---:|
'''
    for t in sorted(data['translations'],key=lambda x:x['model']):text+=f"| {t['model']} | {t['emitted_lines']}/108 | {t['internally_reviewed_lines']} | {t['verbatim_source_lines']} |\n"
    text+='''
The `contract-replay/` directory carries original outputs through draft evaluator **0.3.0-dev.1** and exports 27 source-linked draft blueprints requiring business approval. This is a **post-hoc scoring replay**: its formal campaign lock was created after inference and before replay. It is not retroactive preregistration. Run timing is local replay bookkeeping; original inference timing remains in the linked original records. Replay accounting carries original charges without making new calls. All results remain unqualified. The draft evaluator is still under review; the released evaluator is not silently replaced.

## Cost and failure accounting

'''
    text+=f"Known provider-reported inference charges total **USD {total:.7f}**, plus **{data['unknown_cost_calls']} unresolved charge(s)**. The unresolved reservations total **USD {data['unknown_cost_reserved_usd']:.7f}** and remain carried against the budget. They are conservative reservations, not proven charges. The overall user-authorised key cap is USD 40 including prior tests; this campaign has a USD 30 allowance. Budget is a ceiling, not a spending target.\n\n"
    text+='''Google AI Studio returned HTTP 503 for purchase-approval verification, repetition 2. The original runner stopped when the charge was unknown. The accounting amendment was published before continuation: the complete reservation remained encumbered and the failed assignment was not retried. Zero is never substituted for an unknown charge.

Costs include provider-reported input and completion usage, with reasoning included in completion billing. Token detail is in the machine-readable results. There were no RAG, embedding, paid search, storage-service or tool calls in this cohort. Local engineering, review labour, hosting and electricity are not measured in this inference charge total; this is not a total-cost-of-ownership estimate.

## Reproduce and inspect

The evidence archive includes frozen corpus, prompts, model metadata, manifest, request bodies, response bodies, exact output text, assistant review bank, analysis scripts and post-hoc evaluator replay. One error response contains an account identifier: the public copy removes only `/user_id`, with original and public hashes in a redaction sidecar. The original body is retained privately. Successful response bodies and all model output text remain original. The original hash of that private error body cannot be independently verified from the public copy.

From a checkout of `codex/internal-frontier-tests-20261111`, install `evaluator/requirements.txt`, then run:

```sh
python -m unittest discover -s internal_tests/2026-11-11-frontier -p 'test_*.py'
python internal_tests/2026-11-11-frontier/analyse.py
python internal_tests/2026-11-11-frontier/replay_translation.py /tmp/palo-new-replay
python tools/build_internal_tests.py
```

The replay requires a new destination and does not call a provider. API reruns require explicit credentials and budget; hosted models may change. Do not use `runner.py` to bypass unresolved-charge safeguards. `resume.py` is the documented accounting amendment.

Frozen design: `internal_tests/2026-11-11-frontier/README.md`. Primary counts: `analysis.json`. Label challenge: `label-challenge.json`. Review bank: `translation-assessments.json`. Formal replay: `contract-replay/`. Exact source and response hashes establish byte consistency, not independent authorship, truthful timestamps or custody.

[Research page](https://paloframework.org/PALO_BlueprintBench.html#internal-tests) · [Versioned evidence](https://github.com/sev7enITA/PALO-BlueprintBench/tree/codex/internal-frontier-tests-20261111/internal_tests/2026-11-11-frontier)
'''
    (BASE/'REPORT.md').write_text(text,encoding='utf-8',newline='\n')
    (DL/'internal-tests-report.md').write_text(text,encoding='utf-8',newline='\n')
    (DL/'internal-tests-results.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8',newline='\n')
    files={p.relative_to(BASE).as_posix():p.read_bytes() for p in BASE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    manifest={n:hashlib.sha256(b).hexdigest() for n,b in files.items()}
    files['public-archive-manifest.json']=(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode()
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,body in sorted(files.items()):
            info=zipfile.ZipInfo('internal-tests/'+name,date_time=(2026,11,11,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.create_system=3;info.external_attr=0o100644<<16;z.writestr(info,body)
    (DL/'internal-tests-evidence.zip').write_bytes(output.getvalue())
    print(json.dumps({'status':'built','requests':len(records),'evidence_files':len(files),'archive_bytes':len(output.getvalue())}))

if __name__=='__main__':
    import sys
    paths=[BASE/'analysis.json',BASE/'translation-review-queue.json',BASE/'REPORT.md',DL/'internal-tests-report.md',DL/'internal-tests-results.json',DL/'internal-tests-evidence.zip']
    before={p:p.read_bytes() if p.exists() else None for p in paths} if '--check' in sys.argv else {}
    build()
    if before:
        changed=[str(p.relative_to(ROOT)) for p,b in before.items() if p.read_bytes()!=b]
        if changed:raise SystemExit('Internal artifact drift: '+', '.join(changed))
        print('Internal evidence artifacts verified')

