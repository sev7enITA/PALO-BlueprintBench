# Post-output disagreement review: first repetition

This is an internal model-assisted advisory review of the first OpenAI and Anthropic FEMA outputs. The reviewer also authored the draft design and key. It is not blind, independent human adjudication or semantic validation. No frozen file, expectation, count or denominator was changed.

## Six disagreements, one underlying ambiguity

The reviewed snapshot contains six disagreements: FEMA-01, FEMA-02 and FEMA-12 for each of the two models. Every disagreement concerns `davis_bacon_clause_required`: the frozen draft expects `false`, while the generated decisions return `unknown`.

The relevant input is `contract_category: "other"`. Its frozen description states that “other may contain uncharacterised work”. The key nevertheless treats every category other than `prime_construction` as definitively outside prime construction and returns false. That is a substantive completeness assumption about the input categories.

FEMA page 12 requires the clause for prime construction contracts over USD 2,000 when required by the federal program legislation, and instructs users to consult program guidance to determine applicability. The affected scenarios exceed USD 2,000, do not fall within the explicit PA/HMA exclusion, and supply unknown program-legislation applicability.

Two readings of the input remain possible:

- If `other` guarantees known nonconstruction, false is consistent with the intended key.
- If `other` means unclassified work, as the description permits, construction applicability has not been ruled out. Combined with unknown program legislation, unknown is defensible.

OpenAI falls through to its default unknown. Anthropic matches its explicit unknown-program-applicability rule. Manual inspection of the ordered conditions and recorded execution traces found no interpreter defect in these six decisions. The discrepancy is an input-ontology/key ambiguity candidate, not six demonstrated model errors.

## Reporting and next revision

Keep the frozen expected values and all six disagreement counts. Link this note beside the draft-key comparison; do not silently exclude the cases, award alternative-label credit or describe agreement as independently established accuracy.

For a future separately identified version, distinguish `known_nonconstruction` from `unclassified`, or provide a tri-state prime-construction fact. Keep that factual classification separate from whether program legislation requires the clause. Freeze a paired set varying classification and applicability before new inference, and obtain human adjudication of the mapping.

The JSON companion retains the exact generated rules, scenario inputs, output/record hashes, frozen design/key hashes and the reviewed analysis snapshot summary. This review covers only the six listed first-repetition decisions, not later results or every evaluator path. Human adjudication remains pending. No new paid calls were made.
