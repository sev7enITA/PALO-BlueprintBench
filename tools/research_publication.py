"""Shared publication metadata; never promotes internal observations to qualification."""
from pathlib import Path
import html
import json

ROOT = Path(__file__).resolve().parents[1]
PRESENTATION_REVISION = '2026-11-11.6'
SITE = 'https://paloframework.org/'
NEXT = SITE + 'PALO_BlueprintBench_NextCycle.html'


def release():
    return json.loads((ROOT / 'docs/schema/six-scenario-release.json').read_text(encoding='utf-8'))


def observed_summary(data):
    analysis = data['analysis'] or {}
    rows = analysis.get('attempts', [])
    workflows = [r for r in rows if r['track'] == 'workflow']
    return {
        'scenarios': len(data['case_bank']['cases']),
        'unique_propositions': sum(len(c['probes']) for c in data['case_bank']['cases']),
        'configurations': len(data['configurations']),
        'assigned_requests': analysis.get('assigned_requests', 0),
        'completed_requests': analysis.get('completed_requests', 0),
        'workflow_assignments': len(workflows),
        'structurally_valid_workflows': sum(bool(r['structural_valid']) for r in workflows),
        'known_cost_usd': (data.get('budget') or {}).get('campaign_known_usd'),
    }


def enrich(graph, data):
    page, dataset = graph['@graph']
    r = release()
    immutable = 'https://github.com/sev7enITA/PALO-BlueprintBench/blob/' + r['commit']
    page.update(version=PRESENTATION_REVISION, dateModified='2026-11-11',
                relatedLink=[r['url'], NEXT + '#qualification-plan'],
                image=SITE + 'assets/blueprintbench/brand/blueprintbench-logo.png')
    dataset['creativeWorkStatus'] = 'Recorded internal observations; not independently validated'
    dataset.update(identifier='next-cycle-internal-feasibility-2026-11-11',
                   datePublished='2026-11-11', dateModified='2026-11-11',
                   temporalCoverage='2026-11-11',
                   citation={'@type': 'CreativeWork', 'name': '6-process synthetic test: archived evidence release',
                             'url': r['url'], 'version': r['tag'],
                             'creativeWorkStatus': 'Postcollection internal-test prerelease; not independent validation'},
                   isBasedOn={'@type': 'CreativeWork', 'name': 'Frozen synthetic development case bank',
                              'url': immutable + '/study/next-cycle/case-bank.json'},
                   usageInfo=[NEXT + '#method', immutable + '/internal_tests/2026-11-11-next-cycle/RESULTS.md'])
    dataset['measurementTechnique'] += (' One repetition per configuration; 18 workflow generations are structurally checked only. '
        'The threshold comparison also changes the candidate batch from eight to six, so it is not a single-variable causal test. '
        'No independently adjudicated accuracy, uncertainty bands or numerical ranks are available.')
    summary = observed_summary(data)
    labels = {'scenarios': 'Fictional development scenarios', 'unique_propositions': 'Unique provisional propositions',
              'configurations': 'Serving configurations in this test',
              'assigned_requests': 'Assigned API requests', 'completed_requests': 'Completed API requests',
              'workflow_assignments': 'Assigned workflow-generation requests',
              'structurally_valid_workflows': 'Workflow drafts passing structural checks',
              'known_cost_usd': 'Provider-reported test charge'}
    existing = {v['propertyID']: v for v in dataset['variableMeasured']}
    for key, value in summary.items():
        item = existing.get(key)
        if item is None:
            item = {'@type': 'PropertyValue', 'propertyID': key, 'name': labels[key]}
            dataset['variableMeasured'].append(item)
        if value is not None:
            item['value'] = value
        item['description'] = 'Internal observed count or charge, not an independently validated quality score.'
    distribution = dataset['distribution']
    dataset['distribution'] = [distribution, {
        '@type': 'DataDownload', 'name': 'Original requests, responses, sources and draft exports',
        'encodingFormat': 'application/zip',
        'contentUrl': next(a['url'] for a in r['assets'] if a['name'] == 'next-cycle-evidence.zip')}]
    return graph


def visible_summary(data):
    s = observed_summary(data)
    charge = 'Unavailable' if s['known_cost_usd'] is None else f"USD {s['known_cost_usd']:.7f}"
    return ('<section class="shell section" id="released-evidence"><h2>Released evidence</h2>'
            f'<p>{s["scenarios"]} fictional process descriptions · {s["unique_propositions"]} provisional propositions · '
            f'{s["configurations"]} serving configurations · {s["completed_requests"]}/{s["assigned_requests"]} completed requests.</p>'
            f'<p>{s["structurally_valid_workflows"]}/{s["workflow_assignments"]} workflow drafts pass structural checks. '
            f'Provider-reported test charge: {charge}. These counts do not establish semantic accuracy.</p>'
            f'<p><a href="{html.escape(release()["url"])}">Versioned evidence release on GitHub ↗</a> · '
            f'Presentation {PRESENTATION_REVISION} · Frozen observation revision {data["revision"]}</p></section>')


def roadmap_html():
    p = json.loads((ROOT / 'docs/qualification-roadmap.json').read_text(encoding='utf-8'))
    cards = ''.join('<li><strong>' + html.escape(g['title']) + '</strong><p>' + html.escape(g['requirement']) +
                    '</p><small>Status: ' + html.escape(g['status_label']) + '</small></li>' for g in p['gates'])
    return ('<section class="shell section" id="qualification-plan"><h2>Path to qualified comparison</h2>'
            '<p>Independent acceptance gates remain open. Real-document development collection has started: 3 documents, 200 supplied pages, 27 assigned calls across three serving configurations, including stopped and incomplete requests. Current completion and accounting appear on the real-document generation page.</p>'
            '<details><summary>Six acceptance gates and current status</summary><ol>' + cards + '</ol></details><p><a href="https://github.com/sev7enITA/PALO-BlueprintBench/blob/main/docs/qualification-roadmap.md">'
            'Protocol, rubric and acceptance evidence ↗</a></p></section>')
