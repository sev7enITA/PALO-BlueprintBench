"""Offline tests for cost guards and exact provider requests. No model calls."""
import json
from pathlib import Path
import tempfile
import unittest
import runner


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.manifest = {'cumulative_ceiling_usd': 40, 'new_campaign_ceiling_usd': 12,
            'previous_unknown_cost_reserve_usd': 0.481264729}

    def test_historical_spend_and_unknown_reserve_bound(self):
        value = runner.budget_headroom(self.manifest, {'total_usage': 39, 'total_credits': 50}, {'limit_remaining': 20}, 0, 39)
        self.assertAlmostEqual(value, .518735271)

    def test_lagged_account_adds_observed_campaign_spend(self):
        value = runner.budget_headroom(self.manifest, {'total_usage': 35, 'total_credits': 50}, {'limit_remaining': 20}, 3, 35)
        self.assertAlmostEqual(value, 1.518735271)

    def test_external_spend_and_outstanding_are_reserved(self):
        value = runner.budget_headroom(self.manifest, {'total_usage': 38, 'total_credits': 50}, {'limit_remaining': 20}, 1, 35, .3)
        self.assertAlmostEqual(value, 1.218735271)

    def test_campaign_and_key_caps(self):
        self.assertEqual(runner.budget_headroom(self.manifest, {'total_usage': 20, 'total_credits': 50}, {'limit_remaining': 20}, 11, 9), 1)
        self.assertEqual(runner.budget_headroom(self.manifest, {'total_usage': 20, 'total_credits': 50}, {'limit_remaining': .2}, 0, 20), .2)

    def test_nonfinite_or_unknown_budget_fails_closed(self):
        for value in (None, float('nan'), float('inf'), -1, True):
            with self.assertRaises((TypeError, ValueError)):
                runner.budget_headroom(self.manifest, {'total_usage': value, 'total_credits': 50}, {'limit_remaining': 20}, 0, 0)

    def test_pending_and_unknown_resume_abort(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / 'runs' / 'one'
            directory.mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, 'Orphan'):
                runner.resume_records(root)
            (directory / 'record.json').write_text(json.dumps({'cost_status': 'unknown', 'cost_usd': None}))
            with self.assertRaisesRegex(ValueError, 'Unknown cost'):
                runner.resume_records(root)

    def test_provider_and_schema_pinning_without_label_leak(self):
        task = {'messages': [{'role': 'user', 'content': 'source only'}], 'track': 'verification',
            'assessment_key': {'P001': 'supported'}, 'response_schema': {'type': 'object'}}
        value = runner.payload_for(task, {'id': 'google/example', 'provider': 'google-vertex/global'})
        self.assertEqual(value['provider']['only'], ['google-vertex/global'])
        self.assertFalse(value['provider']['allow_fallbacks'])
        self.assertEqual(value['reasoning']['effort'], 'high')
        self.assertTrue(value['response_format']['json_schema']['strict'])
        self.assertNotIn('assessment_key', json.dumps(value))
        self.assertNotIn('tools', value)

    def test_rates_include_applicable_overrides_and_cache_write(self):
        model = {'endpoint': {'pricing': {'prompt': '0.000002', 'completion': '0.000010',
            'input_cache_write': '0.000003', 'overrides': [{'min_prompt_tokens': 100, 'prompt': '0.000004', 'completion': '0.000015'}]}}}
        self.assertEqual(runner.rates(model, 99), (.000003, .000010))
        self.assertEqual(runner.rates(model, 100), (.000004, .000015))
        expected = ((10 + 4096) * .000004 + 32768 * .000015) * 1.1
        self.assertAlmostEqual(runner.reservation_for(b'x' * 10, model), expected)

    def test_budget_public_contract(self):
        value = runner.make_summary([{}], [], self.manifest, 20, {'total_usage': 20}, None)
        for field in ('authorised_total_usd', 'account_usage_usd', 'previous_unresolved_reserve_usd',
            'current_unknown_reserve_usd', 'campaign_known_usd', 'campaign_ceiling_usd',
            'conservative_cumulative_bound_usd', 'remaining_authorised_headroom_usd'):
            self.assertIn(field, value)
        self.assertEqual(value['not_run'], 1)
        self.assertFalse(value['qualified'])


if __name__ == '__main__':
    unittest.main()
