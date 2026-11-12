"""Separate provider/transport configuration tests, entirely offline."""
from pathlib import Path
import importlib.util
import json
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('real_supplement',ROOT/'analyse-supplement.py')
supplement=importlib.util.module_from_spec(spec);spec.loader.exec_module(supplement)


def clone(root):
    correction=supplement.correction_module(ROOT)
    for name in correction.load(ROOT/'manifest.json')['files']:
        target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    shutil.copyfile(ROOT/'manifest.json',root/'manifest.json')
    shutil.copyfile(ROOT/'transport-amendment.json',root/'transport-amendment.json')
    (root/'corrections').mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'corrections/quote-normalisation-v1.1.py',root/'corrections/quote-normalisation-v1.1.py')
    for ident in ['fta-m0-r1',*correction.load(ROOT/'transport-amendment.json')['stopped_undispatched_assignments']]:
        shutil.copytree(ROOT/'runs'/ident,root/'runs'/ident)
    sub=ROOT/supplement.SUPPLEMENT
    for name in correction.load(sub/'manifest.json')['files']:
        target=root/supplement.SUPPLEMENT/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(sub/name,target)
    shutil.copyfile(sub/'manifest.json',root/supplement.SUPPLEMENT/'manifest.json')
    _,analyse=correction.modules(root);correction.write(root/'analysis.json',analyse.run(root));correction.run(root)
    return correction


class SupplementTests(unittest.TestCase):
    def test_two_google_providers_remain_distinct_and_denominators_fixed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);clone(root);report=supplement.run(root)
            self.assertEqual(36,report['summary']['assigned_calls'])
            self.assertEqual(432,report['summary']['assigned_scenarios'])
            self.assertEqual(1584,report['summary']['assigned_decisions'])
            self.assertEqual(4,len(report['by_configuration']))
            self.assertTrue(all(r['assigned_calls']==9 for r in report['by_configuration']))
            google=[r for r in report['by_configuration'] if r['model']=='google/gemini-4-argon']
            self.assertEqual({'google-vertex/us','google-ai-studio'},{r['provider'] for r in google})
            self.assertEqual(5,report['summary']['administratively_stopped_calls'])
            stopped=[r for r in report['rows'] if r.get('stop_reason')]
            self.assertTrue(all(r['cost_usd']==0 and r['cost_status']=='not_dispatched' and r['cost_zero_reason'] for r in stopped))
            pending=[r for r in report['rows'] if r['cohort']=='transport_supplement']
            self.assertTrue(all(r['cost_usd'] is None and r['elapsed_seconds'] is None for r in pending))
            self.assertTrue(all(r['access_channel']=='OpenRouter MCP Batch API' for r in pending))

    def test_batch_duration_cannot_be_serial_request_latency(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);correction=clone(root);sub=root/supplement.SUPPLEMENT
            assignment=correction.load(sub/'schedule.json')[0];folder=sub/'runs'/assignment['id'];folder.mkdir(parents=True)
            correction.write(folder/'record.json',{**assignment,'state':'fail','cost_usd':None,'cost_status':'unknown','elapsed_seconds':400})
            with self.assertRaisesRegex(ValueError,'Batch elapsed_seconds must be null'):supplement.run(root)

    def test_supplement_prompt_mutation_fails_freeze(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);correction=clone(root);sub=root/supplement.SUPPLEMENT
            path=sub/correction.load(sub/'schedule.json')[0]['request_path']
            path.write_text(path.read_text(encoding='utf-8')+' ',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'Frozen supplement input changed'):supplement.run(root)


if __name__=='__main__':unittest.main()
