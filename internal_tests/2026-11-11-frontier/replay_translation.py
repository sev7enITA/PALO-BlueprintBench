"""Post-hoc contract replay of original translation outputs. No inference calls.

The contract campaign is frozen at replay time, not backdated to model execution.
Actual inference timestamps and charges are archived as source records. Reported
run timing describes replay bookkeeping only and must not be used as model latency.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1] / 'evaluator'))
import blueprintbench as bb
from demo import put, put_text
from analyse import load, translation_claims


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def replay(dest):
    if dest.exists():
        raise ValueError('Use a new destination; prior replay evidence is immutable')
    dest.mkdir(parents=True)
    corpus = load(ROOT / 'corpus.json')
    models = load(ROOT / 'models.json')
    bank = load(ROOT / 'translation-assessments.json')
    tasks, subjects, configurations = [], [], {}
    for case in corpus:
        meaning = {r['id']: r['text'] for r in case['source']}
        gold = put(dest, f"{case['id']}/gold.json", {
            'required_propositions': list(meaning), 'meaning': meaning,
            'annotation_status': 'assistant_draft', 'answerable': True,
            'allowed_match_groups': [], 'allowed_alternatives': {},
            'forbidden_inferences': [dict(id=p['id'], text=p['text'], violated_gold=[p['source_id']]) for p in case['probes'] if p['expected'] == 'contradicted'],
            'critical_rule_ids': list(meaning),
            'source_scope': 'All 12 explicitly numbered synthetic rules. All are treated as critical controls in this internal replay; not a validated severity rubric.',
            'source_text': '\n'.join(r['id'] + ' ' + r['text'] for r in case['source'])})
        tasks.append(dict(id=case['id'], family=case['family'], domain='procurement', scope='12 source-indexed rule propositions', gold=gold))
    for model in models:
        slug = model['id'].replace('/', '__')
        config = put(dest, f'{slug}/configuration.json', {
            'model': {'id': model['id'], 'revision': 'unavailable', 'quantisation': 'unavailable', 'unavailable_reason': 'Hosted weights and quantisation not independently exposed; catalogue metadata is in original models.json'},
            'provider_runtime': {'id': model['provider'], 'revision': 'unavailable', 'unavailable_reason': 'Hosted runtime revision not exposed'},
            'settings': {'reasoning': 'high', 'temperature': None, 'seed': None, 'max_output_tokens': 32768, 'unavailable_reason': 'Temperature and seed omitted in all original requests; provider defaults'},
            'pipeline': {'version': 'internal-frontier-20261111', 'adapter_revision': 'bca269c', 'prompt_sha256': hashlib.sha256(b''.join((ROOT/'prompts'/f"translation-{c['id']}.json").read_bytes() for c in corpus)).hexdigest(), 'schema_sha256': 'unavailable', 'unavailable_reason': 'Translation output is plain source-indexed text, not constrained JSON; prompt hash binds concatenation in corpus order'},
            'environment': {'id': 'OpenRouter hosted inference, local post-hoc replay', 'runtime_version': sys.version.split()[0]}})
        configurations[model['id']] = config
        subjects.append(dict(id=slug, configuration=config))
    campaign = dict(id='internal-procurement-posthoc-contract-replay', benchmark_version=bb.VERSION, split='development', track='interpretation', repetitions=3,
                    success_policy=dict(minimum_precision=1, minimum_recall=1, maximum_critical_errors=0), subjects=subjects, tasks=tasks)
    lock = bb.freeze(campaign, dest)
    put(dest, 'campaign.json', campaign)
    put(dest, 'campaign.lock.json', lock)
    results = []
    for model in models:
        started = now()
        slug = model['id'].replace('/', '__')
        attempts, blueprints = [], []
        for repetition in range(1,4):
            for case in corpus:
                t = time.monotonic()
                ident = f"{repetition}-{case['id']}-translation-{slug}"
                record = load(ROOT/'runs'/ident/'record.json')
                if record['state'] != 'completed':
                    raise ValueError('Translation replay requires explicit handling of failed assignment: ' + ident)
                raw = (ROOT/'runs'/ident/'output.txt').read_bytes().decode('utf-8')
                assert hashlib.sha256(raw.encode()).hexdigest() == record['output_sha256']
                claims, whitespace = translation_claims(raw)
                assert len(claims)==12 and {c['source_id'] for c in claims}=={r['id'] for r in case['source']}
                name = f'{slug}/{repetition}-{case["id"]}'
                emitted = [{k:c[k] for k in ['id','text','span']} for c in claims]
                claims_ref = put(dest, name+'/claims.json', emitted)
                raw_ref = put_text(dest, name+'/raw.txt', raw)
                original_record = put(dest, name+'/original-inference-record.json', record)
                receipt = put(dest, name+'/receipt.json', dict(task_id=case['id'], repetition=repetition, state='pass', termination_reason='completed', all_retry_costs_included=True,
                    artifacts=[claims_ref,raw_ref,original_record], claims_artifact=claims_ref, raw_output=raw_ref, non_claim_spans=whitespace,
                    request_identity=dict(provider_request_id=record['provider_request_id'], request_sha256=record['request_sha256'], unavailable_reason='')))
                assessments=[]
                for claim in claims:
                    reviewed = bank['claims'][case['id']+':'+claim['text_sha256']]
                    assert reviewed['text_sha256']==claim['text_sha256'] and reviewed['source_id']==claim['source_id']
                    if reviewed['verdict']!='supported':
                        raise ValueError('Unsupported proposition requires explicit error mapping')
                    assessments.append(dict(id=claim['id'], equivalence_id=case['id']+':'+claim['source_id'], verdict='supported', matches_gold=[claim['source_id']], critical=False,
                        violated_gold=[], matches_forbidden=[], matches_alternatives=[], error_category='none', critical_rationale='No critical error identified in internal assistant review', text_sha256=claim['text_sha256']))
                annotation = put(dest, name+'/annotation.json', dict(task_id=case['id'], receipt_sha256=receipt['sha256'], scope_complete=True, atomicity_reviewed=True, review_type='assistant_draft', claims=assessments))
                attempts.append(dict(task_id=case['id'], repetition=repetition, state='pass', elapsed_seconds=time.monotonic()-t,
                    cost=dict(status='reported',usd=record['cost_usd'],reason='Original inference charge carried into replay accounting; not charged again'),receipt=receipt,annotation=annotation))
                blueprint = dict(status='internal_draft_requires_business_review', qualified=False, model=model['id'], case=case['id'], repetition=repetition, source_family=case['family'],
                    origin='Source-indexed translation test, not Workbench application end-to-end execution', inference_record_id=ident,
                    rules=[dict(id=c['source_id'], proposed_specification=c['text'].split(' :: ',1)[1], source_text=next(r['text'] for r in case['source'] if r['id']==c['source_id']), internal_review='assistant_draft_supported', business_approval='pending') for c in claims])
                put(dest, name+'/blueprint.json', blueprint)
        run = dict(run_id=slug+'-posthoc-replay', campaign_sha256=lock['sha256'], subject_id=slug, configuration_sha256=configurations[model['id']]['sha256'],
            started_at=started,finished_at=now(),evidence_status='self_reported',attempts=attempts,submitter_id='palo-maintainer',execution=dict(mode='serial',max_concurrency=1))
        put(dest, slug+'/run.json', run)
        result = bb.evaluate(lock,run,dest)
        put(dest,slug+'/result.json',result)
        results.append(dict(model=model['id'],result=result))
    put(dest,'replay-summary.json',dict(status='internal_tests',qualified=False,posthoc=True,evaluator_version=bb.VERSION,
        timing_scope='Local replay bookkeeping; original inference times are in original-inference-record.json',
        limitations=['Formal scoring contract frozen after inference, before replay; no retroactive preregistration claim','Expected source propositions and assessments are assistant drafts','Exports require business review; not Workbench app E2E validation'],results=results))
    return results

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination',type=Path)
    args=parser.parse_args()
    results=replay(args.destination)
    print(json.dumps({'models':len(results),'status':'internal_tests','qualified':False}))
