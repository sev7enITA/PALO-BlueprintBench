# BlueprintBench internal test results: method and qualification

Publication revision `2026-11-11.3`, shared with `release.json`, the public page and announcement. The source observation snapshot remains frozen as dataset `2026-11-11.2`; its exact SHA-256 is recorded in `release.json`. Dataset metadata identifies those unchanged evidence bytes, while page and release metadata identify the new presentation. These are intentionally distinct versions, not competing current methods.

The internal-results dashboard is a research interface for inspecting configurations and evidence. As of 11 November 2026 there are **zero independently qualified results** and no PALO Blueprint Index or numerical model ranks. The interface does not establish superiority over Arena or any other benchmark.

## Separate cohorts

The internal procurement view contains the original three-model baseline and two subsequent extensions, with 18 distinct model IDs and three repetitions per task. The original 54 assignments and their outcomes are preserved. The twelve-model extension adds 216 assignments; the exact legacy-identity supplement adds 54. Sakana Fugu Max has 18 pre-call-blocked assignments because the endpoint catalogue does not expose the bounded-output and response-format controls required by this protocol. Those assignments are missing, not successful or semantic failures. Live recorded/completed counts come from the shared data file. All three cases belong to one maintainer-authored synthetic family; expected labels are assistant drafts. The extensions were selected after observing the baseline, and retain separate campaign IDs.

The historical adapter cohort contains ten configurations on three passages, 4,994 UTF-8 bytes of document text. Settings differ and there are no repetitions or independently adjudicated semantic labels. Structural acceptance is a PALO contract diagnostic. Its all-model 0/43 relation result is a harness investigation signal, not a model capability ranking.

The qualified-results view remains empty until external custody, independent domain annotations, measure validation and independent reproduction are established. A model consultation does not satisfy those gates.

## Read the counts

The all-model catalogue is alphabetical by default and exposes internal and historical configurations together with their cohort. It shows distinct model counts separately from configuration counts. Within the procurement view, users can sort either direction by name, provider, label agreement, disagreements, missing statements, completed calls, known charges and median observed time. This is descriptive sorting, not a qualified rank or a claim of model superiority. No position numbers or winner badges are assigned. Unknown costs and unavailable timing remain last in either direction. Numeric and status filters, selected-only comparison and URL state are retained in CSV exports. For verification, match counts, disagreement counts and missing classifications sum to the fixed assigned denominator. Conditional agreement is matches divided by classified statements; coverage is classified divided by assigned statements. An end-to-end match share uses matches divided by assigned statements and must not be labelled semantic accuracy. Missing data never disappear from the evidence table or exports. An HTTP failure is an availability observation, not a semantic error. Case and dimension filters preserve the assigned opportunities; observations are not pooled across cohorts.

Frozen primary labels are the default. The optional sensitivity lens is explicitly post-hoc and removes invoice-matching P002 for all models and repetitions. Its expected label is contested: a supplier-specific increase may contradict the explicit EUR 10 threshold. The original labels and primary counts are preserved. No ad-hoc item exclusion is available.

Costs distinguish known provider charges, unknown charges and conservative reservations. A reservation is neither an invoice nor a proven charge. Input and completion token usage, reasoning detail, advertised catalogue context and configured output cap are separate fields. Reasoning tokens are included in completion billing; they are not added twice. Historical charges remain unreconciled. Inference charges exclude engineering labour, hosting and electricity.

Latency is descriptive. The internal cohort uses all dispatched requests, including failures, but excludes pre-call blocks with no measured duration; the historical median includes successful calls only. The original baseline ran serially; extension calls use up to four concurrent workers. Different definitions, scheduling, settings, tasks and unseeded provider defaults prevent a controlled latency ranking. Supported reasoning and output caps are disclosed per configuration, including non-reasoning Schematron endpoints with an 8,192-token ceiling. The same high label is not equal compute.

## Inspect the evidence

Source-indexed translations are shown beside their source rules, with verbatim-copy flags. This task permits close restatement, and its many exact copies limit what it measures. The original baseline has 27 draft blueprint exports requiring business approval; its draft evaluator replay was performed after inference and is not Workbench application end-to-end validation. Extension translations link to raw source-indexed outputs and remain unreviewed model drafts. They do not inherit baseline assistant reviews, draft exports or semantic acceptance.

