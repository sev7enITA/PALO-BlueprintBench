# Metrics and denominators

The executable scorer consumes already-adjudicated references and annotations. It checks their consistency; it does not establish semantic truth itself.

| Output | Definition |
|---|---|
| Scoped precision | Supported unique proposition classes / all assessed unique proposition classes |
| Scoped recall | Recovered required gold items / all required gold items |
| `critical_errors` | Distinct equivalence classes marked as critical errors |
| `critical_error_occurrences` | All critical occurrences, including repetitions |
| Critical inversions per 100 rules | Distinct inverted predeclared critical rules / assigned critical rules, multiplied by 100 |
| `reported_completion_rate` | Reported passes / all assigned task-repetitions |
| `accepted_task_rate` | Tasks satisfying the frozen acceptance contract / all assigned task-repetitions |

A supported proposition cannot also be a critical error. Equivalent annotations must agree. Missing and unexecuted tasks remain in the assigned denominator.

## Empty answers and unavailable values

On an answerable task, empty output has zero recall and undefined precision. Zero inversions with zero coverage is not success. A task explicitly registered as unanswerable can accept a completed empty abstention. Undefined or unavailable values remain null, not zero.

## Acceptance, costs and qualification

Answerable-task acceptance requires completed output, assessed precision and recall meeting the frozen policy, and zero critical errors. Acceptance is separate from the run's declared pass and from independent qualification.

Cost per accepted task includes known charges for failures as well as successes. It remains null when costs or assigned attempts are missing, or no task is accepted. Pending reservations are not settled charges. Active human correction time is not yet measured.

There is no composite PBI formula in this release. `qualified` is always false. [Exact contract](https://github.com/sev7enITA/PALO-BlueprintBench/blob/main/docs/evaluator-contract.md) | [[Evidence contract|Evidence-contract]]
