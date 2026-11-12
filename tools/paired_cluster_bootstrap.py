"""Development-only paired family bootstrap. This does not establish qualification."""
import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path


def nonempty(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + ' must be a nonempty string')
    return value


def quantile(values, probability):
    values = sorted(values)
    position = (len(values) - 1) * probability
    low, high = math.floor(position), math.ceil(position)
    return values[low] + (values[high] - values[low]) * (position - low)


def run(data, config_a, config_b, *, repetitions, minimum_families, samples, seed):
    """Estimate equal-family mean difference with both configurations resampled together.

    Each declared task has the exact same assigned repetitions for both configurations.
    Missing, invalid or incomplete records block the interval rather than becoming zeros.
    The task inventory and qualification of families must be established externally.
    """
    nonempty(config_a, 'configuration A'); nonempty(config_b, 'configuration B')
    if config_a == config_b:
        raise ValueError('Configuration IDs must differ')
    if type(repetitions) is not int or repetitions < 3:
        raise ValueError('At least three assigned repetitions are required')
    if type(minimum_families) is not int or minimum_families < 2:
        raise ValueError('Specify a minimum of at least two families')
    if type(samples) is not int or samples < 100 or samples > 100000:
        raise ValueError('samples must be between 100 and 100000')
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    if not isinstance(data, dict):
        raise ValueError('Input must be a JSON object')
    tasks = data.get('tasks')
    observations = data.get('observations')
    if not isinstance(tasks, list) or not tasks or not isinstance(observations, list):
        raise ValueError('A nonempty frozen task inventory and observation list are required')
    declared = set()
    for task in tasks:
        if not isinstance(task, dict) or set(task) != {'family_id', 'task_id'}:
            raise ValueError('Task must contain family_id and task_id')
        pair = (nonempty(task['family_id'], 'family_id'), nonempty(task['task_id'], 'task_id'))
        if pair in declared:
            raise ValueError('Duplicate task assignment')
        declared.add(pair)
    families = sorted({f for f, _ in declared})
    expected = {(f, t, r, c) for f, t in declared for r in range(1, repetitions + 1) for c in (config_a, config_b)}
    seen = {}
    for row in observations:
        if not isinstance(row, dict) or not {'family_id', 'task_id', 'repetition', 'configuration_id', 'status'} <= set(row):
            raise ValueError('Observation lacks required fields')
        if type(row['repetition']) is not int:
            raise ValueError('Repetition must be an integer')
        key = (nonempty(row['family_id'], 'family_id'), nonempty(row['task_id'], 'task_id'),
               row['repetition'], nonempty(row['configuration_id'], 'configuration_id'))
        if key not in expected or key in seen:
            raise ValueError('Unexpected or duplicate observation')
        if row['status'] not in ('completed', 'incomplete', 'failed', 'not_run'):
            raise ValueError('Invalid observation status')
        if row['status'] == 'completed':
            n, d = row.get('numerator'), row.get('denominator')
            if type(n) is not int or type(d) is not int or not 0 <= n <= d or d <= 0:
                raise ValueError('Completed observations require valid integer counts')
        elif row.get('numerator') is not None or row.get('denominator') is not None:
            raise ValueError('Incomplete observations must not contain scored counts')
        seen[key] = row
    blockers = []
    if len(families) < minimum_families:
        blockers.append('insufficient_families')
    missing = sorted(expected - set(seen))
    incomplete = sorted(k for k, v in seen.items() if v['status'] != 'completed')
    if missing:
        blockers.append('missing_observations')
    if incomplete:
        blockers.append('incomplete_observations')
    fixed_denominators = {}
    for (family, task, _, _), observation in seen.items():
        if observation['status'] == 'completed':
            current = observation['denominator']
            if (family, task) in fixed_denominators and fixed_denominators[(family, task)] != current:
                raise ValueError('All repetitions of a task must use the same fixed denominator')
            fixed_denominators[(family, task)] = current
    for family, task in sorted(declared):
        for repetition in range(1, repetitions + 1):
            a = seen.get((family, task, repetition, config_a)); b = seen.get((family, task, repetition, config_b))
            if a and b and a['status'] == b['status'] == 'completed' and a['denominator'] != b['denominator']:
                raise ValueError('Paired observations must use the same fixed denominator')
    result = {'status': 'blocked' if blockers else 'development_diagnostic', 'qualified': False,
              'families': len(families), 'minimum_families': minimum_families,
              'tasks': len(declared), 'assigned_observations': len(expected), 'received_observations': len(seen),
              'missing': [list(x) for x in missing], 'incomplete': [list(x) for x in incomplete],
              'blockers': blockers, 'estimand': 'Equal-family mean of paired aggregate rates, A minus B',
              'samples': samples, 'seed': seed, 'interval': None, 'point_estimate': None,
              'limitations': ['Development-only diagnostic; external custody, gold, independence and sampling assumptions are not established.',
                              'The frozen inventory must include every assigned task; a missing inventory entry cannot be inferred from observations.',
                              'Repetitions stay within sampled family clusters. A small family count cannot establish a reliable population interval.']}
    if blockers:
        return result
    totals = defaultdict(lambda: [0, 0])
    for (family, _, _, config), row in seen.items():
        totals[(family, config)][0] += row['numerator']
        totals[(family, config)][1] += row['denominator']
    differences = [totals[(f, config_a)][0] / totals[(f, config_a)][1] - totals[(f, config_b)][0] / totals[(f, config_b)][1] for f in families]
    rng = random.Random(seed)
    resampled = [sum(differences[rng.randrange(len(families))] for _ in families) / len(families) for _ in range(samples)]
    result['point_estimate'] = sum(differences) / len(differences)
    result['interval'] = {'level': 0.95, 'method': 'paired family-cluster percentile bootstrap',
                          'lower': quantile(resampled, 0.025), 'upper': quantile(resampled, 0.975)}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path); parser.add_argument('--a', required=True); parser.add_argument('--b', required=True)
    parser.add_argument('--repetitions', required=True, type=int); parser.add_argument('--minimum-families', required=True, type=int)
    parser.add_argument('--samples', required=True, type=int); parser.add_argument('--seed', required=True, type=int)
    args = parser.parse_args()
    def strict_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    def reject_constant(value):
        raise ValueError('Invalid numeric constant: ' + value)
    data = json.loads(args.input.read_text(encoding='utf-8'), object_pairs_hook=strict_pairs, parse_constant=reject_constant)
    print(json.dumps(run(data, args.a, args.b, repetitions=args.repetitions, minimum_families=args.minimum_families,
                         samples=args.samples, seed=args.seed), indent=2))


if __name__ == '__main__':
    main()
