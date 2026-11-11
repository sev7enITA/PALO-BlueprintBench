import unittest
import json
import build_roster as r


class RosterTests(unittest.TestCase):
    def test_fixed_scope_and_cohort_separation(self):
        d = r.build()
        self.assertEqual(len(d['rows']), 18)
        self.assertEqual(len(d['historical_unranked']), 10)
        self.assertEqual(d['external_suites_executed'], 0)
        self.assertFalse(d['calibration_included_in_ranks'])
        self.assertFalse(d['qualified'])
        self.assertTrue(all(x['rank'] is None for x in d['historical_unranked']))

    def test_ranks_and_context_from_frozen_records(self):
        d = r.build()
        self.assertEqual(sum(x['agreement_rank'] == 1 for x in d['rows']), 6)
        self.assertEqual(sorted(set(x['agreement_rank'] for x in d['rows'] if x['agreement_rank']))[:2], [1, 7])
        blocked = next(x for x in d['rows'] if x['id']=='sakanaai/fugu-max') if any(x['id']=='sakanaai/fugu-max' for x in d['rows']) else next(x for x in d['rows'] if 'fugu' in x['id'])
        self.assertIsNone(blocked['agreement_rank'])
        self.assertIsNone(blocked['observed_prompt_tokens_max'])
        for row in d['rows']:
            if row['cost_rank'] is not None:
                self.assertTrue(row['charge_rank_eligible'])
                self.assertEqual(row['complete_calls'], row['assigned_calls'])
            if row['observed_prompt_tokens_max'] is not None:
                self.assertGreaterEqual(row['observed_prompt_tokens_max'], row['observed_prompt_tokens_min'])
                self.assertLess(row['observed_prompt_tokens_max'], row['advertised_context_tokens'])


if __name__ == '__main__': unittest.main()
