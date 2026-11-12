"""Synthetic invariance of task ordering, not semantic or human validation."""
import copy
import tempfile
import unittest
from pathlib import Path
import blueprintbench as bb
import demo

class RepresentationInvarianceTests(unittest.TestCase):
    def test_reordering_attempts_preserves_scored_outcomes(self):
        with tempfile.TemporaryDirectory() as directory:
            lock, run = demo.make(Path(directory) / 'fixture')
            original = bb.evaluate(lock, copy.deepcopy(run), Path(directory) / 'fixture')
            changed = copy.deepcopy(run); changed['attempts'].reverse()
            reordered = bb.evaluate(lock, changed, Path(directory) / 'fixture')
            for key in ('assigned_attempts', 'recorded_attempts', 'missing_attempts',
                        'accepted_tasks', 'critical_errors', 'aggregates'):
                self.assertEqual(original[key], reordered[key], key)
            self.assertEqual({(r['task_id'], r['repetition']): r for r in original['rows']},
                             {(r['task_id'], r['repetition']): r for r in reordered['rows']})
            self.assertIsNone(reordered['qualification_decision'])

if __name__ == '__main__': unittest.main()
