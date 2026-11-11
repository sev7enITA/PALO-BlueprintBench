# Fable 5.2 advisory design consultation

The maintainer requested advice from Anthropic Claude Fable 5.2 via the pinned Anthropic OpenRouter route. This is an AI design consultation, not an independent benchmark review, annotation, endorsement or model result. The model is not added to either tested cohort. Recorded charge: USD 0.23984, separate from benchmark inference costs.

Accepted: count-first denominators, a contested-label inspector, recorded-call ledger, source/output translation comparison, configuration comparison with cohort separation, empty qualified-results state, and source-bound Dataset metadata.

Corrections to the advice:

- The frozen design already specifies no automatic retries and retains failures in the assigned denominator. The suggestion that there was no policy is incorrect.
- Offline evidence analysis and replay are reproducible. Hosted inference repetitions do not guarantee byte-identical reruns; these are different claims.
- `additionalProperty` is not used on Dataset because that Schema.org property does not have the appropriate domain. Qualification is expressed in `creativeWorkStatus` and descriptions.
- An unordered ItemList without score positions is not inherently a model ranking. Nevertheless, dataset nodes provide a clearer description here, so the previous model lists are replaced.
- Legitimate statements about hash or CI verification are retained with their narrow scope; they never mean independent semantic validation.

Arena is a reference for category navigation and comparison density, not a source of PALO scores or evidence of superior measurement. Reference inspected: https://arena.ai/leaderboard on 11 November 2026.
