"""Check versioned wiki navigation, repository links and an optional published clone."""
from pathlib import Path
from urllib.parse import unquote, urlparse
import argparse
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://github.com/sev7enITA/PALO-BlueprintBench/'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--published-dir',type=Path)
    args = parser.parse_args()
    source = ROOT/'wiki'
    pages = {p.stem:p for p in source.glob('*.md')}
    problems = []
    for page in [ROOT/'README.md',*pages.values()]:
        text = page.read_text(encoding='utf-8')
        for target in re.findall(r'\[\[(?:[^\]|]+\|)?([^\]]+)\]\]',text):
            if target.split('#')[0] not in pages:problems.append(f'{page.name}: missing wiki page {target}')
        urls = re.findall(r'\]\(([^)]+)\)',text) + re.findall(r'(?:src|href)="([^"]+)"',text)
        for url in urls:
            if url.startswith(BASE+'wiki/'):
                target=unquote(url[len(BASE+'wiki/'):].split('#')[0])
                if target not in pages:problems.append(f'{page.name}: missing wiki destination {target}')
            elif url.startswith(BASE+'blob/main/'):
                target=ROOT/unquote(url[len(BASE+'blob/main/'):].split('#')[0])
                if not target.exists():problems.append(f'{page.name}: missing source {target}')
            elif not urlparse(url).scheme and not url.startswith('#'):
                target=page.parent/unquote(url.split('#')[0])
                if not target.exists():problems.append(f'{page.name}: missing local link {url}')
    if args.published_dir:
        expected={p.name:p.read_bytes() for p in pages.values()}
        actual={p.name:p.read_bytes() for p in args.published_dir.glob('*.md')}
        for name in expected.keys()|actual.keys():
            if expected.get(name)!=actual.get(name):problems.append('Published wiki differs: '+name)
    if problems:raise SystemExit('\n'.join(problems))
    print(f'Wiki verified: {len(pages)-2} content pages, sidebar, footer and source links'+ ('; published clone matches' if args.published_dir else ''))
if __name__=='__main__':main()
