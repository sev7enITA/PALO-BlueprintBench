"""Recompute internal test counts from frozen labels and original model outputs."""
import collections
import hashlib
import json
from pathlib import Path
import statistics
from decimal import Decimal
import jsonschema

ROOT = Path(__file__).resolve().parent
LABELS = ['supported', 'contradicted', 'not_established']

def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(path.read_bytes().decode('utf-8'), object_pairs_hook=pairs)

def translation_claims(raw):
    import re
    claims, ignored, offset = [], [], 0
    for line in raw.splitlines(keepends=True):
        body = line.rstrip('\r\n')
        if body and any(c not in ' \t' for c in body):
            match = re.match(r'^(R\d{2}) :: (.+)$', body)
            claims.append({'id': f'c{len(claims)+1}', 'source_id': match.group(1) if match else None,
                           'text': body, 'span': [offset, offset + len(body)],
                           'text_sha256': hashlib.sha256(body.encode('utf-8')).hexdigest()})
        elif body:
            ignored.append({'span': [offset, offset + len(body)], 'reason': 'ASCII whitespace'})
        if len(body) < len(line):
            ignored.append({'span': [offset + len(body), offset + len(line)], 'reason': 'line separator'})
        offset += len(line)
    return claims, ignored

def assessment(record, directory, case, schema):
    expected = {p['id']: p for p in case['probes']}
    base = {'assigned_probes': len(expected), 'classified': 0, 'correct': 0,
            'missing': sorted(expected), 'duplicates': [], 'unknown_ids': [], 'schema_errors': [], 'contract_pass': False,
            'confusion': {label: {p: 0 for p in LABELS} for label in LABELS}, 'judgments': []}
    if record['state'] != 'completed' or not (directory / 'output.txt').exists():
        return base
    try:
        output = load(directory / 'output.txt')
        jsonschema.Draft202012Validator(schema).validate(output)
    except (ValueError, jsonschema.ValidationError) as error:
        base['schema_errors'] = [str(error)[:500]]
        return base
    grouped = collections.defaultdict(list)
    for item in output['judgments']:
        grouped[item['id']].append(item['verdict'])
    base['duplicates'] = sorted(k for k, v in grouped.items() if len(v) != 1)
    base['unknown_ids'] = sorted(set(grouped) - set(expected))
    for ident, gold in expected.items():
        values = grouped.get(ident, [])
        if len(values) != 1:
            continue
        prediction = values[0]
        base['classified'] += 1
        base['correct'] += int(prediction == gold['expected'])
        base['confusion'][gold['expected']][prediction] += 1
        base['judgments'].append({'id': ident, 'source_id': gold['source_id'], 'dimension': gold['dimension'], 'expected': gold['expected'], 'predicted': prediction, 'correct': prediction == gold['expected']})
    base['missing'] = sorted(set(expected) - {x['id'] for x in base['judgments']})
    base['contract_pass'] = not (base['missing'] or base['duplicates'] or base['unknown_ids'] or base['schema_errors'])
    return base

