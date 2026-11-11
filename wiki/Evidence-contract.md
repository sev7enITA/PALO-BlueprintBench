# Evidence contract

The authoritative machine-readable definition is [`evaluator/evidence.schema.json`](https://github.com/sev7enITA/PALO-BlueprintBench/blob/main/evaluator/evidence.schema.json). The evaluator applies cross-record checks in addition to schema validation.

## Evidence chain

1. A **campaign** assigns tasks, repetitions, subjects and the acceptance policy.
2. Each task binds its **gold** and source scope; each subject binds its **configuration**.
3. A local **lock** records a digest of the campaign payload.
4. A **run** records each assigned attempt, termination, elapsed time and cost status.
5. A **receipt** binds raw output and the emitted-claim artifact.
6. **Annotations** bind the receipt and exact claim text, with verdicts, equivalence classes and adjudication declarations.
7. The evaluator emits scoped scores, accounting and qualification blocks.

Claim spans use half-open Unicode code-point offsets in decoded UTF-8 text. Claim text must match the raw text exactly. Claim and non-claim spans must cover the output without gaps or overlaps. Non-claim classifications need reasons and still require human scrutiny.

## What the checks cannot prove

Hashes do not establish authorship, honest annotation, trusted registration time or independence. The lock uses the documented Python serialization, not RFC 8785. A rehashed or backdated local lock cannot earn a qualified badge, but external registration verification is not implemented.

A declared atomicity review does not prove that a claim is truly atomic. Allowed alternatives and forbidden inferences support adjudication; they are not automatic natural-language truth tests.

Version 0.2 rejects version 0.1 records. Preserve original records and identify retrospective migrations explicitly. [Contract and migration](https://github.com/sev7enITA/PALO-BlueprintBench/blob/main/docs/evaluator-contract.md) | [Corrections policy](https://github.com/sev7enITA/PALO-BlueprintBench/blob/main/docs/corrections.md)
