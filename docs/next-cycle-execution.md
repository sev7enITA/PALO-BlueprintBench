# Next-cycle internal engineering feasibility

Publication revision `2026-11-11.4` adds a separate source-backed execution page. It does not change the original 18-model results, reinstate quality/cost/time ranks, or issue a new evaluator release. The evaluator remains `v0.3.0-internal.1`; the former 0.2 package remains identified as historical in the main release documentation.

## Scope and execution boundary

The campaign has six fictional procurement scenarios with 48 provisional propositions, six workflow specification tasks, seven controlled source variations and one blind-format packet covering the three historical disputed items P002, P013 and P036. All scenarios have one automated authoring provenance group. They are exposed development material, not six independently sourced case families.

Three existing configurations receive 20 fixed assignments each, for 60 requests, one repetition per assignment. Configuration identifiers, exact provider pins, model parameters, endpoint snapshots, request order and source/prompt hashes are retained in `internal_tests/2026-11-11-next-cycle/`. The frozen campaign manifest records the user-authorised engineering-feasibility exception before human adjudicators are available. It does not grant a comparison or qualification gate. Local hashes establish content consistency, not independent custody or trusted time.

This is a bounded harness experiment. It is not an end-to-end test of the installed Workbench application or a 100 MB document ingestion claim. A workflow export is an unapproved model draft, with business approval still required. The emergency workflow tests approval and quotation decisions, not complete purchase-order issuance eligibility.

## Provisional comparisons

The source rubric distinguishes `supported`, `contradicted`, `not_established` and `unresolved_conflict`. A mismatch with the authored key is a disagreement to investigate, not an established model error. The response contract checks IDs, coverage, structure and citations. It does not validate the underlying interpretation.

`policy-transition-P05` remains assigned and its prediction is retained, but is excluded from provisional matching before inference because of rubric sensitivity. Per configuration, the base track therefore has 48 assigned and 47 scoreable propositions; metamorphic variants have 54 assigned and 53 scoreable propositions. Workflow tasks contain 16 decision assignments. All three legacy items are unscored advisory judgments without an adjudicated answer key.

Metamorphic observations compare the baseline and transformed input, including document order and the specified threshold counterfactual. The inspector shows the exact input packet for each variant. Consistency with a proposed relation does not establish that either answer is correct.

No model response fills a human annotation template. The blank first-pass, second-pass and adjudication packets remain separate. Expert review must decide the disputed labels, permissible alternatives and rubric changes before a future qualified comparison.

## Postrun rubric observation

An automated review after observing Claude Opus 5.5's response identified a competing reading for `bank-change-P07`. The source states that the log records operator and approver IDs; the proposition says it **must** contain them. A prescriptive specification reading supports the frozen `supported` key. A strictly descriptive reading makes the introduced obligation `not_established`. Both are defensible until a human adjudicator resolves the rubric convention.

This is a postrun advisory observation, not a blind review or a proven model failure. The frozen label, disagreement count and denominator are retained. No retroactive exclusion or extra accepted label is introduced. This differs from `policy-transition-P05`, whose scoring exclusion was recorded before inference. The [retained observation](../internal_tests/2026-11-11-next-cycle/review/postrun-semantic-observations.json) includes the raw-response hash, both readings and future adjudication questions. It does not change this campaign's frozen inputs.

## Counterfactual advisory review

The threshold counterfactual retains 18 paired observations across three configurations: 15 satisfy their proposed relation and three do not. Two deviations concern whether P01 asserts a general approval duty or only an amount-triggered duty. One is a P07 label-invariance deviation under changing scope interpretations. This is an automated postrun interpretation, not independently adjudicated model error.

The source threshold changes from EUR 12,000 to EUR 15,000, but the request also removes two propositions (eight become six). The complete request is therefore not a strict single-variable experiment. The threshold edit alone cannot be identified as the cause of label instability. All frozen expected labels, counts and exclusions remain unchanged. No majority vote supplies a gold label. The [counterfactual advisory](../internal_tests/2026-11-11-next-cycle/review/counterfactual-advisory-review.json) preserves the paired outputs, hashes and scope questions for human adjudication.

## Missingness, costs and exports

Every fixed request remains in the public analysis, including `not_run`. The explorer separates provider completion, response-contract validity, classified judgments, absent judgments, unassessed output and draft-label divergence. A malformed response does not silently become a semantically wrong judgment, and an absent response does not disappear from the denominator.

The total authorised account budget remains USD 40, including earlier work. This campaign has a separate USD 12 ceiling within that total. The dashboard reports provider-reported account usage, known campaign charges, the earlier unresolved reserve, current unresolved reserves and conservative remaining headroom. Reservations are upper bounds, not invoices. Unknown costs are not replaced by zero; missing runtime measurements remain unavailable.

The request inspector distinguishes the configured 32,768 output-token ceiling from observed prompt, completion, total, reasoning, cached and cache-write tokens reported in each provider receipt. Missing fields stay unavailable, including for undispatched assignments. Reasoning/cache counters may overlap the total; they are not added again or treated as a demonstration of maximum model context capacity. Returned model/provider identity and provider request IDs remain visible beside the pinned configuration.

JSON and CSV export the current request selection. JSON retains filters, evidence status, source hashes and budget context. CSV includes per-request status, assignments, classifications, exclusions through unscored counts, provisional comparisons and cost status. Complete observations, the deterministic source/evidence ZIP and a SHA-256 manifest are downloadable. Request, raw-response and blueprint links point to GitHub; narrative Markdown documents are not served as web landing pages.

## Publication and checks

`python3 tools/build_next_cycle.py` derives the publication from retained analysis and source packets. `--check` fails on byte drift. The builder checks analysis task/schedule hashes, fixed assignment cardinality and frozen case-source hashes when the manifest is present. With no analysis, the page reports preparation rather than execution.

The page has one JSON-LD graph containing `WebPage` and `Dataset`. Its description explicitly identifies internal engineering feasibility and provisional expectations. No `Review`, `aggregateRating`, score, model rank or independently validated result is marked up. The dataset export and page revision share one generator. These checks establish local data/content consistency, not Google indexing, a rich-result award or independent benchmark validation.

`tools/verify_next_cycle_browser.cjs` exercises the real generated snapshot, filters, detail/source inspection, JSON/CSV downloads, JSON-LD agreement, mobile layouts, pending/error states and a clearly synthetic rendering fixture for unsafe text. Rendering fixtures never enter the published campaign. The publication manifest records hashes for the HTML, script, stylesheet, observations and evidence archive.
