"""Publication invariants for specification generation; no inference or rewrites."""
import hashlib
import json
from pathlib import Path
import re
import unittest
import zipfile
import build_generation
import build_site_architecture

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'
DL=WEB/'downloads/blueprintbench'


class GenerationPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((DL/'generation-results.json').read_text(encoding='utf-8'))
        cls.page=(WEB/'PALO_BlueprintBench_Generation.html').read_text(encoding='utf-8')

    def test_upstream_failure_overlay_does_not_change_assessment(self):
        import copy
        study=ROOT/'internal_tests/2026-11-11-real-procurement'
        for identifier in ['far15-m2-r1','fta-m2-r1']:
            accounting=json.loads((study/'runs'/identifier/'get_generation.json').read_text(encoding='utf-8'))
            record=json.loads((study/'runs'/identifier/'record.json').read_text(encoding='utf-8'))
            row={'state':'incomplete','structural_valid':False,'missing_decisions':36,'cost_usd':0,'usage':record['usage']}
            before=copy.deepcopy(row)
            build_generation.capture_provenance(row,accounting)
            self.assertEqual(row['upstream_statuses'],[502])
            self.assertEqual(row['collection_failure'],'Upstream error 502; incomplete capture')
            self.assertFalse(row['native_usage_available'])
            self.assertIn('zero charge',row['cost_zero_reason'])
            for key,value in before.items():self.assertEqual(row[key],value)
        successful={'usage':{'native_prompt_tokens':0,'native_completion_tokens':0}}
        build_generation.capture_provenance(successful,{'data':{'total_cost':0,'provider_responses':[{'status':200}]}})
        self.assertIsNone(successful['collection_failure']);self.assertIsNone(successful['cost_zero_reason'])
        self.assertTrue(successful['native_usage_available'])
        unknown={'usage':None,'cost_usd':None,'cost_status':'unknown'}
        build_generation.capture_provenance(unknown,{'data':None})
        self.assertIsNone(unknown['cost_usd']);self.assertIsNone(unknown['cost_zero_reason'])
        self.assertFalse(unknown['native_usage_available'])
        timeout=json.loads((study/'runs/fema-m2-r1/mcp-response.json').read_text(encoding='utf-8'))
        build_generation.capture_provenance(unknown,{},timeout)
        self.assertEqual(unknown['collection_failure'],'MCP timeout; no complete capture')
        self.assertIsNone(unknown['cost_usd'])

    def test_three_studies_have_distinct_page_and_dataset_identities(self):
        scripts=re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',self.page,re.S)
        self.assertEqual(len(scripts),1)
        graph=json.loads(scripts[0])
        self.assertEqual(graph,build_generation.schema(self.data))
        page,dataset=graph['@graph']
        self.assertEqual(page['@type'],'WebPage');self.assertEqual(dataset['@type'],'Dataset')
        self.assertEqual(dataset['version'],self.data['assessment']['checker_revision'])
        self.assertEqual(dataset['identifier'],'real-procurement-generation-1.0.0')
        self.assertIn('Generation.html#dataset',dataset['@id'])
        self.assertNotIn('NextCycle.html',dataset['@id'])
        self.assertNotIn('Leaderboard.html',dataset['@id'])
        self.assertIn('independent validation pending',dataset['creativeWorkStatus'])
        encoded=json.dumps(graph)
        for key in ['aggregateRating','ratingValue','Review','Certification']:
            self.assertNotIn('"'+key+'"',encoded)
        self.assertEqual({p['source_url']for p in self.data['sources']},set(dataset['citation']))
        measured={v['propertyID']:v['value']for v in dataset['variableMeasured']}
        self.assertTrue(all(value==self.data['analysis']['summary'][key]for key,value in measured.items()))

    def test_correction_and_advisory_scopes_are_explicit(self):
        assessment=self.data['assessment']
        self.assertIn(assessment['analysis_path'],['analysis-corrected.json','analysis-combined.json'])
        self.assertEqual(assessment['checker_revision'],'quote-normalisation-v1.1')
        self.assertEqual(assessment['blueprints_directory'],'blueprints-corrected')
        self.assertIn('retaining the hyphen',self.page)
        self.assertIn('Original v1.0 analysis',self.page)
        self.assertIn('v1.0 replay on the same receipts',self.page)
        self.assertIn('corrections/correction-note.md',self.page)
        if self.data.get('advisory_review'):
            self.assertIn('FEMA draft-key review, first repetition.',self.page)
            self.assertIn('not an established model error',self.page)
            self.assertIn('review/post-output-disagreements-r1.md',self.page)
        for row in self.data['analysis']['rows']:
            if row['cost_status']=='unknown':
                self.assertIsNone(row['cost_usd'])
                self.assertIsNone(row['cost_zero_reason'])
        self.assertIn('Current unresolved-cost reserve', (WEB/'assets/blueprintbench/generation.js').read_text(encoding='utf-8'))

    def test_fixed_assignments_and_partial_results_stay_separate(self):
        a=self.data['analysis'];rows=a['rows'];s=a['summary']
        self.assertFalse(a['qualified']);self.assertEqual(a['independent_human_reviews'],0)
        expected=len(self.data['models'])*9
        self.assertEqual(len(rows),expected);self.assertEqual(s['assigned_calls'],expected)
        self.assertEqual(len({r['id']for r in rows}),expected)
        self.assertEqual(s['completed_calls'],sum(r['state']=='completed'for r in rows))
        for model in self.data['models']:
            own=[r for r in rows if r['configuration_id']==model['id']]
            self.assertEqual(len(own),9)
            self.assertEqual({r['repetition']for r in own},{1,2,3})
            self.assertEqual(len({r['task_id']for r in own}),3)
        for row in rows:
            self.assertFalse(row['qualified'])
            self.assertEqual(row['assigned_decisions'],sum(row[key]for key in ['matched_decisions','disagreed_decisions','missing_decisions','unassessed_decisions']))
            if row['state']=='not_run':
                self.assertEqual(row['cost_status'],'not_dispatched')
                if row['cost_usd']==0:self.assertTrue(row['cost_zero_reason'])
                else:self.assertIsNone(row['cost_usd'])
                self.assertEqual(row['matched_decisions'],0)
            if row['cost_status']=='unknown':self.assertIsNone(row['cost_usd'])
        self.assertAlmostEqual(s['known_cost_usd'],sum(r['cost_usd'] or 0 for r in rows))
        self.assertEqual(s['assigned_decisions'],396*len(self.data['models']))
        self.assertEqual(s['assigned_decisions'],sum(r['assigned_decisions']for r in rows))
        self.assertEqual(s['assigned_decisions'],sum(r['assigned_decisions']for r in a['by_model']))

    def test_provider_configurations_and_amendment_do_not_merge_models(self):
        models=self.data['models'];rows=self.data['analysis']['rows']
        self.assertEqual(len({m['id'] for m in models}),len(models))
        self.assertTrue(all(r['configuration_id'] in {m['id'] for m in models} for r in rows))
        if self.data.get('supplement_manifest'):
            self.assertEqual(len(models),4)
            self.assertEqual(self.data['analysis']['summary']['assigned_calls'],36)
            google=[m for m in models if m['model_id'].startswith('google/')]
            self.assertEqual(len(google),2);self.assertEqual(len({m['model_id'] for m in google}),1)
            self.assertEqual({m['provider_pin'] for m in google},{'google-vertex/us','google-ai-studio'})
            self.assertEqual({m['access_channel'] for m in google},{'OpenRouter MCP','OpenRouter MCP Batch API'})
            self.assertIn('original 27 assignments',self.page)
            self.assertIn('do not isolate a provider effect',self.page)
            self.assertEqual(len(self.data['analysis']['by_configuration']),4)

    def test_scope_and_provider_context_are_visible(self):
        self.assertEqual(len(self.data['sources']),3)
        self.assertEqual(sum(p['supplied_page_count']for p in self.data['sources']),200)
        for source in self.data['sources']:
            self.assertNotIn('pages',source)  # Source bytes remain in the separately downloadable archive.
            self.assertTrue(source['source_url'].startswith('https://'))
            self.assertEqual(len(source['pdf_sha256']),64)
        for model in self.data['models']:
            self.assertIn(model['access_channel'],['OpenRouter MCP','OpenRouter MCP Batch API'])
            self.assertEqual(model['execution_mode'],'Cloud API inference')
            self.assertTrue(model['provider_pin'])
            self.assertEqual(model['reasoning_effort'],'high')
            self.assertEqual(model['maximum_generated_tokens_including_reasoning'],32768)
            self.assertFalse(model['fallbacks'])
        self.assertIn(build_site_architecture.navigation('PALO_BlueprintBench_Generation.html'),self.page)
        self.assertIn(build_site_architecture.footer(),self.page)
        self.assertIn('Contract and citation checks passed',self.page)
        self.assertIn('<button id="export-csv" disabled>',self.page)
        self.assertIn('<button id="export-json" disabled>',self.page)
        self.assertIn('Native provider tokens input / output',self.page)
        self.assertIn('Reasoning and cache counters may overlap',self.page)
        self.assertIn('not interpreted as measured savings',self.page)
        self.assertIn('does not establish full semantic correctness',self.page)
        self.assertIn('original HTTP response bytes are unavailable',self.page)

    def test_blueprint_exports_remain_unapproved_and_source_bound(self):
        for row in self.data['analysis']['rows']:
            artifact=row.get('blueprint')
            if artifact is None:continue
            self.assertEqual(artifact['id'],row['id'])
            self.assertFalse(artifact['qualified']);self.assertFalse(artifact['business_approved'])
            self.assertTrue(artifact['business_approval_required'])
            self.assertEqual(artifact['output_sha256'],row['output_txt_sha256'])
            self.assertIn('not_independent_gold',artifact['assessment'])

    def test_archive_matches_the_published_snapshot(self):
        with zipfile.ZipFile(DL/'generation-evidence.zip') as archive:
            self.assertTrue(all('__pycache__'not in n and not n.endswith('.pyc')for n in archive.namelist()))
            frozen=json.loads(archive.read('manifest.json'))
            self.assertEqual(hashlib.sha256(archive.read('manifest.json')).hexdigest(),self.data['manifest_sha256'])
            source=json.loads(archive.read('source-packets.json'))
            self.assertEqual([{k:v for k,v in p.items()if k!='pages'}for p in source],self.data['sources'])
            analysis=json.loads(archive.read(self.data['assessment']['analysis_path']))
            self.assertEqual(analysis['summary'],self.data['analysis']['summary'])
            for row in self.data['analysis']['rows']:
                if row.get('raw_output') is not None:
                    output=archive.read(row['capture_output_path'])
                    self.assertEqual(output.decode('utf-8'),row['raw_output'])
                    record=json.loads(archive.read(row['capture_record_path']))
                    self.assertEqual(hashlib.sha256(output).hexdigest(),record['output_sha256'])
                elif row['state']=='not_run':self.assertIsNone(row.get('raw_output'))
                if row.get('blueprint'):
                    self.assertEqual(json.loads(archive.read(row['capture_blueprint_path'])),row['blueprint'])


if __name__=='__main__':unittest.main()
