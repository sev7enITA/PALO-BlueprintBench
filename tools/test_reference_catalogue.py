"""Reference expansion preserves prior scope and traceable attention signals."""
import csv
import io
import json
from pathlib import Path
import unittest
import build_references

ROOT = Path(__file__).resolve().parents[1]


class ReferenceCatalogueTests(unittest.TestCase):
    def test_fifteen_new_families_have_sources_and_version_boundaries(self):
        d = json.loads((ROOT/'docs/benchmark-references.json').read_text(encoding='utf-8'))
        rows = d['entries']
        added = [r for r in rows if r['review_group'] == 'visibility-expansion-20261111']
        self.assertEqual(len(rows), 35)
        self.assertEqual(len({r['id'] for r in rows}), 35)
        self.assertEqual(len(added), 15)
        self.assertEqual(sum(r['in_requested_directory'] for r in rows), 12)
        self.assertEqual(d['palo_status']['qualified_heldout_results'], 0)
        self.assertIsNone(d['palo_status']['pbi_score'])
        for row in added:
            for field in ('version_scope','visibility_basis','visibility_sources','caution','lesson'):
                self.assertTrue(row[field], (row['id'], field))
            for url in row['visibility_sources'].split(';'):
                self.assertTrue(url.strip().startswith('https://'))
            self.assertIn(row['palo_transfer'], ['Direct','Method','Context'])
        self.assertIn('Not an exhaustive ranking', d['visibility_selection']['limits'])
        bfcl = next(r for r in added if r['id'] == 'bfcl')
        self.assertIn('not BFCL alone', bfcl['repo_star_scope'])
        snapshots = json.loads((ROOT/'docs/reference-visibility-signals.json').read_text(encoding='utf-8'))
        for row in added:
            if row['repo_stars'] is not None:
                record = next(x for x in snapshots['repositories'] if x['html_url'] == row['repo_url'])
                self.assertEqual(record['stargazers_count'], row['repo_stars'])
                self.assertEqual(record['checked_on'], row['checked_on'])

    def test_exports_and_html_preserve_every_reference(self):
        md, exported, html = build_references.render(ROOT)
        rows = list(csv.DictReader(io.StringIO(exported.decode('utf-8'))))
        self.assertEqual(len(rows), 35)
        self.assertEqual(html.count('data-reference='), 35)
        self.assertIn('Explore 15 added benchmark families', html)
        self.assertIn('Review the original 20 references', html)
        self.assertNotIn('href="downloads/blueprintbench/benchmark-references.md"', html)
        self.assertTrue(all(row['repo_stars'] == '' for row in rows if not row['repo_url']))
        for text in (md.decode('utf-8'), html):
            self.assertNotIn(chr(8212), text)
            self.assertNotIn(chr(8211), text)


if __name__ == '__main__':
    unittest.main()
