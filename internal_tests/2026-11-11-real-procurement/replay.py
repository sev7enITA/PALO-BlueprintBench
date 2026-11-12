"""Replay and verify real-document study evidence offline; never call a provider.

--check fails for stale derived snapshots or pending requests. --output exports
both checker revisions into a new directory without changing the source archive.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import math
import re
import shutil
import tempfile

ROOT=Path(__file__).resolve().parent
VOLATILE_NOTE_FIELDS={'updated_at','first_documented_at'}


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value,message):
    if not value:raise ValueError(message)


def finite(value):
    return type(value) in (int,float) and math.isfinite(value) and value>=0


def semantic_note(value):
    return {k:v for k,v in value.items() if k not in VOLATILE_NOTE_FIELDS}


def correction_module(root):
    spec=importlib.util.spec_from_file_location('offline_quote_correction',root/'corrections/quote-normalisation-v1.1.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def verify_footer(folder,record):
    envelope=load(folder/'mcp-response.json')
    require(sha(folder/'mcp-response.json')==record['mcp_response_sha256'],'MCP envelope hash mismatch: '+folder.name)
    output=folder/'output.txt'
    if output.exists():
        require(sha(output)==record['output_sha256'],'Output hash mismatch: '+folder.name)
        footer=folder/'mcp-accounting-footer.txt'
        require(footer.exists(),'Output exists without archived metadata footer')
        footer_text=footer.read_text(encoding='utf-8')
        match=re.fullmatch(r'\n\n\(model: ([^,\n]+), generation id: ([^,\n]+), input tokens: [0-9]+, output tokens: [0-9]+, reasoning tokens: [0-9]+\)',footer_text)
        require(match is not None,'Unrecognized terminal accounting footer')
        require(match.group(1)==record['model'] and match.group(2)==record['provider_request_id'],'Footer identity differs from receipt')
        text='\n'.join(item['text'] for item in envelope.get('content',[]) if item.get('type')=='text')
        require(text.encode('utf-8')==output.read_bytes()+footer.read_bytes(),'Output extraction altered more than terminal footer: '+folder.name)
    else:
        require(record.get('output_sha256') is None,'Missing output has non-null hash')


def verify_records(root,manifest):
    schedule=load(root/'schedule.json');assignments={a['id']:a for a in schedule}
    require(len(schedule)==len(assignments)==27,'Expected27 unique assigned calls')
    triples={(a['task_id'],a['model'],a['repetition']) for a in schedule}
    require(len(triples)==27 and {a['repetition'] for a in schedule}=={1,2,3},'Task/model/repetition allocation invalid')
    records=[]
    for folder in sorted((root/'runs').iterdir()) if (root/'runs').exists() else []:
        if not folder.is_dir():continue
        require((folder/'record.json').exists(),'Pending/orphan request: '+folder.name+'; final snapshot is not ready')
        record=load(folder/'record.json');assignment=assignments.get(folder.name)
        require(assignment is not None,'Unassigned run directory: '+folder.name)
        for key,value in assignment.items():require(record.get(key)==value,'Receipt/schedule mismatch: '+folder.name+'/'+key)
        if record.get('state')=='not_run':
            amendment=load(root/'transport-amendment.json')
            require(folder.name in amendment['stopped_undispatched_assignments'] or folder.name in (load(root/'user-stop.json')['stopped_undispatched_assignments'] if (root/'user-stop.json').exists() else []),'Unjustified administrative stop')
            require(record.get('cost_status')=='not_dispatched' and type(record.get('cost_usd')) in (int,float) and record['cost_usd']==0,'Undispatched accounting state invalid')
            require(record.get('cost_zero_reason') and record.get('decision_recorded_at'),'Undispatched zero lacks reason/time')
            require(record.get('reserved_usd')==0 and record.get('provider_request_id') is None,'Undispatched record claims request/charge')
            require(record.get('qualified') is False,'Administrative stop claims qualification')
            require(not any((folder/name).exists() for name in ('request.json','output.txt','mcp-response.json','get_generation.json')),'Undispatched assignment contains API evidence')
            require(sha(root/assignment['request_path'])==assignment['request_sha256'],'Stopped prepared request changed')
            require(sha(root/'sources'/(assignment['task_id']+'.json'))==record['source_packet_sha256'],'Stopped source packet changed')
            records.append(record);continue
        require(record.get('finished_at') is not None,'Unfinished receipt: '+folder.name)
        require(record['manifest_sha256']==sha(root/'manifest.json'),'Receipt manifest mismatch')
        request=root/assignment['request_path'];require(sha(request)==assignment['request_sha256'],'Prepared request mismatch')
        require((folder/'request.json').read_bytes()==request.read_bytes(),'Submitted request differs from prepared bytes')
        require(sha(root/'sources'/(assignment['task_id']+'.json'))==record['source_packet_sha256'],'Source packet mismatch')
        payload=load(request)
        require(payload['provider']['only']==[assignment['pinned_provider']] and payload['provider']['allow_fallbacks'] is False,'Provider pin/fallback changed')
        require(not any(key in json.dumps(payload) for key in ('assessment_key','expected_outputs','"expected":','"cases":')),'Hidden key leaked into request')
        interrupted=(root/'user-stop.json').exists() and folder.name==load(root/'user-stop.json')['interrupted_inflight_assignment']
        if interrupted:
            require(record.get('cost_status')=='unknown' and record.get('cost_usd') is None and record.get('reserved_usd',0)>0,'Interrupted request lacks reserve')
            require(not (folder/'output.txt').exists() and not (folder/'mcp-response.json').exists(),'Interrupted response unexpectedly present')
            records.append(record);continue
        verify_footer(folder,record)
        status,cost=record.get('cost_status'),record.get('cost_usd')
        if status=='unknown':require(cost is None,'Unknown cost changed to numeric value')
        else:
            require(status in ('provider_reported','provider_reported_reconciled') and finite(cost),'Invalid cost status/value')
            accounting=load(folder/'get_generation.json')['data']
            require(accounting['id']==record['provider_request_id'],'Accounting generation mismatch')
            require(accounting['total_cost']==cost,'Recorded cost differs from provider total_cost')
            if status=='provider_reported_reconciled':
                previous=load(folder/'record-before-reconciliation.json')
                require(previous.get('cost_status')=='unknown' and previous.get('cost_usd') is None,'Reconciliation lacks unknown-cost history')
                require(record.get('accounting_recovery') and record.get('reconciled_at'),'Reconciliation lacks provenance description/time')
                for key in ('id','task_id','model','repetition','pinned_provider','started_at','finished_at','elapsed_seconds','state','request_sha256','mcp_response_sha256','output_sha256'):
                    require(previous.get(key)==record.get(key),'Reconciliation changed original execution/output evidence: '+key)
                require(record['state']=='fail' and record.get('output_sha256') is None and not (folder/'output.txt').exists(),'Timed-out answer must remain missing after accounting recovery')
                require(accounting.get('model')==record.get('returned_model') and accounting.get('provider_name')==record.get('returned_provider'),'Reconciled provider/model identity differs')
        require(record['response_bytes_original'] is False,'MCP archive mislabeled raw HTTP bytes')
        require(record['qualified'] is False,'Receipt claims qualification')
        records.append(record)
    return records


def check_staleness(root,records,supplement_records=()):
    count=sum(r.get('state')!='not_run' for r in records)
    for name in ('analysis.json','analysis-corrected.json'):
        require((root/name).exists(),'Missing derived snapshot: '+name)
        actual=load(root/name)['summary']['recorded_calls']
        require(actual==count,f'STALE {name}: recorded_calls={actual}, actual_receipts={count}; rerun both analyses')
    note=load(root/'corrections/correction-note.json')
    require(note['comparison_scope']['recorded_snapshot_calls']==count,'STALE correction note: receipt count differs')
    require(note['comparison_scope'].get('snapshot_record_files')==len(records),'STALE correction note: snapshot record files differ')
    budget=load(root/'budget-final.json');all_records=list(records)+list(supplement_records)
    require(budget.get('archived_record_files',budget['recorded_calls'])==len(all_records),'STALE budget snapshot: archived record count differs')
    if 'archived_record_files' in budget:
        require(budget['recorded_calls']==sum(r.get('state')!='not_run' for r in all_records),'Final budget dispatched count differs')


def verify_budget(root,manifest,records,supplement_records=()):
    records=list(records)+list(supplement_records)
    budget=load(root/'budget-final.json');known=sum(r['cost_usd'] for r in records if r['cost_status'] in ('provider_reported','provider_reported_reconciled'))
    reserve=sum(r['reserved_usd'] for r in records if r['cost_status']=='unknown')
    require(math.isclose(known,budget['known_campaign_cost_usd'],abs_tol=1e-10),'Budget known-charge sum differs')
    require(math.isclose(reserve,budget['current_unknown_cost_reserve_usd'],abs_tol=1e-10),'Unknown reservations omitted')
    baseline=budget['account_usage_before_usd'];account=budget['account_usage_after_usd']
    require(finite(baseline) and finite(account),'Account usage unavailable')
    require(budget['previous_unknown_cost_reserve_usd']==manifest['previous_unknown_cost_reserve_usd'],'Previous unknown reserve changed')
    bound=max(account,baseline+known)+budget['previous_unknown_cost_reserve_usd']+reserve
    require(math.isclose(bound,budget['conservative_cumulative_committed_usd'],abs_tol=1e-10),'Budget bound not reproducible')
    require(bound<=manifest['cumulative_ceiling_usd']==40,'Cumulative authorization exceeded')
    require(known+reserve<=manifest['new_study_ceiling_usd'],'Study budget including unknown reserves exceeded')
    return {'known_cost_usd':known,'unknown_reserved_usd':reserve,'conservative_bound_usd':bound}


def verify_supplement(root):
    sub=root/'supplemental-google-ai-studio'
    if not (sub/'manifest.json').exists() or (sub/'cancellation.json').exists():return []
    manifest=load(sub/'manifest.json')
    require(manifest['original_manifest_sha256']==sha(root/'manifest.json'),'Supplement parent manifest changed')
    for name,expected in manifest['files'].items():require(sha(sub/name)==expected,'Supplement frozen file changed: '+name)
    schedule=load(sub/'schedule.json');assigned={a['id']:a for a in schedule}
    require(len(schedule)==len(assigned)==9,'Supplement denominator changed')
    for assignment in schedule:
        payload=load(sub/assignment['request_path']);original=load(root/'prepared'/(assignment['task_id']+'-2.json'))
        require(payload['messages']==[{'role':'system','content':original['system']},{'role':'user','content':original['message']}],'Supplement changed prompt content')
        require(payload['max_tokens']==original['max_tokens']==32768 and payload['reasoning']['effort']==original['reasoning_effort']=='high','Supplement reasoning/output budget changed')
        require(payload['provider']=={'only':['google-ai-studio'],'allow_fallbacks':False},'Supplement provider routing changed')
    records=[]
    for folder in sorted((sub/'runs').iterdir()) if (sub/'runs').exists() else []:
        if not folder.is_dir():continue
        require((folder/'record.json').exists(),'Pending/orphan supplemental request: '+folder.name)
        record=load(folder/'record.json');assignment=assigned.get(folder.name)
        require(assignment is not None,'Unassigned supplemental receipt')
        for key in ('id','model','task_id','repetition','pinned_provider'):
            require(record.get(key)==assignment[key],'Supplement receipt identity differs: '+key)
        require(record.get('manifest_sha256')==sha(sub/'manifest.json'),'Supplement receipt manifest differs')
        require(record.get('request_sha256')==assignment['request_sha256']==sha(sub/assignment['request_path']),'Supplement request hash differs')
        require(record.get('elapsed_seconds') is None,'Batch queue duration misrepresented as client call latency')
        require(record.get('qualified') is False,'Supplement receipt claims qualification')
        status,cost=record.get('cost_status'),record.get('cost_usd')
        if status=='unknown':require(cost is None,'Unknown supplemental cost became numeric')
        else:
            require(status in ('provider_reported','provider_reported_reconciled') and finite(cost),'Invalid supplemental cost evidence')
            if (folder/'get_generation.json').exists():
                accounting=load(folder/'get_generation.json')['data'];require(accounting['total_cost']==cost,'Supplement provider cost differs')
            else:
                body=load(folder/'batch-response.json');require(body.get('usage',{}).get('cost')==cost,'Supplement cost lacks exact provider receipt')
        if (folder/'output.txt').exists():
            body=load(folder/'batch-response.json')
            require(record.get('batch_response_sha256')==sha(folder/'batch-response.json'),'Supplement response-body hash differs')
            require(record.get('output_sha256')==sha(folder/'output.txt'),'Supplement output hash differs')
            content=body['choices'][0]['message']['content']
            require(isinstance(content,str) and content.encode('utf-8')==(folder/'output.txt').read_bytes(),'Supplement answer extraction differs from provider body')
        else:require(record.get('output_sha256') is None,'Supplement missing answer has non-null hash')
        records.append(record)
    return records


def compare_reports(root,snapshot):
    names=['analysis.json','analysis-corrected.json','corrections/analysis-v1.0-replayed.json']
    if (root/'supplemental-google-ai-studio/manifest.json').exists() and not (root/'supplemental-google-ai-studio/cancellation.json').exists():names+=['analysis-supplement.json','analysis-combined.json']
    for name in names:
        require(load(root/name)==load(snapshot/name),'Derived analysis differs from offline replay: '+name)
    folders=['blueprints','blueprints-corrected']
    if (root/'supplemental-google-ai-studio/manifest.json').exists() and not (root/'supplemental-google-ai-studio/cancellation.json').exists():folders.append('supplemental-google-ai-studio/blueprints-corrected')
    for folder in folders:
        expected={f.name for f in (snapshot/folder).glob('*.json')};actual={f.name for f in (root/folder).glob('*.json')}
        require(expected==actual,'Blueprint inventory differs: '+folder)
        for name in expected:require(load(root/folder/name)==load(snapshot/folder/name),'Blueprint differs: '+folder+'/'+name)
    require((root/'corrections/correction-note.md').read_bytes()==(snapshot/'corrections/correction-note.md').read_bytes(),'Human-readable correction note differs from replay')
    published=load(root/'corrections/correction-note.json');replayed=load(snapshot/'corrections/correction-note.json')
    require(semantic_note(published)==semantic_note(replayed),'Correction note differs beyond allowed timestamp fields')
    require(published['corrected_analysis_sha256']==sha(root/'analysis-corrected.json'),'Published corrected analysis hash differs')
    require(published['baseline_replay_sha256']==sha(root/'corrections/analysis-v1.0-replayed.json'),'Published baseline replay hash differs')


def replay(root=ROOT,check=False,output=None):
    root=Path(root);manifest=load(root/'manifest.json')
    for name,expected in manifest['files'].items():require(sha(root/name)==expected,'Frozen file changed: '+name)
    records=verify_records(root,manifest);supplement_records=verify_supplement(root)
    if check:check_staleness(root,records,supplement_records)
    correction=correction_module(root)
    with tempfile.TemporaryDirectory(prefix='palo-real-offline-') as temporary:
        snapshot=Path(temporary)
        for name in manifest['files']:
            target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,target)
        shutil.copyfile(root/'manifest.json',snapshot/'manifest.json')
        if (root/'transport-amendment.json').exists():shutil.copyfile(root/'transport-amendment.json',snapshot/'transport-amendment.json')
        correction.snapshot(root,snapshot)
        _,analyser=correction.modules(snapshot)
        baseline=analyser.run(snapshot)
        correction.write(snapshot/'analysis.json',baseline)
        # Preserve original timestamp provenance for a deterministic semantic diff.
        if (root/'corrections/correction-note.json').exists():
            (snapshot/'corrections').mkdir(exist_ok=True)
            shutil.copyfile(root/'corrections/correction-note.json',snapshot/'corrections/correction-note.json')
        correction.run(snapshot)
        if (root/'supplemental-google-ai-studio/manifest.json').exists() and not (root/'supplemental-google-ai-studio/cancellation.json').exists():
            sub=root/'supplemental-google-ai-studio';target=snapshot/'supplemental-google-ai-studio'
            for name in load(sub/'manifest.json')['files']:
                destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(sub/name,destination)
            shutil.copyfile(sub/'manifest.json',target/'manifest.json')
            if (sub/'runs').exists():shutil.copytree(sub/'runs',target/'runs')
            shutil.copyfile(root/'corrections/quote-normalisation-v1.1.py',snapshot/'corrections/quote-normalisation-v1.1.py')
            spec=importlib.util.spec_from_file_location('offline_supplement',root/'analyse-supplement.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.run(snapshot)
        if check:compare_reports(root,snapshot)
        if output:
            output=Path(output);require(not output.exists(),'Replay output directory must be new')
            require(not output.resolve().is_relative_to(root.resolve()),'Replay output must be outside the source archive')
            output.mkdir(parents=True)
            export_names=['analysis.json','analysis-corrected.json','blueprints','blueprints-corrected','corrections']
            if (snapshot/'analysis-combined.json').exists():export_names+=['analysis-combined.json','analysis-supplement.json','supplemental-google-ai-studio']
            for name in export_names:
                source=snapshot/name
                if source.is_dir():shutil.copytree(source,output/name)
                else:shutil.copyfile(source,output/name)
    budget=verify_budget(root,manifest,records,supplement_records) if check else None
    return {'status':'offline_replay_verified' if check else 'offline_replay_exported','assigned_calls':36 if (root/'supplemental-google-ai-studio/manifest.json').exists() and not (root/'supplemental-google-ai-studio/cancellation.json').exists() else 27,
        'snapshot_record_files':len(records)+len(supplement_records),'recorded_calls':sum(r.get('state')!='not_run' for r in records+supplement_records),'original_missing_record_files':27-len(records),'supplement_missing_record_files':9-len(supplement_records) if (root/'supplemental-google-ai-studio/manifest.json').exists() and not (root/'supplemental-google-ai-studio/cancellation.json').exists() else 0,'paid_calls':0,'budget':budget,
        'timestamp_policy':'Only first_documented_at and updated_at in correction-note.json are ignored; outcome fields and hashes are compared.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--check',action='store_true');parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if not args.check and args.output is None:parser.error('Use --check or --output NEW_DIRECTORY')
    try:print(json.dumps(replay(args.root,args.check,args.output)))
    except (ValueError,KeyError,FileNotFoundError) as error:raise SystemExit('Offline replay check failed: '+str(error))
