"""Account for assigned development calls; no inference or gold adjudication."""
from collections import Counter
from pathlib import Path
import argparse
import json

ROOT = Path(__file__).resolve().parents[1]
STUDIES = ('frontier', 'expansion', 'legacy-extension', 'next-cycle', 'real-procurement')


def inspect(root):
    analysis = json.loads((root / 'analysis.json').read_text(encoding='utf-8'))
    assigned = analysis.get('assigned_calls', analysis.get('assigned_requests', analysis.get('summary', {}).get('assigned_calls')))
    rows = []
    for path in sorted((root / 'runs').glob('*/record.json')):
        record = json.loads(path.read_text(encoding='utf-8'))
        if record.get('id') != path.parent.name:
            raise ValueError('Record ID does not match run directory: ' + str(path))
        state = record.get('state')
        if state not in ('completed', 'incomplete', 'fail', 'not_run'):
            raise ValueError('Unknown execution state: ' + str(state))
        reason = bool(record.get('error') or record.get('stop_reason') or record.get('not_run_reason') or record.get('finish_reason') in ('length', 'error', 'content_filter'))
        if not reason and state == 'incomplete' and (path.parent / 'get_generation.json').exists():
            receipt = json.loads((path.parent / 'get_generation.json').read_text(encoding='utf-8'))['data']
            reason = bool(receipt.get('finish_reason') is None and receipt.get('upstream_inference_cost') is not None or receipt.get('upstream_requests'))
            # Some provider error receipts have a nested upstream status.
            reason = reason or '502' in json.dumps(receipt)
        rows.append({'id': record['id'], 'state': state, 'reason_documented': state == 'completed' or reason})
    ids = [r['id'] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate assignment IDs in ' + str(root))
    counts = Counter(r['state'] for r in rows)
    return {'assigned': assigned, 'record_files': len(rows), 'completed': counts['completed'],
            'not_run': counts['not_run'], 'incomplete_or_failed': len(rows)-counts['completed']-counts['not_run'],
            'unaccounted_assignments': max(0, assigned-len(rows)),
            'exceptions_without_reason': [r['id'] for r in rows if not r['reason_documented']],
            'accounted': len(rows)==assigned and all(r['reason_documented'] for r in rows)}


def report():
    return {'version': '0.1.0', 'scope': 'Five current internal studies. Record presence and reported reason are checked; this does not verify billing, semantic quality or independent validation.',
            'studies': {name: inspect(ROOT / 'internal_tests' / ('2026-11-11-' + name)) for name in STUDIES},
            'historical_adapter': {'recorded_attempts': 26, 'offline_replay': '26 of 26 retained attempts reproduced',
                                   'limitations': 'Original HTTP response bytes and complete provider ledger are unavailable; blocked assignments are documented separately in historical corrections.'}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--check', action='store_true'); args = parser.parse_args()
    result = report(); output = ROOT / 'docs/study-accountability.json'; text = json.dumps(result, indent=2) + '\n'
    if not all(v['accounted'] for v in result['studies'].values()):
        raise SystemExit('Unaccounted assignments or unmotivated exceptions: ' + json.dumps(result['studies']))
    if args.check:
        if output.read_text(encoding='utf-8') != text:
            raise SystemExit('Study accountability report is stale')
    else:
        output.write_text(text, encoding='utf-8')
    print(json.dumps(result['studies']))
