"""Bounded internal extension: immutable inputs, reserved concurrent spend, no retries."""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
API = 'https://openrouter.ai/api/v1'

def load(path):
    return json.loads(path.read_bytes().decode('utf-8'))

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as file:
        json.dump(value, file, indent=2, allow_nan=False)
        file.write('\n')

def now():
    return datetime.now(timezone.utc).isoformat()

def digest(body):
    return hashlib.sha256(body).hexdigest()

def auth(path, key):
    request = urllib.request.Request(API + path, headers={'Authorization': 'Bearer ' + key})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)['data']

def plan():
    models = load(ROOT / 'models.json')
    cases = load(ROOT / 'corpus.json')
    schema = load(ROOT / 'verification.schema.json')
    schedule = []
    for repetition in range(1, 4):
        rotated = models[repetition-1:] + models[:repetition-1]
        for case in cases:
            for track in ['translation', 'verification']:
                for model in rotated:
                    payload = {'model': model['id'], 'messages': load(ROOT / 'prompts' / (track+'-'+case['id']+'.json')),
                               'max_tokens': model['configuration']['max_tokens'], 'stream': False,
                               'provider': {'only': [model['provider']], 'allow_fallbacks': False, 'require_parameters': True}}
                    if model['configuration']['reasoning'] is not None:
                        payload['reasoning'] = model['configuration']['reasoning']
                    if track == 'verification':
                        payload['response_format'] = {'type':'json_schema','json_schema':{'name':'procurement_judgments','strict':True,'schema':schema}}
                    body = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
                    reservation = ((len(body)+4096)*float(model['pricing']['prompt']) + payload['max_tokens']*float(model['pricing']['completion']))*1.10
                    ident = f"{repetition}-{case['id']}-{track}-{model['id'].replace('/', '__')}"
                    schedule.append((ident, model, case['id'], track, repetition, body, reservation))
    return schedule

