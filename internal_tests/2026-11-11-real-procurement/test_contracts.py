"""Adversarial contract and execution checks; never contact a provider."""
import copy
import json
from pathlib import Path
import unittest
import tempfile
import contracts
import analyse

DESIGN={'id':'fixture','input_fields':{'amount':{'type':'number','minimum':0},'threshold':{'type':'number','minimum':0},
    'approved':{'type':'boolean'},'authority':{'type':'string'},'category':{'type':'string'}},'required_outputs':['eligible','notify']}
PAGES={9:'Approval is required above the applicable threshold. Notice may be sent by the authority.',12:'The agency shall maintain a complete procurement record.'}
CITE={'source_pages':[9],'quote':'Approval is required above the applicable threshold.'}


def blueprint():
    return {'requirements':[{'id':'R1','actor':'agency','modality':'obligation','statement':'Approval above threshold.',**CITE}],
        'process':[{'id':'S1','action':'Review approval','requires':[],**CITE}],
        'outputs':{'eligible':{'rules':[{'when':{'all':[{'field':'amount','op':'gt','value':{'field':'threshold'}},
            {'not':{'field':'approved','op':'eq','value':True}}]},'value':False,**CITE}], 'default':True},
            'notify':{'rules':[],'default':'unknown'}}}


def inputs(**changes):
    return {'amount':100,'threshold':100,'approved':False,'authority':'agency','category':'agency',**changes}


def cases():
    return [{'id':'a','inputs':inputs(),'expected':{'eligible':True,'notify':'unknown'}},
        {'id':'b','inputs':inputs(amount=101),'expected':{'eligible':False,'notify':'unknown'}}]


