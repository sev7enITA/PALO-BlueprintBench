"""Regression gates for cohort separation and truthful published JSON-LD."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest
import tempfile
from unittest.mock import patch
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
        self.assertGreaterEqual(len(self.data['internal']['models']),15)
        self.assertEqual(len({m['id'] for m in self.data['internal']['models']}),len(self.data['internal']['models']))
        self.assertEqual(len(self.data['internal']['campaigns']),3)
        self.assertEqual(len(self.data['historical']['models']),10)
        self.assertNotIn('models',self.data)
        self.assertTrue(all(m['rank'] is None for m in self.data['historical']['models']))

    def test_original_denominators_and_unknown_charges(self):
        d=self.data['internal'];r=[r for r in d['records'] if r['campaign_id']=='internal-frontier-2026-11-11']
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
        examples=[e for e in self.data['internal']['translation_examples'] if e['campaign_id']=='internal-frontier-2026-11-11']
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
        self.assertIn(str(self.data['internal']['assigned_calls'])+' assigned requests',internal['description'])
        self.assertIn(str(self.data['internal']['completed_calls'])+' complete responses',internal['description'])
        self.assertIn('one contested label',internal['description'])


    def test_exact_historical_model_identities_are_retained(self):
        current={m['id'] for m in self.data['internal']['models']}
        historical={m['model'] for m in self.data['historical']['models']}
        self.assertTrue(historical <= current, historical-current)
        self.assertIn('prism-ml/ternary-bonsai-2-9b', current)
        self.assertIn('prism-ml/ternary-bonsai-2-27b', current)
        self.assertIn('inference-net/schematron-v2-small', current)
        self.assertIn('inference-net/schematron-v2-turbo', current)

    def test_new_translations_are_source_bound_unreviewed_drafts(self):
        data=self.data['internal']
        for item in data['translation_examples']:
            if item['campaign_id']=='internal-frontier-2026-11-11':continue
            self.assertEqual(item['review_status'],'unreviewed_draft')
            folder=ROOT/'internal_tests'/('2026-11-11-legacy-extension' if 'legacy' in item['campaign_id'] else '2026-11-11-expansion')
            text=(folder/item['evidence_path']).read_bytes().decode('utf-8')
            self.assertIn(item['proposed_specification'],text)
            source=next(c for c in json.loads((folder/'corpus.json').read_text(encoding='utf-8')) if c['id']==item['case'])
            match=next((r['text'] for r in source['source'] if r['id']==item['source_id']),None)
            self.assertEqual(match,item['source_text'])
            self.assertEqual(item['verbatim'],match==item['proposed_specification'])
        for item in data['translations']:
            if item.get('campaign_id')!='internal-frontier-2026-11-11' and item['model'] not in {'openai/gpt-6.1-sol','anthropic/claude-opus-5.5','google/gemini-4-argon'}:
                self.assertEqual(item['internally_reviewed_lines'],0)
                self.assertFalse(item['business_approved'])

    def test_fixed_assignments_and_pre_call_gate(self):
        d=self.data['internal']
        self.assertEqual(d['assigned_calls'],18*len(d['models']))
        self.assertEqual(sum(m['assigned_calls'] for m in d['models']),d['assigned_calls'])
        for m in d['models']:
            self.assertEqual(m['verification_assigned_probes'],324)
            self.assertEqual(m['verification_classified']+m['verification_missing'],324)
        cfg=next(m for m in d['configurations'] if m['id']=='sakana/fugu-max')
        self.assertTrue(cfg['precall_blocked'])
        for r in d['records']:
            if r['state']=='not_run':
                self.assertEqual(r['cost_status'],'not_incurred')
                self.assertTrue(r['cost_zero_reason'])
                self.assertNotIn('provider_request_id',r)
                self.assertNotIn('output_sha256',r)

    def test_extension_inputs_match_original_and_are_frozen(self):
        original=ROOT/'internal_tests/2026-11-11-frontier'
        for name in ['2026-11-11-expansion','2026-11-11-legacy-extension']:
            folder=ROOT/'internal_tests'/name
            manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
            for relative,expected in manifest['files'].items():
                self.assertEqual(hashlib.sha256((folder/relative).read_bytes()).hexdigest(),expected)
            for relative in ['corpus.json','verification.schema.json']+[p.relative_to(original).as_posix() for p in (original/'prompts').glob('*.json')]:
                self.assertEqual((original/relative).read_bytes(),(folder/relative).read_bytes())
            self.assertEqual(manifest['overall_authorised_limit_usd'],40)

    def test_blocked_endpoint_never_dispatches_a_request(self):
        folder=ROOT/'internal_tests/2026-11-11-legacy-extension'
        spec=importlib.util.spec_from_file_location('legacy_runner',folder/'runner.py')
        runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        planned=runner.plan()
        self.assertEqual(len(planned),54)
        item=next(x for x in planned if x[1]['id']=='sakana/fugu-max')
        self.assertEqual(item[-1],0)
        with tempfile.TemporaryDirectory() as directory:
            runner.ROOT=Path(directory)
            with patch.object(runner.urllib.request,'urlopen',side_effect=AssertionError('Network call forbidden')):
                record=runner.call(item,'not-a-real-key',Path(directory)/'private')
            self.assertEqual(record['state'],'not_run')
            self.assertEqual(record['cost_usd'],0)
            self.assertEqual(record['cost_status'],'not_incurred')
            self.assertNotIn('provider_request_id',record)

    def test_public_identity_and_private_presentation(self):
        graph=build.dataset_graph(self.data,build.BOARD)
        images=[n for n in graph['@graph'] if n['@type']=='ImageObject']
        self.assertEqual(len(images),3)
        for image in images:
            self.assertTrue((ROOT/'web'/image['contentUrl'].removeprefix(build.SITE)).is_file())
        for filename in ['PALO_BlueprintBench.html','PALO_BlueprintBench_Leaderboard.html']:
            page=(ROOT/'web'/filename).read_text(encoding='utf-8')
            self.assertNotRegex(page,r'href="[^"\n]*downloads/blueprintbench/presentation/')
            self.assertNotRegex(page,r'href="(?:https://paloframework.org/)?downloads/blueprintbench/[^"\n]*\.md"')
        self.assertNotIn('presentation/',json.dumps(graph))
        rules=(ROOT/'web/downloads/blueprintbench/.htaccess').read_text(encoding='utf-8')
        self.assertIn('presentation(?:/.*)?$ - [G,L]',rules)
        self.assertIn(re.escape('internal-cohort-report.md')+'$',rules)
        self.assertIn('github.com/sev7enITA/PALO-BlueprintBench/blob/',rules)

    def test_archive_drift_is_detectable_without_silent_repair(self):
        archive=ROOT/'web/downloads/blueprintbench/internal-expansion-evidence.zip'
        original=archive.read_bytes()
        try:
            archive.write_bytes(b'corrupted archive fixture')
            expected=build.outputs()
            self.assertEqual(archive.read_bytes(),b'corrupted archive fixture')
            self.assertEqual(expected[archive],original)
        finally:
            archive.write_bytes(original)

if __name__=='__main__':unittest.main()
