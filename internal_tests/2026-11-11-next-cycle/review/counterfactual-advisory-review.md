# Counterfactual advisory review

This postrun automated review examines three observed deviations from proposed metamorphic relations. It preserves the frozen keys, counts and denominators. It is not independent validation or human adjudication.

## Observed paired outputs

| Probe | Proposed variant label | OpenAI baseline → variant | Anthropic baseline → variant | Google baseline → variant |
| --- | --- | --- | --- | --- |
| P01: general approval duty | contradicted | supported → not_established | supported → not_established | supported → contradicted |
| P02: no approval under the amount rule | supported | contradicted → supported | contradicted → supported | contradicted → supported |
| P07: Oracle storage obligation | not_established, invariant | not_established → contradicted | not_established → not_established | not_established → not_established |

Across the six tested propositions and three models, 15 of 18 paired observations satisfy the proposed relations and three do not. These are relation-check observations, not accuracy measurements.

## P01: closure of one trigger is not closure of every approval ground

E01 calls itself the complete **amount-triggered** approval rule. The variant raises its threshold from EUR 12,000 to EUR 15,000, consistently updating E01 and E05. An order of EUR 12,001 therefore no longer triggers approval **under that rule**.

P01, however, says the order requires director approval without explicitly limiting the claim to the amount rule. OpenAI and Anthropic recognise the arithmetic, but return not_established because the source does not exclude approval duties on other grounds. Google implicitly scopes P01 to the amount rule and returns contradicted, matching the proposed key.

P02 explicitly includes “under the amount rule”; all three models return supported. The contrast supports a source/probe scope ambiguity, rather than a demonstrated arithmetic failure. Removing one sufficient approval ground does not establish the absence of all possible grounds.

The earlier preflight accepted the intended amount-scoped flip. This postrun observation records its limitation without changing the frozen expectation. Human review should resolve the scope convention. A future preregistered version can explicitly add “under E01's amount rule” to P01 or state that the approval grounds are exhaustive.

## P07: unchanged source, changed scope interpretation

E06 is unchanged: the policy does not prescribe the storage system. OpenAI's baseline leaves possible Oracle implementation requirements open. Its variant instead interprets the proposition within the supplied policy's scope and treats an Oracle-specific obligation as contradicted. Both rationales distinguish permission to use Oracle from an obligation to use it, but apply different scope boundaries.

The label changed despite an unchanged cited source, so the proposed invariance check records a real observed deviation. That does not establish which label is semantically correct or prove that the threshold number caused the shift. Preserve the result and ask human adjudicators to settle the intended scope.

## Boundaries of the perturbation

The source edit changes one threshold parameter, consistently in E01 and E05. The full requests differ in another respect: the baseline asks eight propositions while the variant asks six, removing P06 and P08. Consequently this is not a strict single-variable full-prompt experiment. Different surrounding propositions and stochastic output can affect interpretation; one pair cannot separate those effects.

A future controlled check should preserve the same proposition set and define the relevant modality/scope conventions before inference. Current results, expected relations and denominators remain untouched. The JSON companion records exact model rationales, source/request/output hashes and the full paired evidence. No new paid calls were made.