def analyse():
    manifest = load(ROOT / 'manifest.json')
    for name, expected in manifest['files'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    corpus = {c['id']: c for c in load(ROOT / 'corpus.json')}
    models = load(ROOT / 'models.json')
    schema = load(ROOT / 'verification.schema.json')
    records = []
    rows = []
    queue = {}
    for path in sorted((ROOT / 'runs').glob('*/record.json')):
        record = load(path)
        directory = path.parent
        assert hashlib.sha256((directory / 'request.json').read_bytes()).hexdigest() == record['request_sha256']
        if record.get('response_sha256'):
            actual_response_hash = hashlib.sha256((directory / 'response.json').read_bytes()).hexdigest()
            if (directory / 'response-redaction.json').exists():
                redaction = load(directory / 'response-redaction.json')
                assert record['state'] == 'fail' and not record.get('output_sha256')
                assert redaction['removed_json_pointers'] == ['/user_id']
                assert redaction['original_sha256'] == record['response_sha256']
                assert actual_response_hash == redaction['public_sha256']
            else:
                assert actual_response_hash == record['response_sha256']
        if record.get('output_sha256'):
            assert hashlib.sha256((directory / 'output.txt').read_bytes()).hexdigest() == record['output_sha256']
            response = load(directory / 'response.json')
            assert response['choices'][0]['message']['content'].encode('utf-8') == (directory / 'output.txt').read_bytes()
        records.append(record)
        if record['track'] == 'verification':
            row = assessment(record, directory, corpus[record['case']], schema)
            row.update(model=record['model'], case=record['case'], repetition=record['repetition'], record_id=record['id'])
            rows.append(row)
        elif (directory / 'output.txt').exists():
            raw = (directory / 'output.txt').read_bytes().decode('utf-8')
            claims, _ = translation_claims(raw)
            for claim in claims:
                key = record['case'] + ':' + claim['text_sha256']
                queue.setdefault(key, {'case': record['case'], 'source_id': claim['source_id'], 'text': claim['text'], 'text_sha256': claim['text_sha256'], 'occurrences': []})['occurrences'].append(record['id'])
    summaries = []
    for model in models:
        own = [r for r in records if r['model'] == model['id']]
        judged = [r for r in rows if r['model'] == model['id']]
        confusion = {label: {p: sum(r['confusion'][label][p] for r in judged) for p in LABELS} for label in LABELS}
        by_dimension = {}
        for case in corpus.values():
            for probe in case['probes']:
                by_dimension.setdefault(probe['dimension'], {'assigned': 0, 'correct': 0, 'classified': 0})['assigned'] += 3
        for r in judged:
            for j in r['judgments']:
                cell = by_dimension[j['dimension']]
                cell['classified'] += 1
                cell['correct'] += int(j['correct'])
        costs = [Decimal(str(r['cost_usd'])) for r in own if r.get('cost_usd') is not None]
        classified = sum(r['classified'] for r in judged)
        control_observed = sum(confusion['supported'].values())
        control_assigned = 108
        summaries.append({'id': model['id'], 'name': model['catalogue_name'], 'pinned_provider': model['provider'],
                          'assigned_calls': 18, 'recorded_calls': len(own), 'completed_calls': sum(r['state'] == 'completed' for r in own),
                          'not_run': 18-len(own), 'verification_assigned_probes': 324, 'verification_classified': classified,
                          'verification_correct': sum(r['correct'] for r in judged), 'verification_missing': 324-classified,
                          'verification_contract_pass_calls': sum(r['contract_pass'] for r in judged),
                          'verification_assigned_calls': 9,
                          'correct_over_assigned': sum(r['correct'] for r in judged)/324,
                          'false_alarms': sum(confusion['supported'][p] for p in ['contradicted','not_established']),
                          'false_alarm_rate': sum(confusion['supported'][p] for p in ['contradicted','not_established']) / control_assigned if control_observed == control_assigned else None,
                          'confusion': confusion, 'by_dimension': by_dimension,
                          'provider_reported_cost_usd': float(sum(costs)),
                          'cost_by_track_usd': {track: float(sum(Decimal(str(r['cost_usd'])) for r in own if r['track'] == track and r.get('cost_usd') is not None)) for track in ['translation','verification']}, 'unknown_cost_calls': len(own)-len(costs),
                          'latency_median_seconds': statistics.median(r['elapsed_seconds'] for r in own) if own else None,
                          'input_tokens': sum(r.get('usage',{}).get('prompt_tokens') or 0 for r in own),
                          'completion_tokens_including_reasoning': sum(r.get('usage',{}).get('completion_tokens') or 0 for r in own),
                          'reasoning_tokens_reported': sum((r.get('usage',{}).get('completion_tokens_details') or {}).get('reasoning_tokens') or 0 for r in own),
                          'reasoning_token_detail_complete': all('reasoning_tokens' in (r.get('usage',{}).get('completion_tokens_details') or {}) for r in own) and len(own)==18,
                          'by_case_repeat': [{k:r[k] for k in ['case','repetition','assigned_probes','classified','correct','missing','duplicates','unknown_ids','schema_errors','contract_pass']} for r in judged]})
    report = {'campaign_id': manifest['campaign_id'], 'status': 'internal_tests', 'qualified': False,
              'source_families': 1, 'cases': 3, 'source_rules': 36, 'verification_probes': 108, 'repetitions': 3,
              'assigned_calls': 54, 'recorded_calls': len(records), 'not_run': 54-len(records),
              'models': summaries, 'verification_rows': rows, 'translation_unique_texts_awaiting_internal_review': len(queue),
              'limitations': ['Original synthetic controls from one maintainer-authored family', 'Expected labels are assistant drafts, not independent gold', 'Verification judgments and source-indexed translation are separate tracks', 'No confidence intervals, independent validation, PBI score, model ranking or 100 MB throughput claim', 'Provider-reported costs are not invoices; exact hosted weights/runtime unavailable']}
    (ROOT / 'analysis.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8',newline='\n')
    (ROOT / 'translation-review-queue.json').write_text(json.dumps(queue, indent=2)+'\n', encoding='utf-8',newline='\n')
    return report

if __name__ == '__main__':
    result = analyse()
    print(json.dumps({'recorded_calls': result['recorded_calls'], 'assigned_calls': 54, 'internal_tests': True, 'models': [{k:m[k] for k in ['id','verification_correct','verification_classified','provider_reported_cost_usd']} for m in result['models']]}))
