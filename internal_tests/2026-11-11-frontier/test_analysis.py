import json
import tempfile
import unittest
from pathlib import Path
from analyse import assessment, load, translation_claims, ROOT

class InternalScoringTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)
        self.case = load(ROOT/'corpus.json')[0]
        self.schema = load(ROOT/'verification.schema.json')
        self.items = [{'id':p['id'],'verdict':p['expected']} for p in self.case['probes']]

    def tearDown(self):
        self.tmp.cleanup()

    def score(self, state='completed'):
        (self.path/'output.txt').write_text(json.dumps({'judgments':self.items}),encoding='utf-8')
        return assessment({'state':state},self.path,self.case,self.schema)

    def test_exact_reference_labels(self):
        result=self.score()
        self.assertEqual((result['correct'],result['assigned_probes']),(36,36))
        self.assertTrue(result['contract_pass'])

    def test_missing_output_stays_in_denominator(self):
        result=self.score('fail')
        self.assertEqual((result['correct'],result['assigned_probes']),(0,36))
        self.assertEqual(len(result['missing']),36)

    def test_duplicate_not_counted_twice_or_cherry_picked(self):
        self.items.append({**self.items[0],'verdict':'contradicted'})
        result=self.score()
        self.assertEqual(result['classified'],35)
        self.assertEqual(result['duplicates'],[self.items[0]['id']])
        self.assertFalse(result['contract_pass'])

    def test_unknown_id_fails_contract(self):
        self.items.append({'id':'new','verdict':'supported'})
        result=self.score()
        self.assertEqual(result['correct'],36)
        self.assertEqual(result['unknown_ids'],['new'])
        self.assertFalse(result['contract_pass'])

    def test_invalid_label_is_not_scored(self):
        self.items[0]['verdict']='probably'
        result=self.score()
        self.assertEqual(result['classified'],0)
        self.assertTrue(result['schema_errors'])

    def test_crlf_and_preamble_preserved_as_claims(self):
        raw='Preamble\r\nR01 :: An obligation.\n'
        claims,ignored=translation_claims(raw)
        self.assertEqual(len(claims),2)
        self.assertIsNone(claims[0]['source_id'])
        spans=sorted([c['span'] for c in claims]+[s['span'] for s in ignored])
        self.assertEqual(spans[0][0],0)
        self.assertEqual(spans[-1][1],len(raw))
        self.assertTrue(all(a[1]==b[0] for a,b in zip(spans,spans[1:])))
        for c in claims:self.assertEqual(raw[slice(*c['span'])],c['text'])

    def test_gold_labels_absent_from_inference_messages(self):
        for p in (ROOT/'prompts').glob('verification-*.json'):
            payload=json.loads(load(p)[1]['content'])
            self.assertTrue(all(set(c)=={'id','text'} for c in payload['candidates']))
            self.assertEqual(len(payload['candidates']),36)

if __name__=='__main__':unittest.main()
