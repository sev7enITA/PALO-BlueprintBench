"""Freeze a bounded internal engineering campaign before any inference dispatch."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.request
import prepare

ROOT = Path(__file__).resolve().parent
API = 'https://openrouter.ai/api/v1'


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write('\n')


def main():
    if (ROOT / 'manifest.json').exists() or (ROOT / 'runs').exists():
        raise SystemExit('Existing freeze or run evidence: refusing to overwrite.')
    models = json.loads((ROOT / 'models.json').read_text(encoding='utf-8'))
    provenance = []
    for model in models:
        url = API + '/models/' + model['id'] + '/endpoints'
        with urllib.request.urlopen(url, timeout=30) as response:
            raw = response.read()
        metadata = json.loads(raw)['data']
        tag = 'google-vertex/us' if model['id'] == 'google/gemini-4-argon' else model['provider']
        selected = [endpoint for endpoint in metadata['endpoints'] if endpoint['tag'] == tag]
        if len(selected) != 1 or selected[0]['status'] != 0:
            raise ValueError('Pinned endpoint unavailable: ' + tag)
        endpoint = selected[0]
        required = {'reasoning', 'max_tokens', 'response_format', 'structured_outputs'}
        if not required <= set(endpoint['supported_parameters']):
            raise ValueError('Pinned endpoint lacks required parameters: ' + tag)
        name = 'endpoint-' + model['id'].replace('/', '__') + '.json'
        (ROOT / name).write_bytes(raw)
        provenance.append({'model': model['id'], 'url': url, 'archive': name,
            'retrieved_at': dt.datetime.now(dt.timezone.utc).isoformat(),
            'previous_pin': model['provider'], 'selected_pin': tag,
            'rationale': 'Google AI Studio standard and Vertex global endpoints report status -2 at freeze; select available Google Vertex US status 0 before freeze. No fallback.' if tag == 'google-vertex/us' else 'Retain exact available endpoint before freeze.'})
        model['provider'] = tag
        model['endpoint'] = endpoint
    (ROOT / 'models.json').write_text(json.dumps(models, indent=2) + '\n', encoding='utf-8')
    write(ROOT / 'endpoint-selection.json', provenance)
    tasks = prepare.build_tasks()
    assert len(tasks) == 20 and len(models) == 3
    for task in tasks:
        if 'policy-transition-P05' in task['expected_ids']:
            assert 'policy-transition-P05' in task.get('unscored_probe_ids', [])
    schedule = []
    for index, task in enumerate(tasks):
        for model in models[index % 3:] + models[:index % 3]:
            schedule.append({'id': f'{len(schedule)+1:03d}-' + task['id'] + '-' + model['id'].replace('/', '__'),
                'task_id': task['id'], 'model': model['id'], 'repetition': 1})
    write(ROOT / 'tasks.json', tasks)
    write(ROOT / 'schedule.json', schedule)
    files = [ROOT / name for name in ('tasks.json', 'schedule.json', 'models.json', 'endpoint-selection.json',
        'prepare.py', 'contracts.py', 'runner.py', 'test_runner.py', 'freeze_campaign.py', 'analyse.py')]
    files += list(ROOT.glob('endpoint-*.json'))
    files += list((prepare.ROOT / 'study/next-cycle').rglob('*.json'))
    files += list((prepare.ROOT / 'study/next-cycle').rglob('*.md'))
    files += [ROOT / 'review/semantic-preflight.json', ROOT / 'review/semantic-preflight.md']
    import os
    hashes = {os.path.relpath(path, ROOT): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(set(files))}
    manifest = {'id': 'next-cycle-internal-feasibility-2026-11-11',
        'frozen_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'assigned_calls': 60, 'tasks': 20,
        'models': 3, 'repetitions': 1, 'execution': 'serial_round_robin_no_retries',
        'new_campaign_ceiling_usd': 12, 'cumulative_ceiling_usd': 40,
        'previous_unknown_cost_reserve_usd': 0.481264729,
        'max_output_tokens': 32768, 'reasoning_effort': 'high',
        'budget_reservation': 'UTF-8 request bytes plus 4096 framing tokens; 32768 output tokens; highest applicable pinned-endpoint rates including cache-write; 10 percent safety.',
        'qualification': 'internal_engineering_feasibility', 'qualified': False,
        'comparison_gate_exception': {'authorized': True, 'purpose': 'User-authorized engineering feasibility before human adjudicators are available.',
            'prohibited_claims': ['independent validation', 'semantic accuracy', 'quality ranking', 'cost ranking', 'time ranking'],
            'labels': 'assistant_draft', 'human_adjudication_completed': False},
        'unscored_probe_ids': ['policy-transition-P05'], 'files': hashes,
        'integrity_note': 'Local hashes prove consistency only, not independent preregistration or trusted time.'}
    write(ROOT / 'manifest.json', manifest)
    print(json.dumps({'status': 'frozen', 'assigned_calls': 60, 'manifest_sha256': hashlib.sha256((ROOT / 'manifest.json').read_bytes()).hexdigest(), 'paid_calls': 0}))


if __name__ == '__main__':
    main()
