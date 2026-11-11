"""Offline publication checks for the immutable next-cycle campaign evidence.

No provider calls and no artifact rewrites. A finished partial/blocked campaign is
valid evidence; an orphan request still in flight is not publishable final evidence.
"""
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / 'internal_tests/2026-11-11-next-cycle'
sys.path.insert(0, str(CAMPAIGN))
import analyse
import contracts
import runner


def read(path):
    return contracts.parse(path.read_bytes().decode('utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def close(left, right):
    return finite(left) and finite(right) and math.isclose(left, right, rel_tol=1e-10, abs_tol=1e-10)


def final_records(root):
    records = []
    for directory in sorted((root / 'runs').iterdir()) if (root / 'runs').exists() else []:
        if not directory.is_dir():
            continue
        require((directory / 'record.json').is_file(), 'Orphan/pending request is not final publication evidence: ' + directory.name)
        record = read(directory / 'record.json')
        require(record.get('id') == directory.name, 'Receipt identity does not match directory')
        require(record.get('finished_at') is not None, 'Unfinished receipt')
        require(record.get('state') in ('completed', 'incomplete', 'fail'), 'Unrecognized final receipt state')
        status, cost = record.get('cost_status'), record.get('cost_usd')
        require(status in ('provider_reported', 'unknown'), 'Unsupported cost status')
        require(cost is None if status == 'unknown' else finite(cost), 'Unknown cost must remain null; known cost must be finite')
        require(finite(record.get('reserved_usd')), 'Missing finite reservation')
        records.append(record)
    require(len({r['id'] for r in records}) == len(records), 'Duplicate receipt identifiers')
    return records


def check_budget(summary, manifest, records, assigned):
    known = sum(r['cost_usd'] for r in records if r['cost_status'] == 'provider_reported')
    unknown = [r for r in records if r['cost_status'] == 'unknown']
    reserve = sum(r['reserved_usd'] for r in unknown)
    baseline = summary['account_usage_before_usd']
    require(finite(baseline), 'Budget baseline unknown')
    account = summary.get('account_usage_after_usd')
    require(account is None or finite(account), 'Invalid account usage')
    bound = max(account or 0, baseline + known) + manifest['previous_unknown_cost_reserve_usd'] + reserve
    require(summary['assigned_calls'] == assigned, 'Budget assigned denominator changed')
    require(summary['recorded_calls'] == len(records), 'Budget receipt count differs')
    require(summary['not_run'] == assigned - len(records), 'Budget missing denominator differs')
    require(close(summary['known_campaign_cost_usd'], known), 'Known cost sum differs')
    require(summary['unknown_costs'] == len(unknown), 'Unknown costs omitted')
    require(close(summary['unknown_cost_reserve_usd'], reserve), 'Unknown cost reserve omitted')
    require(close(summary['conservative_cumulative_committed_usd'], bound), 'Cumulative bound is not conservative/reproducible')
    require(summary['cumulative_ceiling_usd'] == manifest['cumulative_ceiling_usd'] == 40, 'Cumulative ceiling changed')
    require(summary['campaign_ceiling_usd'] == manifest['new_campaign_ceiling_usd'] == 12, 'Campaign ceiling changed')
    compliant = bound <= 40 and known + reserve <= 12
    require(summary['budget_compliant'] == compliant, 'Budget compliance claim contradicts receipts')
    require(compliant, 'Campaign exceeds authorized budget')
    if unknown:
        require(summary['status'] == 'blocked' and summary['blocker'], 'Unknown costs require a recorded block')
    elif len(records) < assigned:
        require(summary['status'] in ('partial', 'blocked'), 'Partial campaign mislabeled complete')
    else:
        require(summary['status'] in ('completed', 'blocked'), 'All-recorded campaign status invalid')
    require(summary.get('qualified') is False, 'Budget claims qualification')


def validate_archive(root=CAMPAIGN):
    manifest = read(root / 'manifest.json')
    runner.verify_frozen(manifest, root)
    require(manifest['qualified'] is False, 'Frozen campaign claims qualification')
    tasks = read(root / 'tasks.json')
    models = {m['id']:m for m in read(root / 'models.json')}
    schedule = read(root / 'schedule.json')
    require(len(schedule) == len({a['id'] for a in schedule}) == manifest['assigned_calls'] == 60, 'Schedule is not 60 unique assignments')
    require(len(tasks) == len({t['id'] for t in tasks}) == 20, 'Task allocation changed')
    require(len(models) == 3, 'Model allocation changed')
    by_task = {t['id']:t for t in tasks}
    assignments = {a['id']:a for a in schedule}
    for model in models:
        own = [a for a in schedule if a['model'] == model]
        require(len(own) == 20 and {a['task_id'] for a in own} == set(by_task), 'Model task allocation differs')
    records = final_records(root)
    require(all(r['id'] in assignments for r in records), 'Unassigned receipt')
    indexed = {r['id']:r for r in records}
    expected_rows = []
    forbidden = ('assessment_key', 'draft_disposition', 'draft_expected_decisions', 'expected_dispositions', 'human_adjudication')
    for assignment in schedule:
        task = by_task[assignment['task_id']]
        record = indexed.get(assignment['id'])
        directory = root / 'runs' / assignment['id']
        raw = None
        if record:
            model = models[assignment['model']]
            require(all(record[k] == assignment[k] for k in ('id','task_id','model')), 'Receipt assignment mismatch')
            body = json.dumps(runner.payload_for(task,model),ensure_ascii=False,separators=(',',':')).encode('utf-8')
            require((directory/'request.json').read_bytes() == body, 'Request differs from frozen task/model')
            require(not any(key in body.decode('utf-8') for key in forbidden), 'Assessment-key leakage')
            require(sha(directory/'request.json') == record['request_sha256'], 'Request hash mismatch')
            require(record['manifest_sha256'] == sha(root/'manifest.json'), 'Receipt manifest mismatch')
            require(record['source_packet_sha256'] == task['source_packet_sha256'], 'Source packet mismatch')
            require(record['pinned_provider'] == model['provider'], 'Pinned provider changed')
            reservation = read(directory/'reservation.json')
            require(close(record['reserved_usd'], runner.reservation_for(body,model)), 'Reservation differs from frozen prices/request')
            require(close(reservation['reserved_usd'],record['reserved_usd']) and reservation['headroom_before_usd'] >= record['reserved_usd'], 'Dispatch lacked headroom')
            response_path = directory/'response.json'
            if response_path.exists():
                require(sha(response_path) == record['response_sha256'], 'Raw response hash mismatch')
                try:
                    response = read(response_path)
                except ValueError:
                    response = None
                if record['cost_status'] == 'provider_reported':
                    require(isinstance(response,dict) and close(response.get('usage',{}).get('cost'),record['cost_usd']), 'Provider usage cost mismatch')
                elif isinstance(response,dict):
                    require(not finite(response.get('usage',{}).get('cost')), 'Known provider cost classified unknown')
                if isinstance(response,dict) and response.get('choices'):
                    content = response['choices'][0].get('message',{}).get('content')
                    if isinstance(content,str):
                        require((directory/'output.txt').read_bytes() == content.encode('utf-8'), 'Extracted output differs from original response content')
                if record['state'] == 'completed':
                    require(record.get('returned_identity_matches_pin') is True, 'Completed receipt lacks pinned identity')
                    require(response.get('provider') == model['endpoint']['provider_name'], 'Returned provider mismatch')
                    require(response.get('model') == record['returned_model'], 'Returned model receipt mismatch')
                    endpoint_version = model['endpoint'].get('name','').split('|')[-1].strip()
                    require(response.get('model') in (model['id'],endpoint_version), 'Returned model is not a frozen canonical/version identity')
            else:
                require(record['cost_status'] == 'unknown' and record['state'] == 'fail', 'Missing raw response without failed unknown-cost state')
            if (directory/'output.txt').exists():
                require(sha(directory/'output.txt') == record['output_sha256'], 'Output hash mismatch')
                raw = (directory/'output.txt').read_bytes().decode('utf-8')
        row,_ = analyse.analyse_attempt(task,assignment,record,raw)
        require(row['classified'] + row['missing'] + row['unassessed'] == len(task['expected_ids']), 'Assigned judgment denominator lost')
        require(row['matches_draft'] + row['divergences'] + row['unscored_classified'] == row['classified'], 'Classification partition invalid')
        expected_rows.append(row)
    report = read(root/'analysis.json')
    require(report['qualified'] is False and report['independent_human_reviews'] == 0, 'Unsupported independent validation')
    require(report['assigned_requests'] == 60 and report['recorded_requests'] == len(records), 'Analysis request denominator changed')
    require(report['inputs'] == {'tasks_sha256':sha(root/'tasks.json'),'schedule_sha256':sha(root/'schedule.json')}, 'Analysis input hashes stale')
    require(len(report['attempts']) == 60, 'Analysis omits assignments')
    actual = {r['id']:r for r in report['attempts']}
    require(len(actual) == 60, 'Duplicate analysis row')
    for expected in expected_rows:
        require(all(actual[expected['id']].get(k) == v for k,v in expected.items()), 'Analysis replay differs: ' + expected['id'])
    reported_models = {m['model']:m for m in report['models']}
    require(set(reported_models) == set(models), 'Analysis model roster differs')
    for model in models:
        own = [r for r in expected_rows if r['model'] == model]
        reported = reported_models[model]
        require(reported['assigned_requests'] == 20, 'Per-model request denominator changed')
        for track in {r['track'] for r in own}:
            require(reported['tracks'][track] == analyse.aggregate([r for r in own if r['track'] == track]), 'Per-track aggregate differs')
        rows = [r for r in own if r['track'] == 'verification']
        require(sum(r['assigned'] for r in rows) == 48, 'Base proposition assignment changed')
        require(sum(r['scored_assigned'] for r in rows) == 47, 'P05 exclusion changed')
    require(report['metamorphic'] == analyse.metamorphic_relations(tasks,expected_rows), 'Paired metamorphic replay differs')
    for row in report['attempts']:
        if row['track'] != 'workflow' or 'raw_path' not in row:
            continue
        blueprint = read(root / row['blueprint_path'])
        require(blueprint['qualified'] is False and blueprint['business_approved'] is False and blueprint['business_approval_required'] is True, 'Blueprint approval boundary altered')
        require(blueprint['source_packet_sha256'] == row['source_packet_sha256'], 'Blueprint source provenance differs')
        expected_status = 'structurally_valid_model_draft' if row['structural_valid'] else 'unusable_model_draft'
        require(blueprint['export_status'] == expected_status, 'Invalid draft presented as accepted')
    check_budget(read(root/'budget-final.json'),manifest,records,60)
    return {'assigned':60,'recorded':len(records),'not_run':60-len(records)}


class EvidenceBoundaryTests(unittest.TestCase):
    def test_final_archive_replays_offline(self):
        validate_archive()

    def test_orphan_cannot_be_final_publication(self):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name);(path/'runs/pending').mkdir(parents=True)
            with self.assertRaisesRegex(ValueError,'Orphan/pending'):
                final_records(path)

    def test_unknown_cost_null_is_preserved_and_zero_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name);dest=path/'runs/failed';dest.mkdir(parents=True)
            record={'id':'failed','finished_at':'2026-11-11T12:00:00Z','state':'fail','cost_status':'unknown','cost_usd':None,'reserved_usd':1}
            (dest/'record.json').write_text(json.dumps(record),encoding='utf-8')
            self.assertIsNone(final_records(path)[0]['cost_usd'])
            record['cost_usd']=0;(dest/'record.json').write_text(json.dumps(record),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'Unknown cost'):
                final_records(path)

    def test_partial_blocked_budget_keeps_missing_assignments(self):
        manifest={'previous_unknown_cost_reserve_usd':.5,'cumulative_ceiling_usd':40,'new_campaign_ceiling_usd':12}
        records=[{'cost_status':'provider_reported','cost_usd':.2,'reserved_usd':1},{'cost_status':'unknown','cost_usd':None,'reserved_usd':1}]
        summary=runner.make_summary([{}]*60,records,manifest,20,{'total_usage':20.2},'unknown_cost_requires_reconciliation')
        check_budget(summary,manifest,records,60)
        self.assertEqual(58,summary['not_run'])
        self.assertAlmostEqual(21.7,summary['conservative_cumulative_committed_usd'])
        summary['unknown_cost_reserve_usd']=0
        with self.assertRaisesRegex(ValueError,'reserve omitted'):
            check_budget(summary,manifest,records,60)


if __name__ == '__main__':
    unittest.main()
