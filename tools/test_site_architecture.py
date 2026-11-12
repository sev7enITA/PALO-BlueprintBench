"""Regression checks for study separation and source-preserving presentation."""
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import json
import re
import unittest
import build_site_architecture as site
import build_references

ROOT=Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self,text):
        super().__init__();self.links=[];self.ids=[];self.tables=0;self.feed(text)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='a':self.links.append(attrs.get('href',''))
        if 'id' in attrs:self.ids.append(attrs['id'])
        if tag=='table':self.tables+=1


class SiteArchitectureTests(unittest.TestCase):
    def test_landing_is_introduction_not_duplicate_results(self):
        text=(ROOT/'web/PALO_BlueprintBench.html').read_text(encoding='utf-8');page=Page(text)
        self.assertEqual(page.tables,0)
        self.assertNotIn('leaderboard.js',text)
        self.assertNotIn('blueprintbench.js',text)
        self.assertNotIn('data-reference=',text)
        for name in ['3-text synthetic test','6-process synthetic test','Real-document generation','What the research measures','How this supports system selection']:
            self.assertIn(name,text)
        self.assertNotIn('Next-cycle',text)
        self.assertFalse(any(n.get('@type')=='Dataset' for n in site.page_graph('overview')['@graph']))

    def test_navigation_and_page_identity_are_consistent(self):
        filenames=[x[0] for x in site.PAGES.values()]+['PALO_BlueprintBench_Leaderboard.html','PALO_BlueprintBench_NextCycle.html','PALO_BlueprintBench_Diagnostics.html']
        for name in filenames:
            text=(ROOT/'web'/name).read_text(encoding='utf-8')
            self.assertIn(site.navigation(name),text,name)
            self.assertIn(site.footer(),text,name)
            self.assertIn('site-architecture.css',text)
            self.assertNotRegex(text,r'href="(?:https://paloframework.org/)?downloads/blueprintbench/[^"\n]*\.md"')
            self.assertNotIn(chr(8212),text)
            self.assertEqual(text.count('rel="canonical"'),1)
            self.assertEqual(len(re.findall(r'<script[^>]*type="application/ld\+json"',text)),1)
            ids=Page(text).ids;self.assertEqual(len(ids),len(set(ids)),name)

    def test_references_live_on_method_only(self):
        self.assertEqual(build_references.TARGET_PAGE,'PALO_BlueprintBench_Method.html')
        text=(ROOT/'web'/build_references.TARGET_PAGE).read_text(encoding='utf-8')
        self.assertEqual(text.count('data-reference='),35)
        self.assertEqual(text.count(build_references.START),1)
        graph=site.page_graph('method')['@graph']
        node=next(n for n in graph if n.get('@id','').endswith('#benchmark-reference-review'))
        self.assertEqual(len(node['citation']),35)
        self.assertIn('External suites have not been executed',node['description'])

    def test_inputs_are_not_conflated(self):
        text=(ROOT/'web/PALO_BlueprintBench_Corpus.html').read_text(encoding='utf-8')
        for label in ['3-text synthetic test','6-process synthetic test','Real-document generation','Adapter diagnostics']:
            self.assertIn(label,text)
        self.assertIn('200 supplied pages',text)
        self.assertIn('4,994 UTF-8 bytes',text)
        self.assertIn('not the three synthetic procurement texts',text)
        packets=json.loads((ROOT/'internal_tests/2026-11-11-real-procurement/source-packets.json').read_text(encoding='utf-8'))
        self.assertEqual(sum(p['supplied_page_count'] for p in packets),200)
        for p in packets:
            self.assertIn(p['pdf_sha256'],text)
            self.assertIn(p['source_url'].replace('&','&amp;'),text)
        for file in ['PALO_BlueprintBench_Leaderboard.html','PALO_BlueprintBench_NextCycle.html']:
            study=(ROOT/'web'/file).read_text(encoding='utf-8')
            for label in ['Input','Task','Models','Repetitions','Execution','OpenRouter API']:
                self.assertIn(label,study)

    def test_frozen_observation_versions_remain_unchanged(self):
        release=json.loads((ROOT/'release.json').read_text(encoding='utf-8'))
        board=ROOT/'web/downloads/blueprintbench/leaderboard-data.json'
        self.assertEqual(hashlib.sha256(board.read_bytes()).hexdigest(),release['frozen_dataset_sha256']) if 'frozen_dataset_sha256' in release else self.assertEqual(hashlib.sha256(board.read_bytes()).hexdigest(),release['source_dataset_sha256'])
        next_release=json.loads((ROOT/'docs/schema/six-scenario-release.json').read_text(encoding='utf-8'))
        for asset in next_release['assets']:
            path=ROOT/'web/downloads/blueprintbench'/asset['name']
            if asset['name'] in ['next-cycle-results.json','next-cycle-evidence.zip']:self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),asset['sha256'])


if __name__=='__main__':unittest.main()
