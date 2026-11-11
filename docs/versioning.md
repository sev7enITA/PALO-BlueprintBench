# Repository and version strategy

BlueprintBench has a dedicated repository because its protocol, evaluator, corpus registry and result submissions need their own release cadence and outside contributions. It is not a fork of an inference engine or of the PALO application.

PALO Workbench remains in `sev7enITA/PALOframework`. Website integration is maintained separately from the benchmark scoring contract. This repository owns the benchmark method and evaluator; copied public artifacts retain provenance to the initial PALO development work.

Version separately:

- **Protocol**: increment when tasks, reference policy, eligibility, weights or gates change. Different protocol cohorts are not silently pooled.
- **Evaluator**: semantic versioning; score-affecting fixes require a correction note and rerun policy.
- **Corpus**: immutable manifests and SHA-256 hashes, family-based split versions and explicit rights status.
- **Runs**: immutable identity, date, exact model/provider configuration, pipeline version, failures and cost receipts.
- **Explorer**: UI release version, separate from measurement date and method validity.
- **PBI**: unavailable until its scoring specification and independent validation gates are adopted.

Initial repository release: `v0.2.0-pilot.1`, containing explorer v0.2 and evaluator v0.1. This is an archival pilot release, not benchmark qualification. Tags and Git hashes establish artifact identity; they are not independent scientific review or trusted preregistration by themselves.

Research launch release `v0.3.0-pilot.1` contains explorer 0.3.0 and evaluator/evidence contract 0.2.0. Component versions remain separate. The release manifest binds source bytes and public packages; no old tag is moved.

## Internal-test corrective release

`v0.3.0-internal.1` contains evaluator and evidence contract `0.3.0`, public revision `2026-11-11.3`. `release.json` is the shared identity source for the toolkit and public manifest. This is a prerelease for inspection and internal testing; independent review remains pending. It replaces the recommended download, not the bytes or tags of historical releases.

The old `v0.3.0-pilot.1` tag embeds evaluator `0.2.0` with known EV-01. Its release description and separate warning asset must disclose that defect. Never replace the historical ZIP silently or move a tag. A signature, if present, identifies a signer and bytes; it does not assert independent review. Publication receipts and actual tag signature status remain separate evidence.
