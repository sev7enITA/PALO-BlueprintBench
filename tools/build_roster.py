"""Default-scope roster derived from the frozen leaderboard, never from catalogue scores."""
from pathlib import Path
import argparse
import csv
import hashlib
import html
import io
import json
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'web/downloads/blueprintbench'


def build():
    source = (BASE/'leaderboard-data.json').read_bytes()
    guard = json.loads((ROOT/'internal_tests/2026-11-11-calibration/legacy-guard.json').read_text(encoding='utf-8'))
    if hashlib.sha256(source).hexdigest() != guard['primary_dataset_sha256']:
        raise ValueError('Roster source differs from frozen cohort')
    data = json.loads(source)
    cohort = data['internal']
    records = cohort['records']
    configs = {r['id']: r for r in cohort['configurations']}
    rows = []
    for m in cohort['models']:
        own = [r for r in records if r['model'] == m['id'] and r['state'] != 'not_run']
        complete = len(own) == m['assigned_calls'] == m['completed_calls']
        known = bool(own) and all(r.get('cost_status') == 'provider_reported' and isinstance(r.get('cost_usd'), (int, float)) for r in own)
        config = configs[m['id']]
        tokens = [r['usage']['prompt_tokens'] for r in own if isinstance((r.get('usage') or {}).get('prompt_tokens'), (int, float))]
        reasoning = config.get('configuration', {}).get('reasoning') or {}
        rows.append({'cohort': 'internal', 'id': m['id'], 'name': m['name'], 'provider': m['pinned_provider'],
                     'campaign': m['campaign_id'], 'reasoning': reasoning.get('effort') or ('enabled' if reasoning['enabled'] else 'disabled') if 'enabled' in reasoning else reasoning.get('effort') or 'not configured',
                     'endpoint_revision': config.get('endpoint_name'), 'output_cap': config.get('configuration', {}).get('max_tokens'),
                     'advertised_context_tokens': config.get('catalogue_context'),
                     'observed_prompt_tokens_min': min(tokens) if tokens else None, 'observed_prompt_tokens_max': max(tokens) if tokens else None,
                     'prompt_usage_records': len(tokens), 'dispatched_calls': len(own),
                     'label_matches': m['verification_correct'], 'assigned_labels': m['verification_assigned_probes'],
                     'complete_calls': m['completed_calls'], 'assigned_calls': m['assigned_calls'],
                     'known_usd': m['provider_reported_cost_usd'], 'median_seconds': m['latency_median_seconds'],
                     'classified_labels': m['verification_classified'],
                     'missing_labels': m['verification_assigned_probes'] - m['verification_classified'],
                     'disagreements': m['verification_classified'] - m['verification_correct'],
                     'agreement_received': m['verification_correct'] / m['verification_classified'] if m['verification_classified'] else None,
                     'classification_coverage': m['verification_classified'] / m['verification_assigned_probes'],
                     'all_calls_complete': complete, 'accounting_complete': known,
                     'evidence_url': m['evidence_base']})
    rows.sort(key=lambda r: r['name'].split(':',1)[-1].strip().casefold())
    historical = [{'cohort':'historical_adapter_diagnostics','id':m.get('id'), 'name':m.get('name'), 'reason':'Different task, settings and evidence contract; retained separately from internal procurement tests.'} for m in data['historical']['models']]
    corpus = json.loads((ROOT/'internal_tests/2026-11-11-adversarial/corpus.json').read_text(encoding='utf-8'))
    if hashlib.sha256((ROOT/'internal_tests/2026-11-11-adversarial/corpus.json').read_bytes()).hexdigest() != guard['corpus_sha256']:
        raise ValueError('Roster corpus changed')
    if len(rows) != 18 or len(historical) != 10 or len(corpus) != 3:
        raise ValueError('Frozen roster scope changed')
    context = [{'case':c['id'],'source_rules':len(c['source']), 'source_text_utf8_bytes':sum(len(r['text'].encode('utf-8')) for r in c['source'])} for c in corpus]
    return {'version':json.loads((ROOT/'release.json').read_text(encoding='utf-8'))['content_revision'],'source_sha256':hashlib.sha256(source).hexdigest(),'qualified':False,
            'scope':'Default primary labels, all cases and dimensions. Descriptive counts in alphabetical order; no model ranks or qualified PBI.',
            'context_note':'Each request uses one short synthetic case, not a full repository. Prompt-token range includes instructions and payload and is provider-tokenizer dependent. Source byte counts exclude identifiers and separators. Advertised context is a catalogue ceiling, not tested capacity.',
            'cases':context,'families':1,'repetitions':3,'rows':rows,'historical_diagnostics':historical,
            'external_reference_count':35,'external_suites_executed':0,'reviewer_diagnostics_included':False}


