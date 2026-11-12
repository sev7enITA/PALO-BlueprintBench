"""Integrity and disclosure checks for the local reviewer observations."""
import hashlib,importlib.util,json,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'internal_tests/2026-11-12-local-agent'
PUBLIC=ROOT/'web/downloads/blueprintbench/local-agent-diagnostics.json'
class LocalAgentDiagnosticsTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records=json.loads((EVIDENCE/'records.json').read_text(encoding='utf-8'))
  cls.data=json.loads(PUBLIC.read_text(encoding='utf-8'))
 def test_qualification_and_hardware_are_explicit(self):
  self.assertFalse(self.records['qualification'])
  self.assertEqual(self.data['status'],'internal_development')
  for run in self.data['runs']:
   self.assertTrue('Apple M3 Max' in run['hardware'] or ('i7-12850HX' in run['hardware'] and 'RTX A5500' in run['hardware']))
   self.assertIn('not independently adjudicated',run['reference'])
 def test_count_and_failure_accounting(self):
  for run in self.data['runs']:
   for row in run['cases']:
    self.assertLessEqual(row['contract_valid'],row['completed'])
    self.assertLessEqual(row['completed'],row['assigned'])
    if not row['contract_valid']:self.assertIsNone(row['agreement_count'])
 def test_captured_bytes_and_public_scope(self):
  private=re.compile(rb'(?:127\.0\.0\.1|192\.168\.\d+\.\d+|10\.29\.\d+\.\d+|/Users/[^/\s]+/|clientPasskey|sk-or-v1-)',re.I)
  for run in self.records['runs']:
   for row in run['observations']:
    for name in ('request','response'):
     item=row.get(name)
     if item:
      path=(EVIDENCE/item['path']).resolve();self.assertTrue(path.is_relative_to(EVIDENCE.resolve()))
      raw=path.read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),item['sha256']);self.assertIsNone(private.search(raw))
 def test_contract_valid_responses_replay(self):
  spec=importlib.util.spec_from_file_location('palo_validation_agent',ROOT/'validation_agent/agent.py')
  agent=importlib.util.module_from_spec(spec);spec.loader.exec_module(agent)
  checked=0
  for run in self.records['runs']:
   for row in run['observations']:
    if row['status'] not in ('advisory_contract_valid','posthoc_contract_valid'):continue
    req=json.loads((EVIDENCE/row['request']['path']).read_text(encoding='utf-8'))
    env=json.loads((EVIDENCE/row['response']['path']).read_text(encoding='utf-8'))
    self.assertEqual(env['choices'][0]['finish_reason'],'stop')
    item=json.loads(req['messages'][1]['content'].rsplit('\n/',1)[0])
    content=env['choices'][0]['message']['content']
    if row['status']=='posthoc_contract_valid':
     obj=json.loads(content)
     if 'review_item' in obj:
      self.assertEqual(obj['review_item'],row['case_id']);del obj['review_item']
     aliases={'Entailed':'supported','Contradicted':'contradicted'}
     obj['label']=aliases.get(obj['label'],obj['label'])
     for claim in obj.get('propositions',[]):claim['label']=aliases.get(claim['label'],claim['label'])
     content=json.dumps(obj,ensure_ascii=False)
    result=agent.validate_output(content,item)
    self.assertEqual(result['label'],row['label']);checked+=1
  self.assertGreaterEqual(checked,17)
 def test_unassessed_raw_gemma_remains_unassessed(self):
  spec=importlib.util.spec_from_file_location('palo_validation_agent_raw',ROOT/'validation_agent/agent.py')
  agent=importlib.util.module_from_spec(spec);spec.loader.exec_module(agent)
  run=next(r for r in self.records['runs'] if r['id']=='gemma-e4b-raw-intel-a5500')
  for row in run['observations']:
   self.assertEqual(row['status'],'unassessed')
   req=json.loads((EVIDENCE/row['request']['path']).read_text(encoding='utf-8'))
   env=json.loads((EVIDENCE/row['response']['path']).read_text(encoding='utf-8'))
   item=json.loads(req['messages'][1]['content'].rsplit('\n/',1)[0])
   with self.assertRaises((ValueError,TypeError,KeyError,IndexError)):
    agent.validate_output(env['choices'][0]['message']['content'],item)
 def test_timeout_is_not_semantic_error(self):
  her=next(r for r in self.records['runs'] if r['id']=='qwen-heretic-mtp-intel-a5500')
  b=next(r for r in her['observations'] if r['case_id']=='ITEM-B')
  self.assertEqual(b['status'],'stopped');self.assertIsNone(b['response']);self.assertGreaterEqual(b['elapsed_seconds'],599)
  row=next(r for r in self.data['runs'] if r['id']==her['id'])
  b=next(x for x in row['cases'] if x['case_id']=='ITEM-B')
  self.assertEqual((b['assigned'],b['completed'],b['contract_valid']),(1,0,0));self.assertIsNone(b['agreement_count'])
  self.assertEqual((b['timeout_count'],b['timeout_seconds']),(1,600))
 def test_posthoc_is_not_new_inference(self):
  run=next(r for r in self.data['runs'] if r['id']=='gemma-e4b-posthoc-intel-a5500')
  self.assertIn('no new model call',run['suite'])
  self.assertIs(run['is_replay'],True)
  self.assertTrue(all(isinstance(x['is_replay'],bool) for x in self.data['runs']))
  self.assertEqual(sum(x['is_replay'] is True for x in self.data['runs']),1)
  self.assertTrue(all(x['median_seconds'] is None for x in run['cases']))
  self.assertTrue(all(x['median_completion_tokens'] is None for x in run['cases']))
if __name__=='__main__':unittest.main()
