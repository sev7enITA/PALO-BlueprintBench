"""Execute frozen feasibility assignments serially, with no retries and conservative cost guards."""
import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
API = 'https://openrouter.ai/api/v1'


def load(path):
    return json.loads(path.read_bytes().decode('utf-8'))


def write(path, value, exclusive=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x' if exclusive else 'w', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def number(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('Expected finite nonnegative budget value')
    return float(value)


def price(value):
    if isinstance(value, str) and value.startswith('$'):
        match = re.fullmatch(r'\$([0-9.]+)/M tokens', value)
        if not match:
            raise ValueError('Unsupported token price')
        return number(float(match.group(1)) / 1_000_000)
    return number(float(value))


def rates(model, prompt_bound):
    pricing = model['endpoint']['pricing']
    applicable = [pricing] + [p for p in pricing.get('overrides', []) if prompt_bound >= p.get('min_prompt_tokens', 0)]
    input_keys = ('prompt', 'input_cache_read', 'input_cache_write', 'input_cache_write_1h')
    input_rate = max(price(p[k]) for p in applicable for k in input_keys if k in p)
    output_rate = max(price(p[k]) for p in applicable for k in ('completion', 'internal_reasoning') if k in p)
    return input_rate, output_rate


def payload_for(task, model):
    return {'model': model['id'], 'messages': task['messages'], 'max_tokens': 32768,
        'reasoning': {'effort': 'high', 'exclude': True},
        'provider': {'only': [model['provider']], 'allow_fallbacks': False, 'require_parameters': True},
        'stream': False, 'response_format': {'type': 'json_schema', 'json_schema': {
            'name': 'palo_internal_' + task['track'], 'strict': True, 'schema': task['response_schema']}}}


def reservation_for(body, model):
    prompt_bound = len(body) + 4096
    input_rate, output_rate = rates(model, prompt_bound)
    return (prompt_bound * input_rate + 32768 * output_rate) * 1.10


def authenticated(path, key):
    request = urllib.request.Request(API + path, headers={'Authorization': 'Bearer ' + key})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)['data']


def budget_headroom(manifest, account, key_state, spent, baseline_usage, outstanding=0):
    usage = max(number(account['total_usage']), number(baseline_usage) + number(spent))
    total = number(account['total_credits'])
    previous = number(manifest['previous_unknown_cost_reserve_usd'])
    pending = number(outstanding)
    return min(number(manifest['cumulative_ceiling_usd']) - usage - previous - pending,
        number(manifest['new_campaign_ceiling_usd']) - spent - pending,
        total - usage - previous - pending,
        number(key_state['limit_remaining']) - pending)


def verify_frozen(manifest, root=ROOT):
    boundary = root.parents[1].resolve()
    for name, expected in manifest['files'].items():
        path = (root / name).resolve()
        if not path.is_relative_to(boundary):
            raise ValueError('Frozen path escapes repository')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen input changed: ' + name)


def resume_records(root=ROOT, schedule=None, bodies=None, models=None):
    runs = root / 'runs'
    records = []
    if not runs.exists():
        return records
    for directory in sorted(runs.iterdir()):
        if not directory.is_dir():
            continue
        if not (directory / 'record.json').exists():
            raise ValueError('Orphan/pending reservation: reconcile before resume: ' + directory.name)
        record = load(directory / 'record.json')
        if record.get('cost_status') == 'unknown':
            raise ValueError('Unknown cost: reconcile before resume: ' + directory.name)
        number(record['cost_usd'])
        if schedule is not None:
            assignments = {a['id']: a for a in schedule}
            expected = assignments.get(directory.name)
            if expected is None or any(record.get(k) != expected[k] for k in ('id', 'model', 'task_id')):
                raise ValueError('Record assignment mismatch: ' + directory.name)
            if record.get('pinned_provider') != models[expected['model']]['provider']:
                raise ValueError('Record provider mismatch')
            if record.get('returned_identity_matches_pin') is not True:
                raise ValueError('Returned provider/model mismatch must be reconciled before resume')
            if record.get('cost_status') != 'provider_reported':
                raise ValueError('Unrecognized cost evidence status')
            if record.get('state') not in ('completed', 'incomplete', 'fail'):
                raise ValueError('Unrecognized record state')
            if not all(record.get(field) for field in ('request_sha256', 'response_sha256', 'manifest_sha256', 'source_packet_sha256')):
                raise ValueError('Required receipt provenance missing')
            if record['manifest_sha256'] != hashlib.sha256((root / 'manifest.json').read_bytes()).hexdigest():
                raise ValueError('Manifest receipt mismatch')
            if (directory / 'output.txt').exists() and not record.get('output_sha256'):
                raise ValueError('Output byte hash missing')
            if (directory / 'request.json').read_bytes() != bodies[directory.name]:
                raise ValueError('Frozen request payload mismatch')
            for filename, field in (('request.json', 'request_sha256'), ('response.json', 'response_sha256'), ('output.txt', 'output_sha256')):
                if field in record and hashlib.sha256((directory / filename).read_bytes()).hexdigest() != record[field]:
                    raise ValueError('Archived byte hash mismatch: ' + filename)
            response = load(directory / 'response.json')
            if response.get('usage', {}).get('cost') != record['cost_usd']:
                raise ValueError('Archived usage cost mismatch')
        records.append(record)
    return records


