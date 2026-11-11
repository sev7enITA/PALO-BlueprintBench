# Document-to-specification generation

Three real, public procurement documents are supplied as complete extracted text within the documented source boundary: FAR Part 15 (56 pages of the full FAR), FTA Circular 4220.1G (97 pages), and FEMA Contract Provisions Guide version 2 (47 pages). Each task requests generated atomic requirements, a process graph and executable declarative rules for one explicitly scoped process. No candidate claims or expected labels are sent to the models.

The study assigns three models to each document with three repetitions: 27 requests. The 36 assessment input vectors and 132 expected component outcomes per repetition are assistant drafts prepared before outputs, not independently adjudicated gold. Across three models and three repetitions, the fixed denominators are 324 vector executions and 1,188 component decisions. The sources are public and development-exposed; FTA and FEMA share federal-grants dependencies. Three documents do not establish a representative or statistically independent source population.

## Execution

Access channel: OpenRouter MCP `send_message`. Provider routing is pinned with `only` and `allow_fallbacks:false`: OpenAI, Anthropic, Google Vertex US. Reasoning effort is `high`; maximum generated tokens including reasoning is 32,768. The full per-document messages and neutral JSON response contract are identical across models and repetitions. Provider-side schema enforcement is not available through this tool; all outputs are checked locally, without repairs. Temperature and seed are not exposed by the tool and are not claimed controlled. The same reasoning label is not equal inference compute.

Requests run serially in three rounds with cyclic model order. No retry or fallback is planned. Raw MCP envelopes, extracted answer text, generation accounting and exact tool arguments are retained. Original HTTP transport bytes are unavailable through this connector. The endpoint catalogue records advertised versions and settings; receipts record identities actually returned. No agent browsing, RAG, embedding, tool use or external retrieval is requested. The documents are interpreted at their supplied editions, not as a claim of current legal guidance.

## Assessment and exports

`contracts.py` validates strict JSON, declared types, original page identifiers, graph dependencies and bounded decision trees. It never executes arbitrary model code. Source-quote matching proves normalized-whitespace literal presence on a cited page, not entailment. `analyse.py` executes generated rules against the pre-output draft vectors. Missing responses and structurally unusable responses remain separate from disagreements. Semantic completeness and correctness of the full generated requirements/workflow remain unadjudicated. No quality rank, independently validated accuracy or PALO Blueprint Index is assigned.

`blueprints/` contains source-linked model drafts, explicitly unapproved. A contract-valid JSON export is not an approved business application. Disagreements, missingness and parser failures are retained; no output or expectation is patched after collection to improve results.

## Budget and integrity

The cumulative authorised budget remains USD 40, even if account credit is higher. Every request is reserved conservatively against current account usage, the preceding unresolved-cost reserve and this study's recorded spend. Unknown accounting or a provider/identity mismatch stops execution pending reconciliation. Request, source and manifest hashes link receipts to the frozen preparation. A GitHub preparation commit is a dated disclosure, not independent custody or scientific validation.

Run offline checks with the repository verification environment:

```sh
python -m unittest discover -s internal_tests/2026-11-11-real-procurement -p 'test_contracts.py'
python internal_tests/2026-11-11-real-procurement/analyse.py
```

Source texts retain their federal-government provenance; source images and trademarks are not included or relicensed. The code licence does not relicense source materials. Reproduction at the same tool-contract level requires an OpenRouter MCP connection, the stored `prepared/*.json` arguments and the selected serving endpoints. Transport internals and nondeterministic sampling prevent a claim of byte-identical independent reproduction.
