"""Publish a separate, explicitly provisional next-cycle feasibility view."""
from pathlib import Path
import argparse
import hashlib
import io
import zipfile
import json
import re
import research_publication

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'internal_tests/2026-11-11-next-cycle'
DL = ROOT / 'web/downloads/blueprintbench'
REVISION = '2026-11-11.4'
URL = 'https://paloframework.org/PALO_BlueprintBench_NextCycle.html'


def load(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def select_input(name):
    for folder in ['inputs', 'frozen-inputs', 'source']:
        candidate = BASE / folder / name
        if candidate.exists():
            return candidate
    return ROOT / 'study/next-cycle' / name


def enrich_usage(analysis):
    """Add receipt observations to the publication without changing frozen analysis."""
    if analysis is None:
        return
    token_paths = {
        'prompt_tokens': ('prompt_tokens',),
        'completion_tokens': ('completion_tokens',),
        'total_tokens': ('total_tokens',),
        'reasoning_tokens': ('completion_tokens_details', 'reasoning_tokens'),
        'cached_tokens': ('prompt_tokens_details', 'cached_tokens'),
        'cache_write_tokens': ('prompt_tokens_details', 'cache_write_tokens'),
    }
    for row in analysis['attempts']:
        receipt = {}
        if row.get('record_path'):
            path = (BASE / row['record_path']).resolve()
            path.relative_to(BASE.resolve())
            receipt = load(path, {})
            for key in ['id', 'task_id', 'model', 'state']:
                if receipt.get(key) != row.get(key):
                    raise ValueError('Analysis/receipt identity mismatch: ' + row['id'] + ' ' + key)
        usage = receipt.get('usage') or {}
        for field, parts in token_paths.items():
            value = usage
            for part in parts:
                value = value.get(part) if isinstance(value, dict) else None
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise ValueError('Invalid provider token count: ' + row['id'] + ' ' + field)
            row[field] = value
        for field in ['returned_model', 'returned_provider', 'provider_request_id']:
            value = receipt.get(field)
            if value is not None and not isinstance(value, str):
                raise ValueError('Invalid returned identity: ' + row['id'] + ' ' + field)
            row[field] = value
        row['usage_status'] = 'provider_reported' if all(row[k] is not None for k in token_paths) else 'partially_reported' if any(row[k] is not None for k in token_paths) else 'unavailable'


def build():
    analysis = load(BASE / 'analysis.json')
    enrich_usage(analysis)
    if analysis:
        for row in analysis.get('attempts', []):
            for judgment in row.get('judgments', []):
                original = judgment.get('rationale', '')
                if '\u2014' in original:
                    judgment['rationale_original_sha256'] = hashlib.sha256(original.encode('utf-8')).hexdigest()
                    judgment['rationale'] = original.replace('\u2014', ', ')
                    judgment['rationale_display_normalised'] = True
    bank_path = select_input('case-bank.json')
    bank = load(bank_path)
    workflows = load(select_input('workflow-tasks.json'))
    metamorphic = load(select_input('metamorphic-checks.json'))
    publication = load(BASE / 'publication.json', {})
    provenance = load(ROOT / 'study/next-cycle/adjudication/custodian-provenance.json', {})
    legacy_identity_map = {'purpose': 'Display-only crosswalk for retained advisory responses, not included in model requests.',
        'items': [{'review_item': item['review_item'], 'original_probe_id': item['original_probe_id']}
                  for item in provenance.get('items', [])]}
    if set((item['review_item'], item['original_probe_id']) for item in legacy_identity_map['items']) != {('ITEM-A', 'P002'), ('ITEM-B', 'P013'), ('ITEM-C', 'P036')}:
        raise ValueError('Legacy display crosswalk must match the three retained original probes')
    data = {
        'revision': REVISION,
        'display_normalisation': 'Model rationale em dashes are replaced with commas in this presentation copy. Original response and analysis bytes remain unchanged in the evidence archive and Git links.',
        'status': analysis.get('status', 'internal_engineering_feasibility') if analysis else 'not_executed',
        'qualified': False,
        'independent_human_reviews': 0,
        'authoring_groups': 1,
        'independent_source_families': 0,
        'case_bank_sha256': hashlib.sha256(bank_path.read_bytes()).hexdigest(),
        'source_reference': publication.get('source_reference', 'main'),
        'campaign_path': 'internal_tests/2026-11-11-next-cycle',
        'case_bank': bank,
        'workflow_tasks': workflows,
        'metamorphic_design': metamorphic,
        'analysis': analysis,
        'legacy_identity_map': legacy_identity_map,
        'postrun_semantic_observations': load(BASE / 'review/postrun-semantic-observations.json'),
        'counterfactual_advisory': load(BASE / 'review/counterfactual-advisory-review.json'),
        'configurations': [{key: model.get(key) for key in ['id', 'name', 'provider']} for model in load(BASE / 'models.json', [])],
        'task_packets': [{'id': t['id'], 'case_id': t['case_id'], 'track': t['track'],
                          'source_packet_sha256': t.get('source_packet_sha256'),
                          'unscored_probe_ids': t.get('unscored_probe_ids', []),
                          'packet': json.loads(next(m['content'] for m in t['messages'] if m['role'] == 'user'))}
                         for t in load(BASE / 'tasks.json', [])],
        'budget': load(BASE / 'budget-final.json'),
        'protocol': load(BASE / 'manifest.json', load(BASE / 'protocol.json', load(BASE / 'freeze.json', {}))),
        'limitations': [
            'Six fictional scenarios belong to one automated authoring provenance group, not six independent business families.',
            'Draft labels and workflow expectations have not been adjudicated by independent human experts.',
            'A source-bound structured draft is not an approved business blueprint or a Workbench application end-to-end result.',
            'Missing requests, malformed responses, unassessed judgments and label disagreements remain distinct.',
            'One-repetition engineering feasibility does not establish uncertainty, generalisation or model superiority.',
            'Model reviews of P002, P013 and P036 are advisory. The separate human annotation templates remain unfilled.',
        ],
    }
    if len(bank['cases']) != 6 or sum(len(c['probes']) for c in bank['cases']) != 48:
        raise ValueError('Publication scope must be six cases and 48 provisional propositions')
    if analysis:
        if analysis.get('qualified') is not False:
            raise ValueError('Next-cycle analysis must explicitly remain unqualified')
        if analysis.get('independent_human_reviews', 0) != 0:
            raise ValueError('This publication path does not verify independent human identities')
        for name in ['tasks', 'schedule']:
            path = BASE / (name + '.json')
            if analysis.get('inputs', {}).get(name + '_sha256') != hashlib.sha256(path.read_bytes()).hexdigest():
                raise ValueError('Analysis/input hash mismatch: ' + name)
        if analysis['assigned_requests'] != len(analysis['attempts']):
            raise ValueError('Assigned requests must retain all observed and missing records')
        data['limitations'] = list(dict.fromkeys(data['limitations'] + analysis.get('limitations', [])))
    advisory = data['postrun_semantic_observations']
    if advisory and any(advisory.get(key) is not False for key in ['qualified', 'independent_human_review', 'original_labels_changed', 'retroactive_exclusions_added']):
        raise ValueError('Postrun advisory cannot imply qualification or silently modify the frozen key')
    counterfactual = data['counterfactual_advisory']
    if counterfactual:
        if counterfactual.get('qualified') is not False or counterfactual.get('independent_human_review') is not False:
            raise ValueError('Counterfactual review must remain internal advisory evidence')
        if any(counterfactual.get('preservation', {}).get(key) is not False for key in ['frozen_keys_changed', 'counts_changed', 'retroactive_exclusions_added', 'majority_vote_used_as_gold']):
            raise ValueError('Counterfactual advisory must preserve frozen counts and expectations')
    for relative, expected in data['protocol'].get('files', {}).items():
        if relative in ['tasks.json', 'schedule.json', '../../study/next-cycle/case-bank.json']:
            if hashlib.sha256((BASE / relative).read_bytes()).hexdigest() != expected:
                raise ValueError('Frozen source hash mismatch: ' + relative)
    return data


def schema(data):
    observed = bool(data['analysis'] and data['analysis']['recorded_requests'] > 0)
    description = ('Observed results from the 6-process synthetic test: 48 provisional propositions, workflow outputs, paired input variations and advisory label reviews.' if observed else 'Prepared fictional process descriptions; no execution outcomes are published yet.')
    observed_tokens = [{'@type': 'PropertyValue', 'propertyID': key, 'name': label, 'unitText': 'tokens'}
        for key, label in [('prompt_tokens', 'Observed provider-reported prompt tokens'), ('completion_tokens', 'Observed provider-reported completion tokens'), ('total_tokens', 'Observed provider-reported total tokens'), ('reasoning_tokens', 'Observed provider-reported reasoning tokens'), ('cached_tokens', 'Observed provider-reported cached prompt tokens'), ('cache_write_tokens', 'Observed provider-reported cache-write tokens')]
        if any(row.get(key) is not None for row in (data['analysis'] or {}).get('attempts', []))]
    graph = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', '@id': URL + '#webpage', 'url': URL,
         'name': '6-process synthetic test | PALO BlueprintBench', 'description': description,
         'version': REVISION, 'inLanguage': 'en', 'isAccessibleForFree': True,
         'isPartOf': {'@id': 'https://paloframework.org/#website'},
         'mainEntity': {'@id': URL + '#dataset'},
         'creativeWorkStatus': 'Internal engineering feasibility; assistant-draft expectations; independent human adjudication pending'},
        {'@type': 'Dataset', '@id': URL + '#dataset', 'name': 'BlueprintBench 6-process synthetic test records',
         'url': URL, 'version': REVISION, 'description': description + ' One authoring group and zero independently sourced families. No ranking or qualified accuracy claim.',
         'creator': {'@type': 'Person', 'name': 'Fabrizio Degni', '@id': 'https://paloframework.org/PALO_Community.html#creator'},
         'isAccessibleForFree': True, 'creativeWorkStatus': 'Recorded internal observations' if observed else 'Prepared development material; not executed',
         'measurementTechnique': 'Fixed request assignments; strict response-contract checks separated from comparisons with provisional labels; explicit missingness and provider-reported cost accounting.',
         'variableMeasured': [
             {'@type': 'PropertyValue', 'propertyID': 'assigned_requests', 'name': 'Assigned requests', 'unitText': 'requests'},
             {'@type': 'PropertyValue', 'propertyID': 'completed_requests', 'name': 'Completed provider requests', 'unitText': 'requests'},
             {'@type': 'PropertyValue', 'propertyID': 'missing', 'name': 'Missing judgments', 'unitText': 'judgments'},
             {'@type': 'PropertyValue', 'propertyID': 'matches_draft', 'name': 'Matches to provisional draft expectations', 'unitText': 'judgments'},
             {'@type': 'PropertyValue', 'propertyID': 'known_cost_usd', 'name': 'Known provider-reported charge', 'unitText': 'USD'},
         ] + observed_tokens,
         'distribution': {'@type': 'DataDownload', 'name': 'Six-process observations JSON', 'encodingFormat': 'application/json', 'contentUrl': 'https://paloframework.org/downloads/blueprintbench/next-cycle-results.json'}},
    ]}
    return research_publication.enrich(graph, data)


