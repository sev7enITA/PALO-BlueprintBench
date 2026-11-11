"""Reproduce copied public artifacts and packages; --check detects drift in CI."""
from pathlib import Path
import argparse,hashlib,io,json,zipfile
from build_references import render, START, END
ROOT=Path(__file__).resolve().parents[1]
DL=ROOT/'web/downloads/blueprintbench'

def archive(files):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,11,11,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=3  # Fixed Unix metadata; identical ZIP headers on Windows.
            info.external_attr=0o100644 << 16;z.writestr(info,data)
    return stream.getvalue()

def outputs():
    mapping={p.relative_to(ROOT).as_posix(): 'web/downloads/blueprintbench/'+p.name for p in (ROOT/'docs').iterdir() if p.is_file()}
    mapping.update({'evaluator/README.md':'web/downloads/blueprintbench/toolkit-readme.md','evaluator/evidence.schema.json':'web/downloads/blueprintbench/evidence.schema.json','results/synthetic-v0.3-draft/result.json':'web/downloads/blueprintbench/demo-result.json','results/release-v0.3.0-pilot.1/toolkit-verification.json':'web/downloads/blueprintbench/toolkit-verification.json'})
    out={ROOT/dest:(ROOT/src).read_bytes() for src,dest in mapping.items()}
    reference_md, reference_csv, reference_html = render(ROOT)
    for suffix, data in [('md',reference_md),('csv',reference_csv)]:
        out[ROOT/'docs'/('benchmark-references.'+suffix)] = data
        out[DL/('benchmark-references.'+suffix)] = data
    page = ROOT/'web/PALO_BlueprintBench.html'
    html = page.read_text(encoding='utf-8')
    assert html.count(START) == html.count(END) == 1
    html = html[:html.index(START)] + reference_html + html[html.index(END)+len(END):]
    out[page] = html.encode('utf-8')
    for src,dest in [('docs/reviewer-kit.md','evaluator/REVIEWER-KIT.md'),('docs/source-registry.json','evaluator/source-registry.json'),('docs/announcement.md','evaluator/SOCIAL-INVITATION.md'),('docs/announcement.md','web/downloads/blueprintbench/social-invitation.md')]:out[ROOT/dest]=(ROOT/src).read_bytes()
    toolkit={}
    for n in ['blueprintbench.py','demo.py','test_blueprintbench.py','test_audit_regressions.py','test_acquire.py','canonical-vectors.json','acquire.py','README.md','requirements.txt','evidence.schema.json','REVIEWER-KIT.md','source-registry.json','LICENSE']:
        p=ROOT/'evaluator'/n;toolkit['palo-blueprintbench/'+n]=out.get(p,p.read_bytes())
    toolkit['palo-blueprintbench/evaluator-contract.md']=(ROOT/'docs/evaluator-contract.md').read_bytes()
    toolkit['palo-blueprintbench/evaluator-0.3-draft.md']=(ROOT/'docs/evaluator-0.3-draft.md').read_bytes()
    out[DL/'toolkit.zip']=archive(toolkit)
    evidence=ROOT/'evidence/development-2026-11-10'
    out[DL/'development-evidence.zip']=archive({'development-evidence/'+p.relative_to(evidence).as_posix():p.read_bytes() for p in evidence.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'})
    sources = {}
    for folder in ['evaluator','docs','semantic','tools','wiki','assets/readme','results/synthetic-v0.3-draft','results/release-v0.3.0-pilot.1']:
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc':
                sources[p.relative_to(ROOT).as_posix()] = out.get(p,p.read_bytes())
    for name in ['README.md','GOVERNANCE.md','CHANGELOG.md','CITATION.cff','web/PALO_BlueprintBench.html','web/assets/blueprintbench/blueprintbench.js','web/assets/blueprintbench/blueprintbench.css','web/assets/blueprintbench/explorer-data.json']:
        sources[name] = out.get(ROOT/name,(ROOT/name).read_bytes())
    sources.update({p.relative_to(ROOT).as_posix():data for p,data in out.items()})
    manifest = {'release_tag':None,'base_release_tag':'v0.3.0-pilot.1','content_revision':'audit-repair-candidate-2026-11-11','scope':'Selected public documentation and toolkit files only; excludes original evidence (covered by its archive manifest), reviews, presentation and historical development results. Not a complete repository manifest. Immutable tags retain their original manifests','evaluator_version':'0.3.0-dev.1','explorer_version':'0.3.0','qualification':'unreleased evaluator review candidate; zero qualified held-out entries','files':{n:hashlib.sha256(data).hexdigest() for n,data in sorted(sources.items())}}
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
