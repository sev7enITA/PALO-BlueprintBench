# Integration notes on the local model review

These notes are the coding assistant's reconciliation of the actual model answer with the supplied data. They are not an independent human review.

## Completed advisory request

The actual LM Studio response identifies `qwen3.8-27b-uncensored`, HTTP 200, finish reason `stop`, 758 completion tokens, 90.625 seconds. It reviews only the supplied summary and proposed UX. It did not browse the pages, inspect source files or execute a counter-test. No cloud request or paid API call was used.

The first chat request returned HTTP 200 but used 1,792 of its 1,800 completion tokens on reasoning and returned no final answer. The subsequent raw completion used an explicitly closed thinking-channel prefix for a bounded final answer. Both exact requests and raw responses are retained. These advisory settings and outcomes are outside the tested model cohort and cannot be used as benchmark results.

## Advice to adopt

- Keep a visible, brief internal/assistant-draft label beside results, with fuller methodology separately accessible.
- Distinguish assigned API slots from per-model probe judgments. Show complete, failed/incomplete and pre-call-blocked counts separately.
- Include exact model/configuration/evidence identifiers in a challenge issue composer, with no automatic submission.
- Preserve missing/unknown outcomes and costs in exports; do not omit blocked assignments.
- Keep Dataset metadata explicit about the synthetic internal scope; do not add rating/certification claims.
- Treat a separate model's critique as an internal robustness check, not independent validation or external ground truth.

## Corrections to the model's answer

1. The model twice says “18 blocked models”. Actual data contain **one configuration, Sakana Fugu Max, with 18 pre-call-blocked request slots**. There are 18 configurations overall, 17 with dispatched calls. Do not reproduce the review's incorrect wording.
2. There are **324 assigned API request slots across the cohort** and separately **324 assigned probe judgments per model**. Blocked Sakana requests produce 324 missing probe judgments for that configuration. The two occurrences of 324 are not the same denominator.
3. Unknown predictions or costs remain unavailable. Observed counters such as zero dispatched or zero completed calls remain legitimate zero counts. Do not indiscriminately replace every blocked-row field with null.
4. “Rule-Consistent Verification” could itself overstate validity. Prefer “Agreement with draft labels” and an explicit assigned denominator.
5. The review's proposed 5% label perturbation is an **offline label-sensitivity analysis**, not a new adversarial model counter-test. If implemented, it needs a fixed seed, separate copies and results, identical perturbations across configurations, and no change to frozen primary labels. No “near-qualified” status exists in the present data.
6. Independent qualification must follow this project's frozen protocol, including independent domain annotation/adjudication and custody outside the benchmark's tuning loop. A custodian merely distinct from a model vendor is insufficient if the benchmark maintainer still controls the reference labels and test selection.

## Status

No scores, primary labels, qualified counts, datasets or publication files were changed by this review task.
