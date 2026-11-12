# Quote-check correction v1.1

This is a post-collection mechanical checker correction. Frozen source documents, prompts, expected outcomes and raw model outputs are unchanged. It does not change the assistant-draft assessment key or establish independent validation.

## Cause and scope

First observed on 11 November 2026 in FTA requirement R25: the PDF text wraps `micro-` and `purchase` across one line ending, while the model quotes `micro-purchase`. The v1.0 whitespace-only check leaves an extra space and rejects the otherwise identical quotation. FEMA also contains `Anti-` / `Kickback` with the same typography.

Version 1.1 joins only an ASCII-letter hyphen, optional horizontal whitespace, exactly one line ending and optional horizontal whitespace before another ASCII letter. It retains the hyphen. No case folding, paraphrase, word deletion, generic hyphen removal or multiple-line joining is performed.

## Uniform replay

All 27 assignments are retained. This snapshot contains 27 record files: 19 dispatched calls and 8 administrative not-run records. 0 assignments do not yet have a record file. Frozen v1.0 and corrected v1.1 are replayed on the same receipt snapshot in an isolated temporary directory. The original analysis and blueprint directory are never overwritten by this tool.

| Measure | Frozen v1.0 replay | Corrected v1.1 |
| --- | ---: | ---: |
| structurally_valid_calls | 11 | 14 |
| assessed_decisions | 456 | 600 |
| matched_decisions | 453 | 591 |
| disagreed_decisions | 3 | 9 |
| unassessed_decisions | 228 | 84 |
| missing_decisions | 504 | 504 |

Affected receipt IDs: fta-m0-r1, fema-m0-r1, fema-m0-r2.

The JSON companion preserves before/after issues, quote locators, receipt hashes and frozen-manifest identity. `analysis.json` and `blueprints/` retain the original checker output; `analysis-corrected.json` and `blueprints-corrected/` are the versioned corrected view. All other parse, schema, type, dependency and source-quote failures remain failures.

Run: `python corrections/quote-normalisation-v1.1.py`

Tests: `python -m unittest discover -s corrections -p test_quote_normalisation_v11.py -v`