def call(item, key, private_dir):
    ident, model, case, track, repetition, body, reservation = item
    dest = ROOT / 'runs' / ident
    dest.mkdir(parents=True)
    (dest / 'request.json').write_bytes(body)
    started = now()
    save(dest / 'reservation.json', {'at': started, 'reserved_usd': reservation})
    record = {'id': ident, 'model': model['id'], 'pinned_provider': model['provider'], 'case': case, 'track': track,
              'repetition': repetition, 'started_at': started, 'request_sha256': digest(body), 'reserved_usd': reservation,
              'cost_status':'unknown', 'cost_usd':None, 'state':'fail', 'qualification':'internal_tests', 'response_bytes_original':True}
    request = urllib.request.Request(API+'/chat/completions',data=body,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','HTTP-Referer':'https://paloframework.org/PALO_BlueprintBench_Leaderboard.html','X-Title':'PALO internal procurement extension'})
    tick = time.monotonic()
    try:
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                raw = response.read()
                record['http_status'] = response.status
                headers = {k:v for k,v in response.headers.items() if k.lower() in ['date','content-type','x-request-id','server']}
        except urllib.error.HTTPError as error:
            raw = error.read()
            record['http_status'] = error.code
            headers = {}
        result = json.loads(raw)
        record['response_sha256'] = digest(raw)
        public = raw
        if 'user_id' in result:
            private_dir.mkdir(parents=True,exist_ok=True)
            (private_dir/(ident+'.json')).write_bytes(raw)
            result.pop('user_id')
            public = (json.dumps(result,indent=2)+'\n').encode()
            save(dest/'response-redaction.json',{'removed_json_pointers':['/user_id'],'original_sha256':digest(raw),'public_sha256':digest(public)})
            record['response_bytes_original'] = False
        (dest/'response.json').write_bytes(public)
        save(dest/'response-headers.json',headers)
        record.update(provider_request_id=result.get('id'),returned_model=result.get('model'),returned_provider=result.get('provider'),usage=result.get('usage',{}))
        cost = record['usage'].get('cost')
        if type(cost) in [int,float] and cost >= 0:
            record.update(cost_status='provider_reported', cost_usd=cost)
        choices = result.get('choices',[])
        if choices:
            choice = choices[0]
            record['finish_reason'] = choice.get('finish_reason')
            content = choice.get('message',{}).get('content')
            if isinstance(content,str):
                (dest/'output.txt').write_bytes(content.encode('utf-8'))
                record['output_sha256'] = digest(content.encode('utf-8'))
                record['state'] = 'completed' if choice.get('finish_reason')=='stop' and content.strip() else 'incomplete'
            else:
                record['error'] = 'No text content'
        elif result.get('error'):
            record['error'] = result['error']
    except (OSError,ValueError) as error:
        record['error'] = {'type':type(error).__name__,'message':str(error)[:180]}
    record.update(elapsed_seconds=time.monotonic()-tick,finished_at=now())
    save(dest/'record.json',record)
    return record

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--key-file',type=Path)
    parser.add_argument('--private-dir',type=Path)
    args = parser.parse_args()
    manifest = load(ROOT/'manifest.json')
    for name, sha in manifest['files'].items():
        assert digest((ROOT/name).read_bytes()) == sha, name
    schedule = plan()
    if not args.execute:
        print(json.dumps({'assigned_calls':len(schedule),'reservation_if_all_outputs_reach_cap_usd':sum(x[-1] for x in schedule)}))
        return
    if not args.key_file or not args.private_dir:
        parser.error('Execution requires key-file and private-dir outside the public repository.')
    key = args.key_file.read_text().strip()
    runs = ROOT/'runs'
    runs.mkdir(exist_ok=True)
    if any(not (p/'record.json').exists() for p in runs.iterdir() if p.is_dir()):
        raise SystemExit('Interrupted request requires accounting before continuation.')
    existing = [load(p) for p in runs.glob('*/record.json')]
    done = {r['id'] for r in existing}
    pending = [item for item in schedule if item[0] not in done]
    known = sum(r['cost_usd'] or 0 for r in existing)
    unknown = sum(r['reserved_usd'] for r in existing if r['cost_status']=='unknown')
    active = {}
    stop_reason = None
    with ThreadPoolExecutor(max_workers=4) as pool:
        while pending or active:
            while pending and len(active)<4 and not stop_reason:
                item = pending[0]
                key_state = auth('/key',key)
                credit = auth('/credits',key)
                outstanding = sum(active.values())
                headroom = min(40-key_state['usage'],key_state['limit_remaining'],credit['total_credits']-credit['total_usage'])
                headroom -= manifest['prior_unknown_reserved_usd']+unknown+outstanding
                campaign = manifest['new_campaign_ceiling_usd']-known-unknown-outstanding
                if item[-1]>min(headroom,campaign):
                    if active:
                        break
                    stop_reason = 'insufficient_reserved_headroom'
                    break
                pending.pop(0)
                active[pool.submit(call,item,key,args.private_dir)] = item[-1]
            if not active:
                break
            ready,_ = wait(active,timeout=1,return_when=FIRST_COMPLETED)
            for future in ready:
                active.pop(future)
                record = future.result()
                if record['cost_status']=='unknown':
                    unknown += record['reserved_usd']
                else:
                    known += record['cost_usd']
                print(json.dumps({k:record.get(k) for k in ['id','state','http_status','cost_usd','elapsed_seconds']}),flush=True)
    records = [load(p) for p in runs.glob('*/record.json')]
    summary = {'status':'blocked' if stop_reason else 'completed','stop_reason':stop_reason,'assigned_calls':len(schedule),'recorded_calls':len(records),'not_run':len(schedule)-len(records),'completed_calls':sum(r['state']=='completed' for r in records),'known_cost_usd':sum(r['cost_usd'] or 0 for r in records),'unknown_cost_calls':sum(r['cost_status']=='unknown' for r in records),'unknown_reserved_usd':sum(r['reserved_usd'] for r in records if r['cost_status']=='unknown'),'qualified':False}
    (ROOT/'execution-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary),flush=True)

if __name__=='__main__':
    main()
