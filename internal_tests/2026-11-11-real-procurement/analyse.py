"""Offline real-document generation analysis against hidden assistant-draft cases.

Literal source-quote matching, structural checks and bounded DSL execution do not
establish semantic accuracy, independent validation or business approval.
"""
from pathlib import Path
import argparse
import hashlib
import json
import statistics
import contracts

ROOT = Path(__file__).resolve().parent
COUNTS = ('assigned_scenarios','assessed_scenarios','matched_scenarios','disagreed_scenarios',
    'missing_scenarios','unassessed_scenarios','assigned_decisions','assessed_decisions',
    'matched_decisions','disagreed_decisions','missing_decisions','unassessed_decisions','unknown_predictions')


def read(path):
    return contracts.parse(path.read_bytes().decode('utf-8'))


def read_archive(path):
    # Source packets can legitimately exceed the generated-response byte limit.
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=contracts.strict_object)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def same(left,right):
    return type(left) is type(right) and left == right


def assess(assignment, design, cases, pages, record, raw):
    names = contracts.output_names(design)
    for case in cases:
        if set(case['expected']) != set(names): raise ValueError('Assessment key output coverage differs')
        if any(not (type(v) is bool or v == 'unknown') for v in case['expected'].values()):
            raise ValueError('Assessment key contains invalid expected value')
    row = {**{k:assignment[k] for k in ('id','model','task_id','repetition')},
        'state':record.get('state','recorded_unknown') if record else 'not_run',
        'access_channel':record.get('access_channel') if record else None,
        'qualified':False,'label_status':'assistant_draft_not_independent_gold',
        'structural_valid':False,'source_quote_match':None,'issues':[],'scenarios':[],
        'cost_usd':record.get('cost_usd') if record else None,
        'cost_status':record.get('cost_status','unknown') if record else 'not_dispatched',
        'elapsed_seconds':record.get('elapsed_seconds') if record else None,
        'returned_provider':record.get('returned_provider') if record else None,
        'provider_request_id':record.get('provider_request_id') if record else None,
        'pinned_provider':record.get('pinned_provider') if record else None,
        'source_pages':sorted(pages),**{name:0 for name in COUNTS}}
    row['assigned_scenarios'] = len(cases)
    row['assigned_decisions'] = len(cases)*len(names)
    if not raw or not raw.strip():
        row['analysis_status'] = 'not_run' if not record else 'no_model_output'
        row['missing_scenarios'],row['missing_decisions'] = len(cases),len(cases)*len(names)
        return row,None
    data,issues = contracts.validate(raw,design,pages)
    row['issues'] = issues
    if issues:
        row['analysis_status'] = 'response_contract_failed'
        row['unassessed_scenarios'],row['unassessed_decisions'] = len(cases),len(cases)*len(names)
        row['source_quote_match'] = False if any(i.startswith('quote:') for i in issues) else None
        return row,data
    row['structural_valid'],row['source_quote_match'] = True,True
    row['analysis_status'] = 'executed_against_assistant_draft_cases'
    for case in cases:
        try:
            actual,trace = contracts.execute(data,case['inputs'],design)
        except contracts.ContractError as error:
            row['unassessed_scenarios'] += 1;row['unassessed_decisions'] += len(names)
            row['scenarios'].append({'id':case['id'],'status':'execution_failed','issues':[str(error)],'inputs':case['inputs']})
            continue
        decisions = []
        for name in names:
            matches = same(actual[name],case['expected'][name])
            row['assessed_decisions'] += 1
            row['matched_decisions' if matches else 'disagreed_decisions'] += 1
            row['unknown_predictions'] += int(actual[name] == 'unknown')
            decisions.append({'output':name,'predicted':actual[name],'draft_expected':case['expected'][name],
                'matches_draft':matches,'trace':trace[name]})
        matched = all(d['matches_draft'] for d in decisions)
        row['assessed_scenarios'] += 1
        row['matched_scenarios' if matched else 'disagreed_scenarios'] += 1
        row['scenarios'].append({'id':case['id'],'status':'executed','inputs':case['inputs'],
            'matches_draft':matched,'decisions':decisions})
    return row,data


def summarize(rows):
    result = {k:sum(r[k] for r in rows) for k in COUNTS}
    result.update(assigned_calls=len(rows),recorded_calls=sum(r['state']!='not_run' for r in rows),
        completed_calls=sum(r['state']=='completed' for r in rows),
        structurally_valid_calls=sum(r['structural_valid'] for r in rows),
        source_quote_match_calls=sum(r['source_quote_match'] is True for r in rows),
        known_cost_usd=sum(r['cost_usd'] for r in rows if type(r['cost_usd']) in (int,float)),
        unknown_cost_count=sum(r['state']!='not_run' and r['cost_usd'] is None for r in rows))
    elapsed = [r['elapsed_seconds'] for r in rows if type(r['elapsed_seconds']) in (int,float)]
    result['median_elapsed_seconds'] = statistics.median(elapsed) if elapsed else None
    result['cost_complete_for_recorded_calls'] = result['unknown_cost_count']==0
    return result


