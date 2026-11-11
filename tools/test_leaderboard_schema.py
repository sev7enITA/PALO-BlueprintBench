"""Regression gates for cohort separation and truthful published JSON-LD."""
import hashlib
import json
from pathlib import Path
import re
import unittest
import build_leaderboard as build

ROOT=Path(__file__).resolve().parents[1]


def objects(value):
    if isinstance(value,dict):
        yield value
        for v in value.values():yield from objects(v)
    elif isinstance(value,list):
        for v in value:yield from objects(v)


class PublicationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'web/downloads/blueprintbench/leaderboard-data.json').read_text(encoding='utf-8'))

    def test_cohorts_remain_separate_and_unqualified(self):
        self.assertEqual(self.data['qualified_count'],0)
        self.assertFalse(self.data['internal']['qualified'])
        self.assertEqual(len(self.data['internal']['models']),3)
        self.assertEqual(len(self.data['historical']['models']),10)
        self.assertNotIn('models',self.data)
        self.assertTrue(all(m['rank'] is None for m in self.data['historical']['models']))

    def test_original_denominators_and_unknown_charges(self):
        d=self.data['internal'];r=d['records']
        self.assertEqual(len(r),54)
        self.assertEqual(len({x['id'] for x in r}),54)
        self.assertEqual(sum(x['state']=='completed' for x in r),53)
        unknown=[x for x in r if x['cost_status']=='unknown']
        self.assertEqual(len(unknown),1)
        self.assertIsNone(unknown[0]['cost_usd'])
        self.assertEqual(unknown[0]['http_status'],503)
        self.assertGreater(unknown[0]['reserved_usd'],0)
        self.assertAlmostEqual(sum(x['cost_usd'] or 0 for x in r),0.8305669)
        for m in d['models']:
            self.assertEqual(m['verification_assigned_probes'],324)
            self.assertEqual(m['verification_classified']+m['verification_missing'],324)

    def test_sensitivity_is_posthoc_and_excludes_same_item_everywhere(self):
        d=self.data['internal']
        for m in d['models']:
            rows=[r for r in d['verification_rows'] if r['model']==m['id']]
            kept=[j for r in rows for j in r['judgments'] if not (r['case']=='invoice-matching' and j['id']=='P002')]
            s=next(x for x in d['sensitivity'] if x['model']==m['id'])
            self.assertTrue(s['posthoc']);self.assertEqual(s['assigned'],321)
            self.assertEqual(s['classified'],len(kept));self.assertEqual(s['correct'],sum(x['correct'] for x in kept))
        self.assertTrue(d['label_challenge']['primary_frozen_labels_unchanged'])

    def test_translation_examples_bind_to_recorded_blueprints(self):
        examples=self.data['internal']['translation_examples']
        self.assertEqual(len(examples),324)
        self.assertEqual(len({(e['model'],e['case'],e['repetition'],e['source_id']) for e in examples}),324)
        base=ROOT/'internal_tests/2026-11-11-frontier'
        for e in examples:
            b=json.loads((base/e['evidence_path']).read_text(encoding='utf-8'))
            self.assertFalse(b['qualified'])
            rule=next(r for r in b['rules'] if r['id']==e['source_id'])
            self.assertEqual(rule['proposed_specification'],e['proposed_specification'])
            self.assertEqual(rule['source_text'],e['source_text'])
            self.assertEqual(e['verbatim'],e['source_text']==e['proposed_specification'])

    def test_schemas_are_source_generated_and_refs_resolve(self):
        for file,url in [('PALO_BlueprintBench.html',build.OVERVIEW),('PALO_BlueprintBench_Leaderboard.html',build.BOARD)]:
            text=(ROOT/'web'/file).read_text(encoding='utf-8')
            scripts=re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',text,re.S)
            self.assertEqual(len(scripts),1)
            actual=json.loads(scripts[0]);self.assertEqual(actual,build.dataset_graph(self.data,url))
            ids=[x['@id'] for x in actual['@graph']]
            self.assertEqual(len(ids),len(set(ids)))
            for node in objects(actual):
                if set(node)=={'@id'}:self.assertIn(node['@id'],ids)
                self.assertNotIn(node.get('@type'),['AggregateRating','Rating','Review','Certification','Product','SoftwareApplication'])
                self.assertNotIn('additionalProperty',node)
                self.assertNotIn('award',node)
                if 'position' in node:self.assertEqual(node['@type'],'ListItem')
            self.assertIn(f'<link rel="canonical" href="{url}">',text)

    def test_dataset_distributions_exist_and_preserve_states(self):
        g=build.dataset_graph(self.data,build.BOARD)
        datasets=[n for n in g['@graph'] if n['@type']=='Dataset']
        self.assertEqual(len(datasets),2)
        for d in datasets:
            self.assertIn('unqualified' if 'historical' in d['@id'] else 'not independently validated',d['creativeWorkStatus'])
            self.assertNotIn('license',d)  # No invented blanket licence over model responses.
            for download in d['distribution']:
                relative=download['contentUrl'].removeprefix(build.SITE)
                self.assertTrue((ROOT/'web'/relative).is_file(),relative)
        internal=datasets[0]
        self.assertIn('54 assigned requests',internal['description'])
        self.assertIn('53 complete responses',internal['description'])
        self.assertIn('one contested label',internal['description'])

if __name__=='__main__':unittest.main()
