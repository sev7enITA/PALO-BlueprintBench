# Procurement diagnostic development bank

Revision 0.1.0-draft, 11 November 2026. Six fictional scenarios, 48 draft probes and seven proposed metamorphic checks. These are development materials, not results, a gold standard, an unseen test set or an independently validated benchmark.

All six scenarios share one automated authoring provenance group. Distinct scenario names do not make independent source families. The controls are original fictional policies, not statements of real procurement law or business practice. Exact underlying author-model identity is unavailable and has not been inferred. Codex drafted the material; no independent domain review has occurred.

## Files and intended use

| File | Purpose |
| --- | --- |
| `case-bank.json` | Six scenario packets with source documents, source-unit IDs and proposed labels. Keep draft labels outside the model request. |
| `workflow-tasks.json` | Six concrete event inputs requiring a source-linked process specification and decision table, beyond copying source sentences. Draft expected decisions must be withheld from model requests. |
| `coverage-matrix.json` | Thirteen design dimensions, with probe IDs. Coverage is a requirement to review, not evidence of discrimination or statistical power. |
| `metamorphic-checks.json` | Six document-order permutations and one controlled threshold change. Proposed expected relations, no executions. |
| `rubric.md` | Draft evidence, modality, atomicity, contradiction and ambiguity rules. |
| `adjudication/reviewer-packet.json` | First-pass sources and statements for the three disputed historical items, without model outputs or frozen expected labels. |
| `adjudication/second-pass-interpretations.json` | Competing interpretations for discussion after independent first-pass submission. |
| `adjudication/custodian-provenance.json` | Exact legacy-source hash and item mapping, including original frozen labels. Do not send it in the first-pass packet. |
| `adjudication/*.template.json` | Empty annotation and adjudication records. They attest to no person or completed review. |
| `sufficiency-gates.json` | Coverage, expert adjudication, construct validation, independent families, statistical design and campaign freeze gates. |
| `validate.py` | Structural/provenance checks only. It does not assess the proposed labels semantically. |

Run `python3 study/next-cycle/validate.py` and `python3 -m unittest discover -s tools -p test_next_cycle.py`. Passing these checks does not make the labels correct or independent.

No new model calls have been made for this bank. No inference charges have been incurred. Existing primary labels and published historical results are unchanged.

## Coverage design

Emergency purchasing tests an exception that removes quotations but leaves authority controls intact. Framework call-offs combine a ledger with a quarterly threshold and cancellation rules. Bank changes separate entry, verification and approval despite an outage exception. Policy transitions require dates and source precedence, with an intentionally unresolved conflicting instruction. Currency approval joins a workbook rate to a strict boundary and role restrictions. Service acceptance separates milestones, receipt substitutions and paused clocks.

The draft bank includes six minimal pairs that differ in a business-critical statement detail. Document-order permutations should preserve the proposed judgments. A threshold counterfactual should change only the declared target judgments and preserve the listed controls. These are hypotheses for human review, not self-proving semantic tests.

## Before another inference campaign

1. Recruit and verify two procurement annotators and a coordinator outside the authoring loop. Record prior exposure to public items. Do not infer independence from string IDs in JSON.
2. Run separate first-pass annotation. Preserve both original records, calculate raw agreement and report confusion by category before adjudication. Three contested items are a focused diagnostic packet, not a reliable estimate of general inter-rater agreement.
3. Adjudicate disagreements with rationale and allowed alternatives. Preserve unresolved cases. Split compound statements when independent propositions would receive different labels. Version changes without rewriting the old labels.
4. Review the 48 new probes, coverage and metamorphic relations. Retire or repair ambiguous controls before freezing a campaign. This bank remains development-exposed even after review.
5. Use independently sourced families for subsequent qualification. Set a meaningful paired effect and precision target; estimate family-level variance in a feasibility study before deciding the required family count. Do not declare six scenarios or 48 probes sufficient for a stable ranking.
6. Freeze eligible tasks, configurations, source/prompt hashes and missingness/retry rules before execution. Reuse the existing cohort only after this gate; adding further model identities is not the current priority.
