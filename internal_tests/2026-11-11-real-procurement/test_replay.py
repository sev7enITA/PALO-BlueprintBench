"""Offline replay boundary regressions; no inference or accounting API calls."""
from pathlib import Path
import copy
import json
import shutil
import tempfile
import unittest
import replay

ROOT=Path(__file__).resolve().parent


def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data),encoding='utf-8')


class ReplayTests(unittest.TestCase):
    def test_actual_frozen_manifest_intact(self):
        manifest=replay.load(ROOT/'manifest.json')
        for name,expected in manifest['files'].items():self.assertEqual(expected,replay.sha(ROOT/name),name)

    def test_timestamp_tolerance_does_not_hide_results_changes(self):
        one={'updated_at':'a','first_documented_at':'b','summary_after':{'matched_decisions':5}}
        two=copy.deepcopy(one);two['updated_at']='c';two['first_documented_at']='d'
        self.assertEqual(replay.semantic_note(one),replay.semantic_note(two))
        two['summary_after']['matched_decisions']=6
        self.assertNotEqual(replay.semantic_note(one),replay.semantic_note(two))

    def test_stale_record_count_fails_with_explicit_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);write(root/'analysis.json',{'summary':{'recorded_calls':3}})
            with self.assertRaisesRegex(ValueError,'STALE analysis.json: recorded_calls=3, actual_receipts=4'):
                replay.check_staleness(root,[{}]*4)

    def test_footer_only_extraction_is_exact(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            footer='\n\n(model: fixture/model, generation id: gen-fixture, input tokens: 3, output tokens: 2, reasoning tokens: 1)'
            write(folder/'mcp-response.json',{'content':[{'type':'text','text':'{}'+footer}]})
            (folder/'output.txt').write_text('{}',encoding='utf-8');(folder/'mcp-accounting-footer.txt').write_bytes(footer.encode('utf-8'))
            record={'model':'fixture/model','provider_request_id':'gen-fixture','output_sha256':replay.sha(folder/'output.txt'),'mcp_response_sha256':replay.sha(folder/'mcp-response.json')}
            replay.verify_footer(folder,record)
            (folder/'output.txt').write_text('{ }',encoding='utf-8');record['output_sha256']=replay.sha(folder/'output.txt')
            with self.assertRaisesRegex(ValueError,'altered more than terminal footer'):replay.verify_footer(folder,record)
            (folder/'output.txt').write_text('{}',encoding='utf-8');record['output_sha256']=replay.sha(folder/'output.txt')
            (folder/'mcp-accounting-footer.txt').write_text('unbounded removed answer text',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'Unrecognized terminal'):replay.verify_footer(folder,record)

    def test_unknown_reserve_cannot_be_omitted(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);manifest={'cumulative_ceiling_usd':40,'new_study_ceiling_usd':17,'previous_unknown_cost_reserve_usd':.5}
            records=[{'cost_status':'provider_reported','cost_usd':1},{'cost_status':'unknown','cost_usd':None,'reserved_usd':2}]
            budget={'known_campaign_cost_usd':1,'current_unknown_cost_reserve_usd':2,'account_usage_before_usd':20,
                'account_usage_after_usd':20.5,'previous_unknown_cost_reserve_usd':.5,'conservative_cumulative_committed_usd':23.5}
            write(root/'budget-final.json',budget);self.assertEqual(23.5,replay.verify_budget(root,manifest,records)['conservative_bound_usd'])
            budget['current_unknown_cost_reserve_usd']=0;write(root/'budget-final.json',budget)
            with self.assertRaisesRegex(ValueError,'Unknown reservations omitted'):replay.verify_budget(root,manifest,records)

    def test_real_administrative_stops_and_accounting_reconciliation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);manifest=replay.load(ROOT/'manifest.json')
            for name in manifest['files']:
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
            shutil.copyfile(ROOT/'manifest.json',root/'manifest.json')
            shutil.copyfile(ROOT/'transport-amendment.json',root/'transport-amendment.json')
            ids=['fema-m2-r1','far15-m2-r2',*replay.load(ROOT/'transport-amendment.json')['stopped_undispatched_assignments']]
            for ident in ids:shutil.copytree(ROOT/'runs'/ident,root/'runs'/ident)
            records=replay.verify_records(root,manifest)
            self.assertEqual(5,sum(r['state']=='not_run' for r in records))
            self.assertEqual(2,sum(r['cost_status']=='provider_reported_reconciled' for r in records))
            stopped=root/'runs'/ids[-1]/'record.json';value=replay.load(stopped);value['cost_zero_reason']='';write(stopped,value)
            with self.assertRaisesRegex(ValueError,'lacks reason/time'):replay.verify_records(root,manifest)

    def test_offline_export_uses_isolated_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            parent=Path(directory);root=parent/'archive';root.mkdir()
            manifest=replay.load(ROOT/'manifest.json')
            for name in manifest['files']:
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
            shutil.copyfile(ROOT/'manifest.json',root/'manifest.json')
            (root/'corrections').mkdir(exist_ok=True)
            shutil.copyfile(ROOT/'corrections/quote-normalisation-v1.1.py',root/'corrections/quote-normalisation-v1.1.py')
            shutil.copytree(ROOT/'runs/fta-m0-r1',root/'runs/fta-m0-r1')
            before=replay.sha(root/'runs/fta-m0-r1/output.txt')
            result=replay.replay(root,output=parent/'replayed')
            self.assertEqual(0,result['paid_calls']);self.assertEqual(1,result['recorded_calls'])
            self.assertEqual(before,replay.sha(root/'runs/fta-m0-r1/output.txt'))
            self.assertFalse((root/'analysis.json').exists())
            self.assertTrue((parent/'replayed/analysis-corrected.json').exists())


if __name__=='__main__':unittest.main()
