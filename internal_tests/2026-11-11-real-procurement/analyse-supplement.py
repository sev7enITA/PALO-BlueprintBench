"""Add a separately frozen provider/transport configuration without merging models.

Uses the original frozen assessor and versioned quote correction. No API calls,
source edits, prompt repair, relabeling or original-schedule replacement.
"""
from pathlib import Path
import argparse
import copy
import importlib.util
import json

ROOT=Path(__file__).resolve().parent
SUPPLEMENT='supplemental-google-ai-studio'


def correction_module(root):
    spec=importlib.util.spec_from_file_location('supplement_quote_correction',root/'corrections/quote-normalisation-v1.1.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def enrich(row,assignment,record,cohort):
    row['provider']=assignment['pinned_provider']
    row['pinned_provider']=assignment['pinned_provider']
    row['configuration_id']=row['model']+'@'+assignment['pinned_provider']
    row['configuration_label']=row['model']+' / '+assignment['pinned_provider']
    row['cohort']=cohort
    row['access_channel']=assignment.get('access_channel','OpenRouter MCP')
    row['timing_comparability']=assignment.get('timing_comparability','Serial request elapsed time; descriptive only')
    for name in ('stop_reason','cost_zero_reason','decision_recorded_at','provider_latency_ms','provider_generation_time_ms','batch_id','accounting_recovery','reconciled_at'):
        if record and name in record:row[name]=record[name]
    return row


def groups(rows,field,analyser):
    return [{field:key,**analyser.summarize([r for r in rows if r[field]==key])} for key in sorted({r[field] for r in rows})]


def configuration_groups(rows,analyser):
    result=[]
    for config in sorted({r['configuration_id'] for r in rows}):
        own=[r for r in rows if r['configuration_id']==config];first=own[0]
        result.append({k:first[k] for k in ('configuration_id','configuration_label','model','provider','cohort','access_channel','timing_comparability')} | analyser.summarize(own))
    return result


def run(root=ROOT):
    root=Path(root);supp=root/SUPPLEMENT;correction=correction_module(root)
    load,sha,write=correction.load,correction.sha,correction.write
    manifest=load(supp/'manifest.json')
    if manifest['original_manifest_sha256']!=sha(root/'manifest.json'):raise ValueError('Supplement original-manifest binding differs')
    for name,expected in manifest['files'].items():
        if sha(supp/name)!=expected:raise ValueError('Frozen supplement input changed: '+name)
    contracts,analyser=correction.modules(root);contracts.normalized=correction.normalized_v11
    designs={t['id']:t for t in load(root/'design/task-design.json')['tasks']}
    cases={t['task_id']:t['cases'] for t in load(root/'design/assessment-key.json')['tasks']}
    packets={p['id']:{x['page']:x['text'] for x in p['pages']} for p in load(root/'source-packets.json')}
    schedule=load(supp/'schedule.json')
    if len(schedule)!=9 or len({a['id'] for a in schedule})!=9:raise ValueError('Supplement must retain9 unique assignments')
    if {(a['task_id'],a['repetition']) for a in schedule}!={(task,repetition) for task in designs for repetition in (1,2,3)}:
        raise ValueError('Supplement document/repetition allocation differs')
    rows=[]
    for assignment in schedule:
        folder=supp/'runs'/assignment['id'];record=load(folder/'record.json') if (folder/'record.json').exists() else None
        raw=(folder/'output.txt').read_bytes().decode('utf-8') if record is not None and (folder/'output.txt').exists() else None
        if record:
            for key in ('id','model','task_id','repetition'):
                if record.get(key)!=assignment[key]:raise ValueError('Supplement receipt identity mismatch')
            if raw is not None and record.get('output_sha256')!=sha(folder/'output.txt'):raise ValueError('Supplement output hash mismatch')
            cost=record.get('cost_usd')
            if cost is not None and not contracts.typed(cost,{'type':'number','minimum':0}):raise ValueError('Invalid supplemental cost')
            if record.get('cost_status')=='unknown' and cost is not None:raise ValueError('Unknown supplemental cost must stay null')
        row,blueprint=analyser.assess(assignment,designs[assignment['task_id']],cases[assignment['task_id']],packets[assignment['task_id']],record,raw)
        enrich(row,assignment,record,'transport_supplement')
        # Batch queue/completion duration is never inserted into serial elapsed-time columns.
        if record and record.get('elapsed_seconds') is not None:
            raise ValueError('Batch elapsed_seconds must be null; provider latency belongs in its own field')
        for name in ('record.json','request.json','output.txt','batch-response.json','mcp-response.json','get_generation.json'):
            if (folder/name).exists():
                row[name.replace('.','_')+'_path']=(folder/name).relative_to(root).as_posix()
                row[name.replace('.','_')+'_sha256']=sha(folder/name)
        if raw is not None:
            artifact={'id':assignment['id'],'model':assignment['model'],'task_id':assignment['task_id'],
                'repetition':assignment['repetition'],'configuration_id':row['configuration_id'],'provider':row['provider'],
                'cohort':'transport_supplement','access_channel':row['access_channel'],'artifact_type':'generated_source_linked_blueprint_draft',
                'business_approval_required':True,'business_approved':False,'qualified':False,
                'export_status':'structurally_usable_model_draft' if row['structural_valid'] else 'unusable_model_draft',
                'source_quote_match':row['source_quote_match'],'issues':row['issues'],'content':blueprint,
                'output_sha256':sha(folder/'output.txt'),'assessment':'hidden_assistant_draft_test_vectors_not_independent_gold',
                'checker_revision':correction.VERSION,'correction_status':'postcollection_mechanical_quote_check_correction'}
            target=supp/'blueprints-corrected'/(assignment['id']+'.json');write(target,artifact)
            row['blueprint_path']=target.relative_to(root).as_posix()
        rows.append(row)
    supplement_analysis={'title':'Real-document generation: supplemental provider and transport configuration',
        'status':'internal_transport_supplement','qualified':False,'independent_human_reviews':0,
        'checker_revision':correction.VERSION,'correction_note':'corrections/correction-note.json',
        'summary':analyser.summarize(rows),'by_configuration':configuration_groups(rows,analyser),
        'by_task':groups(rows,'task_id',analyser),'by_repetition':groups(rows,'repetition',analyser),'rows':rows,
        'manifest_path':SUPPLEMENT+'/manifest.json','manifest_sha256':sha(supp/'manifest.json'),
        'original_manifest_sha256':sha(root/'manifest.json'),'limitations':[
            'Serving provider and asynchronous batch transport both changed after repeated Vertex failures; no single-factor causal attribution.',
            'The original27 assignments, failed outputs and five undispatched assignments remain separately visible.',
            'Batch queue duration is not interactive request latency.','Assistant-draft expectations and source-quote checks do not establish semantic accuracy or independent validation.']}
    supplement_analysis['by_model']=copy.deepcopy(supplement_analysis['by_configuration'])
    write(root/'analysis-supplement.json',supplement_analysis)
    original=load(root/'analysis-corrected.json');original_schedule={a['id']:a for a in load(root/'schedule.json')}
    original_rows=copy.deepcopy(original['rows'])
    for row in original_rows:
        assignment=original_schedule[row['id']];folder=root/'runs'/row['id']
        record=load(folder/'record.json') if (folder/'record.json').exists() else None
        # Fail on stale original outcome/cost rows rather than silently refreshing only the combined view.
        raw=(folder/'output.txt').read_bytes().decode('utf-8') if record is not None and (folder/'output.txt').exists() else None
        fresh,_=analyser.assess(assignment,designs[assignment['task_id']],cases[assignment['task_id']],packets[assignment['task_id']],record,raw)
        if any(row.get(k)!=v for k,v in fresh.items()):raise ValueError('STALE original corrected analysis: '+row['id']+'; refresh v1.0 and v1.1 first')
        enrich(row,assignment,record,'original')
    all_rows=original_rows+rows
    if len(all_rows)!=36 or len({r['id'] for r in all_rows})!=36:raise ValueError('Combined assignments must be36 unique IDs')
    combined=copy.deepcopy(original)
    combined.update(title='Real-document generation',status='internal_generation_with_transport_supplement',
        summary=analyser.summarize(all_rows),rows=all_rows,
        by_configuration=configuration_groups(all_rows,analyser),
        by_task=groups(all_rows,'task_id',analyser),by_repetition=groups(all_rows,'repetition',analyser))
    combined['by_model']=copy.deepcopy(combined['by_configuration'])
    combined['by_model_task_repetition']=[{k:r[k] for k in ('configuration_id','model','provider','cohort','task_id','repetition',*analyser.COUNTS)} for r in all_rows]
    combined['cohorts']=[{'id':'original','assigned_calls':27,'analysis_path':'analysis-corrected.json','manifest_path':'manifest.json'},
        {'id':'transport_supplement','assigned_calls':9,'analysis_path':'analysis-supplement.json','manifest_path':SUPPLEMENT+'/manifest.json'}]
    combined['transport_amendment']='transport-amendment.json'
    combined['supplement_manifest_sha256']=sha(supp/'manifest.json')
    combined['configuration_grouping']='raw_model_id plus pinned serving provider; original and supplemental Google configurations are never pooled'
    combined['limitations']+=supplement_analysis['limitations']
    combined['summary']['not_dispatched_calls']=sum(r['state']=='not_run' for r in all_rows)
    combined['summary']['administratively_stopped_calls']=sum(r.get('stop_reason')=='provider_transport_circuit_breaker' for r in all_rows)
    write(root/'analysis-combined.json',combined)
    return combined


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',nargs='?',type=Path,default=ROOT)
    result=run(parser.parse_args().root)
    print(json.dumps({'summary':result['summary'],'configurations':[r['configuration_id'] for r in result['by_configuration']]}))
