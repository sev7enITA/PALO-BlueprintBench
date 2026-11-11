**Advisory design consultation only.** This is not an independent review or validation, and I have not browsed or added any results.

## 1) Information architecture and hierarchy

Borrow Arena's navigation and density, but not its rank-first framing.

- **Persistent status strip on every page:** "Internal evidence · qualified=false · no model ranking supported · benchmark revision ⟨id⟩".
- **Top-level tabs:**
  - **Qualified ranks:** intentionally empty, showing the four missing prerequisites (independent gold, custodian, annotators, measure validation) as an unchecked list.
  - **Track A, API baselines:** internal evidence.
  - **Track B, historical challengers:** separate route, schema and styling.
  - **Items & labels**, **Calls & runs**, **Methods & limitations**, **Changelog**.
- **Track A sub-tabs:** Verification, Translation and Draft-evaluator replay, each with its own caveat line (for example "posthoc replay of 27 draft blueprints; not app E2E; no human validation").
- **Table rules:**
  - Fixed non-score row order (alphabetical), with no rank column.
  - Counts first, as agree / disagree / missing / assigned. Gemini reads "288 / 0 / 36 / 324", never "88.9%".
  - Frozen primary is the default column, with posthoc exclusion as a visibly tagged secondary column.
- **Model, provider and adapter** are three separate columns, as are **configured output limit (32,768)** and **tokens actually used**.
- **Headline finding above the table:** "All observed disagreements trace to one contested label; no quality ordering is justified."

## 2) Six advanced interactions the data supports

1. **Denominator ledger.** Step through assigned → complete → agreed for each model, switching between frozen primary (324) and posthoc (321). Missing always stays visible as its own segment.
2. **Contested-item inspector.** Show the source rule, seeded statement, draft label (`not_established`), all nine model-by-repetition responses, raw output and the dispute note (overseas tolerance versus the universal EUR 10 threshold). Title it "label under dispute", not "Claude errors".
3. **Repetition matrix.** A 108-statement by 3-repetition grid per model, showing agreement, flips and the missing Gemini block. This makes it obvious that the variance sits in one item and one failed call.
4. **Call ledger.** List all 54 calls with status, HTTP code, provider, adapter, pinned-provider/no-fallback flags, tokens used versus limit, and cost state (known / unknown / reserved). Filter to the 503 call.
5. **Translation diff.** Show source rule against output for the 324 rules, with a computed verbatim-copy flag and filter. Readers can then see how much of the task was copying.
6. **Config diff with pooling guard.** Compare configurations side by side within a track (reasoning, quantization, temperature, seed). Any attempt to compare A with B shows a blocking explanation instead of a merged table.

Every view should also have a revision-pinned permalink and a raw-evidence download.

## 3) UI choices to forbid

- Rank numbers, medals, crowns, podium ordering, "best" bolding, Elo-style scores, or default sort by agreement.
- The words "accuracy", "correct", "verified", "certified", "human-reviewed", "E2E" or "validated" anywhere in the interface.
- Percentages without adjacent counts, or green/red gradients that turn 322 versus 324 into a visual gap.
- Missing shown as zero, blank or failure. The 503 is a provider or infrastructure event, not model behaviour.
- Unknown cost shown as $0, an em-dash or silently summed. Gemini should read "0.365732 USD known + 1 call unknown", with the 0.3821642 reservation as a separate, defined field. Do not draw cost-versus-score "value" charts.
- Posthoc results as the default view or without the "posthoc" tag.
- Any pooled A+B table, chart or aggregate.
- Track B's 0/43 presented as model capability. Label it "structural acceptance only; no repetitions; configs differ in reasoning/quantization".
- "Context window" used for the configured output limit.
- Confidence intervals or significance marks. Three unseeded repetitions on one family do not support them.
- Caveats that exist only in tooltips.

## 4) JSON-LD

- **Use `CollectionPage` for the page, with `hasPart` pointing to two separate `Dataset` nodes (A and B).** Each `Dataset` carries `version` (benchmark revision), `dateModified`, `creator`, `measurementTechnique` ("agreement with assistant-drafted labels"; "structural acceptance"), `variableMeasured`, `distribution` as `DataDownload` of raw evidence, and a `description` that states the limitations.
- **Avoid `ItemList` for models.** `ListItem.position` reads as rank to crawlers. If you need a list, use it only for tracks or datasets, with `itemListOrder: ItemListUnordered`.
- **Omit ratings and endorsements entirely:** no `AggregateRating`, `Rating`, `Review`, `award`, `Certification` or `hasCertification`, and no models typed as `Product` or `SoftwareApplication` with scores.
- **Express status as plain properties**, for example `additionalProperty: {name: "qualified", value: false}`, and `creativeWorkStatus: "Internal evidence – unqualified"`.
- **Keep it in sync.** Generate the JSON-LD from the same source as the tables, and include nothing that is not visible on the page.

## 5) Acceptance tests

- Every page renders the status strip and benchmark revision. `qualified=false` appears on every row and in every export.
- The Qualified tab contains zero rows and four unmet prerequisites.
- The DOM, CSV and JSON-LD contain no ordinal rank field, and a banned-vocabulary linter passes.
- Track A shows exactly 324/324, 322/324 and 288/324 with 36 missing in frozen primary, and 321/321, 321/321 and 285/321 in posthoc. Rows sum to assigned.
- Calls show 54 assigned, 53 complete and one HTTP 503. The failed call is reachable in two clicks or fewer.
- Cost has three distinct states in the schema (`known`, `unknown`, `reserved`). No total is displayed where any component is unknown, except as "≥ known".
- No API endpoint or view returns A and B records in one aggregate, enforced by a schema test.
- The contested item is flagged in every view that includes it.
- Every cell resolves to raw evidence, with a hash matching the revision.
- JSON-LD validates and contains none of the forbidden types.
- Screenshot test: a cropped table image still shows "internal evidence · unqualified".
- The page is usable with greyscale, keyboard and screen reader, with status never conveyed by colour alone.

## 6) Critical flaws in the plan

- **Circular measurement.** Assistant-drafted labels, checked by an engineering assistant, are compared with assistant outputs. Agreement may reflect shared bias rather than correctness.
- **Ceiling and floor.** Track A is saturated, and its only signal is a probable label defect. Track B is 0/43 everywhere. Neither discriminates between models, and B's uniform failure more plausibly indicates a harness or task problem than a model one.
- **Thin base.** The data comes from one maintainer-authored synthetic family with three repetitions at default temperature and no seed. It is not reproducible and says nothing beyond that family.
- **Translation track is near-vacuous.** Many outputs are verbatim copies, so it measures little.
- **Unequal coverage.** There is no predeclared retry or missing-data policy, so one transient 503 leaves Gemini's coverage and cost incomplete.
- **Posthoc exclusion.** It is defensible only as a sensitivity view. Without a custodian, label changes have no legitimate governance path.
- **The name and the polish are the main risk.** Arena-style finish plus the word "leaderboard" will produce screenshots that read as rankings regardless of disclaimers. Consider the subtitle "Evidence board (no qualified ranks)", and publish the qualification criteria before adding more models.

The interface can show that this evidence is traceable, but it cannot show that it is meaningful. I would fund independent gold labels and harder task families before further interface work.