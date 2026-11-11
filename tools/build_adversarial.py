"""Build a separate internal adversarial-review view without changing primary scores."""
from pathlib import Path
import json,hashlib,itertools,datetime,re,argparse
ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'internal_tests/2026-11-11-adversarial'
REV='80df7db';EVIDENCE_REV='4494d6b';GIT='https://github.com/sev7enITA/PALO-BlueprintBench/blob/'+REV+'/internal_tests/2026-11-11-adversarial/'
REVIEWERS=[{'id':'glm','label':'GLM 5.3 MAX','actual_model':'GLM-5.3','interface':'Z.ai web','setting':'Effort Max','family_prefix':'z-ai/'},{'id':'gemini','label':'Gemini 4 Argon High','actual_model':'Gemini 4 Argon','interface':'Gemini web','setting':'High','family_prefix':'google/'},{'id':'qwen','label':'Qwen local','actual_model':'qwen3.8-27b-uncensored','interface':'LM Studio','setting':'Q6_K; temperature 0; 8,192-token loaded context','family_prefix':'qwen/'}]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
 for name,digest in read(BASE/'manifest.json')['files'].items():
  assert sha(BASE/name)==digest, 'Frozen input drift: '+name
 protocol=read(BASE/'protocol.json');items=read(BASE/'items.json');selection={x['id']:x for x in read(BASE/'selection.json')};corpus={x['id']:x['source'] for x in read(BASE/'corpus.json')};main=read(ROOT/'web/downloads/blueprintbench/leaderboard-data.json')['internal'];reviewers=[dict(x) for x in REVIEWERS];results={};diagnostics=[]
 assert sha(ROOT/'web/downloads/blueprintbench/leaderboard-data.json')==protocol['data_sha256'], 'Primary cohort changed'
 response_base='https://github.com/sev7enITA/PALO-BlueprintBench/blob/'+EVIDENCE_REV+'/internal_tests/2026-11-11-adversarial/'
 for reviewer in reviewers:
  received={};cases=[]
  for case in corpus:
   path=BASE/'responses'/reviewer['id']/(case+'-parsed.json');expected={i['id']:i for i in items if i['case']==case};valid_ids={s['id'] for s in corpus[case]};status='pending';invalid=[]
   receipt_path=path.with_name(case+'-receipt.json')
   if receipt_path.exists() and not path.exists():
    failure=read(receipt_path);assert failure['prompt_sha256']==sha(BASE/(case+'-prompt.txt'));status=failure.get('status','missing')
   if path.exists():
    raw=read(path);receipt=read(path.with_name(case+'-receipt.json'));rawpath=BASE/receipt['raw_text_path'] if 'raw_text_path' in receipt else path.with_name(case+'-raw.txt')
    assert sha(rawpath)==receipt['raw_text_sha256'], 'Response hash mismatch'
    assert json.loads(rawpath.read_text(encoding='utf-8'))==raw, 'Parsed response differs from original'
    assert receipt['prompt_sha256']==sha(BASE/(case+'-prompt.txt')), 'Prompt hash mismatch'
    if 'parsed_sha256' in receipt:assert sha(path)==receipt['parsed_sha256'], 'Parsed hash mismatch'
    rows=raw.get('items',[]) if isinstance(raw,dict) else raw if isinstance(raw,list) else [];counts={rid:sum(x.get('id')==rid for x in rows if isinstance(x,dict)) for rid in expected};status='received'
    for row in rows:
     if not isinstance(row,dict):invalid.append('non_object');continue
     uid=row.get('id');item=expected.get(uid)
     if not item:invalid.append('unknown_id');continue
     allowed={'supported','contradicted','not_established','uncertain'} if item['task']=='verification' else {'faithful','altered','uncertain'}
     ok=counts[uid]==1 and row.get('relation') in allowed and isinstance(row.get('reason'),str) and isinstance(row.get('source_ids'),list) and set(row['source_ids'])<=valid_ids
     if not ok:invalid.append(uid);continue
     received[uid]={'status':'valid','relation':row['relation'],'reason':row['reason'],'source_ids':row['source_ids'],'citation_missing':not row['source_ids'],'projection':'array_to_items_object' if isinstance(raw,list) else None,'evidence_url':response_base+rawpath.relative_to(BASE).as_posix(),'receipt_url':response_base+path.with_name(case+'-receipt.json').relative_to(BASE).as_posix()}
   cases.append({'case':case,'status':status,'assigned':len(expected),'valid':sum(uid in received for uid in expected),'invalid':invalid,'strict_envelope_valid':bool(path.exists() and isinstance(raw,dict) and set(raw)=={'items'}),'projection':'array_to_items_object' if path.exists() and isinstance(raw,list) else None})
  reviewer.update({'assigned':len(items),'valid':len(received),'missing':len(items)-len(received),'cases':cases,'strict_envelope_valid_batches':sum(c['strict_envelope_valid'] for c in cases),'expected_batches':len(cases)});results[reviewer['id']]=received
 enriched=[]
 for item in items:
  s=selection[item['id']];judgments={r['id']:results[r['id']].get(item['id'],{'status':'missing','relation':None,'reason':'No valid recorded review.' ,'source_ids':[]}) for r in reviewers};rels=[j['relation'] for j in judgments.values() if j['status']=='valid']
  status='incomplete' if len(rels)!=len(reviewers) else 'uncertain' if 'uncertain' in rels else 'unanimous' if len(set(rels))==1 else 'divergent'
  for r in reviewers:
   caseinfo=next(c for c in r['cases'] if c['case']==item['case'])
   if judgments[r['id']]['status']=='missing' and caseinfo['status']=='provider_capacity_blocked':
    judgments[r['id']].update({'reason':'GLM provider capacity blocked this case; no response, no retry or model switch.','receipt_url':response_base+'responses/'+r['id']+'/'+item['case']+'-receipt.json','failure_status':'provider_capacity_blocked'})
  enriched.append({**item,'source_rules':corpus[item['case']],'original_draft_label':s.get('original_draft_label'),'source_rule_id':s.get('source_id'),'author_model':s.get('model'),'evidence_url':s.get('evidence_base',GIT)+'/'+s['evidence_path'] if s.get('evidence_path') else GIT+'corpus.json','reviewers':judgments,'agreement':status,'observed_pairwise_disagreement':len(set(r for r in rels if r!='uncertain'))>1,'self_family_reviewers':[r['id'] for r in reviewers if s.get('model','').startswith(r['family_prefix'])]})
 pairwise=[]
 for a,b in itertools.combinations([r['id'] for r in reviewers],2):
  both=[x for x in enriched if all(x['reviewers'][r]['status']=='valid' for r in [a,b])];decisive=[x for x in both if all(x['reviewers'][r]['relation']!='uncertain' for r in [a,b])];agree=sum(x['reviewers'][a]['relation']==x['reviewers'][b]['relation'] for x in decisive)
  pairwise.append({'a':a,'b':b,'assigned':len(items),'comparable':len(decisive),'agree':agree,'differ':len(decisive)-agree,'uncertain':len(both)-len(decisive),'missing':len(items)-len(both)})
 label_comparison=[]
 for reviewer in reviewers:
  answered=[x for x in enriched if x['task']=='verification' and x['reviewers'][reviewer['id']]['status']=='valid'];decisive=[x for x in answered if x['reviewers'][reviewer['id']]['relation']!='uncertain'];agree=sum(x['original_draft_label']==x['reviewers'][reviewer['id']]['relation'] for x in decisive)
  label_comparison.append({'reviewer':reviewer['id'],'assigned':18,'agree':agree,'differ':len(decisive)-agree,'uncertain':len(answered)-len(decisive),'missing':18-len(answered)})
 replay=[]
 probes=[x for x in enriched if x['task']=='verification']
 for model in main['models']:
  m={'model':model['id'],'name':model['name'],'assigned':len(probes)*main['repetitions'],'reviewers':{}};oldmatch=0;predictions=0
  for reviewer in reviewers:
   match=disagree=missing_prediction=missing_review=uncertain=0
   for item in probes:
    sel=selection[item['id']];judge=item['reviewers'][reviewer['id']]
    for rep in range(1,main['repetitions']+1):
     row=next((r for r in main['verification_rows'] if r['model']==model['id'] and r['case']==item['case'] and r['repetition']==rep),None);j=next((j for j in row['judgments'] if j['id']==sel['probe_id']),None) if row else None
     if not j:missing_prediction+=1;continue
     if reviewer['id']=='glm':predictions+=1;oldmatch+=j['predicted']==sel['original_draft_label']
     if judge['status']!='valid':missing_review+=1
     elif judge['relation']=='uncertain':uncertain+=1
     elif j['predicted']==judge['relation']:match+=1
     else:disagree+=1
   m['reviewers'][reviewer['id']]={'matches':match,'disagreements':disagree,'missing_predictions':missing_prediction,'missing_reviews':missing_review,'uncertain_reviews':uncertain,'self_family':model['id'].startswith(reviewer['family_prefix'])}
  m.update({'original_draft_matches':oldmatch,'recorded_predictions':predictions});replay.append(m)
 summary={s:sum(x['agreement']==s for x in enriched) for s in ['unanimous','divergent','uncertain','incomplete']};summary.update({'items':len(items),'items_with_observed_disagreement':sum(x['observed_pairwise_disagreement'] for x in enriched),'assigned_review_records':len(items)*len(reviewers),'valid_review_records':sum(r['valid'] for r in reviewers),'missing_review_records':sum(r['missing'] for r in reviewers),'verification_items':18,'translation_items':18,'translation_models':15,'strict_envelope_valid_batches':sum(r['strict_envelope_valid_batches'] for r in reviewers),'expected_batches':9,'projected_review_records':sum(j.get('projection')=='array_to_items_object' for x in enriched for j in x['reviewers'].values()),'citation_missing_records':sum(j.get('citation_missing',False) for x in enriched for j in x['reviewers'].values())})
 return {'version':'2026-11-11.adversarial.1','status':'internal_tests','qualified':False,'primary_scores_unchanged':True,'protocol_url':GIT+'protocol.json','source_revision':REV,'data_source_sha256':protocol['data_sha256'],'reviewers':reviewers,'summary':summary,'items':enriched,'pairwise':pairwise,'label_comparison':label_comparison,'model_replay':replay,'sampling':protocol['sampling'],'limitations':[protocol['family_overlap'],protocol['reviewer_identity_masking'],protocol['claims'],'One reviewer pass per case. This targets known disagreements and is not a representative sample.','Qwen returned arrays in all three batches. A disclosed post-hoc structural projection makes its 36 record-level judgments inspectable; answers are unchanged. Its strict envelope compliance is 0 of 3.','Web responses are captured visible JSON, not provider HTTP bytes. Local energy and hardware costs are unmeasured.'], 'translation_scope':protocol['translation_scope']}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();d=build();body=(json.dumps(d,indent=2,ensure_ascii=False)+'\n').encode();out=ROOT/'web/downloads/blueprintbench/adversarial-tests.json'
 if args.check:assert out.read_bytes()==body,'Adversarial view drift'
 else:out.write_bytes(body)
 print(json.dumps(d['summary']))
