"""Render methodological comparisons and sourced visibility signals."""
import csv
import io
import json
from html import escape

START = '<!-- benchmark-references:start -->'
END = '<!-- benchmark-references:end -->'
REPO = 'https://github.com/sev7enITA/PALO-BlueprintBench/blob/codex/blueprintbench-leaderboard-20261111/'


def visibility_html(row):
    if row['review_group'] != 'visibility-expansion-20261111':
        return '<small>Original reference set; visibility not reassessed in this extension.</small>'
    links = [url.strip() for url in row['visibility_sources'].split(';') if url.strip()]
    sources = ' / '.join(f'<a href="{escape(url, quote=True)}">Source {i+1}</a>' for i, url in enumerate(links))
    text = f'<p>{escape(row["visibility_basis"])}</p><small>{sources}</small>'
    if row['repo_stars'] is not None:
        text += f'<p><a href="{escape(row["repo_url"], quote=True)}">{row["repo_stars"]:,} GitHub stars</a><small>{escape(row["repo_star_scope"])}; {escape(row["checked_on"])}</small></p>'
    return text


def render(root):
    data = json.loads((root / 'docs/benchmark-references.json').read_text(encoding='utf-8'))
    rows = data['entries']
    added = [r for r in rows if r['review_group'] == 'visibility-expansion-20261111']
    assert len({r['id'] for r in rows}) == len(rows)
    assert sum(r['in_requested_directory'] for r in rows) == 12
    assert len(added) == data['visibility_selection']['added']
    checked = data['checked_on']
    intro = ('These references compare documented tasks, evidence and evaluation practices, not model scores. '
             'PALO differences and transfer priorities are maintainer assessments, not claims of superiority or exclusive novelty. '
             f'External suites were not executed. Sources checked {checked}.')
    selection = data['visibility_selection']
    discovery = 'https://github.com/terryyz/llm-benchmark/blob/' + data['discovery']['revision'] + '/README.md'
    md = '# Benchmark references\n\n' + intro + '\n\n'
    md += f'{len(rows)} references: the original 20, including all 12 entries in [terryyz/llm-benchmark]({discovery}), plus {len(added)} high-visibility benchmark families. Dataset libraries, harnesses, platforms and task benchmarks have different roles.\n\n'
    md += '## Selection and visibility\n\n' + selection['method'] + '\n\n' + selection['limits'] + '\n\n' + selection['priority_definition'] + '\n\n'
    md += '[Dated repository snapshots](reference-visibility-signals.json) preserve the API sources. No popularity or quality score is calculated.\n\n'
    p = data['palo_status']
    md += '## PALO today\n\n**Implemented:** ' + p['implemented'] + '\n\n**Proposed study:** ' + p['proposed'] + '\n\n**Open qualification work:** ' + p['open_gates'] + '\n\nQualified held-out results: **0**. No PALO Blueprint Index score is assigned. References imply no affiliation, endorsement or operational integration.\n\n'
    md += '## Transfer priorities\n\n'
    for item in data['transfer_priorities']:
        md += '### ' + item['title'] + '\n\n' + item['action'] + '\n\nReferences: ' + ', '.join(next(r['name'] for r in rows if r['id'] == key) for key in item['references']) + '. These are proposed actions, not completed qualification.\n\n'
    md += '## Comparison\n\n| Reference and version | Target and evidence | Visibility signal | PALO difference and caution | Practice to carry forward |\n|---|---|---|---|---|\n'
    for r in rows:
        attention = r['visibility_basis']
        if r['visibility_sources']:
            attention += ' ' + ' / '.join(f'[Source {i+1}]({u.strip()})' for i,u in enumerate(r['visibility_sources'].split(';')))
        if r['repo_stars'] is not None:
            attention += f" [{r['repo_stars']:,} stars]({r['repo_url']}); {r['repo_star_scope']}; {checked}."
        md += f"| [{r['name']}]({r['source_url']}) ({r['kind']}). {r['version_scope']} | {r['focus']} {r['evidence']} | {attention} | {r['palo_difference']} {r['caution']} | {r['lesson']} Transfer: {r['palo_transfer']}. |\n"
    md += '\n## Source status\n\n' + ''.join(f"- **{r['name']}:** {r['source_status']} [Source]({r['source_url']}).\n" for r in rows if r['source_status'] != 'Primary source reviewed')
    md += '\nThe [earlier methodological review](research.md) retains additional context. Original reference status statements were preserved; the visibility expansion assesses only the 15 added families.\n'
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    html = f'''{START}
<section class="section shell references-section" id="references" aria-labelledby="references-title">
<div class="section-heading"><div><p class="eyebrow">Research context</p><h2 id="references-title">Benchmark references</h2></div><p>{escape(intro)}</p></div>
<div class="tracks reference-summary"><article><span>{len(rows)}</span><div><h3>Reference catalogue</h3><p>The original 20 references and {len(added)} additional benchmark families selected for documented visibility.</p></div></article><article><span>{len(added)}</span><div><h3>Visibility profiles</h3><p>Model-launch references, public leaderboards, competitions and dated repository signals. No hype or quality score is inferred.</p></div></article><article><span>4</span><div><h3>Transfer priorities</h3><p>Expert rubrics, workflow reliability, separate structural and semantic evidence, and unseen-case custody. Proposed work for PALO.</p></div></article></div>
<p class="method-note">{escape(selection['method'])} {escape(selection['limits'])}</p>
<details class="reference-details"><summary>Priorities for PALO</summary>'''
    for item in data['transfer_priorities']:
        names = ', '.join(next(r['name'] for r in rows if r['id'] == key) for key in item['references'])
        html += f'<h3>{escape(item["title"])}</h3><p>{escape(item["action"])}</p><p class="method-note">References: {escape(names)}. Proposed work; not completed qualification.</p>'
    html += '</details>'
    for group, label in [(added, f'Explore {len(added)} added benchmark families'), ([r for r in rows if r not in added], 'Review the original 20 references')]:
        html += f'<details class="reference-details"><summary>{label}</summary><div class="table-scroll" role="region" aria-label="{label}" tabindex="0"><table class="reference-table"><caption>Documented scope, visibility signals and PALO transfer assessment. Checked {checked}.</caption><thead><tr><th scope="col">Reference and version</th><th scope="col">Target and evidence</th><th scope="col">Visibility signal</th><th scope="col">PALO difference and caution</th><th scope="col">Practice to adopt</th></tr></thead><tbody>'
        for r in group:
            html += f'<tr data-reference="{escape(r["id"], quote=True)}"><th scope="row"><a href="{escape(r["source_url"], quote=True)}">{escape(r["name"])}</a><small>{escape(r["kind"])}</small><p>{escape(r["version_scope"])}</p></th><td>{escape(r["focus"])}<p>{escape(r["evidence"])}</p><small>{escape(r["source_status"])}</small></td><td>{visibility_html(r)}</td><td>{escape(r["palo_difference"])}<p>{escape(r["caution"])}</p></td><td>{escape(r["lesson"])}<small>Transfer: {escape(r["palo_transfer"])}</small></td></tr>'
        html += '</tbody></table></div></details>'
    html += f'''<p class="method-note">{escape(selection['priority_definition'])} Discovery: <a href="{discovery}">terryyz/llm-benchmark</a>. All 12 directory entries remain covered. References imply no endorsement or integration.</p>
<p class="method-note"><a href="{REPO}docs/benchmark-references.md">Read the full comparison on GitHub</a> / <a href="downloads/blueprintbench/benchmark-references.csv">Download CSV</a> / <a href="downloads/blueprintbench/benchmark-references.json">Inspect source records</a> / <a href="downloads/blueprintbench/reference-visibility-signals.json">Repository snapshots</a> / <a href="{REPO}docs/research.md">Earlier methodological review</a></p>
</section>
{END}'''
    return md.encode('utf-8'), stream.getvalue().encode('utf-8'), html
