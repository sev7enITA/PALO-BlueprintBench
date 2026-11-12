# Real-document generation: execution and evidence notes

This is an internal development study using public procurement documents. The frozen allocation is three source documents, three model configurations and three scheduled repetitions: 27 assigned calls. Each document has 12 hidden assistant-draft input vectors. The allocation contains 324 scenario executions and 1,188 component decisions. The expected outcomes were frozen before model outputs, but have not been independently adjudicated.

The current recorded/completed counts, costs and outcomes are in `analysis-corrected.json` and `budget-final.json`. These notes deliberately do not turn a partial collection snapshot into a final result. A completed scheduled call can still contain a provider error, malformed output, invalid quote or unusable blueprint.

## Access channel and retained evidence

Inference uses the OpenRouter MCP connector. The archive retains its tool envelopes in `runs/<assignment>/mcp-response.json`, extracted answer text in `output.txt`, normalized execution/accounting records in `record.json`, and available provider accounting responses in `get_generation.json`.

The connector adds a terminal accounting footer containing the model, generation ID and token counts. The collector removes only that terminal metadata footer to obtain the answer text. The full envelope and the footer remain archived. This extraction is not JSON repair: fenced, malformed or failed answer text is not salvaged into a blueprint. Where the connector itself returns an error without an answer, an answer is not invented.

The retained envelopes are original MCP tool results, not the provider's original HTTP response bytes. `response_bytes_original: false` records that limitation. Account identifiers may be redacted from accounting envelopes; the redaction scope is recorded and does not change generation accounting fields. The answer hashes bind the checker inputs to the extracted texts.

## Accounting recovery is separate from inference

An accounting lookup can initially return 404 or be not yet available. For the Anthropic FTA first repetition (`fta-m1-r1`), the collector recovered accounting using read-only `get_generation` lookups for the existing generation ID. `accounting-lookups.json` records the initial unavailability and `get_generation.json` retains the recovered accounting response. This was not a second inference, a new model answer or an extra scored attempt.

For Google first-repetition FAR and FTA assignments (`far15-m2-r1`, `fta-m2-r1`), the accounting response records upstream status 502 and reports zero charge. The connector error text remains in the archive. Those explicit provider-reported zeros are distinct from an unknown cost; they are not estimates based on a failed output. These attempts remain in the assigned denominators and are not treated as successful rule generation.

The Google FEMA first repetition (`fema-m2-r1`) and FAR second repetition (`far15-m2-r2`) timed out at the connector after 300 seconds, without a generation ID or recoverable answer text. Initially their costs remained `null` with `cost_status: unknown`, and their full reservations were retained. Read-only accounting recovery subsequently identified the serial requests in authenticated OpenRouter Logs by time, model and provider. `get_generation` confirmed charges of USD 0.338899 and USD 0.3983716, with provider generation durations of 309,689 ms and 327,036 ms respectively. The provider completed after the connector cutoff; this is not evidence that the model itself failed to generate.

The original records are preserved as `record-before-reconciliation.json`. The normalized records now use `cost_status: provider_reported_reconciled`, but retain the original client `state: fail`, timeout timings and absent output. Provider `finish_reason: stop` does not restore an answer that was never retained. The generation input/output logging was unavailable, and no answer was reconstructed from metadata. These are two upstream 502 incidents and two client connector timeouts, not four established model reasoning failures.

The timeout reservations are released only after the corresponding known charges are recorded. The earlier unresolved-cost reserve remains separate. Unknown cost is never converted to zero. Later scheduled repetitions or a transport supplement do not erase or replace the original assignments.

The budget guard compares the account usage snapshot with baseline usage plus observed study spending and uses the higher amount, then adds unresolved reservations. The account snapshot may lag the generation receipts. `budget-final.json` is the authoritative current budget snapshot; a sum of known charges is not the complete cost while any charge remains unknown.

## Versioned quote-check correction

The frozen v1.0 checker normalizes whitespace only. A real PDF line wrap, such as `micro-` followed by a newline and `purchase`, therefore becomes `micro- purchase`, whereas the model may correctly quote `micro-purchase`. This caused a mechanical rejection for FTA requirement R25. The same typography occurs in FEMA's `Anti-` / `Kickback` phrase.

