# Real-document generation

The reproducible result artifacts are:

- [Corrected v1.1 analysis](analysis-corrected.json), including every assigned call, scenario and component decision.
- [Original v1.0 analysis](analysis.json), retained alongside its original blueprint exports.
- [Quote-check erratum](corrections/correction-note.md), with [machine-readable before/after evidence](corrections/correction-note.json).
- [Execution and accounting notes](execution-notes.md), covering connector evidence, failed requests and unresolved cost reservations.
- [First-repetition semantic disagreement note](review/post-output-disagreements-r1.md), with the reviewer's role and limited scope disclosed.
- [Budget snapshot](budget-final.json), including known charges and retained reserves for unknown charges.
- [Frozen manifest](manifest.json) and [scheduled assignments](schedule.json).

Use the recorded status in these artifacts to distinguish an ongoing collection from a final snapshot. The fixed study allocation is 27 calls, three public documents, three configurations and three repetitions. Missing or failed calls remain assigned.

Results compare generated rules with frozen assistant-draft test outcomes. They are internal evidence, not independently adjudicated semantic accuracy or a model ranking. The v1.1 default fixes only a PDF hyphen-linewrap quote-check artifact; it does not change source documents, model outputs or expected outcomes.
