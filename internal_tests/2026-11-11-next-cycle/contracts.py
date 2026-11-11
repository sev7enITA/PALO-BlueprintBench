"""Strict interchange contracts for an internal feasibility run, not semantic gold."""
import json
from jsonschema import Draft202012Validator

LABELS = ['supported', 'contradicted', 'not_established', 'unresolved_conflict']
DECISIONS = ['required', 'not_required', 'permitted', 'prohibited', 'not_established', 'unresolved_conflict']


def obj(properties):
    return {'type': 'object', 'properties': properties, 'required': list(properties), 'additionalProperties': False}


def string(enum=None):
    return {'type': 'string', **({'enum': list(enum)} if enum is not None else {'minLength': 1})}


def array(item, minimum=0, maximum=None):
    out = {'type': 'array', 'items': item, 'minItems': minimum}
    if maximum is not None:
        out['maxItems'] = maximum
    return out


def verification_schema(ids, sources):
    return obj({'items': array(obj({'id': string(ids), 'label': string(LABELS),
        'source_units': array(string(sources)), 'rationale': string()}), len(ids), len(ids))})


def workflow_schema(decisions, sources):
    citations = lambda: array(string(sources), 1)
    return obj({
        'typed_entities_and_identifiers': array(obj({
            'name': string(), 'identifier_status': string(['source_supported', 'proposed_design', 'not_established']),
            'fields': array(obj({'name': string(), 'type': string(), 'source_units': citations()}), 1),
            'source_units': citations()}), 1),
        'decision_predicates': array(obj({'id': string(), 'decision': string(decisions),
            'actor': string(), 'scope': string(), 'condition': string(), 'units': string(),
            'comparison': string(), 'source_units': citations()}), 1),
        'process_transitions': array(obj({'from_state': string(), 'to_state': string(),
            'event': string(), 'guard': string(), 'predicate_ids': array(string(), 1),
            'source_units': citations()}), 1),
        'scenario_decisions': array(obj({'decision': string(decisions), 'disposition': string(DECISIONS),
            'predicate_ids': array(string(), 1), 'source_units': citations(), 'rationale': string()}), len(decisions), len(decisions)),
        'unresolved_questions': array(string()),
    })


def unique_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('Duplicate JSON key: ' + key)
        out[key] = value
    return out


def parse(raw):
    return json.loads(raw, object_pairs_hook=unique_object,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Non-finite JSON value: ' + value)))


def validate(raw, task):
    """Return parsed value plus defects. No JSON repairs or partial semantic scoring."""
    try:
        data = parse(raw)
    except (ValueError, TypeError) as exc:
        return None, ['json_parse: ' + str(exc)]
    issues = ['schema: ' + '/'.join(map(str, e.absolute_path)) + ': ' + e.message
        for e in Draft202012Validator(task['response_schema']).iter_errors(data)]
    if issues:
        return data, issues
    workflow = task['track'] == 'workflow'
    rows = data['scenario_decisions'] if workflow else data['items']
    field = 'decision' if workflow else 'id'
    ids = [row[field] for row in rows]
    if len(set(ids)) != len(ids) or set(ids) != set(task['expected_ids']):
        issues.append('coverage: duplicate, missing or extra item identifiers')
    sources = set(task['source_units'])
    if not workflow:
        for row in rows:
            refs = row['source_units']
            if len(refs) != len(set(refs)) or not set(refs) <= sources:
                issues.append('citations: invalid/duplicate source reference for ' + row['id'])
            if row['label'] != 'not_established' and not refs:
                issues.append('citations: judgment requires a cited source for ' + row['id'])
            if task['track'] == 'legacy' and any(not ref.startswith(row['id'] + ':') for ref in refs):
                issues.append('citations: legacy item references another item source')
    else:
        predicates = data['decision_predicates']
        pids = [row['id'] for row in predicates]
        if len(pids) != len(set(pids)):
            issues.append('predicates: duplicate identifiers')
        for row in data['process_transitions'] + rows:
            if not set(row['predicate_ids']) <= set(pids) or len(row['predicate_ids']) != len(set(row['predicate_ids'])):
                issues.append('predicates: unknown/duplicate predicate references')
        by_id = {p['id']: p for p in predicates}
        for row in rows:
            if not any(by_id.get(pid, {}).get('decision') == row['decision'] for pid in row['predicate_ids']):
                issues.append('predicates: decision lacks a matching predicate: ' + row['decision'])
        def inspect(value):
            if isinstance(value, dict):
                if 'source_units' in value:
                    refs = value['source_units']
                    if len(refs) != len(set(refs)) or not set(refs) <= sources:
                        issues.append('citations: invalid/duplicate workflow source reference')
                for child in value.values(): inspect(child)
            elif isinstance(value, list):
                for child in value: inspect(child)
        inspect(data)
    return data, issues
