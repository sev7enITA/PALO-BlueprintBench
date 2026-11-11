"""Render the methodological comparison from the dated reference catalogue."""
import csv
import io
import json
from html import escape

START = '<!-- benchmark-references:start -->'
END = '<!-- benchmark-references:end -->'

def render(root):
    data = json.loads((root / 'docs/benchmark-references.json').read_text(encoding='utf-8'))
    rows = data['entries']
    assert len({r['id'] for r in rows}) == len(rows)
    assert sum(r['in_requested_directory'] for r in rows) == 12
    intro = ('These references compare documented task scope and evidence, not model scores. '
             'PALO differences are maintainer interpretations, not claims of superiority or exclusive novelty. '
             'External suites were not executed for this review. Sources checked 11 November 2026.')
    md = '# Benchmark references\n\n' + intro + '\n\n'
    md += ('Discovery: [terryyz/llm-benchmark](https://github.com/terryyz/llm-benchmark/blob/'
           + data['discovery']['revision'] + '/README.md). All 12 entries in that directory are accounted for below, alongside eight applied comparators. '
           'The directory mixes datasets, task suites, harnesses and platforms. Its historical dataset counts are not reused as current facts. '
           'Scholar Evals could not be verified at the referenced URL.\n\n')
    p = data['palo_status']
    md += '## PALO today\n\n**Implemented:** ' + p['implemented'] + '\n\n**Proposed study:** ' + p['proposed'] + '\n\n**Open qualification work:** ' + p['open_gates'] + '\n\nQualified held-out results: **0**. No PALO Blueprint Index score is assigned. References do not imply affiliation, endorsement or operational integration.\n\n'
    md += '| Reference and type | Evaluation target and evidence | Difference from PALO | Practice to carry forward |\n|---|---|---|---|\n'
    for r in rows:
        md += f"| [{r['name']}]({r['source_url']}) ({r['kind']}) | {r['focus']} {r['evidence']} | {r['palo_difference']} | {r['lesson']} |\n"
    md += '\n## Source status\n\n'
    md += ''.join(f"- **{r['name']}:** {r['source_status']} [Source]({r['source_url']}).\n" for r in rows if r['source_status'] != 'Primary source reviewed')
    md += '\n[jiant maintenance notice](https://github.com/nyu-mll/jiant) supports the implementation-status distinction for GLUE and SuperGLUE. The [earlier methodological review](research.md) retains additional references, including process modelling, spreadsheet tasks, agent security and contamination.\n'
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    html = f'''{START}
<section class="section shell references-section" id="references" aria-labelledby="references-title">
<div class="section-heading"><div><p class="eyebrow">Research context</p><h2 id="references-title">Benchmark references</h2></div><p>{escape(intro)}</p></div>
<div class="tracks reference-summary"><article><span>A</span><div><h3>Established foundations</h3><p>Task suites, reproducible harnesses, document evaluation and uncertainty-aware leaderboards provide the methodological foundations.</p></div></article><article><span>B</span><div><h3>PALO research focus</h3><p>Preserving obligations, permissions, ownership and exceptions in a business specification. The first proposed study focuses on procurement and human correction effort.</p></div></article><article><span>C</span><div><h3>Evidence available today</h3><p>Executable evidence checks and replayable development diagnostics. Zero qualified held-out results. Independent annotation and metric calibration remain open.</p></div></article></div>
<p class="method-note">Discovery reference: <a href="https://github.com/terryyz/llm-benchmark/blob/{data['discovery']['revision']}/README.md">terryyz/llm-benchmark</a>. All 12 directory entries are covered, with eight applied comparators. Dataset libraries, harnesses and benchmarks have different roles. A reference does not imply endorsement or integration.</p>
<details class="reference-details"><summary>Compare all 20 references with PALO</summary><div class="table-scroll" role="region" aria-label="Benchmark reference comparison" tabindex="0"><table class="reference-table"><caption>Documented scope and PALO's proposed contribution. Sources checked 11 November 2026.</caption><thead><tr><th scope="col">Reference</th><th scope="col">Target and evidence</th><th scope="col">Difference from PALO</th><th scope="col">Practice to adopt</th></tr></thead><tbody>'''
    for r in rows:
        html += f'<tr><th scope="row"><a href="{escape(r["source_url"],quote=True)}">{escape(r["name"])}</a><small>{escape(r["kind"])}</small></th><td>{escape(r["focus"])}<p>{escape(r["evidence"])}</p><small>{escape(r["source_status"])}</small></td><td>{escape(r["palo_difference"])}</td><td>{escape(r["lesson"])}</td></tr>'
    html += '''</tbody></table></div></details>
<p class="method-note"><a href="https://github.com/sev7enITA/PALO-BlueprintBench/blob/3effa4c/docs/benchmark-references.md">Read the reference comparison</a> / <a href="downloads/blueprintbench/benchmark-references.csv">Download CSV</a> / <a href="downloads/blueprintbench/benchmark-references.json">Inspect dated source records</a> / <a href="https://github.com/sev7enITA/PALO-BlueprintBench/blob/3effa4c/docs/research.md">Earlier methodological review</a></p>
</section>
''' + END
    return md.encode('utf-8'),stream.getvalue().encode('utf-8'),html
