import sys,tempfile,json,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2] / 'evaluator'))
import blueprintbench as bb
from demo import make,put
results={}
for case in ['duplicate_critical','supported_critical','declared_pass','rehashed_lock','one_claim_all_gold','unknown_cost']:
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);lock,run=make(root)
  idx=1 if case in ['duplicate_critical','declared_pass'] else 0
  a=run['attempts'][idx];receipt=bb.read_json(root/a['receipt']['path']);ann=bb.read_json(root/a['annotation']['path']);emitted=bb.read_json(root/receipt['claims_artifact']['path'])
  if case=='duplicate_critical':
   for n in range(2,5):
    c=copy.deepcopy(ann['claims'][1]);c['id']=f'c{n}';ann['claims'].append(c); e=copy.deepcopy(emitted[1]);e['id']=f'c{n}';emitted.append(e)
  elif case=='supported_critical':
   for c in ann['claims']:c['critical']=True
  elif case=='declared_pass':
   a['state']=receipt['state']='pass'
   for c in ann['claims']:c['verdict']='unsupported';c['matches_gold']=[]
  elif case=='rehashed_lock':
   lock['payload']['registered_at']='2020-01-01T00:00:00Z';lock['payload']['campaign']['split']='heldout_candidate';lock['sha256']=bb.digest(lock['payload']);run['campaign_sha256']=lock['sha256']
  elif case=='one_claim_all_gold':
   emitted=[{'id':'c0','text':'An opaque claim asserting all rules.'}];ann['claims']=[{'id':'c0','equivalence_id':'p0','verdict':'supported','matches_gold':['g1','g2'],'critical':False}]
  elif case=='unknown_cost':a['cost']={'status':'unknown','usd':None}
  receipt['claims_artifact']=put(root,f'{case}/claims.json',emitted);receipt['artifacts']=[receipt['claims_artifact']]
  a['receipt']=put(root,f'{case}/receipt.json',receipt);ann['receipt_sha256']=a['receipt']['sha256'];a['annotation']=put(root,f'{case}/annotation.json',ann)
  r=bb.evaluate(lock,run,root)
  results[case]={k:r[k] for k in ['qualified','reported_completion_rate','critical_errors','cost_complete','cost_per_success_usd','comparability_blocks']};results[case]['affected_row']=r['rows'][idx]
Path(__file__).with_name('reproduced-findings.json').write_text(json.dumps({'source_commit':'66c6c5b','cases':results},indent=2),encoding='utf-8')
for k,r in results.items(): print(k,json.dumps({x:r[x] for x in ['qualified','reported_completion_rate','critical_errors','cost_complete','cost_per_success_usd']}),'precision',r['affected_row']['precision'],'recall',r['affected_row']['recall'])