class ContractsTests(unittest.TestCase):
    def test_strict_valid_contract_and_boundary_execution(self):
        data,issues=contracts.validate(json.dumps(blueprint()),DESIGN,PAGES)
        self.assertEqual([],issues)
        self.assertEqual({'eligible':True,'notify':'unknown'},contracts.execute(data,inputs(),DESIGN)[0])
        self.assertFalse(contracts.execute(data,inputs(amount=101),DESIGN)[0]['eligible'])
        self.assertTrue(contracts.execute(data,inputs(amount=101,threshold=102),DESIGN)[0]['eligible'])
        self.assertTrue(contracts.execute(data,inputs(amount=101,approved=True),DESIGN)[0]['eligible'])

    def test_first_match_and_explicit_unknown(self):
        data=blueprint();rule={'when':{'field':'amount','op':'gte','value':100},'value':'unknown',**CITE}
        data['outputs']['eligible']['rules'].insert(0,rule)
        value,trace=contracts.execute(data,inputs(amount=101),DESIGN)
        self.assertEqual('unknown',value['eligible']);self.assertEqual(0,trace['eligible']['matched_rule_index'])
        self.assertTrue(trace['notify']['used_default'])

    def test_no_boolean_numeric_or_invalid_input_coercion(self):
        data=blueprint()
        for vector in (inputs(amount=True),inputs(approved=1),inputs(amount=float('nan')),{'amount':10},inputs(extra=1)):
            with self.assertRaises(contracts.ContractError): contracts.execute(data,vector,DESIGN)
        data['outputs']['eligible']['rules'][0]['when']={'field':'amount','op':'eq','value':True}
        self.assertTrue(contracts.validate(json.dumps(data),DESIGN,PAGES)[1])

    def test_cross_field_types_unknown_fields_and_numeric_order(self):
        valid={'field':'authority','op':'eq','value':{'field':'category'}}
        contracts.check_expression(valid,DESIGN)
        self.assertTrue(contracts.evaluate_expression(valid,inputs()))
        for atom in ({'field':'amount','op':'gt','value':{'field':'approved'}},
            {'field':'authority','op':'lt','value':{'field':'category'}},
            {'field':'amount','op':'gt','value':{'field':'missing'}},
            {'field':'amount','op':'gt','value':{'field':'threshold','extra':True}},
            {'field':'amount','op':'eval','value':'__import__("os")'}):
            with self.assertRaises(contracts.ContractError): contracts.check_expression(atom,DESIGN)

    def test_quotes_need_actual_cited_page_and_allow_whitespace_only(self):
        data=blueprint();data['requirements'][0]['quote']='Approval\n is required above the applicable threshold.'
        self.assertEqual([],contracts.validate(json.dumps(data),DESIGN,PAGES)[1])
        data['requirements'][0]['source_pages']=[12]
        self.assertTrue(any(i.startswith('quote:') for i in contracts.validate(json.dumps(data),DESIGN,PAGES)[1]))
        data=blueprint();data['requirements'][0]['quote']='Approval is not required above the applicable threshold.'
        self.assertTrue(contracts.validate(json.dumps(data),DESIGN,PAGES)[1])

    def test_duplicate_keys_nonfinite_and_markdown_not_salvaged(self):
        for raw in ('{"a":1,"a":2}','{"a":1e999}','{"a":NaN}', '{"a":'+str(10**400)+'}','```json\n{}\n```'):
            self.assertTrue(contracts.validate(raw,DESIGN,PAGES)[1])
        with self.assertRaises(contracts.ContractError): contracts.parse('['*40+'0'+']'*40)

    def test_process_dag_full_outputs_and_duplicate_ids(self):
        mutations=[]
        data=blueprint();data['process'][0]['requires']=['S1'];mutations.append(data)
        data=blueprint();data['process'][0]['requires']=['missing'];mutations.append(data)
        data=blueprint();data['requirements']*=2;mutations.append(data)
        data=blueprint();del data['outputs']['notify'];mutations.append(data)
        data=blueprint();data['outputs']['notify']['default']=0;mutations.append(data)
        for data in mutations: self.assertTrue(contracts.validate(json.dumps(data),DESIGN,PAGES)[1])

    def test_malformed_outputs_are_unassessed_not_missing_or_false(self):
        assignment={'id':'one','model':'fixture','task_id':'fixture','repetition':1}
        missing,_=analyse.assess(assignment,DESIGN,cases(),PAGES,None,None)
        bad,_=analyse.assess(assignment,DESIGN,cases(),PAGES,{'state':'completed'},'{}')
        good,_=analyse.assess(assignment,DESIGN,cases(),PAGES,{'state':'completed'},json.dumps(blueprint()))
        self.assertEqual(4,missing['missing_decisions']);self.assertEqual(4,bad['unassessed_decisions'])
        self.assertEqual(0,bad['assessed_decisions']);self.assertEqual(4,good['matched_decisions'])
        self.assertEqual(2,good['unknown_predictions'])
        summary=analyse.summarize([missing,bad,good]);self.assertEqual(12,summary['assigned_decisions'])
        self.assertEqual(2,summary['unknown_cost_count']);self.assertEqual(0,summary['known_cost_usd'])

    def test_mismatch_is_draft_disagreement_with_per_output_trace(self):
        data=blueprint();data['outputs']['notify']['default']=False
        row,_=analyse.assess({'id':'one','model':'fixture','task_id':'fixture','repetition':1},DESIGN,cases(),PAGES,{'state':'completed'},json.dumps(data))
        self.assertEqual(2,row['disagreed_decisions']);self.assertEqual(0,row['matched_scenarios'])
        self.assertFalse(row['qualified']);self.assertTrue(row['source_quote_match'])

    def test_full_schedule_preserves_all_component_denominators(self):
        root=Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory);(path/'design').mkdir()
            for name in ('task-design.json','assessment-key.json'):
                (path/'design'/name).write_bytes((root/'design'/name).read_bytes())
            (path/'source-packets.json').write_bytes((root/'source-packets.json').read_bytes())
            designs=analyse.read_archive(root/'design/task-design.json')['tasks']
            packets={p['id']:p for p in analyse.read_archive(root/'source-packets.json')}
            schedule=[]
            for design in designs:
                for model in ('fixture/a','fixture/b','fixture/c'):
                    for repetition in (1,2,3):
                        schedule.append({'id':str(len(schedule)+1),'task_id':design['id'],'model':model,'repetition':repetition})
            (path/'schedule.json').write_text(json.dumps(schedule),encoding='utf-8')
            design=designs[0];source=packets[design['id']]['pages'][0]
            quote=contracts.normalized(source['text'])[:80]
            cite={'source_pages':[source['page']],'quote':quote}
            draft={'requirements':[{'id':'r','actor':'fixture','modality':'definition','statement':'Fixture only',**cite}],
                'process':[{'id':'s','action':'Fixture only','requires':[],**cite}],
                'outputs':{name:{'rules':[],'default':'unknown'} for name in design['required_outputs']}}
            for item,output in ((schedule[0],json.dumps(draft)),(schedule[1],'{}')):
                folder=path/'runs'/item['id'];folder.mkdir(parents=True)
                record={**item,'state':'completed','cost_status':'unknown','cost_usd':None}
                (folder/'record.json').write_text(json.dumps(record),encoding='utf-8')
                (folder/'output.txt').write_text(output,encoding='utf-8')
            report=analyse.run(path);summary=report['summary']
            self.assertEqual(27,summary['assigned_calls']);self.assertEqual(324,summary['assigned_scenarios'])
            self.assertEqual(1188,summary['assigned_decisions'])
            first=12*len(design['required_outputs'])
            self.assertEqual(first,summary['assessed_decisions']);self.assertEqual(first,summary['unassessed_decisions'])
            self.assertEqual(1188-2*first,summary['missing_decisions']);self.assertEqual(2,summary['unknown_cost_count'])
            self.assertEqual(2,len(list((path/'blueprints').glob('*.json'))))
            for export in (path/'blueprints').glob('*.json'):
                artifact=analyse.read_archive(export);self.assertFalse(artifact['qualified']);self.assertTrue(artifact['business_approval_required'])

    def test_actual_design_cases_and_quotes_preflight(self):
        root=Path(__file__).resolve().parent
        if not (root/'design/assessment-key.json').exists():self.skipTest('Design not yet frozen')
        designs={x['id']:x for x in analyse.read_archive(root/'design/task-design.json')['tasks']}
        keys=analyse.read_archive(root/'design/assessment-key.json')['tasks']
        packets={p['id']:p for p in analyse.read_archive(root/'source-packets.json')}
        self.assertEqual(3,len(keys));total=0
        for key in keys:
            design=designs[key['task_id']];pages={p['page']:p['text'] for p in packets[key['task_id']]['pages']}
            self.assertEqual(12,len(key['cases']))
            contracts.Draft202012Validator.check_schema(contracts.response_schema(design,pages))
            for case in key['cases']:
                self.assertEqual(set(design['input_fields']),set(case['inputs']))
                for name,spec in design['input_fields'].items():self.assertTrue(contracts.typed(case['inputs'][name],spec),(case['id'],name))
                self.assertEqual(set(design['required_outputs']),set(case['expected']))
                total+=len(case['expected'])
                for evidence in case['evidence'].values():
                    self.assertTrue(any(contracts.normalized(evidence['quote']) in contracts.normalized(pages[page]) for page in evidence['source_pages']))
        self.assertEqual(132,total)


if __name__=='__main__':unittest.main()
