"""Replay additional internal campaigns without modifying frozen baseline evidence."""
import collections
import hashlib
import importlib.util
import io
import json
import statistics
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / 'internal_tests/2026-11-11-frontier'
EXPANSIONS = [ROOT / 'internal_tests/2026-11-11-expansion', ROOT / 'internal_tests/2026-11-11-legacy-extension']
WEB = ROOT / 'web/downloads/blueprintbench'

def load(path):
    return json.loads(path.read_bytes().decode('utf-8'))

def extensions():
    spec = importlib.util.spec_from_file_location('baseline_analysis', BASELINE / 'analyse.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    results = []
    for base in EXPANSIONS:
        if not (base / 'manifest.json').exists():
            continue
        module.ROOT = base
        data = module.analyse()
        configs = load(base / 'models.json')
        data['assigned_calls'] = len(configs) * 18
        data['not_run'] = data['assigned_calls'] - data['recorded_calls']
        records = [load(p) for p in sorted((base / 'runs').glob('*/record.json'))]
        data['not_run'] += sum(r['state'] == 'not_run' for r in records)
        data['completed_calls'] = sum(r['state'] == 'completed' for r in records)
        data['failed_calls'] = sum(r['state'] not in ['completed','not_run'] for r in records)
        data['unknown_cost_calls'] = sum(r['cost_status'] == 'unknown' for r in records)
        data['unknown_cost_reserved_usd'] = sum(r['reserved_usd'] for r in records if r['cost_status'] == 'unknown')
        data['configurations'] = configs
        data['records'] = records
        data['sensitivity'] = []
        data['translations'] = []
        data['translation_examples'] = []
        corpus = load(base / 'corpus.json')
        for model in data['models']:
            own = [r for r in records if r['model'] == model['id']]
            model['not_run'] += sum(r['state'] == 'not_run' for r in own)
            actual_calls = [r for r in own if r['state'] != 'not_run']
            model['latency_median_seconds'] = statistics.median(r['elapsed_seconds'] for r in actual_calls) if actual_calls else None
            model['attempted_calls'] = len(actual_calls)
            rows = [r for r in data['verification_rows'] if r['model'] == model['id']]
            kept = [j for r in rows for j in r['judgments'] if not (r['case'] == 'invoice-matching' and j['id'] == 'P002')]
            data['sensitivity'].append(dict(model=model['id'],assigned=321,classified=len(kept),correct=sum(j['correct'] for j in kept),posthoc=True))
            translated, verbatim = 0, 0
            for record in own:
                if record['track'] != 'translation':
                    continue
                path = base / 'runs' / record['id'] / 'output.txt'
                if not path.exists():
                    continue
                claims, _ = module.translation_claims(path.read_bytes().decode('utf-8'))
                sources = {r['id']:r['text'] for c in corpus if c['id'] == record['case'] for r in c['source']}
                for claim in claims:
                    proposed = claim['text'].split(' :: ',1)[-1]
                    source = sources.get(claim['source_id'])
                    translated += 1
                    verbatim += int(source == proposed)
                    data['translation_examples'].append(dict(model=model['id'],case=record['case'],repetition=record['repetition'],source_id=claim['source_id'],source_text=source,proposed_specification=proposed,verbatim=source==proposed,evidence_path=path.relative_to(base).as_posix(),review_status='unreviewed_draft',record_id=record['id']))
            data['translations'].append(dict(model=model['id'],assigned_source_rules=108,emitted_lines=translated,internally_reviewed_lines=0,verbatim_source_lines=verbatim,review_type='unreviewed_draft',business_approved=False))
        # Keep the baseline interpreter version and post-hoc extension boundary visible.
        data['analysis_implementation_sha256'] = hashlib.sha256((BASELINE/'analyse.py').read_bytes()).hexdigest()
        (base/'analysis.json').write_bytes((json.dumps(data,indent=2)+'\n').encode('utf-8'))
        results.append((base,data))
    return results

def archive(results):
    files = {}
    for base, _ in results:
        for path in base.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                files[base.name+'/'+path.relative_to(base).as_posix()] = path.read_bytes()
    files['baseline-analysis.py'] = (BASELINE/'analyse.py').read_bytes()
    files['build_expansion.py'] = Path(__file__).read_bytes()
    hashes = {name:hashlib.sha256(body).hexdigest() for name,body in files.items()}
    files['public-archive-manifest.json'] = (json.dumps(hashes,indent=2,sort_keys=True)+'\n').encode()
    out = io.BytesIO()
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as zipped:
        for name, body in sorted(files.items()):
            info = zipfile.ZipInfo(name,date_time=(2026,11,11,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            zipped.writestr(info,body)
    (WEB/'internal-expansion-evidence.zip').write_bytes(out.getvalue())

if __name__ == '__main__':
    results = extensions()
    archive(results)
    print(json.dumps({'campaigns':len(results),'models':sum(len(d['models']) for _,d in results),'recorded_calls':sum(d['recorded_calls'] for _,d in results)}))
