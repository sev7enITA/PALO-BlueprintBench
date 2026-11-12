"""Release status must not count cancelled requests as a completed study."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class QualificationConsistencyTests(unittest.TestCase):
    def test_generation_scope_matches_retained_results(self):
        roadmap = json.loads((ROOT / 'docs/qualification-roadmap.json').read_text(encoding='utf-8'))
        published = json.loads((ROOT / 'web/downloads/blueprintbench/generation-results.json').read_text(encoding='utf-8'))
        scope = roadmap['current_development_study']; result = published['analysis']['summary']
        self.assertEqual(scope['state'], 'closed_incomplete')
        self.assertEqual(scope['assigned_calls'], result['assigned_calls'])
        self.assertEqual(scope['model_configurations'], len(published['models']))
        self.assertEqual(scope['supplemental_assignments'], 0)
        self.assertEqual(scope['original_assignments'], result['assigned_calls'])
        self.assertFalse(roadmap['independently_qualified'])
        self.assertFalse(roadmap['numerical_ranks_enabled'])

if __name__ == '__main__': unittest.main()
