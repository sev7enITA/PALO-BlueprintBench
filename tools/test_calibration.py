import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import calibration as c


class CalibrationTests(unittest.TestCase):
    def setUp(self):
        self.key = c.read(c.BASE / 'answer-key.json')
        self.ids = {x['id'] for x in self.key}
        self.obj = {'items': [{'id': x['id'], 'verdict': x['expected'], 'reason': 'fixture'} for x in self.key], 'review': {'verdict': 'fixture', 'blocking_findings': [], 'recommendations': [], 'claims_to_avoid': []}}

    def valid(self, obj):
        return c.validate_response(json.dumps(obj), self.ids)

    def test_seeded_defects_and_controls(self):
        obj, err = self.valid(self.obj)
        self.assertIsNone(err)
        counts = c.tally(self.key, {r['id']: r for r in obj['items']})
        self.assertEqual((counts['detected'], counts['mutations'], counts['false_alarms'], counts['faithful_controls']), (6, 6, 0, 12))

    def test_all_faithful_cannot_detect_mutations(self):
        for row in self.obj['items']: row['verdict'] = 'faithful'
        counts = c.tally(self.key, {r['id']: r for r in self.obj['items']})
        self.assertEqual(counts['detected'], 0)
        self.assertEqual(counts['missed_mutations'], 6)

    def test_abstention_and_missing_are_not_success(self):
        counts = c.tally(self.key, {})
        self.assertEqual(counts['missing'], 18)
        self.assertEqual(counts['mutations_unresolved'], 6)
        self.assertFalse(counts['false_alarm_rate_interpretable'])
        counts = c.tally(self.key, {r['id']: {'verdict': 'uncertain'} for r in self.key})
        self.assertEqual(counts['uncertain'], 18)
        self.assertEqual(counts['classified'], 0)

    def test_duplicate_unknown_ids_and_extra_fields_rejected(self):
        for mode in ('duplicate', 'unknown', 'extra', 'reason'):
            obj = copy.deepcopy(self.obj)
            if mode == 'duplicate': obj['items'].append(obj['items'][0])
            if mode == 'unknown': obj['items'][0]['id'] = 'HIDDEN'
            if mode == 'extra': obj['items'][0]['non_claim'] = True
            if mode == 'reason': obj['items'][0]['reason'] = ''
            self.assertIsNone(self.valid(obj)[0], mode)

    def test_partial_response_retains_denominator(self):
        self.obj['items'].pop()
        obj, err = self.valid(self.obj)
        self.assertIsNone(err)
        counts = c.tally(self.key, {r['id']: r for r in obj['items']})
        self.assertEqual(counts['assigned'], 18)
        self.assertEqual(counts['missing'], 1)

    def test_duplicate_json_keys_and_fences_rejected(self):
        self.assertIsNone(c.validate_response('{"items":[],"items":[],"review":{}}', self.ids)[0])
        self.assertIsNone(c.validate_response('```json\n' + json.dumps(self.obj) + '\n```', self.ids)[0])

    def test_scope_source_and_policy_changes_invalidate_reuse(self):
        rule = c.read(c.BASE / 'proposition-bank.json')[0]
        for field in ('scope', 'source_sha256', 'rubric_version', 'critical', 'answerability'):
            changed = copy.deepcopy(rule)
            changed[field] = str(changed[field]) + 'changed'
            self.assertNotEqual(c.reuse_key(rule), c.reuse_key(changed))

    def test_local_identity_strings_cannot_qualify(self):
        rule = c.read(c.BASE / 'proposition-bank.json')[0]
        self.assertIn('source_exposed_to_engineering', c.eligibility(rule)['blockers'])
        rule.update(exposure='unexposed', label_status='human_adjudicated', custodian='a')
        self.assertFalse(c.eligibility(rule)['qualified'])
        self.assertIn('independent_identity_and_custody_not_verified', c.eligibility(rule)['blockers'])

    def test_frozen_inputs_detect_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = Path(tmp) / 'calibration'
            shutil.copytree(c.BASE, b)
            (b / 'items.json').write_text('[]', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Frozen input drift'):
                c.build(b)

    def test_blind_packet_has_no_draft_labels_or_judgments(self):
        packet = c.blind_packet(c.read(c.BASE / 'items.json'))
        self.assertFalse(packet['qualified'])
        for row in packet['items']:
            self.assertEqual(set(row), {'id', 'source', 'candidate'})
        self.assertNotEqual([x['id'] for x in packet['items']], [x['id'] for x in c.read(c.BASE / 'items.json')])

    def test_panel_assets_and_invalid_envelopes_are_explicit(self):
        page = (c.ROOT / 'web/PALO_BlueprintBench_Diagnostics.html').read_text(encoding='utf-8')
        self.assertIn('src="assets/blueprintbench/calibration.js?', page)
        self.assertIn('href="assets/blueprintbench/calibration.css?', page)
        for row in c.build()['results']:
            if row['structural_error'] and row['receipt']:
                self.assertEqual(row['counts']['invalid'], 18)
                self.assertEqual(row['counts']['missing'], 0)
                self.assertIsNone(row['counts']['false_alarm_assigned_ratio'])
                self.assertEqual(row['semantic_status'], 'not_assessed')

    def test_result_consistency_and_no_qualification(self):
        data = c.build()
        self.assertFalse(data['qualified'])
        self.assertTrue(data['primary_scores_unchanged'])
        self.assertEqual(len(data['review_export']), 18)
        for result in data['results']:
            counts = result['counts']
            self.assertEqual(counts['assigned'], counts['classified'] + counts['missing'] + counts['invalid'] + counts['uncertain'])
            self.assertEqual(counts['mutations'], counts['detected'] + counts['missed_mutations'] + counts['mutations_unresolved'])



class ReviewRegressionTests(unittest.TestCase):
    def test_missing_controls_do_not_get_zero_false_alarm_rate(self):
        key = c.read(c.BASE / 'answer-key.json')
        mutants = {r['id']: {'verdict': 'altered'} for r in key if r['expected'] == 'altered'}
        self.assertIsNone(c.tally(key, mutants)['false_alarm_assigned_ratio'])
        self.assertFalse(c.tally([], {})['false_alarm_rate_interpretable'])

    def test_candidate_and_prompt_are_part_of_reuse_identity(self):
        rule = c.read(c.BASE / 'proposition-bank.json')[0]
        self.assertNotEqual(c.reuse_key(rule, 'may', 'p1'), c.reuse_key(rule, 'must', 'p1'))
        self.assertNotEqual(c.reuse_key(rule, 'may', 'p1'), c.reuse_key(rule, 'may', 'p2'))
        for field in ('allowed_alternatives', 'forbidden_inferences'):
            changed = copy.deepcopy(rule); changed[field] = []
            self.assertNotEqual(c.reuse_key(rule, 'may', 'p1'), c.reuse_key(changed, 'may', 'p1'))

    def test_capture_repair_and_receipt_rewrite_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = Path(tmp) / 'calibration'; shutil.copytree(c.BASE, b)
            raw = b / 'responses/gemini-raw.txt'; raw.write_text('{}', encoding='utf-8')
            receipt_path = b / 'responses/gemini-receipt.json'
            receipt = c.read(receipt_path); receipt['raw_text_sha256'] = c.digest(raw.read_bytes())
            receipt_path.write_text(json.dumps(receipt), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Capture lock mismatch'): c.build(b)

    def test_required_frozen_inputs_cannot_be_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = Path(tmp) / 'calibration'; shutil.copytree(c.BASE, b)
            p = b / 'manifest.json'; obj = c.read(p); del obj['files']['answer-key.json']; p.write_text(json.dumps(obj), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Required frozen input'): c.build(b)

    def test_blind_packet_is_separate_from_labelled_export(self):
        self.assertNotIn('blind_annotation_preparation', c.build())
        packet = c.blind_packet(c.read(c.BASE / 'items.json'))
        self.assertEqual({r['id'] for r in packet['items']}, {r['id'] for r in c.read(c.BASE / 'items.json')})
        self.assertTrue(all(set(r) == {'id', 'source', 'candidate'} for r in packet['items']))

    def test_deeply_nested_response_is_invalid(self):
        self.assertIsNone(c.validate_response('[' * 2000 + '0' + ']' * 2000, set())[0])

if __name__ == '__main__': unittest.main()
