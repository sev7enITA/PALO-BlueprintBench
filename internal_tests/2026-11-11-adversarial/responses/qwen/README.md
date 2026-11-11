# Local Qwen adversarial counter-test

Three actual local requests returned 36 of 36 assigned records. All three
responses are complete JSON arrays, but the frozen prompt requested an object
with an `items` array. Strict envelope acceptance is therefore **0 of 3 batches**.
All 36 records have valid IDs, task-specific relation values, source references
where supplied, and reasons of at most 18 whitespace-delimited words.
Four records omit citations; these are flagged `citation_missing`, not removed.

The records are usable for a separately labelled **post-hoc structural
projection** (`array_to_items_object`). The projection changes no ID, relation,
citation or reason. It is not a successful strict-format submission, semantic
gold adjudication or independent validation. Primary scores remain unchanged.

The actual server returned `qwen3.8-27b-uncensored`. Its runtime metadata reports
publisher `JonathanColetti`, architecture `qwen35`, Q6_K quantisation and an
8,192-token loaded context. This is a local Qwen-family reviewer, with different
weights from the Qwen Max Prime cohort configuration. Family overlap remains a
limitation; a different local model is not independent human review. No external
verification of the model publisher's lineage claims is implied.

The exact frozen prompts were submitted through `/v1/completions` with a
disclosed ChatML final-only wrapper, temperature 0 and maximum 3,000 output
tokens. No author identities, prior labels or selection keys were supplied.
All three calls stopped normally. Total request time was 77.609 seconds.
No cloud calls or cloud charges occurred. Local energy and hardware costs were
not measured and are represented as unknown.

Each case directory retains original request bytes, frozen prompt bytes,
provider response bytes, completion text, parsed output, initial strict
validation, runtime metadata and the original receipt. The top-level
`*-parsed.json` files retain the original arrays; `*-receipt.json` binds those
files to the raw bytes and discloses the projection. Original invalid receipts
have not been overwritten or reclassified. No inference retries were made.

From this study directory, `python3 summarize_qwen.py` checks response/request
hash bindings and recreates the diagnostic projections, receipt links and
summary without inference. `python3 run_qwen.py` performs new local requests
and creates new attempt directories; it should not be used to silently replace
the frozen one-attempt results. The summary tool refuses multiple attempts so
any future attempt selection requires an explicit protocol decision.

The hash manifest detects accidental changes only. It is not an externally
anchored timestamp or an attestation of reviewer independence.