def run(root=ROOT):
    root=Path(root)
    design_path=root/'design/task-design.json';key_path=root/'design/assessment-key.json'
    designs={t['id']:t for t in read_archive(design_path)['tasks']}
    keys={t['task_id']:t['cases'] for t in read_archive(key_path)['tasks']}
    packets={p['id']:p for p in read_archive(root/'source-packets.json')}
    schedule=read_archive(root/'schedule.json')
    if isinstance(schedule,dict):schedule=schedule['assignments']
    if len(schedule)!=27 or len({a['id'] for a in schedule})!=27:
        raise ValueError('Expected exactly27 unique frozen assignments')
    if len(designs)!=3 or any(len(cases)!=12 for cases in keys.values()):
        raise ValueError('Expected3 documents and12 hidden cases/document')
    rows=[]
    for assignment in schedule:
        task=designs[assignment['task_id']];cases=keys[assignment['task_id']]
        pages={item['page']:item['text'] for item in packets[assignment['task_id']]['pages']}
        path=root/'runs'/assignment['id'];record_path=path/'record.json';output_path=path/'output.txt'
        record=read_archive(record_path) if record_path.exists() else None
        raw=output_path.read_bytes().decode('utf-8') if output_path.exists() else None
        if record:
            for name in ('id','model','task_id','repetition'):
                if record.get(name)!=assignment[name]: raise ValueError('Receipt assignment mismatch: '+assignment['id'])
            if record.get('output_sha256') and output_path.exists() and record['output_sha256']!=sha(output_path):
                raise ValueError('Model output hash differs: '+assignment['id'])
            if record.get('cost_usd') is not None and not contracts.typed(record['cost_usd'],{'type':'number','minimum':0}):
                raise ValueError('Invalid recorded cost')
            if record.get('cost_status')=='unknown' and record.get('cost_usd') is not None:
                raise ValueError('Unknown cost cannot be represented by a number')
        row,blueprint=assess(assignment,task,cases,pages,record,raw)
        for name in ('mcp-response.json','get_generation.json','request.json','output.txt','record.json'):
            if (path/name).exists():
                row[name.replace('.','_')+'_path']=(path/name).relative_to(root).as_posix()
                row[name.replace('.','_')+'_sha256']=sha(path/name)
        if raw is not None:
            dest=root/'blueprints'/(assignment['id']+'.json');dest.parent.mkdir(exist_ok=True)
            export={'id':assignment['id'],'model':assignment['model'],'task_id':assignment['task_id'],
                'repetition':assignment['repetition'],'artifact_type':'generated_source_linked_blueprint_draft',
                'business_approval_required':True,'business_approved':False,'qualified':False,
                'export_status':'structurally_usable_model_draft' if row['structural_valid'] else 'unusable_model_draft',
                'source_quote_match':row['source_quote_match'],'issues':row['issues'],'content':blueprint,
                'output_sha256':sha(output_path),'assessment':'hidden_assistant_draft_test_vectors_not_independent_gold'}
            dest.write_text(json.dumps(export,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
            row['blueprint_path']=dest.relative_to(root).as_posix()
        for prefix in ('scenarios','decisions'):
            assert row['assigned_'+prefix] == row['assessed_'+prefix]+row['missing_'+prefix]+row['unassessed_'+prefix]
        rows.append(row)
    groups=lambda field:[{field:value,**summarize([r for r in rows if r[field]==value])} for value in sorted({r[field] for r in rows})]
    return {'title':'Real-document generation','status':'internal_development_generation_study',
        'qualified':False,'independent_human_reviews':0,'assessment_key_status':'assistant_draft_frozen_before_outputs',
        'summary':summarize(rows),'by_model':groups('model'),'by_task':groups('task_id'),'by_repetition':groups('repetition'),
        'by_model_task_repetition':[{k:r[k] for k in ('model','task_id','repetition',*COUNTS)} for r in rows],
        'rows':rows,'input_hashes':{str(f.relative_to(root)):sha(f) for f in (design_path,key_path,root/'source-packets.json',root/'schedule.json')},
        'limitations':['Real public source documents; hidden test vectors and expected outcomes are assistant drafts, not independently adjudicated gold.',
            'Source quote match checks literal presence after whitespace normalization, not semantic entailment or completeness.',
            'DSL outcomes measure generated decision rules on fixed vectors, not a full executable business application or legal advice.',
            'All assigned calls and vector/component denominators remain visible, including missing and malformed responses.',
            'MCP tool envelopes are retained; original HTTP transport response bytes are unavailable through this access channel.',
            'Known costs are provider-reported usage costs; unknown costs remain unknown and no prices are imputed.',
            'No independent validation, model superiority, semantic precision or PALO Blueprint Index is established.']}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path,nargs='?',default=ROOT)
    args=parser.parse_args();result=run(args.root)
    (args.root/'analysis.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(result['summary']))


if __name__=='__main__':main()
