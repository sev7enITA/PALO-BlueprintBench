"""Regression and adversarial tests for the narrow v1.1 quote correction."""
from pathlib import Path
import importlib.util
import json
import shutil
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
spec=importlib.util.spec_from_file_location('quote_v11_correction',HERE/'quote-normalisation-v1.1.py')
correction=importlib.util.module_from_spec(spec);spec.loader.exec_module(correction)


class QuoteCorrectionTests(unittest.TestCase):
    def test_retains_hyphen_and_joins_exactly_one_line_ending(self):
        for newline in ('\n','\r\n','\r'):
            self.assertEqual('micro-purchase',correction.normalized_v11('micro- \t'+newline+' \tpurchase'))
        self.assertEqual('Anti-Kickback',correction.normalized_v11('Anti-\n   Kickback'))
        self.assertNotEqual('micropurchase',correction.normalized_v11('micro-\npurchase'))

    def test_does_not_expand_to_other_typography(self):
        for source in ('micro- purchase','micro-\n\npurchase','micro-\n \npurchase','micro‐\npurchase','micro–\npurchase'):
            self.assertNotEqual('micro-purchase',correction.normalized_v11(source))
        self.assertNotEqual('café-purchase',correction.normalized_v11('café-\npurchase'))
        self.assertNotEqual('micro-élan',correction.normalized_v11('micro-\nélan'))

    def test_changed_modality_word_and_missing_word_still_rejected(self):
        source=correction.normalized_v11('The recipient may use a micro-\n purchase with approval.')
        self.assertIn(correction.normalized_v11('The recipient may use a micro-purchase with approval.'),source)
        for bad in ('The recipient must use a micro-purchase with approval.',
            'The recipient may use a macro-purchase with approval.',
            'The recipient may use a micro-purchase approval.',
            'THE RECIPIENT MAY USE A MICRO-PURCHASE WITH APPROVAL.'):
            self.assertNotIn(correction.normalized_v11(bad),source)

    def test_actual_fta_r25_and_fema_r18_are_same_narrow_case(self):
        packets={p['id']:{x['page']:x['text'] for x in p['pages']} for p in correction.load(ROOT/'source-packets.json')}
        contracts,_=correction.modules(ROOT)
        for ident,index in (('fta-m0-r1',24),('fema-m0-r1',17)):
            output=ROOT/'runs'/ident/'output.txt'
            if not output.exists():self.skipTest('Actual response not available')
            document=ident.split('-')[0];data=correction.load(output);item=data['requirements'][index]
            source=packets[document][item['source_pages'][0]]
            self.assertNotIn(contracts.normalized(item['quote']),contracts.normalized(source))
            self.assertIn(correction.normalized_v11(item['quote']),correction.normalized_v11(source))
        item=correction.load(ROOT/'runs/fta-m0-r1/output.txt')['requirements'][24]
        source=correction.normalized_v11(packets['fta'][74])
        for bad in (item['quote'].replace('micro-purchase','macro-purchase'),
            item['quote'].replace('does not permit','does permit'),
            item['quote'].replace('Federal threshold','Federal')):
            self.assertNotIn(correction.normalized_v11(bad),source)

    def test_isolated_replay_preserves_frozen_files_raw_outputs_and_originals(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            names=['contracts.py','analyse.py','design/task-design.json','design/assessment-key.json','source-packets.json','schedule.json']
            for name in names:
                dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
            record_id='fta-m0-r1'
            shutil.copytree(ROOT/'runs'/record_id,root/'runs'/record_id)
            (root/'blueprints').mkdir();(root/'blueprints/original.json').write_text('{"original":true}',encoding='utf-8')
            (root/'analysis.json').write_text('{"original":true}',encoding='utf-8')
            manifest={'files':{name:correction.sha(root/name) for name in names}}
            (root/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
            before={name:correction.sha(root/name) for name in names+['manifest.json','analysis.json','blueprints/original.json','runs/'+record_id+'/output.txt']}
            note=correction.run(root)
            self.assertEqual(before,{name:correction.sha(root/name) for name in before})
            self.assertEqual(1,note['comparison_scope']['recorded_snapshot_calls'])
            self.assertEqual(27,note['comparison_scope']['assigned_calls'])
            self.assertEqual([record_id],[r['id'] for r in note['affected_rows']])
            self.assertEqual(1,note['summary_after']['structurally_valid_calls'])
            self.assertEqual(0,note['summary_before']['structurally_valid_calls'])
            export=correction.load(root/'blueprints-corrected'/f'{record_id}.json')
            self.assertFalse(export['qualified']);self.assertTrue(export['business_approval_required'])
            self.assertEqual(correction.sha(root/'runs'/record_id/'output.txt'),export['output_sha256'])
            repeated=correction.run(root)
            self.assertEqual(note['first_documented_at'],repeated['first_documented_at'])
            self.assertEqual(note['summary_after'],repeated['summary_after'])


if __name__=='__main__':unittest.main()
