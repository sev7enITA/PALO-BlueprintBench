# Six-scenario internal feasibility cycle

This campaign tests document interpretation and the production of source-linked draft blueprints. Its labels and sources were authored within PALO development. Results are internal engineering evidence, not independent adjudication or a PALO Blueprint Index.

## Fixed work allocation

The request builder produces 20 tasks per model:

| Track | Requests | Assigned judgments per model |
| --- | ---: | ---: |
| Base document verification | 6 | 48 propositions, 47 draft-scoreable |
| Source-linked process blueprint | 6 | 16 named event decisions |
| Source order and threshold transformations | 7 | 54 proposition judgments, 53 draft-scoreable |
| Blind legacy advisory review | 1 | 3 unscored items |

Three models therefore require 60 assigned requests. Assignment is fixed before inference. The campaign runner owns the exact model catalogue, budget ceiling, maximum output, reasoning setting, scheduling and immutable freeze. This module never calls a provider. One repetition only supports feasibility and diagnostic comparisons.

`policy-transition-P05` remains assigned and visible but is excluded from draft-label agreement and metamorphic invariance counts. The pre-inference semantic review identified multiple defensible interpretations of its metaclaim. Its draft label is preserved. The blind legacy packet retains all original statement text, including the compound legacy proposition; it contains no old labels or competing model answers.

## Requests and contracts

`prepare.py` builds provider messages from source text, candidate statements, concrete workflow inputs and requested decision names. Draft dispositions and expected decisions are kept in `assessment_key`, outside both messages and the provider response schema. The runner must send only `messages` and `response_schema`; never send the complete task object.

Source units retain their identifiers. Legacy units are namespaced by blind item ID to prevent citations from one item being attached to another. Document-order variants reverse documents without altering source units. The threshold variant changes only the preregistered units and sends the two changed probes and four declared invariants. Its source packet receives a distinct SHA-256 digest.

Verification responses must contain every assigned ID exactly once with a label, rationale and source-unit references. Workflow responses contain typed entities and fields, source-linked decision predicates, guarded state transitions and every requested concrete decision. Predicate references and source references are checked. These checks demonstrate structural correspondence only; they cannot prove that a guard or citation correctly interprets its source.

Parsing is strict JSON with duplicate-key and non-finite-number rejection. No fenced-output repair, answer imputation or partial scoring occurs after a response contract failure.

## Archive and offline analysis

The runner writes:

```text
tasks.json
schedule.json
runs/<assignment-id>/request.json
runs/<assignment-id>/record.json
runs/<assignment-id>/output.txt
```

The task list and schedule are fixed denominators. Every assignment contributes to analysis, including requests not dispatched, API failures, missing outputs and malformed outputs. `missing` means no usable response content was received; `unassessed` means content exists but fails the response contract. Neither category is silently dropped or scored as semantic agreement. Unknown costs remain unknown; the known-cost sum is not represented as a reconciled total.

Run offline:

```sh
python internal_tests/2026-11-11-next-cycle/analyse.py
python -m unittest discover -s tools -p test_next_cycle_execution.py -v
```

`analysis.json` records source/task hashes, per-assignment judgments and citations, separate counts by model and track, and paired metamorphic relationships. Ordering invariance is consistency only. Counterfactual checks compare the observed before/after predictions against a preregistered development relation; they do not turn a model into its own semantic judge. Missing pairs and rubric-sensitive pairs are explicit.

Every received workflow response gets a `blueprints/<assignment-id>.json` export. A failed response becomes an `unusable_model_draft`, not an accepted artifact. Every blueprint has `qualified: false`, `business_approved: false` and `business_approval_required: true`. Export is not executable process verification or Workbench application end-to-end validation.

## Coverage and adjudication limits

All six scenarios share one automated authoring provenance group. They are development-exposed synthetic cases, not six independent source families. Agreement with assistant-draft labels is not accuracy against expert gold. The emergency workflow covers approval and quotation decisions but does not establish full issuance eligibility: documented urgency, actor identity and other prerequisites need separate process coverage.

The P002/P013/P036 review outputs are automated advisory first passes. Human annotation templates remain unfilled. External domain annotators must still independently interpret the sources, document disagreements and adjudicate the applicable labels. No rank, superiority claim, confidence interval or independently qualified result follows from this cycle.
