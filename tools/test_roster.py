import unittest
import build_roster as r


class RosterTests(unittest.TestCase):
    def test_fixed_scope_and_cohort_separation(self):
        d = r.build()
        self.assertEqual(len(d['rows']), 18)
        self.assertEqual(len(d['historical_diagnostics']), 10)
        self.assertEqual(d['external_suites_executed'], 0)
        self.assertFalse(d['reviewer_diagnostics_included'])
        self.assertFalse(d['qualified'])
        self.assertEqual(d['version'], '2026-11-11.3')
        self.assertTrue(all(not any('rank' in key for key in row) for row in d['rows']))

    def test_counts_coverage_and_context_from_frozen_records(self):
        d = r.build()
        self.assertEqual(sum(x['label_matches'] == x['assigned_labels'] for x in d['rows']), 6)
        self.assertEqual([r['name'] for r in d['rows']], sorted((r['name'] for r in d['rows']), key=lambda n:n.split(':',1)[-1].strip().casefold()))
        blocked = next(x for x in d['rows'] if 'fugu' in x['id'])
        self.assertIsNone(blocked['agreement_received'])
        self.assertEqual(blocked['classification_coverage'], 0)
        self.assertEqual(blocked['missing_labels'], 324)
        self.assertIsNone(blocked['observed_prompt_tokens_max'])
        gemini = next(x for x in d['rows'] if x['id'].startswith('google/'))
        self.assertEqual(gemini['agreement_received'], 1)
        self.assertEqual(gemini['missing_labels'], 36)
        self.assertLess(gemini['classification_coverage'], 1)
        for row in d['rows']:
            self.assertEqual(row['classified_labels'] + row['missing_labels'], row['assigned_labels'])
            self.assertEqual(row['label_matches'] + row['disagreements'], row['classified_labels'])
            if row['observed_prompt_tokens_max'] is not None:
                self.assertGreaterEqual(row['observed_prompt_tokens_max'], row['observed_prompt_tokens_min'])
                self.assertLess(row['observed_prompt_tokens_max'], row['advertised_context_tokens'])


if __name__ == '__main__': unittest.main()
