import unittest
import build_measurement_diagnostics as diagnostics

class MeasurementDiagnosticsTests(unittest.TestCase):
    def test_missing_invalid_are_not_scores(self):
        data = diagnostics.build()
        self.assertFalse(data['qualified'])
        for row in data['reviewers']:
            if not row['envelope_valid']:
                self.assertIsNone(row['detection_rate_conditional'])
                self.assertIsNone(row['false_alarm_rate_conditional'])
                self.assertIsNone(row['tp']); self.assertIsNone(row['fp'])
                self.assertEqual(row['invalid'], row['assigned'])
    def test_known_determinate_rates(self):
        row = next(r for r in diagnostics.build()['reviewers'] if r['reviewer'] == 'fable')
        self.assertEqual((row['tp'], row['fn'], row['fp'], row['tn']), (6, 0, 0, 12))
        self.assertEqual(row['detection_denominator_classified'], 6)
        self.assertEqual(row['false_alarm_denominator_classified'], 12)

if __name__ == '__main__': unittest.main()
