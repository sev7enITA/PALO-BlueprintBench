"""Reproduce the November audit attacks against the draft evidence contract."""
import copy
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

import blueprintbench as bb
import test_blueprintbench as fixtures
from demo import put, put_text


class AuditRegressionTests(unittest.TestCase):
    setUp = fixtures.EvidenceTests.setUp
    tearDown = fixtures.EvidenceTests.tearDown
    evaluate = fixtures.EvidenceTests.evaluate
    rewrite_attempt = fixtures.EvidenceTests.rewrite_attempt
    alter_gold = fixtures.EvidenceTests.alter_gold
    change_receipt = fixtures.EvidenceTests.change_receipt

    def rebind(self, index, receipt, annotation=None):
        attempt = self.run['attempts'][index]
        attempt['receipt'] = put(self.root, f'audit-{index}/receipt.json', receipt)
        if annotation is not None:
            annotation['receipt_sha256'] = attempt['receipt']['sha256']
            attempt['annotation'] = put(self.root, f'audit-{index}/annotation.json', annotation)

    def test_ev01_substantive_claim_hidden_as_formatting(self):
        attempt = self.run['attempts'][1]
        receipt = bb.read_json(self.root / attempt['receipt']['path'])
        emitted = bb.read_json(self.root / receipt['claims_artifact']['path'])
        annotation = bb.read_json(self.root / attempt['annotation']['path'])
        hidden = emitted.pop()
        annotation['claims'].pop()
        receipt['non_claim_spans'].append({'span': hidden['span'], 'reason': 'formatting'})
        receipt['claims_artifact'] = put(self.root, 'hidden/claims.json', emitted)
        attempt['state'] = receipt['state'] = 'pass'
        self.rebind(1, receipt, annotation)
        with self.assertRaisesRegex(bb.Invalid, 'ASCII whitespace'):
            self.evaluate()

    def test_ev01_unanswerable_assertion_hidden_as_preamble(self):
        self.alter_gold(2, lambda g: g.update(required_propositions=[], meaning={}, critical_rule_ids=[], forbidden_inferences=[], answerable=False))
        attempt = self.run['attempts'][2]
        receipt = bb.read_json(self.root / attempt['receipt']['path'])
        raw = 'All purchases require approval.'
        receipt['raw_output'] = put_text(self.root, 'hidden/raw.txt', raw)
        receipt['non_claim_spans'] = [{'span': [0, len(raw)], 'reason': 'preamble'}]
        attempt['annotation'] = None
        self.rebind(2, receipt)
        with self.assertRaisesRegex(bb.Invalid, 'ASCII whitespace'):
            self.evaluate()

    def test_ev02_forbidden_match_forces_critical_inversion(self):
        self.rewrite_attempt(1, lambda a, r, n, e: n['claims'][1].update(critical=False, violated_gold=[], error_category='other_noncritical'))
        row = self.evaluate()['rows'][1]
        self.assertEqual((row['critical_errors'], row['critical_source_rule_inversions']), (1, 1))
        self.assertFalse(row['accepted_task'])

    def test_ev02_unknown_forbidden_id_rejected(self):
        self.rewrite_attempt(1, lambda a, r, n, e: n['claims'][1].update(matches_forbidden=['made-up']))
        with self.assertRaisesRegex(bb.Invalid, 'unknown forbidden'):
            self.evaluate()

    def test_ev02_alternative_must_map_to_registered_gold(self):
        self.alter_gold(0, lambda g: g.update(allowed_alternatives={'g2': [{'id': 'a2', 'text': 'Permission at EUR 500 or less'}]}))
        self.rewrite_attempt(0, lambda a, r, n, e: n['claims'][0].update(matches_alternatives=['a2']))
        with self.assertRaisesRegex(bb.Invalid, 'alternative must map'):
            self.evaluate()

    def test_ev03_family_aggregates_include_missing_assignments(self):
        self.run['attempts'].pop()
        result = self.evaluate()
        family = result['aggregates']['family']['synthetic-purchasing']
        self.assertEqual((family['assigned_attempts'], family['recorded_attempts']), (3, 2))
        self.assertIsNone(family['inversions_per_100_rules'])
        self.assertEqual(family['critical_occurrences'], 1)

    def test_ev05_declared_names_cannot_remove_identity_block(self):
        for i in range(3):
            self.alter_gold(i, lambda g: g.update(annotation_status='independent_adjudicated', annotator_ids=['gold-a', 'gold-b'], adjudicator_id='gold-c'))
            self.rewrite_attempt(i, lambda a, r, n, e: n.update(review_type='independent_human', reviewer_ids=['output-a', 'output-b'], adjudicator_id='output-c'))
        result = self.evaluate()
        self.assertIn('independent_human_gold_or_assessment_missing', result['comparability_blocks'])
        self.assertIn('identity_and_independence_not_verified', result['comparability_blocks'])
        self.assertFalse(result['qualified'])

    def test_ev05_gold_and_output_panel_overlap_rejected(self):
        self.alter_gold(0, lambda g: g.update(annotation_status='independent_adjudicated', annotator_ids=['a', 'b'], adjudicator_id='c'))
        self.rewrite_attempt(0, lambda a, r, n, e: n.update(review_type='independent_human', reviewer_ids=['a', 'b'], adjudicator_id='c'))
        with self.assertRaisesRegex(bb.Invalid, 'panels overlap'):
            self.evaluate()

    def test_ev05_submitter_cannot_review_own_output(self):
        self.rewrite_attempt(0, lambda a, r, n, e: n.update(review_type='independent_human', reviewer_ids=[self.run['submitter_id'], 'b'], adjudicator_id='c'))
        with self.assertRaisesRegex(bb.Invalid, 'submitter cannot'):
            self.evaluate()

    def test_ev07_placeholder_configuration_rejected(self):
        config = {name: {'x': 1} for name in ['model', 'provider_runtime', 'settings', 'pipeline', 'environment']}
        with self.assertRaisesRegex(bb.Invalid, 'schema'):
            bb.validate_record('configuration', config)

    def test_ev07_unavailable_needs_reason(self):
        campaign = self.lock['payload']['campaign']
        config = bb.read_json(self.root / campaign['subjects'][0]['configuration']['path'])
        config['model']['revision'] = 'unavailable'
        campaign['subjects'][0]['configuration'] = put(self.root, 'missing-config.json', config)
        with self.assertRaisesRegex(bb.Invalid, 'unavailable value needs reason'):
            bb.freeze(campaign, self.root)

    def test_ev08_future_run_rejected(self):
        self.run['started_at'] = self.run['finished_at'] = '2099-01-01T00:00:00Z'
        with self.assertRaisesRegex(bb.Invalid, 'future'):
            self.evaluate()

    def test_ev08_impossible_elapsed_rejected(self):
        self.run['attempts'][0]['elapsed_seconds'] = 10**9
        with self.assertRaisesRegex(bb.Invalid, 'elapsed time exceeds'):
            self.evaluate()

    def test_ev08_serial_cannot_declare_parallel_capacity(self):
        self.run['execution']['max_concurrency'] = 3
        with self.assertRaisesRegex(bb.Invalid, 'serial execution'):
            self.evaluate()

    def test_ev09_provider_request_reuse_rejected(self):
        for i in [0, 1]:
            self.change_receipt(i, lambda r: r.update(request_identity={'provider_request_id': 'same-call', 'request_sha256': 'a' * 64, 'unavailable_reason': ''}))
        # change_receipt's fixture path is shared, so preserve the first binding.
            receipt = bb.read_json(self.root / self.run['attempts'][i]['receipt']['path'])
            annotation = bb.read_json(self.root / self.run['attempts'][i]['annotation']['path'])
            self.rebind(i, receipt, annotation)
        with self.assertRaisesRegex(bb.Invalid, 'request ID reused'):
            self.evaluate()

    def add_repetition(self):
        campaign = self.lock['payload']['campaign']
        campaign['repetitions'] = 2
        self.lock = bb.freeze(campaign, self.root)
        self.run['campaign_sha256'] = self.lock['sha256']
        self.run['started_at'] = self.run['finished_at'] = self.lock['payload']['registered_at']
        attempt = copy.deepcopy(self.run['attempts'][0])
        attempt['repetition'] = 2
        receipt = bb.read_json(self.root / attempt['receipt']['path'])
        receipt['repetition'] = 2
        annotation = bb.read_json(self.root / attempt['annotation']['path'])
        self.run['attempts'].append(attempt)
        self.rebind(3, receipt, annotation)

    def test_ev09_identical_output_warned_not_assumed_fraud(self):
        self.add_repetition()
        self.assertIn('identical_output_across_repetitions', [w['code'] for w in self.evaluate()['warnings']])

    def test_ev10_equivalence_consistency_across_repetitions(self):
        self.add_repetition()
        self.rewrite_attempt(3, lambda a, r, n, e: n['claims'][0].update(verdict='unsupported', matches_gold=[], error_category='other_noncritical'))
        with self.assertRaisesRegex(bb.Invalid, 'across repetitions'):
            self.evaluate()

    def test_ev11_trivial_policy_flagged(self):
        campaign = self.lock['payload']['campaign']
        campaign['success_policy'].update(minimum_precision=0, minimum_recall=0)
        self.lock = bb.freeze(campaign, self.root)
        self.run['campaign_sha256'] = self.lock['sha256']
        self.run['started_at'] = self.run['finished_at'] = self.lock['payload']['registered_at']
        result = self.evaluate()
        self.assertTrue(result['policy_is_trivial'])
        self.assertIn('trivial_success_policy', result['comparability_blocks'])

    def test_ev12_crlf_cannot_use_normalised_offsets(self):
        def change(receipt):
            raw = (self.root / receipt['raw_output']['path']).read_bytes().decode('utf-8').replace('\n', '\r\n')
            receipt['raw_output'] = put_text(self.root, 'crlf/raw.txt', raw)
        self.change_receipt(0, change)
        with self.assertRaisesRegex(bb.Invalid, 'span/text'):
            self.evaluate()

    def test_ev12_exact_crlf_inside_claim_preserved(self):
        self.rewrite_attempt(0, lambda a, r, n, e: e[0].update(text='Purchases\r\nabove EUR 500 require approval.'))
        self.assertEqual(self.evaluate()['rows'][0]['emitted'], 2)

    def test_ev13_reported_zero_requires_reason(self):
        for status in ['reported', 'reconciled']:
            self.run['attempts'][0]['cost'] = {'status': status, 'usd': 0}
            with self.assertRaisesRegex(bb.Invalid, 'zero cost needs'):
                self.evaluate()

    def test_ev15_critical_without_category_rejected(self):
        self.rewrite_attempt(1, lambda a, r, n, e: n['claims'][1].update(matches_forbidden=[], violated_gold=[]))
        with self.assertRaisesRegex(bb.Invalid, 'unsupported_addition category'):
            self.evaluate()

    def test_ev15_unsupported_addition_separate_from_inversion(self):
        self.rewrite_attempt(1, lambda a, r, n, e: n['claims'][1].update(matches_forbidden=[], violated_gold=[], error_category='unsupported_addition'))
        row = self.evaluate()['rows'][1]
        self.assertEqual((row['critical_errors'], row['critical_source_rule_inversions']), (1, 0))

    def test_ev14_published_canonical_vectors(self):
        vectors = json.loads(Path(bb.__file__).with_name('canonical-vectors.json').read_text(encoding='utf-8'))
        for vector in vectors['vectors']:
            self.assertEqual(bb.canonical(vector['input']).hex(), vector['canonical_utf8_hex'])
            self.assertEqual(bb.digest(vector['input']), vector['sha256'])

    def cli(self, *args):
        return subprocess.run([sys.executable, str(Path(bb.__file__).resolve()), *map(str, args)], capture_output=True, text=True)

    def test_ev17_cli_evaluates_bound_fixture(self):
        output = self.root / 'cli-result.json'
        result = self.cli('evaluate', self.root / 'campaign.lock.json', self.root / 'run.json', '--evidence-root', self.root, '--output', output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(output.read_text(encoding='utf-8'))['qualified'])

    def test_ev17_cli_malformed_input_fails_without_output(self):
        bad = self.root / 'bad.json'
        bad.write_text('{"x":1,"x":2}', encoding='utf-8')
        output = self.root / 'no-result.json'
        result = self.cli('freeze', bad, '--evidence-root', self.root, '--output', output)
        self.assertEqual(result.returncode, 2)
        self.assertIn('duplicate JSON key', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertFalse(output.exists())

    def test_ev17_cli_does_not_overwrite_existing_evidence(self):
        result = self.cli('evaluate', self.root / 'campaign.lock.json', self.root / 'run.json', '--evidence-root', self.root, '--output', self.root / 'run.json')
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