The post-collection v1.1 checker performs one additional transformation before the original whitespace normalization: it joins an ASCII letter plus hyphen followed by exactly one line ending and optional horizontal whitespace before another ASCII letter. It retains the hyphen. It does not remove arbitrary hyphens, join paragraphs, fold case, paraphrase, drop words or change source meaning.

The implementation and adversarial tests are new, versioned files under `corrections/`. They never alter the frozen checker, manifest, documents, prompts, expected outcomes or raw model text. The correction is applied uniformly to every assignment in the same receipt snapshot, including failed and missing assignments. It is a mechanical checker correction after collection, not an amendment to the expected answers.

The evidence views remain separate:

| Artifact | Meaning |
| --- | --- |
| `analysis.json`, `blueprints/` | Original frozen v1.0 analysis and exports |
| `corrections/analysis-v1.0-replayed.json` | Original checker replayed on the exact snapshot used for the correction |
| `analysis-corrected.json`, `blueprints-corrected/` | Versioned v1.1 view, used as the corrected presentation default |
| `corrections/correction-note.json` | Before/after rows, quote locators, receipt hashes, manifest identity and correction scope |
| `corrections/correction-note.md` | Visible human-readable erratum |

Reproduce the current corrected view with `python corrections/quote-normalisation-v1.1.py`. Run its regressions with `python -m unittest discover -s corrections -p test_quote_normalisation_v11.py -v`. All other parse, schema, type, dependency and quote-presence failures remain failures.

## What the outcomes measure

The model generates requirements, a dependency graph and ordered decision rules from the supplied document and task scope. The evaluator checks structure, literal quote presence on cited pages and execution of a bounded DSL against fixed vectors. Rules use first-match semantics, typed input fields and explicit `unknown` outputs. Requirements and process prose are not independently adjudicated assertion by assertion. Graph transitions are not deployed business processes.

The documents are real, but the requested output functions are scoped. Reading a full supplied document does not establish complete extraction of every rule in that document. Matches to the assistant-draft expected outcomes are reported as `matches_draft`, not semantic accuracy, precision, expert agreement or model superiority.

A post-output review identified a possible ambiguity in FEMA's `contract_category: other`: the input description can include uncharacterised work, while the frozen key treats it as known non-construction. A model's `unknown` can therefore be defensible. That is an input-ontology/key issue for future adjudication, not evidence that the interpreter misexecuted the model's rule. Current keys and disagreement counts remain unchanged; the typography correction does not resolve this issue. See [the scoped first-repetition review](review/post-output-disagreements-r1.md). Its author also drafted the key, so this is a disclosed internal review rather than independent adjudication.

Missing responses retain missing denominators. Malformed or structurally invalid responses retain unassessed denominators. A structurally usable blueprint remains an unapproved model draft. No independent human validation, business approval, quality ranking or PALO Blueprint Index is established by this study.

## Offline reproduction and final-snapshot gate

Run `python replay.py --check` after collection and both analysis views are refreshed. This verifies every frozen manifest hash, exact submitted requests, metadata-footer-only extraction, MCP/output hashes, provider-reported costs, unknown reservations and all derived analyses and blueprints. A pending request, stale receipt count or changed outcome makes the check fail. This intentionally prevents an in-flight snapshot being presented as final.

To reproduce without writing into the source archive, run `python replay.py --output /tmp/palo-real-procurement-replay` with a new destination outside the archive. Both checker revisions are executed in an isolated temporary tree. No inference or accounting API is called.

Only `first_documented_at` and `updated_at` in the correction-note JSON are excluded from replay comparison. Outcome data, record hashes, correction scope, before/after evidence and the human-readable erratum must still match. The CI runs the frozen contract suite, the versioned correction suite, replay boundary regressions and the final `--check` gate.

## Stopped collection

The Google AI Studio supplement was cancelled before dispatch. Its nine prepared requests were not sent and are excluded from the 27-assignment results. Collection of the original schedule was stopped at the user's request. One in-flight request has unknown final cost and no captured response; its full pre-call reserve is retained. Eight assignments were not dispatched.
