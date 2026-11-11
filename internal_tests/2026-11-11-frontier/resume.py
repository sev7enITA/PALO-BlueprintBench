"""Resume remaining assignments, reserving full ceilings for unknown charges.

Accounting-only amendment: no prompt, model, schedule, retry or output change.
Original records and failed assignments remain untouched.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
API = 'https://openrouter.ai/api/v1'

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')

def load(path):
    return json.loads(path.read_bytes().decode('utf-8'))

def authenticated(path, key):
    request = urllib.request.Request(API + path, headers={'Authorization': 'Bearer ' + key})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)['data']

def verify_frozen(manifest):
    for name, expected in manifest['files'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen input changed: ' + name)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key-file', type=Path)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--limit', type=int, default=54)
    args = parser.parse_args()
    manifest = load(ROOT / 'manifest.json')
    verify_frozen(manifest)
    models = load(ROOT / 'models.json')
    corpus = load(ROOT / 'corpus.json')
    schema = load(ROOT / 'verification.schema.json')
    schedule = []
    for repetition in range(1, 4):
        for case in corpus:
            for track in ['translation', 'verification']:
                for model in models[repetition - 1:] + models[:repetition - 1]:
                    schedule.append((repetition, case, track, model))
    if not args.execute:
        print(json.dumps({'status': 'preflight', 'assigned': len(schedule), 'models': [m['id'] for m in models]}))
        return
    key = args.key_file.read_text().strip() if args.key_file else os.environ['OPENROUTER_API_KEY']
    runs = ROOT / 'runs'
    runs.mkdir(exist_ok=True)
    existing = [load(p) for p in runs.glob('*/record.json')]
    if any(r.get('cost_status') == 'unknown' and not isinstance(r.get('reserved_usd'), (int, float)) for r in existing):
        raise SystemExit('Unknown cost without a reservation: reconcile before resuming.')
    if any(not (p / 'record.json').exists() for p in runs.iterdir() if p.is_dir()):
        raise SystemExit('Interrupted request: preserve evidence and reconcile before resuming.')
    spent = sum(r['reserved_usd'] if r.get('cost_status') == 'unknown' else r['cost_usd'] for r in existing)
    executed = 0
    blocked = None
    for repetition, case, track, model in schedule:
        slug = model['id'].replace('/', '__')
        ident = f'{repetition}-{case["id"]}-{track}-{slug}'
        dest = runs / ident
        if (dest / 'record.json').exists():
            continue
        if executed >= args.limit:
            break
        messages = load(ROOT / 'prompts' / f'{track}-{case["id"]}.json')
        payload = {'model': model['id'], 'messages': messages, 'max_tokens': 32768,
                   'reasoning': {'effort': 'high', 'exclude': True},
                   'provider': {'only': [model['provider']], 'allow_fallbacks': False, 'require_parameters': True},
                   'stream': False}
        if track == 'verification':
            payload['response_format'] = {'type': 'json_schema', 'json_schema': {'name': 'procurement_judgments', 'strict': True, 'schema': schema}}
        body = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        # Deliberately loose bound for prompt tokens + gateway framing. API key limit is a second cap.
        reservation = ((len(body) + 4096) * float(model['pricing']['prompt']) + 32768 * float(model['pricing']['completion'])) * 1.10
        key_state = authenticated('/key', key)
        account = authenticated('/credits', key)
        key_remaining = key_state.get('limit_remaining')
        account_remaining = account['total_credits'] - account['total_usage']
        if key_remaining is None or reservation > min(key_remaining, account_remaining, manifest['new_campaign_ceiling_usd'] - spent):
            blocked = 'insufficient_reserved_headroom'
            break
        dest.mkdir()
        (dest / 'request.json').write_bytes(body)
        started = dt.datetime.now(dt.timezone.utc).isoformat()
        record = {'id': ident, 'model': model['id'], 'pinned_provider': model['provider'],
                  'case': case['id'], 'track': track, 'repetition': repetition,
                  'started_at': started, 'request_sha256': hashlib.sha256(body).hexdigest(),
                  'reserved_usd': reservation, 'cost_status': 'unknown', 'cost_usd': None,
                  'state': 'fail', 'qualification': 'internal_tests', 'response_bytes_original': True}
        write(dest / 'reservation.json', {'at': started, 'reserved_usd': reservation, 'campaign_spent_before_usd': spent})
        request = urllib.request.Request(API + '/chat/completions', data=body, headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json', 'HTTP-Referer': 'https://paloframework.org/PALO_BlueprintBench.html', 'X-Title': 'PALO internal procurement baseline tests'})
        t = time.monotonic()
        try:
            try:
                with urllib.request.urlopen(request, timeout=180) as response:
                    raw = response.read()
                    record['http_status'] = response.status
                    headers = {k: v for k, v in response.headers.items() if k.lower() in ['date','content-type','x-request-id','server']}
            except urllib.error.HTTPError as error:
                raw = error.read()
                record['http_status'] = error.code
                headers = {}
            (dest / 'response.json').write_bytes(raw)
            write(dest / 'response-headers.json', headers)
            record['response_sha256'] = hashlib.sha256(raw).hexdigest()
            result = json.loads(raw)
            record['provider_request_id'] = result.get('id')
            record['returned_model'] = result.get('model')
            record['returned_provider'] = result.get('provider')
            usage = result.get('usage', {})
            record['usage'] = usage
            if type(usage.get('cost')) in [int, float] and usage['cost'] >= 0:
                record.update(cost_status='provider_reported', cost_usd=usage['cost'])
                spent += usage['cost']
            choices = result.get('choices', [])
            if choices:
                choice = choices[0]
                record['finish_reason'] = choice.get('finish_reason')
                content = choice.get('message', {}).get('content')
                if isinstance(content, str):
                    (dest / 'output.txt').write_bytes(content.encode('utf-8'))
                    record['output_sha256'] = hashlib.sha256(content.encode('utf-8')).hexdigest()
                    record['state'] = 'completed' if choice.get('finish_reason') == 'stop' and content.strip() else 'incomplete'
                else:
                    record['error'] = 'Response has no text content'
            elif result.get('error'):
                record['error'] = result['error']
        except (OSError, ValueError) as error:
            record['error'] = {'type': type(error).__name__, 'message': str(error)[:200]}
        record['elapsed_seconds'] = time.monotonic() - t
        record['finished_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
        write(dest / 'record.json', record)
        executed += 1
        print(json.dumps({'model': model['id'], 'case': case['id'], 'track': track, 'repetition': repetition, 'state': record['state'], 'cost_usd': record['cost_usd'], 'spent_usd': round(spent, 6), 'seconds': round(record['elapsed_seconds'], 2)}), flush=True)
        if record['cost_status'] == 'unknown':
            blocked = 'unknown_cost_requires_reconciliation'
            break
    all_records = [load(p) for p in sorted(runs.glob('*/record.json'))]
    summary = {'status': 'blocked' if blocked else 'completed' if len(all_records) == len(schedule) else 'partial', 'blocker': blocked, 'assigned_calls': len(schedule), 'recorded_calls': len(all_records), 'not_run': len(schedule) - len(all_records), 'provider_reported_cost_usd': sum(r.get('cost_usd') or 0 for r in all_records), 'unknown_costs': sum(r['cost_status'] == 'unknown' for r in all_records), 'qualified': False, 'label': 'internal_tests'}
    (ROOT / 'execution-summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary), flush=True)

if __name__ == '__main__':
    main()
