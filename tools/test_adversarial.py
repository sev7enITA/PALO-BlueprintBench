import copy,hashlib,json,unittest
from unittest.mock import patch
import build_adversarial as b
class AdversarialTests(unittest.TestCase):
 def setUp(self):self.d=b.build()
 def test_fixed_denominators(self):
  s=self.d['summary'];self.assertEqual(s['assigned_review_records'],108);self.assertEqual(s['items'],36)
  self.assertEqual(sum(s[x] for x in ['unanimous','divergent','uncertain','incomplete']),36)
  self.assertEqual(s['valid_review_records']+s['missing_review_records'],108)
  for x in self.d['pairwise']:self.assertEqual(x['agree']+x['differ']+x['uncertain']+x['missing'],36)
  for x in self.d['label_comparison']:self.assertEqual(sum(x[k] for k in ['agree','differ','uncertain','missing']),18)
 def test_primary_data_and_labels_preserved(self):
  self.assertFalse(self.d['qualified']);self.assertTrue(self.d['primary_scores_unchanged'])
  self.assertEqual(b.sha(b.ROOT/'web/downloads/blueprintbench/leaderboard-data.json'),self.d['data_source_sha256'])
 def test_projection_is_not_strict_compliance(self):
  q=next(r for r in self.d['reviewers'] if r['id']=='qwen');self.assertEqual(q['valid'],36);self.assertEqual(q['strict_envelope_valid_batches'],0)
  self.assertEqual(self.d['summary']['projected_review_records'],36)
  for x in self.d['items']:self.assertEqual(x['reviewers']['qwen']['projection'],'array_to_items_object')
 def test_replay_retains_all_models_and_missing(self):
  self.assertEqual(len(self.d['model_replay']),18)
  for m in self.d['model_replay']:
   self.assertEqual(m['assigned'],54)
   for j in m['reviewers'].values():self.assertEqual(sum(j[k] for k in ['matches','disagreements','missing_predictions','missing_reviews','uncertain_reviews']),54)
  m=next(m for m in self.d['model_replay'] if m['model']=='sakana/fugu-max');self.assertEqual(m['recorded_predictions'],0)
 def test_frozen_input_tampering_rejected(self):
  original=b.sha
  with patch.object(b,'sha',side_effect=lambda p:'tampered' if p.name=='items.json' else original(p)):
   with self.assertRaisesRegex(AssertionError,'Frozen input drift'):b.build()
 def test_response_tampering_rejected(self):
  original=b.sha
  with patch.object(b,'sha',side_effect=lambda p:'tampered' if p.name=='purchase-approval-raw.txt' else original(p)):
   with self.assertRaisesRegex(AssertionError,'Response hash mismatch'):b.build()
 def test_empty_citations_exposed(self):
  missing=sum(j.get('citation_missing',False) for i in self.d['items'] for j in i['reviewers'].values());self.assertGreater(missing,0);self.assertEqual(missing,self.d['summary']['citation_missing_records'])
 def test_capacity_block_and_partial_disagreements(self):
  self.assertEqual(self.d['summary']['valid_review_records'],96)
  self.assertEqual(self.d['summary']['items_with_observed_disagreement'],3)
  disputed=[x for x in self.d['items'] if x['observed_pairwise_disagreement']]
  self.assertEqual({x['id'] for x in disputed},{'V-purchase-approval-P013','T08','T18'})
  for x in self.d['items']:
   if x['case']=='invoice-matching':
    self.assertEqual(x['reviewers']['glm']['status'],'missing')
    self.assertEqual(x['reviewers']['glm']['failure_status'],'provider_capacity_blocked')
 def test_blinded_prompts(self):
  for p in b.BASE.glob('*-prompt.txt'):
   s=p.read_text();self.assertNotIn('author_model',s);self.assertNotIn('original_draft_label',s)
if __name__=='__main__':unittest.main()