def make_summary(schedule, records, manifest, baseline, last_account, blocked):
    known = sum(r.get('cost_usd') or 0 for r in records)
    unknown = [r for r in records if r.get('cost_status') == 'unknown']
    reserve = sum(r['reserved_usd'] for r in unknown)
    reported_usage = last_account.get('total_usage') if last_account else None
    conservative = max(reported_usage or 0, baseline + known) + manifest['previous_unknown_cost_reserve_usd'] + reserve
    return {'status': 'blocked' if blocked else 'completed' if len(records) == len(schedule) else 'partial',
        'blocker': blocked, 'assigned_calls': len(schedule), 'recorded_calls': len(records),
        'not_run': len(schedule) - len(records), 'known_campaign_cost_usd': known,
        'provider_reported_cost_usd': known, 'unknown_costs': len(unknown),
        'unknown_cost_reserve_usd': reserve, 'previous_unknown_cost_reserve_usd': manifest['previous_unknown_cost_reserve_usd'],
        'account_usage_before_usd': baseline, 'account_usage_after_usd': reported_usage,
        'conservative_cumulative_committed_usd': conservative,
        'cumulative_ceiling_usd': manifest['cumulative_ceiling_usd'],
        'campaign_ceiling_usd': manifest['new_campaign_ceiling_usd'],
        'authorised_total_usd': manifest['cumulative_ceiling_usd'],
        'account_usage_usd': reported_usage,
        'previous_unresolved_reserve_usd': manifest['previous_unknown_cost_reserve_usd'],
        'current_unknown_reserve_usd': reserve, 'campaign_known_usd': known,
        'conservative_cumulative_bound_usd': conservative,
        'remaining_authorised_headroom_usd': manifest['cumulative_ceiling_usd'] - conservative,
        'budget_compliant': conservative <= manifest['cumulative_ceiling_usd'] and known + reserve <= manifest['new_campaign_ceiling_usd'],
        'qualified': False, 'label': 'internal_engineering_feasibility', 'updated_at': now()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key-file', type=Path)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--limit', type=int, default=60)
    args = parser.parse_args()
    if args.limit < 0:
        raise SystemExit('Limit must be nonnegative')
    manifest = load(ROOT / 'manifest.json')
    verify_frozen(manifest)
    tasks = {task['id']: task for task in load(ROOT / 'tasks.json')}
    models = {model['id']: model for model in load(ROOT / 'models.json')}
    schedule = load(ROOT / 'schedule.json')
    assert len(schedule) == manifest['assigned_calls'] == 60
    assert len({assignment['id'] for assignment in schedule}) == 60
    bodies = {}
    reservations = []
    for assignment in schedule:
        task, model = tasks[assignment['task_id']], models[assignment['model']]
        body = json.dumps(payload_for(task, model), ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        bodies[assignment['id']] = body
        reservations.append(reservation_for(body, model))
    records = resume_records(ROOT, schedule, bodies, models)
    if not args.execute:
        print(json.dumps({'status': 'dry_run_no_network_or_inference', 'assigned_calls': len(schedule),
            'recorded_calls': len(records), 'maximum_single_reservation_usd': max(reservations),
            'worst_case_all_reservations_usd': sum(reservations), 'campaign_cap_usd': 12, 'cumulative_cap_usd': 40,
            'note': 'Worst-case reservations need not fit all assignments; headroom is checked serially before every call.'}))
        return
    key = args.key_file.read_text(encoding='utf-8').strip() if args.key_file else os.environ.get('OPENROUTER_API_KEY', '').strip()
    if not key:
        raise SystemExit('Supply --key-file or OPENROUTER_API_KEY; no credential was provided.')
    before_path = ROOT / 'budget-before.json'
    account = authenticated('/credits', key)
    key_state = authenticated('/key', key)
    if not before_path.exists():
        write(before_path, {'at': now(), 'account_total_usage': number(account['total_usage']),
            'account_total_credits': number(account['total_credits']), 'key_remaining': number(key_state['limit_remaining'])})
    baseline = load(before_path)['account_total_usage']
    spent = sum(r['cost_usd'] for r in records)
    done = {r['id'] for r in records}
    blocked = None
    executed = 0
    for assignment in schedule:
        if assignment['id'] in done:
            continue
        if executed >= args.limit:
            break
        model = models[assignment['model']]
        body = bodies[assignment['id']]
        reservation = reservation_for(body, model)
        try:
            account = authenticated('/credits', key)
            key_state = authenticated('/key', key)
            headroom = budget_headroom(manifest, account, key_state, spent, baseline)
        except (OSError, ValueError, KeyError):
            blocked = 'budget_state_unavailable'
            break
        if reservation > headroom:
            blocked = 'insufficient_reserved_headroom'
            break
        dest = ROOT / 'runs' / assignment['id']
        dest.mkdir(parents=True, exist_ok=False)
        (dest / 'request.json').write_bytes(body)
        record = {**assignment, 'pinned_provider': model['provider'], 'started_at': now(),
            'source_packet_sha256': tasks[assignment['task_id']]['source_packet_sha256'],
            'manifest_sha256': hashlib.sha256((ROOT / 'manifest.json').read_bytes()).hexdigest(),
            'request_sha256': hashlib.sha256(body).hexdigest(), 'reserved_usd': reservation,
            'cost_status': 'unknown', 'cost_usd': None, 'state': 'fail', 'qualified': False,
            'qualification': 'internal_engineering_feasibility', 'response_bytes_original': True}
        write(dest / 'reservation.json', {'at': now(), 'reserved_usd': reservation,
            'headroom_before_usd': headroom, 'account_usage': account['total_usage'],
            'campaign_spent_before_usd': spent, 'key_remaining': key_state['limit_remaining']})
        request = urllib.request.Request(API + '/chat/completions', data=body, headers={
            'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json',
            'HTTP-Referer': 'https://paloframework.org/PALO_BlueprintBench.html',
            'X-Title': 'PALO internal engineering feasibility'})
        started = time.monotonic()
        try:
            try:
                with urllib.request.urlopen(request, timeout=300) as response:
                    raw = response.read()
                    record['http_status'] = response.status
                    headers = {k: v for k, v in response.headers.items() if k.lower() in ('date', 'content-type', 'x-request-id', 'server')}
            except urllib.error.HTTPError as error:
                raw = error.read()
                record['http_status'] = error.code
                headers = {}
            (dest / 'response.json').write_bytes(raw)
            write(dest / 'response-headers.json', headers)
            record['response_sha256'] = hashlib.sha256(raw).hexdigest()
            result = json.loads(raw)
            record.update(provider_request_id=result.get('id'), returned_model=result.get('model'), returned_provider=result.get('provider'))
            returned_model = result.get('model')
            returned_provider = result.get('provider')
            model_matches = isinstance(returned_model, str) and (returned_model == model['id'] or returned_model.startswith(model['id'] + '-'))
            provider_matches = returned_provider == model['endpoint']['provider_name']
            record['returned_identity_matches_pin'] = model_matches and provider_matches
            usage = result.get('usage') or {}
            record['usage'] = usage
            if type(usage.get('cost')) in (int, float) and math.isfinite(usage['cost']) and usage['cost'] >= 0:
                record.update(cost_status='provider_reported', cost_usd=usage['cost'])
                spent += usage['cost']
            choices = result.get('choices') or []
            if choices:
                choice = choices[0]
                record['finish_reason'] = choice.get('finish_reason')
                content = (choice.get('message') or {}).get('content')
                if isinstance(content, str):
                    output = content.encode('utf-8')
                    (dest / 'output.txt').write_bytes(output)
                    record['output_sha256'] = hashlib.sha256(output).hexdigest()
                    record['state'] = 'completed' if record['http_status'] == 200 and choice.get('finish_reason') == 'stop' and content.strip() else 'incomplete'
            if result.get('error'):
                record['error'] = result['error']
        except (OSError, ValueError, TypeError, AttributeError) as error:
            record['error'] = {'type': type(error).__name__, 'message': 'Response or transport failure; inspect archived evidence.'}
        record['elapsed_seconds'] = time.monotonic() - started
        record['finished_at'] = now()
        write(dest / 'record.json', record)
        records.append(record)
        executed += 1
        print(json.dumps({'id': assignment['id'], 'state': record['state'], 'cost_usd': record['cost_usd'], 'spent_usd': spent}), flush=True)
        if record['cost_status'] == 'unknown':
            blocked = 'unknown_cost_requires_reconciliation'
            break
        if record.get('returned_identity_matches_pin') is not True:
            blocked = 'returned_identity_mismatch_or_unavailable'
            break
        if record['cost_usd'] > reservation:
            blocked = 'provider_cost_exceeded_reservation'
            break
    try:
        account = authenticated('/credits', key)
    except (OSError, ValueError):
        pass
    summary = make_summary(schedule, records, manifest, baseline, account, blocked)
    write(ROOT / 'execution-summary.json', summary, exclusive=False)
    write(ROOT / 'budget-final.json', summary, exclusive=False)
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
