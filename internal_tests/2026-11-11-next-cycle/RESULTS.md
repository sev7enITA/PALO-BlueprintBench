# Six-scenario internal feasibility results

Recorded 11 November 2026. Publication revision 2026-11-11.4. This is an internal engineering study with provisional labels, one automated authoring group and no independent human adjudication. The original cohort and evaluator release remain unchanged.

All 60 assigned API requests completed. The serial collection window was 42.09 minutes; this is not a Workbench application throughput measurement. Three existing model identities were used with separately frozen serving configurations.

| Track | Requests | Classified / assigned | Draft matches / scoreable assignments | Divergences | Unassessed |
| --- | ---: | ---: | ---: | ---: | ---: |
| verification | 18 | 144 / 144 | 140 / 141 | 1 | 0 |
| workflow | 18 | 45 / 48 | 44 / 48 | 1 | 3 |
| metamorphic | 21 | 162 / 162 | 155 / 159 | 4 | 0 |
| legacy | 3 | 9 / 9 | Not scored | 0 | 0 |

## Findings

- All 18 workflow responses were exported: 17 structurally usable model drafts and one unusable draft containing a dangling predicate reference. No draft is business-approved or proven executable.
- The 48 unique base propositions produced 144 classifications. P05 was excluded before inference, leaving 141 scoreable assignments. There were 140 draft matches and one draft-label disagreement; this is not independently measured accuracy.
- Reversing document order preserved all 141 scored judgments. Three additional P05 pairs remained excluded. In the threshold comparison, 15 of 18 proposed relations held. The comparison also changed the candidate batch from eight to six propositions, so it does not isolate a single causal input variable.
- P002 and P036 received two not_established opinions and one contradicted opinion. P013 received three not_established opinions. Majority agreement does not adjudicate the labels.
- Postresponse reviews identify scope ambiguity in bank-change-P07 and counterfactual P01, and an observed interpretation change in counterfactual P07. Original labels, denominators and deviations remain intact.

## Accounting

Provider-reported charge for this cycle: **USD 2.5539187**. No current request has an unknown charge. Conservative cumulative commitment, including the prior unresolved reserve and protection against provider-ledger lag: **USD 21.581286351 of USD 40**. These are provider request charges, not a complete total-cost-of-ownership measure.

## Review and reproduction

Use [execution method](README.md), [frozen manifest](manifest.json), [analysis](analysis.json), [full archive review](review/postrun-review.md), [legacy opinions](review/legacy-advisory-review.md) and [counterfactual review](review/counterfactual-advisory-review.md). Run `python internal_tests/2026-11-11-next-cycle/analyse.py` and `python -m unittest discover -s tools -p test_next_cycle_evidence.py` from the repository root.

The next study needs expert adjudication of obligation/description and closure scope, an equal-batch counterfactual design, additional issuance-eligibility checks and independently sourced families. No quality, cost or time ranking follows from this cycle.
