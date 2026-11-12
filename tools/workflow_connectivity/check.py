"""Post-hoc weak connectivity diagnostics; never changes frozen scores."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def assess(nodes, edges):
    if not nodes:
        return {'status': 'unassessed', 'reason': 'no identifiable nodes'}
    if any(a not in nodes or b not in nodes for a, b in edges):
        return {'status': 'unassessed', 'reason': 'edge refers to an unknown node'}
    neighbours = {node: set() for node in nodes}
    for a, b in edges:
        neighbours[a].add(b)
        neighbours[b].add(a)
    remaining, components = set(nodes), []
    while remaining:
        stack, component = [min(remaining)], set()
        while stack:
            node = stack.pop()
            if node in component:
                continue
            component.add(node)
            stack.extend(neighbours[node] - component)
        remaining -= component
        components.append(sorted(component))
    return {'status': 'connected' if len(components) == 1 else 'disconnected',
            'nodes': len(nodes), 'edges': len(edges), 'components': components}


def dependency_graph(data):
    if not isinstance(data, dict):
        return {'status': 'unassessed', 'reason': 'output is not an object'}
    process = data.get('process')
    if not isinstance(process, list) or not process:
        return {'status': 'unassessed', 'reason': 'process missing'}
    try:
        ids = [p['id'] for p in process]
        if len(ids) != len(set(ids)) or not all(isinstance(i, str) for i in ids):
            raise ValueError('duplicate or invalid step ID')
        edges = [(step['id'], parent) for step in process for parent in step['requires']]
        return assess(set(ids), edges)
    except (KeyError, TypeError, ValueError):
        return {'status': 'unassessed', 'reason': 'invalid step dependencies'}


def transition_graph(data):
    if not isinstance(data, dict):
        return {'status': 'unassessed', 'reason': 'output is not an object'}
    transitions = data.get('process_transitions')
    if not isinstance(transitions, list) or not transitions:
        return {'status': 'unassessed', 'reason': 'transitions missing'}
    try:
        edges = [(t['from_state'], t['to_state']) for t in transitions]
        if not all(isinstance(v, str) and v.strip() for edge in edges for v in edge):
            raise ValueError('invalid state')
        return assess({v for edge in edges for v in edge}, edges)
    except (KeyError, TypeError, ValueError):
        return {'status': 'unassessed', 'reason': 'invalid transitions'}


def report():
    rows = []
    for folder, analysis, field, parser in [
        ('internal_tests/2026-11-11-real-procurement', 'analysis-corrected.json', 'rows', dependency_graph),
        ('internal_tests/2026-11-11-next-cycle', 'analysis.json', 'attempts', transition_graph),
    ]:
        root = ROOT / folder
        data = json.loads((root / analysis).read_text(encoding='utf-8'))
        for row in data[field]:
            if field == 'attempts' and row.get('track') != 'workflow':
                continue
            path = root / 'runs' / row['id'] / 'output.txt'
            result = {'status': 'unassessed', 'reason': 'no complete captured output'}
            if row.get('state') == 'completed' and path.exists():
                try:
                    result = parser(json.loads(path.read_text(encoding='utf-8')))
                except (ValueError, TypeError):
                    result = {'status': 'unassessed', 'reason': 'output is not valid JSON object'}
            rows.append({'study': folder.split('/')[-1], 'id': row['id'],
                         'original_structural_valid': row.get('structural_valid'),
                         'output_sha256': hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,
                         'connectivity': result})
    return {'version': '0.1.0', 'status': 'posthoc_internal_diagnostic', 'qualified': False,
            'method': 'Weak connectivity on explicitly represented dependency steps or transition endpoints; isolated states omitted by a model cannot be observed. No required initial or terminal state is supplied. Connectivity does not establish correct branches, reachability under guards, source fidelity or completeness. Disconnected components require review and are not automatic failures.',
            'historical_scores_changed': False, 'rows': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--check', action='store_true'); args = parser.parse_args()
    output = ROOT / 'docs/workflow-connectivity-diagnostic.json'
    text = json.dumps(report(), indent=2, ensure_ascii=False) + '\n'
    if args.check:
        if output.read_text(encoding='utf-8') != text:
            raise SystemExit('Connectivity report differs from retained outputs')
    else:
        output.write_text(text, encoding='utf-8')
    print('Workflow connectivity diagnostic verified' if args.check else 'Workflow connectivity diagnostic generated')
