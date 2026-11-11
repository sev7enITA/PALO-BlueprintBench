"""Country metadata is a sourced overlay, not part of frozen campaign evidence."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ModelOriginsTests(unittest.TestCase):
    def test_complete_sourced_overlay(self):
        source = ROOT / 'docs/model-origins.json'
        public = ROOT / 'web/downloads/blueprintbench/model-origins.json'
        self.assertEqual(source.read_bytes(), public.read_bytes())
        metadata = json.loads(source.read_text(encoding='utf-8'))
        data = json.loads((ROOT / 'web/downloads/blueprintbench/leaderboard-data.json').read_text(encoding='utf-8'))
        makers = {row['id']: row for row in metadata['makers']}
        self.assertEqual(len(makers), len(metadata['makers']))
        prefixes = {(m.get('id') or m['model']).split('/')[0] for cohort in ('internal', 'historical') for m in data[cohort]['models']}
        self.assertTrue(prefixes <= makers.keys())
        valid = {'US': 'United States', 'CA': 'Canada', 'CN': 'China', 'FR': 'France', 'JP': 'Japan', 'KR': 'South Korea'}
        for row in makers.values():
            self.assertTrue(row['basis'])
            self.assertTrue(row['sources'])
            self.assertEqual(bool(row['countries']), row['status'] == 'verified')
            for country in row['countries']:
                self.assertEqual(valid[country['code']], country['name'])
            for citation in row['sources']:
                self.assertTrue(citation['url'].startswith('https://'))
                self.assertEqual(citation['checked_at'], metadata['as_of'])
        self.assertEqual(makers['nex-agi']['countries'], [])
        self.assertIn('data residency', metadata['definition'])
        self.assertFalse(data['internal']['qualified'])
        self.assertEqual(data['qualified_count'], 0)


if __name__ == '__main__':
    unittest.main()
