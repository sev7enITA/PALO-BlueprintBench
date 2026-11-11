"""Offline descriptive analysis and draft exports. No independent correctness claims."""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import contracts

METRICS = ('assigned', 'classified', 'missing', 'unassessed', 'scored_assigned',
           'unscored_classified', 'matches_draft', 'divergences', 'unresolved_conflict')


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aggregate(rows):
    return {key: sum(row.get(key, 0) for row in rows) for key in METRICS}


def analyse_attempt(task, assignment, record, raw):
    expected = task.get('assessment_key', {})
    excluded = set(task.get('unscored_probe_ids', []))
    assigned = len(task['expected_ids'])
    scored = [ident for ident in task['expected_ids'] if ident in expected and ident not in excluded]
    row = {'id': assignment['id'], 'task_id': task['id'], 'case_id': task['case_id'],
        'track': task['track'], 'variant': task['variant'], 'model': assignment['model'],
        'state': (record.get('state') or record.get('status') or 'recorded_unknown') if record else 'not_run',
        'structural_valid': False, 'issues': [], 'assigned': assigned, 'classified': 0,
        'missing': 0, 'unassessed': 0, 'scored_assigned': len(scored), 'unscored_classified': 0,
        'matches_draft': 0, 'divergences': 0, 'unresolved_conflict': 0,
        'unscored_probe_ids': sorted(excluded), 'judgments': [], 'qualified': False,
        'source_packet_sha256': task['source_packet_sha256'],
        'cost_usd': record.get('cost_usd') if record else None,
        'cost_status': record.get('cost_status', 'unknown') if record else 'not_dispatched',
        'elapsed_seconds': record.get('elapsed_seconds') if record else None,
        'http_status': record.get('http_status') if record else None,
        'reserved_usd': record.get('reserved_usd') if record else None}
    if raw is None or not raw.strip():
        row['missing'] = assigned
        row['analysis_status'] = 'not_run' if not record else 'no_usable_response'
        row['issues'] = ['no_output: response content absent; no semantic judgment inferred']
        return row, None
    data, issues = contracts.validate(raw, task)
    row['issues'] = issues
    if issues:
        row['analysis_status'] = 'response_contract_failed'
        row['unassessed'] = assigned
        return row, data
    row['structural_valid'] = True
    row['analysis_status'] = 'classified_internal_draft_comparison' if expected else 'advisory_labels_only'
    workflow = task['track'] == 'workflow'
    emitted = data['scenario_decisions'] if workflow else data['items']
    for item in emitted:
        ident = item['decision'] if workflow else item['id']
        label = item['disposition'] if workflow else item['label']
        scoreable = ident in expected and ident not in excluded
        matches = label == expected[ident] if scoreable else None
        row['judgments'].append({'id': ident, 'predicted': label, 'draft_expected': expected.get(ident),
            'scored': scoreable, 'matches_draft': matches, 'source_units': item['source_units'],
            'rationale': item['rationale'], **({'predicate_ids': item['predicate_ids']} if workflow else {})})
        row['classified'] += 1
        row['unresolved_conflict'] += int(label == 'unresolved_conflict')
        if matches is None: row['unscored_classified'] += 1
        elif matches: row['matches_draft'] += 1
        else: row['divergences'] += 1
    assert row['classified'] + row['missing'] + row['unassessed'] == assigned
    return row, data


def metamorphic_relations(tasks, attempts):
    results = []
    index = {(r['task_id'], r['model']): r for r in attempts}
    for task in tasks:
        if task['track'] != 'metamorphic': continue
        check = task['metamorphic']
        for variant in [r for r in attempts if r['task_id'] == task['id']]:
            base = index.get((task['baseline_task_id'], variant['model']))
            a = {j['id']: j for j in base['judgments']} if base else {}
            b = {j['id']: j for j in variant['judgments']}
            rows = []
            targeted = check.get('expected_dispositions', {})
            for ident in task['expected_ids']:
                before, after = a.get(ident), b.get(ident)
                available = before is not None and after is not None
                sensitive = ident in task.get('unscored_probe_ids', [])
                relation = 'counterfactual_disposition' if ident in targeted else 'invariant'
                satisfied = None
                if available and not sensitive:
                    satisfied = (after['predicted'] == targeted[ident] and before['predicted'] != after['predicted']) if ident in targeted else before['predicted'] == after['predicted']
                rows.append({'id': ident, 'relation': relation, 'baseline': before['predicted'] if before else None,
                    'variant': after['predicted'] if after else None, 'expected_variant': targeted.get(ident),
                    'satisfied': satisfied, 'status': 'rubric_sensitive_unscored' if sensitive else 'observed' if available else 'missing_pair'})
            scored = [r for r in rows if r['satisfied'] is not None]
            results.append({'model': variant['model'], 'check_id': check['id'],
                'baseline_task_id': task['baseline_task_id'], 'variant_task_id': task['id'],
                'comparable': len(scored) == len([r for r in rows if r['status'] != 'rubric_sensitive_unscored']),
                'assigned_pairs': len(rows), 'observed_pairs': sum(r['status'] == 'observed' for r in rows),
                'missing_pairs': sum(r['status'] == 'missing_pair' for r in rows),
                'unscored_pairs': sum(r['status'] == 'rubric_sensitive_unscored' for r in rows),
                'satisfied': sum(r['satisfied'] is True for r in rows),
                'violated': sum(r['satisfied'] is False for r in rows), 'checks': rows,
                'interpretation': 'Consistency against a proposed development relation, not semantic validation.'})
    return results