def outputs():
    data = build()
    page = ROOT / 'web/PALO_BlueprintBench_NextCycle.html'
    text = page.read_text(encoding='utf-8')
    for name, body in [('RELEASE-SUMMARY', research_publication.visible_summary(data)), ('QUALIFICATION-PLAN', research_publication.roadmap_html())]:
        start, end = '<!-- ' + name + ':START -->', '<!-- ' + name + ':END -->'
        if start not in text:
            text = text.replace('</main>', start + end + '</main>')
        text = text[:text.index(start) + len(start)] + body + text[text.index(end):]
    payload = json.dumps(schema(data), ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    text, n = re.subn(r'(<script type="application/ld\+json" id="next-cycle-schema">).*?(</script>)', lambda m: m[1] + payload + m[2], text, flags=re.S)
    if n != 1:
        raise ValueError('Expected one next-cycle structured-data block')
    result = {DL / 'next-cycle-results.json': (json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode(), page: text.encode()}
    archived = {'LICENSE': (ROOT / 'LICENSE').read_bytes()}
    for folder in [BASE, ROOT / 'study/next-cycle']:
        for path in sorted(folder.rglob('*')):
            if path.is_file() and not any(part.startswith('.') or part == '__pycache__' for part in path.relative_to(folder).parts) and path.suffix not in ['.pyc', '.pyo']:
                archived[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    archive_manifest = {'revision': REVISION, 'qualified': False,
        'integrity_scope': 'Content hashes establish consistency only; not trusted time or independent custody.',
        'files': {name: hashlib.sha256(body).hexdigest() for name, body in sorted(archived.items())}}
    archived['NEXT-CYCLE-MANIFEST.json'] = (json.dumps(archive_manifest, indent=2) + '\n').encode()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, body in sorted(archived.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 11, 0, 0, 0))
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, body, compresslevel=9)
    result[DL / 'next-cycle-evidence.zip'] = buffer.getvalue()
    public_hashes = {path.relative_to(ROOT / 'web').as_posix(): hashlib.sha256(body).hexdigest() for path, body in result.items()}
    for name in ['next-cycle.js', 'next-cycle.css']:
        path = ROOT / 'web/assets/blueprintbench' / name
        public_hashes[path.relative_to(ROOT / 'web').as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    result[DL / 'next-cycle-manifest.json'] = (json.dumps({**archive_manifest,
        'presentation_revision': research_publication.PRESENTATION_REVISION,
        'publication_kind': 'page_only_internal_feasibility', 'evaluator_release': 'v0.3.0-internal.1',
        'original_18_model_results_modified': False, 'public_files': public_hashes}, indent=2) + '\n').encode()
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for path, body in outputs().items():
        if args.check:
            if not path.exists() or path.read_bytes() != body:
                raise SystemExit('Next-cycle publication drift: ' + str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
    print('Next-cycle publication ' + ('verified' if args.check else 'built') + '; no independent qualification')
