"""Keep the current public release distinct from historical and qualified evidence."""
import hashlib
import json
from pathlib import Path
import re
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DL = ROOT / 'web/downloads/blueprintbench'


class ReleaseContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.release = json.loads((ROOT / 'release.json').read_text(encoding='utf-8'))

    def test_current_component_and_contract_versions_agree(self):
        source = (ROOT / 'evaluator/blueprintbench.py').read_text(encoding='utf-8')
        version = re.search(r'^VERSION = "([^"]+)"', source, re.M).group(1)
        self.assertEqual(version, self.release['evaluator_version'])
        schema = json.loads((ROOT / 'evaluator/evidence.schema.json').read_text(encoding='utf-8'))
        self.assertEqual(schema['$defs']['campaign']['properties']['benchmark_version']['const'], version)
        self.assertFalse(self.release['independent_human_review'])
        self.assertEqual(self.release['independently_qualified_results'], 0)

    def test_manifest_and_current_copies_share_revision(self):
        manifest = json.loads((DL / 'release-manifest.json').read_text(encoding='utf-8'))
        for key in ['release_tag', 'evaluator_version', 'content_revision', 'leaderboard_revision']:
            self.assertEqual(manifest[key], self.release[key], key)
        self.assertEqual(json.loads((DL / 'release.json').read_text(encoding='utf-8')), self.release)
        self.assertEqual(manifest['source_dataset_revision'], self.release['frozen_dataset_revision'])
        self.assertEqual(manifest['source_dataset_sha256'], hashlib.sha256((DL / 'leaderboard-data.json').read_bytes()).hexdigest())
        status = json.loads((DL / 'release-status.json').read_text(encoding='utf-8'))
        self.assertEqual(status['tool_version'], self.release['evaluator_version'])
        self.assertEqual(status['release'], self.release['release_tag'])
        self.assertEqual(status['content_revision'], self.release['content_revision'])
        self.assertFalse(status['independent_human_review'])
        archived = json.loads((ROOT / 'results/release-v0.3.0-pilot.1/release-status.json').read_text(encoding='utf-8'))
        self.assertEqual(archived['tool_version'], '0.2.0')
        for name in ['docs/leaderboard-method.md', 'docs/announcement.md', 'docs/launch-readiness.md']:
            self.assertIn(self.release['content_revision'], (ROOT / name).read_text(encoding='utf-8'))

    def test_toolkit_embeds_version_and_legacy_warning(self):
        with zipfile.ZipFile(DL / 'toolkit.zip') as package:
            base = 'palo-blueprintbench/'
            self.assertEqual(json.loads(package.read(base + 'RELEASE.json')), self.release)
            self.assertIn(('VERSION = "' + self.release['evaluator_version'] + '"').encode(), package.read(base + 'blueprintbench.py'))
            warning = package.read(base + 'EVALUATOR-0.2-WARNING.md').decode('utf-8')
            self.assertIn('EV-01', warning)
            self.assertIn('Do not use', warning)
            self.assertIn('v0.3.0-pilot.1', warning)

    def test_current_brand_archive_has_no_testing_seal(self):
        with zipfile.ZipFile(DL / 'brand-kit.zip') as package:
            self.assertFalse(any('badge' in name.lower() for name in package.namelist()))
            self.assertTrue(any(name.endswith('blueprintbench-logo.png') for name in package.namelist()))

    def test_historical_version_not_rewritten(self):
        original = json.loads((ROOT / 'results/release-v0.3.0-pilot.1/toolkit-verification.json').read_text(encoding='utf-8'))
        self.assertEqual(original['evaluator_version'], '0.2.0')
        old_demo = json.loads((ROOT / 'results/synthetic-v0.3-draft/result.json').read_text(encoding='utf-8'))
        self.assertEqual(old_demo['tool_version'], '0.3.0-dev.1')
        current = json.loads((ROOT / 'results/synthetic-v0.3.0/result.json').read_text(encoding='utf-8'))
        self.assertEqual(current['tool_version'], self.release['evaluator_version'])
        self.assertFalse(current['qualified'])


if __name__ == '__main__':
    unittest.main()
