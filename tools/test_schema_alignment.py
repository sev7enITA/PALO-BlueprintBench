"""Source-bound schema and qualification regression tests; no inference calls."""
import hashlib
import json
from pathlib import Path
import re
import unittest
import build_next_cycle
import research_publication as publication

ROOT = Path(__file__).resolve().parents[1]


def graph(filename):
    text = (ROOT / 'web' / filename).read_text(encoding='utf-8')
    scripts = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', text, re.S)
    if len(scripts) != 1:
        raise AssertionError('Exactly one JSON-LD document required')
    return json.loads(scripts[0])['@graph']


class SchemaAlignmentTests(unittest.TestCase):
    def test_shared_dataset_preserves_observation_version(self):
        expected = build_next_cycle.schema(build_next_cycle.build())['@graph'][1]
        for name in ('PALO_BlueprintBench_Leaderboard.html', 'PALO_BlueprintBench_NextCycle.html'):
            nodes = graph(name)
            self.assertEqual(next(n for n in nodes if n.get('@id') == expected['@id']), expected)
            page = next(n for n in nodes if n.get('@type') in ('WebPage', 'CollectionPage'))
            self.assertEqual(page['version'], publication.PRESENTATION_REVISION)
        landing=graph('PALO_BlueprintBench.html')
        self.assertFalse(any(n.get('@type')=='Dataset' for n in landing))
        self.assertIn('https://paloframework.org/PALO_BlueprintBench_NextCycle.html',landing[0]['relatedLink'])
        self.assertEqual(expected['version'], '2026-11-11.4')
        self.assertIn('not independently validated', expected['creativeWorkStatus'])

    def test_counts_are_derived_from_the_receipts(self):
        data = build_next_cycle.build()
        counts = publication.observed_summary(data)
        self.assertEqual(counts, dict(scenarios=6, unique_propositions=48, configurations=3,
                                     assigned_requests=60, completed_requests=60,
                                     workflow_assignments=18, structurally_valid_workflows=17,
                                     known_cost_usd=2.5539187))
        dataset = build_next_cycle.schema(data)['@graph'][1]
        values = {v['propertyID']: v.get('value') for v in dataset['variableMeasured']}
        for key, value in counts.items():
            self.assertEqual(values[key], value)
        text = (ROOT/'web/PALO_BlueprintBench_NextCycle.html').read_text(encoding='utf-8')
        self.assertIn(publication.visible_summary(data), text)
        self.assertEqual(text.count('id="released-evidence"'), 1)
        self.assertEqual(text.count('id="qualification-plan"'), 1)

    def test_github_evidence_is_immutable_and_hash_matched(self):
        release = publication.release()
        self.assertTrue(release['prerelease'])
        self.assertEqual(release['commit'], 'db6bd39f1ef84f908c5e10ba0f0024a6c969984f')
        archive = ROOT/'web/downloads/blueprintbench/next-cycle-evidence.zip'
        asset = next(a for a in release['assets'] if a['name'] == archive.name)
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), asset['sha256'])
        dataset = build_next_cycle.schema(build_next_cycle.build())['@graph'][1]
        self.assertIn(release['commit'], dataset['isBasedOn']['url'])
        self.assertEqual(dataset['citation']['url'], release['url'])
        self.assertEqual(dataset['distribution'][1]['contentUrl'], asset['url'])

    def test_no_planned_gate_is_promoted_to_completed_validation(self):
        plan = json.loads((ROOT/'docs/qualification-roadmap.json').read_text(encoding='utf-8'))
        self.assertEqual(len(plan['gates']), 6)
        self.assertFalse(plan['independently_qualified'])
        self.assertFalse(plan['numerical_ranks_enabled'])
        self.assertEqual(plan['current_development_study']['assigned_calls'], 36)
        self.assertEqual(plan['current_development_study']['assigned_repetitions'], 3)
        self.assertEqual(plan['current_development_study']['qualification'], 'not_independently_validated')
        self.assertTrue(all(g['acceptance_evidence_received'] is False for g in plan['gates']))
        self.assertIn('not a single-variable causal test', build_next_cycle.schema(build_next_cycle.build())['@graph'][1]['measurementTechnique'])
        manifest = json.loads((ROOT/'web/downloads/blueprintbench/next-cycle-manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['presentation_revision'], publication.PRESENTATION_REVISION)


if __name__ == '__main__':
    unittest.main()
