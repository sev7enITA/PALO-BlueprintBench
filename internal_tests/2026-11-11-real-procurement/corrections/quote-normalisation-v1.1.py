"""Post-collection, versioned mechanical quote-check correction.

Never edits frozen sources, prompts, expectations, contracts or raw model outputs.
The sole change joins ASCII letter + hyphen + one line ending + ASCII letter,
retaining the hyphen, before the existing whitespace normalization.
"""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import re
import shutil
import sys
import tempfile

VERSION='quote-normalisation-v1.1'
ROOT=Path(__file__).resolve().parents[1]
LINEWRAP=re.compile(r'(?<=[A-Za-z])-[ \t]*(?:\r\n|\n|\r)[ \t]*(?=[A-Za-z])')


def normalized_v11(value):
    return re.sub(r'\s+',' ',LINEWRAP.sub('-',value)).strip()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False) as handle:
        handle.write(json.dumps(value,indent=2,ensure_ascii=False)+'\n');temporary=Path(handle.name)
    temporary.replace(path)


def modules(root):
    spec=importlib.util.spec_from_file_location('quote_v11_frozen_contracts',root/'contracts.py')
    contracts=importlib.util.module_from_spec(spec);spec.loader.exec_module(contracts)
    previous=sys.modules.get('contracts');sys.modules['contracts']=contracts
    try:
        spec=importlib.util.spec_from_file_location('quote_v11_frozen_analyse',root/'analyse.py')
        analyser=importlib.util.module_from_spec(spec);spec.loader.exec_module(analyser)
    finally:
        if previous is None:sys.modules.pop('contracts',None)
        else:sys.modules['contracts']=previous
    return contracts,analyser


def snapshot(root,dest):
    for name in ('design/task-design.json','design/assessment-key.json','source-packets.json','schedule.json'):
        target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,target)
    receipts=[]
    for folder in sorted((root/'runs').iterdir()) if (root/'runs').exists() else []:
        if not folder.is_dir() or not (folder/'record.json').exists():continue
        before=(folder/'record.json').read_bytes();record=json.loads(before)
        target=dest/'runs'/folder.name;target.mkdir(parents=True)
        for source in folder.iterdir():
            if source.is_file():shutil.copyfile(source,target/source.name)
        if before!=(folder/'record.json').read_bytes():raise ValueError('Receipt changed during snapshot')
        for name,key in (('output.txt','output_sha256'),('request.json','request_sha256')):
            if record.get(key) and (target/name).exists() and sha(target/name)!=record[key]:
                raise ValueError('Receipt hash mismatch during snapshot: '+folder.name+'/'+name)
        receipts.append({'id':record['id'],'state':record['state'],'cost_status':record.get('cost_status'),'record_sha256':sha(target/'record.json'),
            'output_sha256':sha(target/'output.txt') if (target/'output.txt').exists() else None})
    return receipts


def quote_changes(blueprint,pages,old_normalized):
    changes=[]
    def walk(value,path=''):
        if isinstance(value,dict):
            if 'quote' in value and 'source_pages' in value:
                refs=value['source_pages'];quote=value['quote']
                old=any(old_normalized(quote) in old_normalized(pages.get(page,'')) for page in refs)
                new=any(normalized_v11(quote) in normalized_v11(pages.get(page,'')) for page in refs)
                if old!=new:changes.append({'path':path,'source_pages':refs,'quote':quote,
                    'v1_0_source_quote_match':old,'v1_1_source_quote_match':new})
            for key,child in value.items():walk(child,path+'/'+key)
        elif isinstance(value,list):
            for i,child in enumerate(value):walk(child,path+'/'+str(i))
    walk(blueprint)
    return changes


