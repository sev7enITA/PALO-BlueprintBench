# Qualification protocol and next study

Presentation revision 2026-11-11.6. **Development collection has started; independent qualification remains pending.**

The current [six-scenario release](https://github.com/sev7enITA/PALO-BlueprintBench/releases/tag/study-2026-11-11-six-scenario.1) is development-exposed internal engineering evidence: six fictional scenarios, 48 provisional propositions, one authoring group, one repetition and 60 requests. Seventeen of eighteen workflow drafts pass structural checks. This is not a measurement of generated-specification semantic accuracy. All historical labels, source bytes and outcomes remain frozen.

The [real-document generation study](https://paloframework.org/PALO_BlueprintBench_Generation.html) has started with three public procurement documents, 200 supplied pages, three model IDs and three assigned repetitions. The original 27 assignments are retained; the Google supplement was cancelled before dispatch. Models generate requirements, process steps and executable decision rules without receiving the assessment situations. Reference outcomes are pre-output assistant drafts. The results page reports the current completion, upstream failures, unknown costs and retained reserves; assigned work is not presented as completed. The v1.1 mechanical quote-check correction joins a PDF hyphen and line break while retaining the hyphen, with original v1.0 analysis and the correction record preserved. It does not change source content or semantic labels.

## 1. Documents and difficulty

Assemble separately licensed procurement document families: source policy, tender or contract, schedules, amendments and operational instructions. Record publisher, edition, effective dates, rights, retrieval timestamp, page count, exact bytes and extracted-text hashes. Packs should contain tens of meaningful pages and real cross-document dependencies, not padding to satisfy a byte threshold. Include exception chains, conflicting clauses, version precedence, ambiguous scope and genuinely unanswerable requirements. Extraction/OCR failures are distinct from interpretation failures.

Use a development-only sample to test whether the tasks discriminate. A 60–85% result range for strong systems is a proposed diagnostic after the metric is validated, not an acceptance target or a reason to alter gold. Inspect ceiling effects and item difficulty across systems and categories. Do not target an average by introducing ambiguity, removing easy items post hoc or selecting a sealed test after seeing model outputs. Preregister sampling and the construct before the custodian releases any held-out scores.

## 2. Generation as the primary task

Give each system the documents and a neutral specification contract. Do not give it the propositions or candidate labels it will be scored against. Require source-linked atomic requirements, actors and responsibilities, typed entities and identifiers, decision guards, process transitions, exceptions, temporal applicability, unresolved questions and unsupported design choices explicitly separated from source facts.

The primary assessment covers generated content and omissions against a persistent expert proposition bank. It must support alternative faithful formulations, explicit forbidden inferences, mandatory scope and predeclared critical-error severity. Review all substantive output spans, including submitter-labelled non-claims. Record the source-to-text and output-to-proposition transformations, so extraction, generation and judging errors can be separated. Recall uses the fixed eligible gold inventory; precision uses reviewed emitted equivalence classes. Also show occurrence counts and human correction effort. Classification of prewritten statements remains a secondary diagnostic. An exported JSON blueprint does not prove an executable or approved application.

## 3. Freeze the semantic rubric before labels

This proposed convention requires approval by the external domain panel before use as gold:

| Label | Proposed decision rule |
| --- | --- |
| Supported | The source entails the atomic statement in the same actor, action, modality, temporal and jurisdictional scope. |
| Contradicted | The source entails the negation in that same scope. Explicit closure can support contradiction only within the scope it closes. |
| Not established | Neither the assertion nor its negation is entailed. Missing detail, an unclosed set of grounds or an unspecified implementation stays open. |
| Unresolved conflict | Applicable sources give conflicting requirements and no declared precedence resolves them, or the task cannot select one material interpretation. |

An amount-triggered approval rule closes only amount grounds; it does not exclude other approval grounds. “May” does not create a duty or establish a prohibition. “Records” is not automatically “must record” unless a declared document convention makes it normative. Separate a duty to request something from a duty about its channel if a request is made. Split compounds before adjudication. Document which source establishes closure, applicability or precedence; never use annotator intuition alone. Unresolved gold items remain explicit and are excluded only under a frozen policy, with exclusions and coverage reported.

Two procurement experts independently annotate sources before seeing model outputs or model identities. A distinct third expert adjudicates. Record verified roles, conflicts, independent first-pass labels, evidence spans, elapsed annotation time and decisions. Publish raw agreement and an appropriate chance-corrected agreement statistic by category, together with counts, prevalence and uncertainty; agreement is not proof of truth. Reusable equivalence classes reduce repeat annotation, but new claims and changed context require review. Automated suggestions remain advisory and must not be described as human gold.

## 4. External custody

No custodian or domain annotators have yet been appointed. New held-out families must be chosen and controlled outside PALO engineering. Public or previously inspected material cannot be relabelled as hidden. Keep encrypted gold, identity attestations, access logs, preregistered commitments, release dates, appeals and conflict disclosures under the agreed external process. A signed hash alone does not establish independence or scientific quality. The current local freeze and postcollection GitHub release do not meet this gate.

## 5. Execute the seeded-defect study

The repository contains internal calibration diagnostics, including faithful controls and seeded changes. They do not complete independent metric validation. Before the next scored campaign, freeze human-adjudicated controls and defects spanning modality, negation, actor, exception, threshold/unit, temporal scope and unsupported additions. Preserve source and candidate batch across paired conditions, including order, response contract and decoding conditions. The present threshold comparison changed eight candidate propositions to six; it is retained as a confounded development observation, not reused as a clean causal test.

Measure true positives, false negatives, false positives and true negatives separately. Detection is TP/(TP+FN); false-alarm rate is FP/(FP+TN). Publish conditional denominators plus total assigned opportunities, abstentions, unrun calls and parse failures; a missing response is neither a negative decision nor a free pass. Show severity-specific results and family-level uncertainty. Choose required sensitivity, acceptable false alarms and practically meaningful effects with domain experts before observations, then estimate family count from a separate pilot. Do not choose thresholds after inspecting results. Known rubric disagreements must be resolved before declaring this study successful.

## 6. Conditions, repeats, bands and rank eligibility

Preregister model identity and revision, serving provider, quantisation, prompt/extraction/retrieval/harness hashes, context and output budgets, supported reasoning settings, sampling controls, timeout, concurrency, caching, prices and retry policy. A shared “high” label is not equal compute. Use a common supported-resource track and, if useful, a separately labelled model-optimised track; do not silently pool incompatible settings or collapse different systems into a model identity.

Run at least three repetitions for every fixed assignment. Repetitions do not create new independent document families. Define the source-family unit, primary metrics, critical-error rules and a meaningful paired difference before inference. Estimate family-level variance in development and preregister an adequate family count and stopping rule. Preserve the same resampled families for paired configuration comparisons. Use a documented cluster-aware procedure, with sensitivity analysis when few families make uncertainty unstable. Cost and timing require equivalent accounting, retry coverage and scheduling before they can support comparative claims.

Publish descriptive bands only when their assumptions and coverage are supportable. Separate missingness from semantic scores. Preregister multiplicity control for the planned paired comparisons and require both uncertainty and practical-effect criteria before asserting an order. Disjoint marginal intervals alone are not a complete ranking procedure; overlapping intervals do not establish equivalence. If evidence leaves an ordering unresolved, show that explicitly instead of forcing consecutive positions or treating pairwise ties as transitive. No qualified ranks or bands are enabled for the current synthetic cycle.

## Acceptance evidence and references

[The machine-readable gate register](qualification-roadmap.json) tracks the current unmet gates. Its booleans are a status record, not a mechanism for granting qualification. The next promotion requires verified external roles, independent gold, completed metric validation, frozen comparative conditions, sufficient independent families and independent reproduction.

The evidence and reproducibility emphasis is informed by [BetterBench](https://arxiv.org/abs/2411.12990). Dataset markup follows [Schema.org Dataset](https://schema.org/Dataset) and [Google's dataset guidance](https://developers.google.com/search/docs/appearance/structured-data/dataset). These references do not endorse PALO, validate its metric or guarantee search visibility.
