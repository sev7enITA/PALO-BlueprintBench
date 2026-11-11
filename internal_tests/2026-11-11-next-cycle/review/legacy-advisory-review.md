# Legacy advisory model review

Three recorded model responses cover P002, P013 and P036, with nine advisory judgments. One item has unanimous label agreement; two have a two-to-one split. These observations are internal automated tests, not human adjudication, semantic validation or evidence of model superiority.

| Legacy item | Anthropic Claude Opus 5.5 | Google Gemini 4 Argon | OpenAI GPT-6.1 Sol |
| --- | --- | --- | --- |
| P002 / ITEM-A | not_established | not_established | contradicted |
| P013 / ITEM-B | not_established | not_established | not_established |
| P036 / ITEM-C | not_established | not_established | contradicted |

## P002: scope of the stated threshold

The source says exactly EUR 10 is within tolerance and variance above EUR 10 blocks automatic payment. The proposition adds a five-percent increase for overseas suppliers.

OpenAI treats the unqualified blocking rule as covering overseas invoices, so increasing the relevant tolerance conflicts with it. Anthropic and Google refuse to assume that the source excludes an unstated supplier-location exception, returning not_established. Anthropic explicitly identifies the opposing interpretation as a closure assumption.

This disagreement concerns whether the stated rule is treated as complete within its scope. It does not establish an arithmetic failure. Human adjudicators must decide which completeness convention applies consistently across the corpus, and whether the proposition refers to the same automatic-payment tolerance. A two-to-one vote does not resolve that methodological question.

## P013: processing order remains unspecified

All three models return not_established. The rule assesses thresholds separately per request; it does not describe automatic merging or its timing. An administrative merge after assessment could coexist with the stated rule. A contradiction would need an additional assumption that merging replaces the original assessment units.

Record this unanimous automated opinion without promoting it to a human-adjudicated label.

## P036: obligation and channel are combined

The source explicitly permits an Accounts Payable analyst to ask for corrections while stating that asking is not obligatory. The proposition says an analyst must request corrections through a supplier portal.

OpenAI returns contradicted for the added obligation and separately notes that the portal is unspecified. Anthropic returns not_established by preferring a channel reading, while explicitly acknowledging that a general duty would contradict the source. Google returns not_established and emphasises the missing portal detail after noting optional requesting.

Two readings remain visible: an unconditional obligation to make a request through a portal, or a channel restriction conditional on choosing to request. Human review should split the duty and channel claims, then specify how a compound statement is aggregated when one component is contradicted and another unspecified. This review does not impose that rule after seeing outputs.

## Provenance and preservation

The JSON companion stores exact rationales, model/provider identities, source mapping, and SHA-256 references for original output bytes, response bytes and execution records. This synthesis was written after seeing the model outputs. Prior labels were withheld from their prompts, but independence or absence of prior exposure is not established.

Original labels, scoring and human annotation templates remain unchanged. Human adjudication is pending for all three items. No new paid calls were made for this review.
