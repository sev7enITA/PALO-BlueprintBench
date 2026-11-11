"""Render capture diagnostics separately from model result pages."""
from pathlib import Path
import argparse
import html
import json
import re
import calibration

ROOT = Path(__file__).resolve().parents[1]
GIT = 'https://github.com/sev7enITA/PALO-BlueprintBench/tree/main/internal_tests/2026-11-11-calibration'
NAMES = {'fable': 'Fable 5.2 High', 'glm': 'GLM 5.3 Max', 'gemini': 'Gemini 4 Argon High'}


def panel(data):
    cards = ''
    for r in data['results']:
        c = r['counts']
        available = r['semantic_status'] != 'not_assessed'
        detected = str(c['detected']) if available else 'N/A'
        alarm = str(c['false_alarms']) if available else 'N/A'
        receipt = r.get('receipt') or {}
        channel = receipt.get('interface', 'API' if receipt.get('generation_id') else 'Not recorded')
        cards += f'''<article class="calibration-card"><h3>{NAMES[r['reviewer']]}</h3><p>Capture channel: {html.escape(channel)}</p><p class="mono">{'Envelope accepted' if r['strict_envelope_valid'] else 'Captured envelope invalid' if r['receipt'] else 'Response not received'}</p><p>{'Retained judgments available; no comparative accuracy claim.' if available else 'Semantic assessment unavailable; capture failure is not a reasoning score.'}</p><details><summary>Historical capture counts and advisory text</summary><p>Detected alterations: {detected} / {c['mutations']}. False alarms: {alarm} / {c['faithful_controls']}. Unresolved: {c['missing'] + c['invalid'] + c['uncertain']} / {c['assigned']}.</p><p>{html.escape(r['review']['verdict']) if r['review'] else 'Raw advisory text is preserved on GitHub; no semantic score is assigned.'}</p></details></article>'''
    return f'''<!-- CALIBRATION:START -->
<section class="wrap calibration-section" id="calibration" aria-labelledby="calibration-title"><div class="section-heading"><div><p class="eyebrow">Internal method checks</p><h2 id="calibration-title">Reviewer capture diagnostics</h2></div><p>Six seeded alterations, six unchanged rules and six paraphrases. One authored source family, three procurement cases. This checks an elementary reviewer workflow, not general judging ability or independent accuracy.</p></div>
<ol class="calibration-flow"><li>Freeze source and draft rubric</li><li>Review without expected labels</li><li>Check response structure</li><li>Compare semantic judgments</li><li>Export source-bound drafts</li></ol><div class="calibration-grid">{cards}</div>
<p class="calibration-note"><strong>Interpretation:</strong> Missing, invalid and uncertain answers remain assigned. A zero false-alarm count is not interpretable without complete control responses. Fable flags C10 as a potentially ambiguous paraphrase; the original draft label is preserved. These easy examples do not validate the judge or change the recorded model results. Channels, prompts and attempt histories differ; the counts cannot rank reviewers.</p>
<p class="calibration-note"><strong>Post-hoc lexical baseline:</strong> exact source/candidate equality detects 6/6 alterations but raises 6/12 false alarms on faithful controls. This exposes the weakness of copy matching; it does not establish model generalisation. Gemini and GLM advisory text is preserved even when its captured JSON is invalid. Their copied interface responses are not provider API bytes; the source of the formatting defect cannot be isolated.</p>
<p><a href="https://github.com/sev7enITA/PALO-BlueprintBench/blob/main/docs/calibration-review-decisions.md">Review agreements, disagreements and implementation decisions ↗</a></p>
<div class="calibration-toolbar"><label for="calibration-filter">Inspect examples</label><select id="calibration-filter"><option value="all">All 18 examples</option><option value="mutation">Seeded alterations</option><option value="paraphrase">Paraphrase controls</option><option value="unchanged">Unchanged controls</option><option value="disputed">Disputed or unresolved</option></select><a href="downloads/blueprintbench/calibration.json" download>Export calibration JSON</a><a href="{GIT}">Protocol, raw responses and replay on GitHub ↗</a></div><div id="calibration-items" aria-live="polite"></div>
<details class="method-details"><summary>Delivered checks and further development</summary><ul><li>Versioned source-bound proposition bank and explicit draft rubric. Independent expert gold remains pending.</li><li>Replayable review-to-export harness, strict identifiers and fixed denominators. No new Workbench document-ingestion or 100 MB test is claimed here.</li><li>Structural failures and semantic outcomes are separate. A schema-valid judgment can still be wrong.</li><li>Exposed sources remain ineligible for independent qualification. Local hashes establish byte identity, not external custody.</li><li>Next study: subtle alterations, instruction-bearing candidates, order-shuffled repetitions, unanswerable items, new independent source families and blind human adjudication.</li></ul></details></section>
<!-- CALIBRATION:END -->'''


def outputs():
    data = calibration.build()
    result = {}
    page = ROOT / 'web/PALO_BlueprintBench_Diagnostics.html'
    text = page.read_text(encoding='utf-8')
    assert text.count('<!-- CALIBRATION:START -->') == 1
    text = re.sub(r'<!-- CALIBRATION:START -->.*?<!-- CALIBRATION:END -->', lambda _: panel(data), text, flags=re.S)
    result[page] = text.encode('utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for path, body in outputs().items():
        if args.check:
            assert path.read_bytes() == body, str(path)
        else:
            path.write_bytes(body)
    print('Calibration panels verified')
