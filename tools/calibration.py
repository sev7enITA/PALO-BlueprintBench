"""Replay internal semantic calibration. No model calls and no qualification path."""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'internal_tests/2026-11-11-calibration'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError('Duplicate JSON key: ' + key)
        obj[key] = value
    return obj


def parse(raw):
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def read(path):
    return parse(path.read_bytes().decode('utf-8'))


def reuse_key(rule, candidate=None, prompt_sha256=None):
    """No fuzzy matching: any context, source or rubric change invalidates reuse."""
    fields = {k: rule[k] for k in ('id', 'family_id', 'source_sha256', 'scope',
                                  'rubric_version', 'allowed_alternatives',
                                  'forbidden_inferences', 'critical', 'answerability')}
    fields.update(candidate_sha256=digest(candidate.encode()) if candidate is not None else None, prompt_sha256=prompt_sha256)
    return digest(json.dumps(fields, sort_keys=True, ensure_ascii=False).encode())


def blind_packet(items, seed=20261111):
    """Preparation aid only: this public exposed material is not an independent study."""
    import random
    pairs = [{'id': x['id'], 'source': x['source'], 'candidate': x['candidate']} for x in items]
    random.Random(seed).shuffle(pairs)
    return {'status': 'internal_annotation_preparation_only', 'qualified': False,
            'instructions': 'Annotate without consulting model outputs or public draft labels. This public, engineering-exposed packet cannot establish independent holdout evidence.',
            'items': pairs}


def eligibility(rule):
    # A local string cannot establish external custody or human independence.
    reasons = ['independent_identity_and_custody_not_verified']
    if rule['exposure'] != 'unexposed':
        reasons.append('source_exposed_to_engineering')
    if rule['label_status'] != 'human_adjudicated':
        reasons.append('labels_not_human_adjudicated')
    return {'qualified': False, 'blockers': reasons}


def validate_response(raw, expected_ids):
    """Invalid envelopes are retained but never silently repaired or partly scored."""
    try:
        obj = parse(raw)
        if not isinstance(obj, dict) or set(obj) != {'items', 'review'}:
            raise ValueError('Expected items and review envelope')
        if not isinstance(obj['items'], list) or not isinstance(obj['review'], dict):
            raise ValueError('Invalid envelope types')
        review = obj['review']
        if set(review) != {'verdict', 'blocking_findings', 'recommendations', 'claims_to_avoid'}:
            raise ValueError('Invalid review fields')
        if not isinstance(review['verdict'], str) or any(
            not isinstance(review[k], list) or any(not isinstance(x, str) for x in review[k])
            for k in ('blocking_findings', 'recommendations', 'claims_to_avoid')
        ):
            raise ValueError('Invalid review values')
        ids = []
        for row in obj['items']:
            if not isinstance(row, dict) or set(row) != {'id', 'verdict', 'reason'}:
                raise ValueError('Invalid item fields')
            if not isinstance(row['id'], str) or row['id'] not in expected_ids:
                raise ValueError('Unknown item ID')
            if row['verdict'] not in ('faithful', 'altered', 'uncertain'):
                raise ValueError('Invalid verdict')
            if not isinstance(row['reason'], str) or not row['reason'].strip():
                raise ValueError('Missing rationale')
            ids.append(row['id'])
        if len(set(ids)) != len(ids):
            raise ValueError('Duplicate item IDs')
        return obj, None
    except (ValueError, TypeError, KeyError, RecursionError) as exc:
        return None, str(exc)


