"""Reproduce copied public artifacts and packages; --check detects drift in CI."""
from pathlib import Path
import argparse,hashlib,io,json,zipfile
from build_references import render, START, END, TARGET_PAGE
from research_publication import PRESENTATION_REVISION
ROOT=Path(__file__).resolve().parents[1]
DL=ROOT/'web/downloads/blueprintbench'
RELEASE=json.loads((ROOT/'release.json').read_text(encoding='utf-8'))
RELEASE_RESULTS=ROOT/'results'/('release-'+RELEASE['release_tag'])

def archive(files):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,11,11,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=3  # Fixed Unix metadata; identical ZIP headers on Windows.
            info.external_attr=0o100644 << 16;z.writestr(info,data)
    return stream.getvalue()

def outputs():
    mapping={p.relative_to(ROOT).as_posix(): 'web/downloads/blueprintbench/'+p.name for p in (ROOT/'docs').iterdir() if p.is_file() and p.suffix != '.md'}
    mapping.update({'evaluator/evidence.schema.json':'web/downloads/blueprintbench/evidence.schema.json','results/synthetic-v0.3.0/result.json':'web/downloads/blueprintbench/demo-result.json',str((RELEASE_RESULTS/'toolkit-verification.json').relative_to(ROOT)):'web/downloads/blueprintbench/toolkit-verification.json','release.json':'web/downloads/blueprintbench/release.json'})
    out={ROOT/dest:(ROOT/src).read_bytes() for src,dest in mapping.items()}
    verified=json.loads((RELEASE_RESULTS/'toolkit-verification.json').read_text(encoding='utf-8'))
    current_status={
        'presentation_revision':PRESENTATION_REVISION, 'observation_revision':'2026-11-11.4',
        'current_evidence_release':'study-2026-11-11-six-scenario.1',
        'as_of':RELEASE['release_date'], 'release':RELEASE['release_tag'],
        'content_revision':RELEASE['content_revision'], 'tool_version':RELEASE['evaluator_version'],
        'evidence_contract':RELEASE['evidence_contract'], 'test_count':verified['tests_passed'],
        'test_result':'passed', 'test_scope':verified['test_scope'],
        'qualified_heldout_entries':0, 'independent_human_review':False,
        'new_100mb_corpora_qualified':0, 'current_workbench_qualification':'not_completed',
        'original_cases':'development_only', 'explorer_version':RELEASE['content_revision'],
        'explorer_scope':'Descriptive internal results and separate historical diagnostics; no numerical ranks or independently qualified scores.',
        'publication_scope':'Corrective evaluator internal-test release, descriptive dashboard and next-cycle adjudication materials',
        'known_vulnerable_release':RELEASE['known_vulnerable_release']}
    out[DL/'release-status.json']=(json.dumps(current_status,indent=2)+'\n').encode('utf-8')
    reference_md, reference_csv, reference_html = render(ROOT)
    for suffix, data in [('md',reference_md),('csv',reference_csv)]:
        out[ROOT/'docs'/('benchmark-references.'+suffix)] = data
        if suffix != 'md': out[DL/('benchmark-references.'+suffix)] = data
    page = ROOT/'web'/TARGET_PAGE
    html = page.read_text(encoding='utf-8')
    assert html.count(START) == html.count(END) == 1
    html = html[:html.index(START)] + reference_html + html[html.index(END)+len(END):]
    out[page] = html.encode('utf-8')
    for src,dest in [('docs/reviewer-kit.md','evaluator/REVIEWER-KIT.md'),('docs/source-registry.json','evaluator/source-registry.json'),('docs/announcement.md','evaluator/SOCIAL-INVITATION.md')]:out[ROOT/dest]=(ROOT/src).read_bytes()
    toolkit={}
    for n in ['blueprintbench.py','demo.py','test_blueprintbench.py','test_audit_regressions.py','test_acquire.py','canonical-vectors.json','acquire.py','README.md','requirements.txt','evidence.schema.json','REVIEWER-KIT.md','source-registry.json','LICENSE','EVALUATOR-0.2-WARNING.md']:
        p=ROOT/'evaluator'/n;toolkit['palo-blueprintbench/'+n]=out.get(p,p.read_bytes())
    toolkit['palo-blueprintbench/evaluator-contract.md']=(ROOT/'docs/evaluator-contract.md').read_bytes()
    toolkit['palo-blueprintbench/evaluator-0.3-draft.md']=(ROOT/'docs/evaluator-0.3-draft.md').read_bytes()
    toolkit['palo-blueprintbench/RELEASE.json']=(ROOT/'release.json').read_bytes()
    out[DL/'toolkit.zip']=archive(toolkit)
    evidence=ROOT/'evidence/development-2026-11-10'
    out[DL/'development-evidence.zip']=archive({'development-evidence/'+p.relative_to(evidence).as_posix():p.read_bytes() for p in evidence.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'})
    out[DL/'brand-kit.zip']=archive({'blueprintbench-brand/'+p.name:p.read_bytes() for p in (ROOT/'web/assets/blueprintbench/brand').glob('*') if p.is_file() and 'badge' not in p.name.lower()} | {'blueprintbench-brand/USAGE.md':(ROOT/'docs/brand-usage.md').read_bytes(), 'blueprintbench-brand/GENERATION.md':(ROOT/'presentation/brand-generation.md').read_bytes(), 'blueprintbench-brand/palo-framework-logo.webp':(ROOT/'web/assets/logo.webp').read_bytes()})
    sources = {}
    for folder in ['internal_tests/2026-11-11-real-procurement','internal_tests/2026-11-11-calibration','evaluator','docs','semantic','tools','wiki','assets/readme','results/synthetic-v0.3-draft','results/synthetic-v0.3.0','results/release-v0.3.0-pilot.1',str(RELEASE_RESULTS.relative_to(ROOT)),'study/next-cycle','internal_tests/2026-11-11-next-cycle','web/assets/blueprintbench/brand']:
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc' and not ('web/assets/blueprintbench/brand' in p.as_posix() and 'badge' in p.name.lower()):
                sources[p.relative_to(ROOT).as_posix()] = out.get(p,p.read_bytes())
    for name in ['web/PALO_BlueprintBench_Generation.html','web/assets/blueprintbench/generation.js','web/assets/blueprintbench/generation.css','web/downloads/blueprintbench/generation-results.json','web/downloads/blueprintbench/generation-evidence.zip','web/PALO_BlueprintBench_Method.html','web/PALO_BlueprintBench_Corpus.html','web/assets/blueprintbench/site-architecture.css','web/PALO_BlueprintBench_NextCycle.html','web/assets/blueprintbench/next-cycle.js','web/assets/blueprintbench/next-cycle.css','web/downloads/blueprintbench/next-cycle-results.json','web/downloads/blueprintbench/next-cycle-manifest.json','web/downloads/blueprintbench/next-cycle-evidence.zip','release.json','web/PALO_BlueprintBench_Diagnostics.html','web/assets/blueprintbench/reviewer-diagnostics.js','web/assets/blueprintbench/calibration.css','web/assets/blueprintbench/calibration.js','web/downloads/blueprintbench/calibration.json','web/downloads/blueprintbench/model-roster.json','web/downloads/blueprintbench/model-roster.csv','web/downloads/blueprintbench/.htaccess','web/downloads/blueprintbench/presentation/.htaccess','README.md','GOVERNANCE.md','CHANGELOG.md','CITATION.cff','web/PALO_BlueprintBench.html','web/assets/blueprintbench/blueprintbench.js','web/assets/blueprintbench/blueprintbench.css','web/assets/blueprintbench/explorer-data.json','web/PALO_BlueprintBench_Leaderboard.html','web/assets/blueprintbench/leaderboard.css','web/assets/blueprintbench/leaderboard.js','web/downloads/blueprintbench/adversarial-tests.json','web/downloads/blueprintbench/leaderboard-data.json','web/downloads/blueprintbench/internal-tests-results.json','web/downloads/blueprintbench/internal-tests-report.md','web/downloads/blueprintbench/internal-tests-evidence.zip','web/downloads/blueprintbench/internal-expansion-evidence.zip','web/downloads/blueprintbench/internal-cohort-report.md']:
        sources[name] = out.get(ROOT/name,(ROOT/name).read_bytes())
    sources.update({p.relative_to(ROOT).as_posix():data for p,data in out.items()})
    sources = {name: data for name, data in sources.items() if '/presentation/' not in name or name.endswith('/.htaccess')}
    manifest = {'presentation_revision':PRESENTATION_REVISION,'observation_revision':'2026-11-11.4','current_evidence_release':'study-2026-11-11-six-scenario.1','release_tag':RELEASE['release_tag'],'base_release_tag':'v0.3.0-pilot.1','content_revision':RELEASE['content_revision'],'leaderboard_revision':RELEASE['leaderboard_revision'],'scope':'Selected public documentation and toolkit files only; original evidence is covered by archive manifests. Historical tags and packages retain their original bytes. Internal presentation and withdrawn testing badges are excluded. Not a complete repository manifest.','evaluator_version':RELEASE['evaluator_version'],'source_dataset_revision':RELEASE['frozen_dataset_revision'],'source_dataset_sha256':RELEASE['source_dataset_sha256'],'explorer_version':'0.3.0','qualification':'internal tests only; no independent human approval or qualified held-out entries','known_vulnerable_release':RELEASE['known_vulnerable_release'],'files':{n:hashlib.sha256(data).hexdigest() for n,data in sorted(sources.items())}}
    out[DL/'release-manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode('utf-8')
    return out

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    out=outputs();bad=[]
    for path,data in out.items():
        if args.check:
            if not path.exists() or path.read_bytes()!=data:bad.append(str(path.relative_to(ROOT)))
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    if bad:raise SystemExit('Public artifact drift: '+', '.join(bad))
    print(json.dumps({'status':'verified' if args.check else 'built','artifacts':len(out)}))
if __name__=='__main__':main()
