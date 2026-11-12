"""Summarise retained seeded-defect diagnostics, not a validated measurement study."""
import argparse
import json
from pathlib import Path
import calibration

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/measurement-diagnostics.json'


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def summarise(name, counts, valid):
    # An invalid envelope supplies no observed true/false decisions.
    tp = counts['detected'] if valid else None
    fn = counts['missed_mutations'] if valid else None
    fp = counts['false_alarms'] if valid else None
    tn = counts['faithful_controls'] - fp - counts['controls_unresolved'] if valid else None
    classified_mutations = tp + fn if valid else 0
    classified_controls = fp + tn if valid else 0
    return {'reviewer': name, 'envelope_valid': valid, 'assigned': counts['assigned'],
            'mutations_assigned': counts['mutations'], 'controls_assigned': counts['faithful_controls'],
            'tp': tp, 'fn': fn, 'fp': fp, 'tn': tn,
            'mutation_unresolved': counts['mutations_unresolved'], 'control_unresolved': counts['controls_unresolved'],
            'invalid': counts['invalid'], 'missing': counts['missing'], 'uncertain': counts['uncertain'],
            'detection_rate_conditional': ratio(tp, classified_mutations) if valid else None,
            'detection_denominator_classified': classified_mutations,
            'false_alarm_rate_conditional': ratio(fp, classified_controls) if valid else None,
            'false_alarm_denominator_classified': classified_controls}


def build():
    original = calibration.build()
    return {'version': 'development-diagnostics-1', 'qualified': False,
            'status': 'internal_retrospective_diagnostics_not_metric_validation',
            'input_manifest_sha256': original['input_manifest_sha256'],
            'scope': 'Six seeded altered statements and twelve faithful controls across three development cases from one authored family; one pass per reviewer.',
            'reference_status': 'Assistant-authored draft labels; not independently adjudicated; no independent source family.',
            'rates': 'Detection TP/(TP+FN) and false alarms FP/(FP+TN), conditional on determinate classifications. Assigned, missing, invalid and uncertain counts remain separate; unknown rates are null.',
            'reviewers': [summarise(r['reviewer'], r['counts'], r['strict_envelope_valid']) for r in original['results']],
            'lexical_baseline': summarise('exact-string post-hoc comparator', original['lexical_baseline']['counts'], True),
            'limitations': ['The reviewer study is not a validation of the evaluator on requirements or generated process graphs.',
                            'One authored family and one pass do not support confidence intervals or generalised model comparisons.',
                            'No model majority vote changes the reference labels.',
                            'Independent defect adjudication, representation invariance and human review remain open.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--check', action='store_true'); args = parser.parse_args()
    result = json.dumps(build(), indent=2, ensure_ascii=False) + '\n'
    if args.check:
        if OUT.read_text(encoding='utf-8') != result:
            raise SystemExit('Measurement diagnostics changed')
    else:
        OUT.write_text(result, encoding='utf-8')
    print('Measurement diagnostics ' + ('verified' if args.check else 'built'))
