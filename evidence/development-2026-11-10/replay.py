import json,pathlib,sys
from types import SimpleNamespace
from palo_workbench.models import Claim
from palo_workbench.pipeline import validate_claims
R=pathlib.Path(__file__).parent
rows=[]
for folder in ['challenger-expanded']:
 for p in sorted((R/folder).glob('*.json')):
  if p.name.endswith('-ledger.json'):continue
  v=json.loads(p.read_text())
  if 'case' not in v:continue
  case=v['case'];request=json.loads((R/f'{case}-probe-request.json').read_text());units=json.loads(request['messages'][1]['content']);raw=v.get('output',{});claims=[];errors=[]
  for i,c in enumerate(raw.get('claims',[]),1):
   try:
    refs=[{'unit_id':u['id'],'quote':u['text']} for k in c['evidence'] for u in units if u['id']==k]
    item=Claim(**{k:v for k,v in c.items() if k!='evidence'},sources=refs).model_dump();item['id']=f'c{i:03}';claims.append(item)
   except Exception as e:errors.append({'ordinal':i,'error':str(e)[:300]})
  valid=validate_claims(claims,units,SimpleNamespace(classes=[]))
  schema=request['response_format']['json_schema']['schema'];strict_errors=[]
  try:
   import jsonschema
   if raw:strict_errors=[e.message[:200] for e in jsonschema.Draft202012Validator(schema).iter_errors(raw)]
  except ImportError:strict_errors=['JSON Schema validator unavailable']
  rows.append({'campaign':folder,'file':p.name,'case':case,'model':v['model'],'provider':v.get('provider'),'elapsed_seconds':v.get('seconds'), 'error':v.get('error'),'raw_claims':len(raw.get('claims',[])),'mechanically_valid':sum(c['valid'] for c in valid),'schema_errors':errors,'json_schema_errors':strict_errors,'validation':valid,'cost_usd':v.get('metric',{}).get('accounting',{}).get('usage',{}).get('cost')})
expected = json.loads((R/'recorded-audit.json').read_text(encoding='utf-8'))
key = lambda row: (row['model'], row['case'])
observed = {key(row): row for row in rows}
diffs = []
for old in expected:
 new = observed.get(key(old))
 for field in ('raw_claims', 'mechanically_valid'):
  if new is None or old[field] != new[field]: diffs.append({'model':old['model'],'case':old['case'],'field':field,'recorded':old[field],'replayed':None if new is None else new[field]})
result = {'mode':'offline checker replay; no inference', 'recorded_attempts':len(expected),'replayed_attempts':len(rows),'differences':diffs,'counts_match':not diffs and len(expected)==len(rows)}
print(json.dumps(result, indent=2))
if not result['counts_match']: raise SystemExit(1)