def tally(key, judgments, invalid=False):
    mutants = [r for r in key if r['expected'] == 'altered']
    controls = [r for r in key if r['expected'] == 'faithful']
    missing = sum(r['id'] not in judgments for r in key)
    uncertain = sum(judgments.get(r['id'], {}).get('verdict') == 'uncertain' for r in key)
    detected = sum(judgments.get(r['id'], {}).get('verdict') == 'altered' for r in mutants)
    false_alarm = sum(judgments.get(r['id'], {}).get('verdict') == 'altered' for r in controls)
    return {'assigned': len(key), 'classified': len(key) - missing - uncertain,
            'missing': 0 if invalid else missing, 'invalid': len(key) if invalid else 0, 'uncertain': uncertain,
            'mutations': len(mutants), 'detected': detected,
            'faithful_controls': len(controls), 'false_alarms': false_alarm,
            'missed_mutations': sum(judgments.get(r['id'], {}).get('verdict') == 'faithful' for r in mutants),
            'mutations_unresolved': sum(judgments.get(r['id'], {}).get('verdict') in (None, 'uncertain') for r in mutants),
            'controls_unresolved': sum(judgments.get(r['id'], {}).get('verdict') in (None, 'uncertain') for r in controls),
            'detection_assigned_ratio': detected / len(mutants) if mutants and not invalid else None,
            'false_alarm_assigned_ratio': false_alarm / len(controls) if controls and not invalid and all(judgments.get(r['id'], {}).get('verdict') in ('faithful', 'altered') for r in controls) else None,
            'false_alarm_rate_interpretable': bool(controls) and not invalid and not any(judgments.get(r['id'], {}).get('verdict') in (None, 'uncertain') for r in controls)}


