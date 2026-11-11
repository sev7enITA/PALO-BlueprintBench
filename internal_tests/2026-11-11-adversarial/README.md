# Internal adversarial countertest, 11 November 2026

GLM 5.3 Max and Gemini 4 Argon High were queried through their web interfaces; Qwen3.8 27B Uncensored Q6_K ran in LM Studio with an 8,192-token loaded context. These are internal automated reviews, with model-family overlap in the tested cohort. They are not independent validation or human gold.

## Recorded coverage

The sample and prompts were committed as `80df7db` before execution. It contains 18 verification propositions and 18 source-bound translations from 15 models, over the three synthetic procurement cases. Selection deliberately targets existing disagreement and is not representative of general model performance. All 18 cohort models remain in the separate selected-probe replay, with 54 assigned slots per model. Missing original predictions remain missing.

| Reviewer | Usable judgments / assigned | Requested JSON envelope / assigned batches |
|---|---:|---:|
| GLM 5.3 Max | 24 / 36 | 2 / 3 |
| Gemini 4 Argon High | 36 / 36 | 3 / 3 |
| Qwen local | 36 / 36 | 0 / 3 |

GLM rejected the invoice case during peak capacity. No retry or model substitution was made. Its 12 missing judgments remain in the denominator. Qwen returned bare arrays; a disclosed post-hoc structural projection exposes its record-level answers without rewriting any answer. Five judgments across reviewers have no source ID. They remain visible with a missing-citation flag.

There are 23 items with three-way agreement, one complete three-way disagreement and 12 incomplete panels. Among the incomplete panels, Gemini and Qwen also disagree on two translations. Therefore **three items have an observed disagreement**, not just one.

| Reviewer pair | Agree | Differ | Missing | Assigned |
|---|---:|---:|---:|---:|
| GLM / Gemini | 23 | 1 | 12 | 36 |
| GLM / Qwen | 23 | 1 | 12 | 36 |
| Gemini / Qwen | 34 | 2 | 0 | 36 |

Disputed items are purchase-approval P013 (automatic merging of related requests), T08 (invoice-number uniqueness expressed with must), and T18 (permission to request a corrected invoice, phrased for any blocked invoice). The dashboard retains each reasoning statement and exact source. Agreement does not establish correctness, and no majority vote replaces the frozen draft label. No PALO Blueprint Index is assigned.

## Reproduction

Run `python tools/build_adversarial.py --check` and `python -m unittest discover -s tools -p test_adversarial.py`. Original visible web JSON, local HTTP responses, exact prompts and receipts are retained under this directory. Web JSON is not claimed to be original HTTP bytes. Conversation URLs and unrelated browser history are excluded from the public record.

The model countertest makes no OpenRouter calls. Web subscriptions and local hardware/energy are outside OpenRouter usage and are not represented as zero economic cost. The authorised cap remains USD 40. Primary leaderboard data and scores are unchanged.
