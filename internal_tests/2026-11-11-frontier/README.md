# Internal procurement baseline tests

Status: **internal tests**, not independent benchmark validation. Approved by the project owner on 11 November 2026. Independent reviewers will be appointed later. No PALO Blueprint Index or public rank is assigned.

The cohort contains three original synthetic procurement policies, 36 source rules and 108 seeded candidate statements. All cases belong to **one maintainer-authored family**. These are short controlled tests, not real company repositories or 100 MB processing tests. Source material and expected labels were prepared by the engineering assistant and frozen before inference. The models receive policy text and, on the verification track, unlabelled candidate statements. They do not receive expected labels.

| Baseline | Requested route | Reason for inclusion |
|---|---|---|
| OpenAI GPT-6.1 Sol | `openai/gpt-6.1-sol`, OpenAI endpoint | Current general-purpose GPT family baseline, rather than a specialist challenger. |
| Anthropic Claude Opus 5.5 | `anthropic/claude-opus-5.5`, Anthropic endpoint | Flagship Claude reasoning baseline for difficult interpretations. |
| Google Gemini 4 Argon | `google/gemini-4-argon`, Google AI Studio endpoint | Flagship Gemini reasoning baseline with a separate provider implementation. |

Names identify API models. This is not a test of the complete ChatGPT, Claude or Gemini consumer application. Dated endpoint names, catalogue prices, supported parameters and reasoning options are retained in `models.json`. Exact weights and hosted runtime revisions remain unavailable. Providers are pinned and automatic provider fallback is disabled.

The models all use supported `high` reasoning, a 32,768-token total output ceiling, and no tools. High effort does not mean identical compute across providers. Temperature and seed are omitted consistently because a common supported setting is not available; provider defaults and measured token counts must therefore be reported. Repetitions estimate variation within this small setup, not variation across independent companies.

## Tasks

1. **Source-indexed translation:** one faithful specification proposition per numbered source rule, retaining conditions, permissions, negation, exceptions, ownership, thresholds, time, scope and uniqueness. Exact raw response bytes and output text are retained. Subsequent semantic annotation is an internal assistant draft.
2. **Seeded-statement verification:** classify 36 statements per case as supported, contradicted or not established. Each case has 12 of each class, with deterministically shuffled identifiers. The expected labels remain outside the prompts. This measures model verification on known controls; it does not independently validate the benchmark's human annotation rubric.

There are 3 models × 3 cases × 3 repetitions × 2 tracks = 54 assigned requests. Missing, malformed, failed and not-run assignments remain visible. No automatic inference retry or silent truncation repair is permitted. A change of prompt or configuration requires a separately labelled cohort.

The overall authorised budget is USD 40 including prior project tests; this campaign has an additional USD 30 ceiling. The runner reserves a conservative maximum before each request, records returned charges and checks key/account headroom. Unknown charges stop new calls pending reconciliation. Reasoning tokens consume the common completion allowance; they are not silently counted as free. No embeddings, RAG service, paid search, storage service or tool calls are used in this bounded interpretation test.

## Files and provenance

`manifest.json` binds corpus, prompts, schema and configurations before execution. Git publication before model calls is observable project provenance, not independent custody or externally qualified preregistration. Original request/response bodies are retained under `runs/`; headers exclude credentials. `runner.py` reads a key only from an environment variable or a user-specified private local path and never archives it.

Corpus and human-readable synthetic fixtures in this directory are licensed CC BY 4.0 by the project maintainer; code remains under the repository MIT licence. Model responses are supplied as recorded evaluation evidence, with no claim to override provider terms. No corporate or personal records are used.

Sources checked 11 November 2026: [OpenRouter model catalogue](https://openrouter.ai/api/v1/models), [reasoning controls](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens), [Claude Opus 5.5](https://openrouter.ai/anthropic/claude-opus-5.5), [GPT-6.1 Sol](https://openrouter.ai/openai/gpt-6.1-sol), [Gemini 4 Argon](https://openrouter.ai/google/gemini-4-argon). Selection is our experimental design, not a provider endorsement or a claim of measured superiority.
