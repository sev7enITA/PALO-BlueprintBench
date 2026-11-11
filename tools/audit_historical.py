"""Reconstruct adapter diagnostics from the frozen archive; no model calls."""
import collections
import hashlib
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'evidence/development-2026-11-10'

def audit():
    rows = json.loads((ARCHIVE / 'recorded-audit.json').read_text(encoding='utf-8'))
    kinds = collections.defaultdict(lambda: {'proposed': 0, 'passed': 0})
    causes = collections.Counter()
    models = {}
    for row in rows:
        model = models.setdefault(row['model'], {'assigned': 3, 'attempted': 0, 'proposed': 0, 'passed': 0, 'archive_cost_usd': Decimal(0), 'attempts_without_cost': 0})
        model['attempted'] += 1
        model['proposed'] += row['raw_claims']
        model['passed'] += row['mechanically_valid']
        for claim in row.get('validation', []):
            kinds[claim['kind']]['proposed'] += 1
            kinds[claim['kind']]['passed'] += int(claim['valid'])
            if not claim['valid']:
                graph = any('missing from the extracted' in issue or 'Unexpected entity' in issue for issue in claim['issues'])
                source = any('evidence' in issue for issue in claim['issues'])
                causes['both' if graph and source else 'contract_only' if graph else 'source_only' if source else 'other'] += 1
        cost = row.get('cost_usd')
        if cost is None:
            model['attempts_without_cost'] += 1
        else:
            model['archive_cost_usd'] += Decimal(str(cost))
    ledger_file = ROOT / 'docs/historical-ledger-correction.json'
    if ledger_file.exists():
        ledger = json.loads(ledger_file.read_text(encoding='utf-8'))
        for model_id, model in models.items():
            entries = [e for e in ledger['entries'] if e['model'] == model_id]
            known = [e for e in entries if e['state'] == 'reported' and e['charged_microusd'] is not None]
            model['ledger_reported_microusd'] = sum(e['charged_microusd'] for e in known)
            model['ledger_known_attempts'] = len(known)
            model['ledger_unknown_attempts'] = len(entries) - len(known)
            model['ledger_status'] = 'reconstructible local accounting; not invoice reconciliation'
    passages = []
    for path in sorted(ARCHIVE.glob('*probe-request.json')):
        units = json.loads(json.loads(path.read_text(encoding='utf-8'))['messages'][1]['content'])
        passages.append({'file': path.name, 'source_units': len(units), 'characters': sum(len(u['text']) for u in units), 'utf8_bytes': sum(len(u['text'].encode('utf-8')) for u in units), 'request_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    for model in models.values():
        model['archive_cost_usd'] = str(model['archive_cost_usd'])
        model['not_run'] = model['assigned'] - model['attempted']
    return {'scope': 'Historical adapter smoke tests; no semantic gold or model ranking', 'passages': passages, 'total_passage_utf8_bytes': sum(p['utf8_bytes'] for p in passages), 'by_kind': dict(sorted(kinds.items())), 'rejection_causes': dict(sorted(causes.items())), 'models': models, 'cost_limit': 'Archived recorded-audit.cost_usd only. Missing costs remain unknown. Provider accounting and former explorer totals are not invoice reconciliation.', 'replay_limit': 'Replays frozen checker counts; original HTTP response bytes and trusted production time are not established.'}

if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