The call ledger describes recorded past calls, not a live feed. Source links identify each campaign and point to versioned evidence. Source-policy and label bytes are unchanged across the three internal campaigns. Historical tests retain their exact original model identities, including Schematron Small versus Turbo and Bonsai 9B versus 27B; these are not interchangeable aliases. One error envelope removes an account identifier in its public copy; original and public hashes are recorded separately. Successful responses and all model output text are retained. A hash check establishes byte consistency, not truthful authorship, independent custody or semantic correctness.

The same deterministic data builder supplies both the launch page and internal-results dashboard, including their JSON-LD. All ten historical model IDs remain discoverable on both pages. A historical row and a new procurement row describe distinct configurations and are not merged into a pooled score. CSV exports retain cohort, selected lens, filters, fixed denominators and qualification state. Unknown values are not converted to zero.

## Design and external references

[Arena](https://arena.ai/leaderboard) informed category navigation, dense comparisons and the editorial layout. PALO adds evidence-specific interactions for this research programme: denominators, disputed-label inspection, source/output comparison and recorded-call accounting. These interface choices do not make the underlying measurements better validated.

Anthropic Claude Fable 5.2 supplied an advisory design consultation. Its original response, request, cost receipt and maintainer decisions are retained in `reviews/leaderboard-2026-11-11/`. Fable is not a member of either measured cohort and did not independently validate the benchmark. The maintainer corrected its inaccurate statement that the campaign lacked a retry/missing-data policy.

Structured data follows [Schema.org Dataset](https://schema.org/Dataset), [CollectionPage](https://schema.org/CollectionPage) and [Google's dataset metadata guidance](https://developers.google.com/search/docs/appearance/structured-data/dataset). Dataset discovery metadata is not a rating, endorsement, certification or guarantee of search appearance.

## Budget and compatibility

The user-authorised ceiling is USD40 across prior tests, current extension and advisory model consultations, not USD40 per campaign. Provider-reported key usage is checked before dispatch; outstanding reservations and unresolved earlier charges reduce available headroom. The first extension has a USD20 sub-ceiling and the legacy supplement a USD5 sub-ceiling. The supplement starts only after the preceding campaign finishes. Unknown charges retain their full reservation; a pre-call block has zero charge with an explicit no-request-dispatched reason. The final budget receipt records actual provider-reported usage and reserved unknown charges separately. No automatic inference retries change the original denominators.

The PALO navy/cyan palette is shared across both pages. Detailed research qualification, limitations and further development are in the dedicated lower section, with a concise internal-test label and direct link alongside the evidence controls. Sorting and expanded model coverage do not confer independent validation.


## Interface verification

`tools/verify_leaderboard_browser.cjs` checks both pages against the same downloaded catalogue, sorting in both directions, unknown values last, numeric/status/selection filters, URL restoration, CSV metadata, endpoint output limits, pre-call disclosure and responsive layouts. It requires an installed Playwright module. `PALO_SITE_URL` selects the local or published origin; `PALO_SCREENSHOT_DIR` selects the receipt and screenshot directory. The script makes no model inference calls. The publication receipt identifies the exact source commit and live file hashes.

## Saturation and authoring provenance

Six configurations match all 324 assigned verification labels; eleven are within three matches of that ceiling. Generalist configurations have 20 divergences from draft labels across 4,680 classified responses and 5,184 assigned opportunities, leaving 504 missing. Sixteen divergences concern invoice P002/P036 and purchase P013. P002 is already contested; P013/P036 require adjudication, not automatic relabelling. Repetition does not make these independent observations: there are 108 unique probes, three cases, one authored family.

The original manifest describes the source and label author as an engineering assistant, but does not record its model ID or revision. Both are explicitly unavailable in `release.json`; the current assistant's identity must not be substituted. Human adjudication and a documented rubric are required before a quality ranking.

## Reviewer diagnostics

Automatic reviewer evidence is published separately from model results. API and web/desktop captures are not exchangeable measurement channels. Format-invalid or incomplete captures remain unassessed, not semantic failures. Advisory labels, overlaps with measured model families and prompt differences must stay visible. These records cannot establish reviewer superiority or independent validation.

## Next cycle

Freeze a discriminating case matrix and annotation rubric before new inference. Prioritise new procurement families and human adjudication over adding model IDs. Necessary coverage and a sufficient sample must be justified by the intended comparison and variance across independent families; no fixed item count guarantees sufficiency. See the [next-cycle protocol and annotation package](next-cycle-plan.md).
