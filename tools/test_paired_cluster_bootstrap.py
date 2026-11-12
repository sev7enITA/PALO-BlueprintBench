"""In-memory synthetic checks; no benchmark outcomes or human qualification."""
import copy
import unittest
import paired_cluster_bootstrap as b


def fixture():
    tasks = [{'family_id': f, 'task_id': 't'} for f in ('f1', 'f2', 'f3')]
    rows = []
    for task in tasks:
        for repetition in range(1, 4):
            for config, count in [('A', 7), ('B', 5)]:
                rows.append({**task, 'repetition': repetition, 'configuration_id': config,
                             'status': 'completed', 'numerator': count, 'denominator': 10})
    return {'tasks': tasks, 'observations': rows}


def evaluate(data, **changes):
    options = {'repetitions': 3, 'minimum_families': 3, 'samples': 200, 'seed': 42}; options.update(changes)
    return b.run(data, 'A', 'B', **options)


class PairedBootstrapTests(unittest.TestCase):
    def test_constant_difference_and_reproducibility(self):
        result = evaluate(fixture()); self.assertAlmostEqual(result['point_estimate'], .2)
        self.assertAlmostEqual(result['interval']['lower'], .2); self.assertAlmostEqual(result['interval']['upper'], .2)
        self.assertFalse(result['qualified']); self.assertEqual(result, evaluate(fixture()))

    def test_missing_and_failed_block_inference(self):
        data = fixture(); data['observations'].pop(); out = evaluate(data)
        self.assertIsNone(out['interval']); self.assertEqual(len(out['missing']), 1)
        data = fixture(); data['observations'][0].update(status='failed', numerator=None, denominator=None)
        out = evaluate(data); self.assertIsNone(out['interval']); self.assertEqual(len(out['incomplete']), 1)

    def test_family_minimum_and_fixed_denominators(self):
        self.assertIn('insufficient_families', evaluate(fixture(), minimum_families=4)['blockers'])
        data = fixture(); data['observations'][0]['denominator'] = 11
        with self.assertRaisesRegex(ValueError, 'same fixed denominator'): evaluate(data)

    def test_task_denominator_cannot_change_between_repetitions(self):
        data = fixture()
        for row in data['observations']:
            if row['family_id'] == 'f1' and row['repetition'] == 2:
                row['denominator'] = 11
        with self.assertRaisesRegex(ValueError, 'same fixed denominator'): evaluate(data)

    def test_row_order_does_not_change_seeded_estimate(self):
        data = fixture(); expected = evaluate(data)
        data['observations'].reverse(); data['tasks'].reverse()
        self.assertEqual(evaluate(data), expected)

    def test_duplicate_unexpected_and_incomplete_counts_rejected(self):
        data = fixture(); data['observations'].append(copy.deepcopy(data['observations'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate'): evaluate(data)
        data = fixture(); data['observations'][0]['repetition'] = 4
        with self.assertRaisesRegex(ValueError, 'Unexpected'): evaluate(data)
        data = fixture(); data['observations'][0]['status'] = 'not_run'
        with self.assertRaisesRegex(ValueError, 'must not contain'): evaluate(data)

    def test_paired_swap_reverses_difference(self):
        data = fixture(); left = evaluate(data)
        right = b.run(data, 'B', 'A', repetitions=3, minimum_families=3, samples=200, seed=42)
        self.assertAlmostEqual(left['point_estimate'], -right['point_estimate'])
        self.assertAlmostEqual(left['interval']['lower'], -right['interval']['upper'])

    def test_equal_family_weight_with_unequal_task_counts(self):
        data = fixture()
        extra = {'family_id': 'f1', 'task_id': 'second'}
        data['tasks'].append(extra)
        for repetition in range(1, 4):
            for config, numerator in [('A', 10), ('B', 0)]:
                data['observations'].append({**extra, 'repetition': repetition,
                    'configuration_id': config, 'status': 'completed',
                    'numerator': numerator, 'denominator': 10})
        result = evaluate(data)
        self.assertAlmostEqual(result['point_estimate'], (0.6 + 0.2 + 0.2) / 3)
        self.assertLess(result['interval']['lower'], result['interval']['upper'])

    def test_invalid_input_types_rejected(self):
        with self.assertRaisesRegex(ValueError, 'JSON object'): evaluate([])
        data = fixture(); data['observations'][0]['family_id'] = []
        with self.assertRaisesRegex(ValueError, 'family_id'): evaluate(data)

if __name__ == '__main__': unittest.main()
