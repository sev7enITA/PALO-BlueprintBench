# Measurement Validation Protocol (Draft)

Status: development design. No external panel has approved the annotation guidelines, the defect key, the estimand or this protocol. The current evaluator remains unqualified. Do not use these development checks to assign a PALO Blueprint Index or ranking.

## Existing Diagnostics

The retained calibration contains six seeded altered statements and twelve faithful controls across three development cases from one authored family. Three model reviewers were requested once. The Fable capture classified all 18 against assistant-draft labels: six detected mutations out of six and zero false alarms out of twelve controls. GLM and Gemini captures failed the strict response contract; their detection and false-alarm rates are unavailable, not zero. The post-hoc exact-string comparator detects six of six mutations and raises six false alarms on twelve controls. These observations are not independent validation, a representative sample or a model ranking. [Machine-readable summary](measurement-diagnostics.json) · [Original calibration evidence](../internal_tests/2026-11-11-calibration/README.md).

## Independent Study Design

1. The independent custodian selects new, non-exposed procurement document families. Two domain experts independently annotate the sources and the initially drafted claims without seeing model identities or outputs; a separate adjudicator resolves disagreements. Declare the source, scope, approved rubric version, eligible propositions, criticality and allowed alternatives before scoring. Record unresolved conflicts separately.
2. Predefine, before inspection of model output, transformations representing modality, negation, actor, exception, threshold, unit, applicability, temporal scope, unsupported addition and omission. Have experts adjudicate whether each proposed defect is truly defective in the applicable scope. Preserve the original, transformed version, source reference and transformation record.
3. Include faithful controls of equal scope. Tests cover atomic generated requirements, state and dependency graphs, and executable decision rules as distinct outcomes. A graph test must identify required nodes and edges, guards, branch outcomes and any intended start/end semantics; weak connectivity alone does not establish source fidelity or executable reachability. Do not treat missing graph nodes as correct because they do not appear in a generated graph.
4. Present defective and faithful material in balanced blinded packets. Annotators record each item as detected, not detected or unresolved, with evidence, reason, individual identity, applicable rubric and time. A third reviewer adjudicates. Invalid responses, abstentions, missing annotations and non-dispatched assignments remain separate; they are not false negatives or true negatives.
5. For determinate items report TP, FN, FP and TN, detection TP/(TP+FN) and false-alarm rate FP/(FP+TN). Also report all assigned and unresolved items and rates by defect category. Report uncertainty by independently sampled document family when the design supports it. Predefine minimum acceptable detection, false-alarm rate and sample-size rule with experts; no target has been approved.

## Development Calibration

Use only development materials to explore a reference-model range of approximately 60–85% on a defined metric. Record selection, task difficulty changes and configurations prospectively. Do not alter reference keys to force a target. If a reference model remains at the ceiling, keep calibration open and report it. Do not tune, replace or inspect sealed material to reach this range. A useful difficulty range does not establish measurement validity.

## Representation Invariance

Before a scored campaign, identify transformations that preserve meaning and have an expert confirm that preservation for each family. Candidate controls include JSON key order and whitespace, reordering of unordered requirements, graph node renaming with a bijective mapping, and reordering of graph edges. Do not reorder first-match decision rules, change guards, remove scope, or transform text without evidence of equivalence. Include negative controls that reverse modality, remove a required exception or detach a required graph component. Freeze the transformation set, expected equivalence and test protocol before observing target results.

Current engineering tests cover order and identifier changes for weak-connectivity graphs and order of synthetic evaluator attempts. They do not prove paraphrase invariance, semantic correctness, complete graph coverage or representation invariance of the complete measurement pipeline.

## Family-Cluster Bootstrap

`tools/paired_cluster_bootstrap.py` is a development-only utility for a declared inventory of tasks, configurations and at least three repetitions. It resamples each family as a paired cluster, retaining all of its tasks and repetitions. It compares equal-family means of rates using matching fixed denominators. Missing or incomplete observations block the interval rather than becoming zero; the required minimum family count, number of resamples and seed must be specified. Tests use synthetic fixtures only.

An external study must preregister family independence, inventory, eligibility, estimand, missing-data policy, minimum family count, primary comparison, practical difference and multiplicity rule. The utility does not verify these claims, select a sufficient sample, establish independence, calculate a rank or qualify any result. Bootstrap intervals do not repair a small or biased set of families. Separation of marginal intervals is not by itself a validated pairwise ranking rule.