def run(root=ROOT):
    root=Path(root);manifest=load(root/'manifest.json')
    frozen={name:sha(root/name) for name in manifest['files']}
    if frozen!=manifest['files']:raise ValueError('Frozen manifest does not match before replay')
    manifest_hash=sha(root/'manifest.json')
    original_analysis_hash=sha(root/'analysis.json') if (root/'analysis.json').exists() else None
    original_blueprints={p.name:sha(p) for p in (root/'blueprints').glob('*.json')}
    contracts,analyser=modules(root);old_normalized=contracts.normalized
    with tempfile.TemporaryDirectory(prefix='palo-quote-v11-') as temporary:
        isolated=Path(temporary);receipts=snapshot(root,isolated)
        before=analyser.run(isolated)
        contracts.normalized=normalized_v11
        after=analyser.run(isolated)
        packets={p['id']:{x['page']:x['text'] for x in p['pages']} for p in load(isolated/'source-packets.json')}
        original_rows={r['id']:r for r in before['rows']};affected=[]
        fields=('structural_valid','source_quote_match','issues','assessed_scenarios','unassessed_scenarios',
            'assessed_decisions','matched_decisions','disagreed_decisions','unassessed_decisions')
        for row in after['rows']:
            old=original_rows[row['id']]
            differences={key:{'v1_0':old[key],'v1_1':row[key]} for key in fields if old[key]!=row[key]}
            if differences:
                output=isolated/'runs'/row['id']/'output.txt'
                data=contracts.parse(output.read_text(encoding='utf-8'))
                affected.append({'id':row['id'],'task_id':row['task_id'],'output_sha256':sha(output),
                    'differences':differences,'quote_changes':quote_changes(data,packets[row['task_id']],old_normalized)})
            if 'blueprint_path' in row:
                source=isolated/row['blueprint_path'];artifact=load(source)
                artifact['checker_revision']=VERSION
                artifact['correction_status']='postcollection_mechanical_quote_check_correction'
                row['blueprint_path']='blueprints-corrected/'+source.name
                write(root/row['blueprint_path'],artifact)
        after['checker_revision']=VERSION
        after['correction_note']='corrections/correction-note.json'
        after['original_analysis']='analysis.json'
        after['correction_status']='postcollection_mechanical_quote_check_correction_not_gold_change'
        before['checker_revision']='frozen-v1.0-replayed'
        write(root/'corrections/analysis-v1.0-replayed.json',before)
        write(root/'analysis-corrected.json',after)
    frozen_after={name:sha(root/name) for name in manifest['files']}
    if frozen_after!=frozen or sha(root/'manifest.json')!=manifest_hash:
        raise ValueError('Frozen inputs changed during correction replay')
    # Existing original analysis and exports may be refreshed by the collector,
    # but this tool never writes them. Report snapshot hashes instead of asserting
    # their immutability while collection is active.
    prior=load(root/'corrections/correction-note.json') if (root/'corrections/correction-note.json').exists() else {}
    note={'id':VERSION,'status':'postcollection_mechanical_checker_correction','qualified':False,
        'first_observed_on':prior.get('first_observed_on','2026-11-11'),
        'first_documented_at':prior.get('first_documented_at',dt.datetime.now(dt.timezone.utc).isoformat()),
        'updated_at':dt.datetime.now(dt.timezone.utc).isoformat(),
        'trigger':'fta-m0-r1 requirement R25: source micro-hyphen-newline-purchase versus quoted micro-purchase.',
        'scope':'Join ASCII-letter hyphen followed by exactly one CRLF/LF/CR line ending and optional horizontal spaces before an ASCII letter; retain the hyphen; then original whitespace normalization.',
        'excluded_transformations':['hyphen removal','multiple-newline joining','space-only joining','Unicode dash folding','case folding','paraphrase','word deletion','semantic label changes'],
        'source_output_or_gold_edits':False,'prompts_changed':False,'additional_model_calls':0,
        'manifest_sha256':manifest_hash,'frozen_hashes_unchanged':True,
        'original_analysis_sha256_at_snapshot':original_analysis_hash,
        'original_blueprints_sha256_at_snapshot':original_blueprints,
        'baseline_replay_path':'corrections/analysis-v1.0-replayed.json',
        'baseline_replay_sha256':sha(root/'corrections/analysis-v1.0-replayed.json'),
        'corrected_analysis_path':'analysis-corrected.json','corrected_analysis_sha256':sha(root/'analysis-corrected.json'),
        'comparison_scope':{'assigned_calls':27,'snapshot_record_files':len(receipts),
            'recorded_snapshot_calls':after['summary']['recorded_calls'],'dispatched_calls':after['summary']['recorded_calls'],
            'administrative_not_run_records':sum(r['state']=='not_run' for r in receipts),
            'missing_record_files':27-len(receipts),'not_dispatched_assignments':27-after['summary']['recorded_calls'],
            'missing_assignments_retained':27-after['summary']['recorded_calls'],'uniform_all_assignments':True},
        'summary_before':before['summary'],'summary_after':after['summary'],'affected_rows':affected,
        'receipts':receipts,'remaining_contract_failures':[{'id':r['id'],'issues':r['issues']} for r in after['rows'] if r['issues']],
        'interpretation':'Mechanical source-quote presence correction only. No semantic entailment, draft-key correctness or independent validation is established.'}
    write(root/'corrections/correction-note.json',note)
    lines=['# Quote-check correction v1.1','',
        'This is a post-collection mechanical checker correction. Frozen source documents, prompts, expected outcomes and raw model outputs are unchanged. It does not change the assistant-draft assessment key or establish independent validation.','',
        '## Cause and scope','',
        'First observed on 11 November 2026 in FTA requirement R25: the PDF text wraps `micro-` and `purchase` across one line ending, while the model quotes `micro-purchase`. The v1.0 whitespace-only check leaves an extra space and rejects the otherwise identical quotation. FEMA also contains `Anti-` / `Kickback` with the same typography.','',
        'Version 1.1 joins only an ASCII-letter hyphen, optional horizontal whitespace, exactly one line ending and optional horizontal whitespace before another ASCII letter. It retains the hyphen. No case folding, paraphrase, word deletion, generic hyphen removal or multiple-line joining is performed.','',
        '## Uniform replay','',f"All 27 assignments are retained. This snapshot contains {len(receipts)} record files: {after['summary']['recorded_calls']} dispatched calls and {sum(r['state']=='not_run' for r in receipts)} administrative not-run records. {27-len(receipts)} assignments do not yet have a record file. Frozen v1.0 and corrected v1.1 are replayed on the same receipt snapshot in an isolated temporary directory. The original analysis and blueprint directory are never overwritten by this tool.",'',
        '| Measure | Frozen v1.0 replay | Corrected v1.1 |','| --- | ---: | ---: |']
    for key in ('structurally_valid_calls','assessed_decisions','matched_decisions','disagreed_decisions','unassessed_decisions','missing_decisions'):
        lines.append(f"| {key} | {before['summary'][key]} | {after['summary'][key]} |")
    lines += ['','Affected receipt IDs: '+(', '.join(x['id'] for x in affected) or 'none in this snapshot')+'.','',
        'The JSON companion preserves before/after issues, quote locators, receipt hashes and frozen-manifest identity. `analysis.json` and `blueprints/` retain the original checker output; `analysis-corrected.json` and `blueprints-corrected/` are the versioned corrected view. All other parse, schema, type, dependency and source-quote failures remain failures.','',
        'Run: `python corrections/quote-normalisation-v1.1.py`','',
        'Tests: `python -m unittest discover -s corrections -p test_quote_normalisation_v11.py -v`','']
    (root/'corrections/correction-note.md').write_text('\n'.join(lines),encoding='utf-8')
    return note


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',nargs='?',type=Path,default=ROOT)
    args=parser.parse_args();result=run(args.root)
    print(json.dumps({'revision':VERSION,'affected_rows':[r['id'] for r in result['affected_rows']],
        'snapshot_record_files':result['comparison_scope']['snapshot_record_files'],'dispatched_calls':result['comparison_scope']['dispatched_calls'],'summary_after':result['summary_after']}))