def run(directory):
    directory = Path(directory)
    tasks = load(directory / 'tasks.json')
    schedule = load(directory / 'schedule.json')
    if isinstance(schedule, dict): schedule = schedule.get('assignments', schedule.get('schedule'))
    if not isinstance(schedule, list): raise ValueError('Schedule must be a list of assignments')
    by_task = {task['id']: task for task in tasks}
    if len(by_task) != len(tasks): raise ValueError('Duplicate task identifiers')
    if len({row['id'] for row in schedule}) != len(schedule): raise ValueError('Duplicate assignment identifiers')
    rows = []
    for assignment in schedule:
        task = by_task[assignment['task_id']]
        attempt = directory / 'runs' / assignment['id']
        record_path, output_path = attempt / 'record.json', attempt / 'output.txt'
        record = load(record_path) if record_path.exists() else None
        raw = output_path.read_bytes().decode('utf-8') if output_path.exists() else None
        row, response = analyse_attempt(task, assignment, record, raw)
        for key, path in [('request_path', attempt / 'request.json'), ('record_path', record_path), ('raw_path', output_path)]:
            if path.exists(): row[key] = path.relative_to(directory).as_posix()
        if record and record.get('output_sha256') and output_path.exists() and sha(output_path) != record['output_sha256']:
            raise ValueError('Output byte hash mismatch: ' + assignment['id'])
        if task['track'] == 'workflow' and raw is not None:
            dest = directory / 'blueprints' / (assignment['id'] + '.json')
            dest.parent.mkdir(exist_ok=True)
            artifact = {'artifact_type': 'source_linked_model_draft', 'id': assignment['id'],
                'model': assignment['model'], 'case_id': task['case_id'], 'qualified': False,
                'business_approval_required': True, 'business_approved': False,
                'export_status': 'structurally_valid_model_draft' if row['structural_valid'] else 'unusable_model_draft',
                'semantic_status': 'unreviewed_model_output', 'structural_issues': row['issues'],
                'source_packet_sha256': task['source_packet_sha256'], 'raw_output_sha256': sha(output_path),
                'raw_output_path': row.get('raw_path'), 'content': response,
                'draft_decision_comparison': row['judgments'],
                'limitations': 'Structural validity and matches to assistant-draft decisions do not establish semantic correctness, executability or independent validation.'}
            dest.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            row['blueprint_path'] = dest.relative_to(directory).as_posix()
        rows.append(row)
    models = []
    for model in sorted({r['model'] for r in schedule}):
        own = [r for r in rows if r['model'] == model]
        models.append({'model': model, 'assigned_requests': len(own),
            'recorded_requests': sum('record_path' in r for r in own),
            'completed_requests': sum(r['state'] == 'completed' for r in own),
            'structurally_valid_responses': sum(r['structural_valid'] for r in own),
            'known_cost_usd': sum(r['cost_usd'] or 0 for r in own),
            'unknown_cost_requests': sum(r['cost_status'] == 'unknown' for r in own),
            'tracks': {track: aggregate([r for r in own if r['track'] == track]) for track in sorted({r['track'] for r in own})}})
    return {'status': 'internal_engineering_feasibility', 'qualified': False, 'independent_human_reviews': 0,
        'assigned_requests': len(schedule), 'recorded_requests': sum('record_path' in r for r in rows),
        'completed_requests': sum(r['state'] == 'completed' for r in rows),
        'inputs': {'tasks_sha256': sha(directory / 'tasks.json'), 'schedule_sha256': sha(directory / 'schedule.json')},
        'models': models, 'attempts': rows, 'metamorphic': metamorphic_relations(tasks, rows),
        'limitations': ['One automated authoring provenance group, not six independent source families.',
            'One repetition per assignment; no confidence interval, superiority or ranking claim.',
            'Draft-label agreement is not independently adjudicated semantic accuracy.',
            'Policy-transition-P05 is retained but excluded from draft scoring before inference due to rubric sensitivity.',
            'Workflow draft exports are not business-approved or Workbench application end-to-end validation.',
            'The emergency workflow tests approval and quotation decisions, not complete purchase-order issuance eligibility; actor identity, documented urgency and remaining prerequisites require separate coverage.',
            'Legacy items receive advisory model judgments only; human annotation templates remain unfilled.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path, nargs='?', default=Path(__file__).resolve().parent)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    data = run(args.directory)
    target = args.output or args.directory / 'analysis.json'
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'assigned_requests': data['assigned_requests'], 'recorded_requests': data['recorded_requests'], 'qualified': False}))


if __name__ == '__main__':
    main()