def outputs():
    d=build();rows=d['rows'];out={BASE/'model-roster.json':(json.dumps(d,indent=2)+'\n').encode()}
    stream=io.StringIO(newline='');w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    out[BASE/'model-roster.csv']=stream.getvalue().encode()
    display=lambda x:'N/A' if x is None else str(x)
    body=''.join('<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in [r['name'],r['provider'],f"{r['label_matches']}/{r['assigned_labels']}",f"{100*r['agreement_received']:.1f}%" if r['agreement_received'] is not None else 'N/A',r['missing_labels'],r['reasoning'],f"{display(r['observed_prompt_tokens_min'])} to {display(r['observed_prompt_tokens_max'])}",f"{r['complete_calls']}/{r['assigned_calls']}"])+'</tr>' for r in rows)
    block=f'''<!-- ROSTER:START --><section class="wrap calibration-section" id="model-roster"><div class="section-heading"><div><p class="eyebrow">Configurations and evidence scope</p><h2>Model roster</h2></div><p>Alphabetical configurations, frozen primary labels and all three cases. Agreement uses received classifications; missing classifications retain their assigned opportunities.</p></div><p>18 configurations in the Policy Interpretation; one authored source group; three repetitions. Execution uses the OpenRouter API, with the serving provider recorded separately. Each request sees one case. The 10 historical adapter configurations remain a separate cohort. The 35 benchmark references are methodological comparisons, not suites run on these models.</p><div class="calibration-toolbar"><a href="downloads/blueprintbench/model-roster.csv" download>Export roster CSV</a><a href="downloads/blueprintbench/model-roster.json" download>Export full configuration JSON</a><a href="#workspace">Explore observations ↗</a></div><div class="roster-scroll"><table><caption>Default-scope internal observations. No quality, charge or time ranks are assigned.</caption><thead><tr><th>Model</th><th>Serving provider</th><th>Matches / assigned</th><th>Agreement / received</th><th>Missing</th><th>Reasoning</th><th>Observed input tokens per call</th><th>Complete calls</th></tr></thead><tbody>{body}</tbody></table></div><p>Observed input tokens include instructions and payload. They are not the advertised context window or evidence of 100 MB processing. Exact configurations, output caps, catalogue ceilings, campaign identities and raw-record links are in the JSON export.</p></section><!-- ROSTER:END -->'''
    p=ROOT/'web/PALO_BlueprintBench_Leaderboard.html';s=p.read_text(encoding='utf-8')
    if '<!-- ROSTER:START -->' in s:s=re.sub(r'<!-- ROSTER:START -->.*?<!-- ROSTER:END -->',lambda _:block,s,flags=re.S)
    else:
        assert '</main>' in s, 'Missing roster insertion anchor'
        s=s.replace('</main>',block+'\n</main>')
    # Make the explanatory roster discoverable without changing ranking semantics.
    out[p]=s.encode()
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    for path,body in outputs().items():
        if args.check:assert path.read_bytes()==body,str(path)
        else:path.write_bytes(body)
    print('Roster ' + ('verified' if args.check else 'built') + ': 18 internal, 10 historical, 35 external references not executed')
