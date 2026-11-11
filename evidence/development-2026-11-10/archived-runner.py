from pathlib import Path
import os,json,time,concurrent.futures
from palo_workbench.models import Connection
from palo_workbench.connection import infer
from palo_workbench.finops import Ledger
root=Path(__file__).parent
raise SystemExit('Archived runner: do not execute against retained evidence. Use a new workspace and separately authorise any live inference budget.')
out=root/'challenger-expanded';out.mkdir(exist_ok=True)
configs=json.loads((root/'challenger-configs.json').read_text())
# Separate bounded qualification workspaces. The previous campaign remains blocked
# with its unresolved Mistral reservation intact. No charge is erased or called zero.
# Maximum NEW allocations: 9*.15+.30 = $1.65; provider key total cap remains $6.
# Full repository baseline has stopped; no competing full-run expenditure.
(root/'challenger-expanded-allocation.json').write_text(json.dumps({'new_budget_usd':1.65,'previous_unknown_reservation_microusd':9225,'previous_ledger_preserved':True,'output_cap':8000,'parallel_models':2,'note':'Independent qualification workspaces, not resumed failed workspace. All ledgers must be aggregated in report.'},indent=2))
def run(config):
 c=Connection.model_validate(config);c.finops.budget_usd=.30 if c.model.startswith('sakana/') else .15
 # Mistral rejected explicit effort=none at the original route. Test default
 # rather than asserting the catalogue setting works. This is recorded below.
 if c.model.startswith('mistralai/'):c.reasoning_effort=''
 slug=c.model.split('/')[1];ledger=Ledger(out/(slug+'-ledger.json'))
 for case in ('restoration','redevelopment','maintenance'):
  dest=out/(slug+'-'+case+'.json')
  if dest.exists():continue
  request=json.loads((root/(case+'-probe-request.json')).read_text());schema=request['response_format']['json_schema']['schema'];t=time.monotonic()
  result={'case':case,'model':c.model,'provider':c.provider,'output_cap':8000,'reasoning_effort':c.reasoning_effort or 'provider default','scope':'Single frozen public passage, not full repository'}
  try:
   raw,metric=infer(c,request['messages'],schema,8000,ledger=ledger,case_id=case+'-canary')
   result.update(output=raw,metric=metric)
  except Exception as e:result['error']=str(e)
  result['seconds']=time.monotonic()-t;dest.write_text(json.dumps(result,indent=2))
  print(c.model,case,round(result['seconds'],2),'error' if 'error' in result else 'output',result.get('error','')[:140],flush=True)
  if ledger.summary(c)['unknown_requests']:break
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(run,configs))
