"""Adversarial offline checks for the next-cycle request and analysis boundary."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / 'internal_tests/2026-11-11-next-cycle'
sys.path.insert(0, str(CAMPAIGN))
import prepare
import contracts
import analyse


def answer(task):
    return {'items': [{'id': ident, 'label': task['assessment_key'].get(ident, 'not_established'),
        'source_units': [next(s for s in task['source_units'] if task['track'] != 'legacy' or s.startswith(ident + ':'))],
        'rationale': 'Offline test fixture, not a model response.'} for ident in task['expected_ids']]}


def blueprint(task):
    refs = task['source_units'][:1]
    decisions = task['expected_ids']
    return {
        'typed_entities_and_identifiers': [{'name': 'Purchase', 'identifier_status': 'proposed_design',
            'fields': [{'name': 'amount', 'type': 'decimal', 'source_units': refs}], 'source_units': refs}],
        'decision_predicates': [{'id': 'p' + str(i), 'decision': d, 'actor': 'not specified', 'scope': 'fixture',
            'condition': 'fixture', 'units': 'not applicable', 'comparison': 'not applicable', 'source_units': refs} for i,d in enumerate(decisions)],
        'process_transitions': [{'from_state': 'draft', 'to_state': 'review', 'event': 'submit',
            'guard': 'fixture', 'predicate_ids': ['p0'], 'source_units': refs}],
        'scenario_decisions': [{'decision': d, 'disposition': task['assessment_key'][d],
            'predicate_ids': ['p' + str(i)], 'source_units': refs, 'rationale': 'Offline fixture.'} for i,d in enumerate(decisions)],
        'unresolved_questions': []}


class ExecutionBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks = prepare.build_tasks(ROOT)
        cls.by_id = {t['id']: t for t in cls.tasks}

    def attempt(self, task, data=None, record=None):
        return analyse.analyse_attempt(task, {'id':'test', 'model':'fixture/model'}, record,
            json.dumps(data) if data is not None else None)[0]

    def test_plan_fixed_assignments_and_exclusion(self):
        self.assertEqual(20, len(self.tasks))
        base = [t for t in self.tasks if t['track'] == 'verification']
        self.assertEqual(48, sum(len(t['expected_ids']) for t in base))
        self.assertEqual(47, sum(len(t['expected_ids']) - len(t['unscored_probe_ids']) for t in base))
        self.assertEqual(7, sum(t['track'] == 'metamorphic' for t in self.tasks))

    def test_provider_payload_withholds_keys_and_adjudication(self):
        forbidden = {'assessment_key', 'draft_disposition', 'draft_expected_decisions', 'expected_dispositions',
            'human_adjudication', 'label_status', 'review_status', 'minimal_pair_group'}
        def inspect(value):
            if isinstance(value, dict):
                self.assertFalse(forbidden.intersection(value))
                for child in value.values(): inspect(child)
            elif isinstance(value, list):
                for child in value: inspect(child)
        for task in self.tasks:
            inspect(json.loads(task['messages'][-1]['content']))
            contracts.Draft202012Validator.check_schema(task['response_schema'])

    def test_source_order_and_counterfactual_provenance(self):
        base = self.by_id['verification-emergency-spares']
        reordered = self.by_id['metamorphic-emergency-spares-document-order']
        counter = self.by_id['metamorphic-emergency-threshold-counterfactual']
        payload = lambda t: json.loads(t['messages'][-1]['content'])
        self.assertEqual(payload(base)['documents'][::-1], payload(reordered)['documents'])
        before = {u['id']:u['text'] for d in payload(base)['documents'] for u in d['units']}
        after = {u['id']:u['text'] for d in payload(counter)['documents'] for u in d['units']}
        self.assertEqual({'E01','E05'}, {k for k in before if before[k] != after[k]})
        for ident in ('E01', 'E05'):
            self.assertEqual(before[ident].replace('EUR 12,000','EUR 15,000'), after[ident])
        self.assertEqual(6, len(counter['expected_ids']))
        self.assertNotEqual(base['source_packet_sha256'], counter['source_packet_sha256'])

    def test_duplicate_and_foreign_sources_fail_without_partial_scores(self):
        task = self.by_id['verification-emergency-spares']
        for mutate in ('duplicate', 'foreign_source', 'duplicate_source'):
            data = answer(task)
            if mutate == 'duplicate': data['items'][1]['id'] = data['items'][0]['id']
            elif mutate == 'foreign_source': data['items'][0]['source_units'] = ['OTHER-SOURCE']
            else: data['items'][0]['source_units'] *= 2
            row = self.attempt(task, data, {'state':'completed'})
            self.assertFalse(row['structural_valid'])
            self.assertEqual(8, row['unassessed'])
            self.assertEqual(0, row['matches_draft'])
            self.assertEqual([], row['judgments'])

    def test_duplicate_json_keys_and_invalid_json_rejected(self):
        task = self.by_id['verification-emergency-spares']
        for raw in ('{"items":[],"items":[]}', '```json\n{}\n```', '{"items":NaN}'):
            data, issues = contracts.validate(raw, task)
            self.assertTrue(issues)

    def test_missing_keeps_fixed_denominator(self):
        task = self.by_id['verification-emergency-spares']
        for record in (None, {'state':'api_failed','cost_status':'unknown'}):
            row = self.attempt(task, record=record)
            self.assertEqual(8, row['assigned'])
            self.assertEqual(8, row['missing'])
            self.assertEqual(0, row['matches_draft'])
            self.assertIsNone(row['cost_usd'])
        row = self.attempt(task, {'items': []}, {'state':'completed'})
        self.assertEqual(8, row['unassessed'])
        self.assertEqual(0, row['missing'])

    def test_rubric_sensitive_item_is_retained_unscored(self):
        task = self.by_id['verification-policy-transition']
        data = answer(task)
        row = self.attempt(task, data, {'state':'completed'})
        self.assertEqual(8, row['classified'])
        self.assertEqual(7, row['matches_draft'])
        self.assertEqual(1, row['unscored_classified'])
        sensitive = next(j for j in row['judgments'] if j['id'].endswith('P05'))
        self.assertFalse(sensitive['scored'])
        self.assertIsNone(sensitive['matches_draft'])

    def test_legacy_sources_are_item_scoped_and_unscored(self):
        task = self.by_id['legacy-blind-items']
        data = answer(task)
        row = self.attempt(task, data, {'state':'completed'})
        self.assertEqual(3, row['classified'])
        self.assertEqual(0, row['scored_assigned'])
        self.assertEqual(3, row['unscored_classified'])
        data['items'][0]['source_units'] = data['items'][1]['source_units']
        self.assertTrue(contracts.validate(json.dumps(data),task)[1])

    def test_workflow_exact_decisions_and_predicate_integrity(self):
        task = self.by_id['workflow-emergency-spares']
        data = blueprint(task)
        row = self.attempt(task, data, {'state':'completed'})
        self.assertTrue(row['structural_valid'], row['issues'])
        self.assertEqual(3, row['matches_draft'])
        data['scenario_decisions'][0]['disposition'] = 'permitted'
        row = self.attempt(task, data, {'state':'completed'})
        self.assertEqual(1, row['divergences'])
        data['scenario_decisions'][0]['predicate_ids'] = ['p1']
        self.assertFalse(self.attempt(task,data)['structural_valid'])
        data = blueprint(task)
        data['process_transitions'][0]['predicate_ids'] = ['unknown']
        self.assertFalse(self.attempt(task,data)['structural_valid'])

    def test_metamorphic_relations_require_observed_pair(self):
        base = self.by_id['verification-emergency-spares']
        variant = self.by_id['metamorphic-emergency-spares-document-order']
        rows = [self.attempt(base, answer(base)), self.attempt(variant)]
        checks = analyse.metamorphic_relations([base,variant], rows)
        self.assertEqual(8, checks[0]['missing_pairs'])
        self.assertEqual(0, checks[0]['satisfied'])
        self.assertFalse(checks[0]['comparable'])
        changed = answer(variant)
        changed['items'][0]['label'] = 'not_established'
        rows[1] = self.attempt(variant, changed)
        checks = analyse.metamorphic_relations([base,variant],rows)
        self.assertEqual(1, checks[0]['violated'])

    def test_full_analysis_exports_invalid_drafts_and_retains_not_run(self):
        task = self.by_id['workflow-emergency-spares']
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path/'tasks.json').write_text(json.dumps([task]),encoding='utf-8')
            schedule = [{'id':'done','task_id':task['id'],'model':'fixture/a'},
                {'id':'invalid','task_id':task['id'],'model':'fixture/a'},
                {'id':'missing','task_id':task['id'],'model':'fixture/a'}]
            (path/'schedule.json').write_text(json.dumps(schedule),encoding='utf-8')
            for ident,content in [('done',json.dumps(blueprint(task))),('invalid','{}')]:
                attempt = path/'runs'/ident
                attempt.mkdir(parents=True)
                (attempt/'record.json').write_text(json.dumps({'state':'completed','cost_usd':None}),encoding='utf-8')
                (attempt/'output.txt').write_text(content,encoding='utf-8')
            report = analyse.run(path)
            self.assertEqual(3, report['assigned_requests'])
            track = report['models'][0]['tracks']['workflow']
            self.assertEqual((9,3,3,3),(track['assigned'],track['classified'],track['missing'],track['unassessed']))
            good = json.loads((path/'blueprints/done.json').read_text(encoding='utf-8'))
            bad = json.loads((path/'blueprints/invalid.json').read_text(encoding='utf-8'))
            self.assertTrue(good['business_approval_required'])
            self.assertFalse(good['qualified'])
            self.assertEqual('unusable_model_draft',bad['export_status'])
            self.assertFalse((path/'blueprints/missing.json').exists())
            self.assertEqual(2,report['models'][0]['unknown_cost_requests'])


if __name__ == '__main__':
    unittest.main()