def build(base=BASE):
    guard = read(base / 'legacy-guard.json')
    if digest((ROOT / 'web/downloads/blueprintbench/leaderboard-data.json').read_bytes()) != guard['primary_dataset_sha256']:
        raise ValueError('Primary cohort changed; calibration cannot silently inherit new scores')
    manifest = read(base / 'manifest.json')
    required = {'proposition-bank.json', 'items.json', 'answer-key.json', 'protocol.json', 'review-prompt.txt'}
    if not required <= set(manifest['files']):
        raise ValueError('Required frozen input missing')
    for name, expected in manifest['files'].items():
        path = base / name
        if path.parent != base or path.is_symlink() or digest(path.read_bytes()) != expected:
            raise ValueError('Frozen input drift or unsafe path: ' + name)
    capture_lock = read(base / 'capture-lock.json')
    for name, expected in capture_lock['files'].items():
        path = base / name
        if path.parent != base / 'responses' or path.is_symlink() or digest(path.read_bytes()) != expected:
            raise ValueError('Capture lock mismatch: ' + name)
    bank = read(base / 'proposition-bank.json')
    items = read(base / 'items.json')
    key = read(base / 'answer-key.json')
    protocol = read(base / 'protocol.json')
    if len({r['id'] for r in bank}) != len(bank):
        raise ValueError('Duplicate proposition ID')
    by_rule = {r['id']: r for r in bank}
    for r in bank:
        if digest(r['source_text'].encode()) != r['source_sha256']:
            raise ValueError('Source digest mismatch')
    by_item = {r['id']: r for r in items}
    if len(by_item) != len(items) or {r['id'] for r in key} != set(by_item) or len(key) != len(items):
        raise ValueError('Assignment/key mismatch')
    for r in key:
        rule = by_rule[r['rule_id']]
        if by_item[r['id']]['source'] != rule['source_text']:
            raise ValueError('Source mapping mismatch')
        if r['expected'] not in ('faithful', 'altered'):
            raise ValueError('Invalid draft label')
    families = sorted({r['family_id'] for r in bank})
    if len(families) != protocol['independent_source_families']:
        raise ValueError('Family count differs from frozen protocol')
    results = []
    for reviewer in protocol['reviewers']:
        path = base / 'responses' / (reviewer + '-raw.txt')
        obj = None
        error = 'Response not received'
        receipt = None
        receipt_path = path.with_name(reviewer + '-receipt.json')
        if path.exists() != receipt_path.exists():
            raise ValueError('Incomplete capture pair: ' + reviewer)
        if path.exists():
            if not {path.relative_to(base).as_posix(), receipt_path.relative_to(base).as_posix()} <= set(capture_lock['files']):
                raise ValueError('Unpinned capture: ' + reviewer)
            receipt = read(path.with_name(reviewer + '-receipt.json'))
            if receipt['raw_text_sha256'] != digest(path.read_bytes()) or receipt['prompt_sha256'] != manifest['files']['review-prompt.txt']:
                raise ValueError('Response/prompt receipt mismatch: ' + reviewer)
            try:
                obj, error = validate_response(path.read_bytes().decode('utf-8'), set(by_item))
            except UnicodeDecodeError:
                error = 'Invalid UTF-8 response capture'
        judgments = {r['id']: r for r in obj['items']} if obj else {}
        results.append({'reviewer': reviewer, 'strict_envelope_valid': obj is not None,
                        'structural_error': error, 'semantic_status': 'assessed_against_draft_labels' if obj else 'not_assessed', 'review_complete': len(judgments) == len(items), 'review_determinate': len(judgments) == len(items) and not any(r['verdict'] == 'uncertain' for r in judgments.values()),
                        'counts': tally(key, judgments, invalid=path.exists() and obj is None),
                        'by_case': {c: tally([r for r in key if r['case'] == c], judgments, invalid=path.exists() and obj is None) for c in sorted({r['case'] for r in key})},
                        'by_dimension': {d: tally([r for r in key if r['dimension'] == d], judgments, invalid=path.exists() and obj is None) for d in sorted({r['dimension'] for r in key})},
                        'by_family': {f: tally([r for r in key if by_rule[r['rule_id']]['family_id'] == f], judgments, invalid=path.exists() and obj is None) for f in families},
                        'review': obj['review'] if obj else None, 'judgments': judgments, 'receipt': receipt})
    exported = []
    for item in items:
        label = next(r for r in key if r['id'] == item['id'])
        rule = by_rule[label['rule_id']]
        votes = {r['reviewer']: r['judgments'].get(item['id']) for r in results}
        values = [v['verdict'] for v in votes.values() if v]
        exported.append({**item, **label, 'source_sha256': rule['source_sha256'],
                         'reuse_key': reuse_key(rule, item['candidate'], manifest['files']['review-prompt.txt']), 'label_status': 'assistant_draft',
                         'reviews': votes, 'vote_counts': dict(Counter(values)), 'has_dissent': 'faithful' in values and 'altered' in values, 'agreement': 'incomplete' if len(values) != len(results) else 'uncertain' if 'uncertain' in values else 'agree' if len(set(values)) == 1 else 'diverge'})
    return {'version': protocol['version'], 'status': 'internal_tests', 'qualified': False,
            'primary_scores_unchanged': True, 'protocol': protocol,
            'lexical_baseline': {'name': 'Exact string equality', 'rule': 'faithful iff candidate bytes equal source bytes; otherwise altered. Post-hoc diagnostic suggested by reviewers, not a preregistered comparator.', 'counts': tally(key, {x['id']: {'verdict': 'faithful' if x['candidate'] == x['source'] else 'altered'} for x in items})},
            'source_eligibility': {r['id']: eligibility(r) for r in bank},
            'results': results, 'review_export': exported,
            'agreement': dict(Counter(r['agreement'] for r in exported)),
            'input_manifest_sha256': digest((base / 'manifest.json').read_bytes()),
            'draft_status': 'LLM-generated internal diagnostics; not human-validated',
            'capture_lock_sha256': digest((base / 'capture-lock.json').read_bytes()),
            'blind_annotation_packet': 'annotation-packet.json'}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--check', action='store_true')
    args = p.parse_args()
    out = ROOT / 'web/downloads/blueprintbench/calibration.json'
    data = (json.dumps(build(), indent=2, ensure_ascii=False) + '\n').encode()
    packet_path = BASE / 'annotation-packet.json'
    packet = (json.dumps(blind_packet(read(BASE / 'items.json')), indent=2, ensure_ascii=False) + '\n').encode()
    if args.check:
        if packet_path.read_bytes() != packet:
            raise SystemExit('Annotation packet drift')
        if out.read_bytes() != data:
            raise SystemExit('Calibration export drift')
    else:
        out.write_bytes(data)
        packet_path.write_bytes(packet)
    print('Calibration evidence ' + ('verified' if args.check else 'built'))


if __name__ == '__main__':
    main()
