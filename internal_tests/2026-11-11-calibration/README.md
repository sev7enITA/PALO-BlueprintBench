# Internal semantic calibration smoke test

This elementary, engineering-exposed packet is separate from the 18-model leaderboard. Six source rules are reused as verbatim controls, paraphrase controls and obvious alterations. One authored family, not eighteen independent observations. Expected labels are assistant drafts.

## Evidence and replay

- `manifest.json`: pre-review local input hashes; no independent timestamp claim.
- `proposition-bank.json`: source, scope, alternatives, forbidden inferences and draft criticality.
- `items.json`: reviewer-visible pairs without expected labels.
- `answer-key.json`: released internal draft labels; this packet cannot become a future independent holdout.
- `responses/`: original API bytes where available; copied interface text for web/desktop, with capture limits and retries in receipts.
- `legacy-guard.json`: post-hoc byte-preservation check for the unchanged model cohort.
- `budget-after.json`: bounded account expenditure and reserve, not a sum of only this experiment.

Run `python tools/calibration.py --check` from repository root. Replay makes no model calls. Strict invalid JSON remains unassessed, with all assigned items retained as invalid. It is not silently repaired or treated as a semantic error. Advisory prose can inform engineering while remaining outside the scored contract.

The complete draft review export is `web/downloads/blueprintbench/calibration.json`. The separate `annotation-packet.json` contains preparation items without labels or model reasons. This public material is not an independently blinded study. The exact-equality lexical baseline is explicitly post hoc.

See `docs/calibration-review-decisions.md` for adopted recommendations and disagreements, including why human names alone do not establish independence and why missing output is not a demonstrated normative inversion.
