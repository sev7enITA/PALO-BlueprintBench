# November audit and pre-announcement finding register

Revision `2026-11-11.3`; internal corrective release `v0.3.0-internal.1`.

The original 63 findings are preserved and the 14 pre-announcement findings are added. Status describes maintainer action, not independent closure. Earlier repair PRs are merged. Technical corrections and remaining external gates are distinguished. Current publication checks and release receipts must establish deployment separately.

| ID | Severity | Status | Evidence / remaining gate |
|---|---|---|---|
| EV-01 | critical | implemented_internal_tests | Version 0.3.0 contract and regression checks implemented; repair merged. Independent human review remains pending. Semantic annotations and identities are not externally verified. |
| EV-02 | high | implemented_internal_tests | Version 0.3.0 contract and regression checks implemented; repair merged. Independent human review remains pending. Semantic annotations and identities are not externally verified. |
| EV-03 | high | partial | Descriptive run/family/domain/repetition totals implemented. Family-level uncertainty and a real procurement run remain open. |
| EV-04 | high | open | No closure is claimed. See the supplied audit criterion. |
| EV-05 | high | implemented_internal_tests | Version 0.3.0 contract and regression checks implemented; repair merged. Independent human review remains pending. Semantic annotations and identities are not externally verified. |
| EV-06 | medium | partial | Output explicitly states external verification is not implemented; no trusted timestamp or signature verification has been added. |
| EV-07 | medium | implemented_internal_tests | Version 0.3.0 contract and regression checks implemented; repair merged. Independent human review remains pending. Semantic annotations and identities are not externally verified. |
| EV-08 | medium | implemented_internal_tests | Version 0.3.0 contract and regression checks implemented; repair merged. Independent human review remains pending. Semantic annotations and identities are not externally verified. |
| EV-09 | medium | implemented_internal_tests | Version 0.3.0 contract and regression checks implemented; repair merged. Independent human review remains pending. Semantic annotations and identities are not externally verified. |
| EV-10 | medium | implemented_internal_tests | Version 0.3.0 contract and regression checks implemented; repair merged. Independent human review remains pending. Semantic annotations and identities are not externally verified. |
| EV-11 | medium | implemented_internal_tests | Version 0.3.0 contract and regression checks implemented; repair merged. Independent human review remains pending. Semantic annotations and identities are not externally verified. |
| EV-12 | low | implemented_internal_tests | Version 0.3.0 contract and regression checks implemented; repair merged. Independent human review remains pending. Semantic annotations and identities are not externally verified. |
| EV-13 | low | implemented_internal_tests | Version 0.3.0 contract and regression checks implemented; repair merged. Independent human review remains pending. Semantic annotations and identities are not externally verified. |
| EV-14 | low | implemented_internal_tests | Version 0.3.0 contract and regression checks implemented; repair merged. Independent human review remains pending. Semantic annotations and identities are not externally verified. |
| EV-15 | low | implemented_internal_tests | Version 0.3.0 contract and regression checks implemented; repair merged. Independent human review remains pending. Semantic annotations and identities are not externally verified. |
| EV-16 | low | open | No closure is claimed. See the supplied audit criterion. |
| EV-17 | low | partial | Adversarial and CLI tests added. Acquisition uses mocked HTTPS responses; a local-server integration test, systematic fuzzing and independent review remain open. |
| EV-18 | low | documented_limit | Full bounded annotation only; probability-sampled scoring not implemented. |
| MS-01 | critical | partial | Removed model scatter/ranking; pooled type/cause charts published. Frozen relationship contract satisfiable in a synthetic three-candidate test, which also exposes semantic blindness. No model-quality measure validated. |
| MS-02 | high | partial | Historical adapter diagnostics and internal procurement tests are separated. Procurement repeats exist, but independent gold, multiple independent families and controlled comparison remain open. |
| MS-03 | high | partial | Historical adapter diagnostics and internal procurement tests are separated. Procurement repeats exist, but independent gold, multiple independent families and controlled comparison remain open. |
| MS-04 | high | partial | Historical adapter diagnostics and internal procurement tests are separated. Procurement repeats exist, but independent gold, multiple independent families and controlled comparison remain open. |
| MS-05 | high | open | No closure is claimed. See the supplied audit criterion. |
| MS-06 | high | partial | Draft severity rubric and annotation fields exist. Two blind expert annotations, adjudication and category agreement are not yet available. |
| MS-07 | medium | open | No closure is claimed. See the supplied audit criterion. |
| MS-08 | medium | open | No closure is claimed. See the supplied audit criterion. |
| MS-09 | medium | partial | OpenAI, Anthropic and Google configurations are present in the 18-model internal pilot. Independent comparable gold, sufficient families and qualified baseline comparison remain open. |
| MS-10 | low | implemented_internal_tests | Both unique errors and occurrences retained in descriptive summaries; measured human repair time remains unavailable. |
| DT-01 | high | partial | Sanitised local ledger reconstructs former explorer totals; independently attested invoices and original response bytes remain unavailable. Costs remain withdrawn from ranking. |
| DT-02 | high | published_correction | Correction published on main at 0aafacc. Independent re-audit remains pending; original archives and release tags are preserved. |
| DT-03 | high | open | No closure is claimed. See the supplied audit criterion. |
| DT-04 | medium | published_correction | Correction published on main at 0aafacc. Independent re-audit remains pending; original archives and release tags are preserved. |
| DT-05 | medium | documented_limit | Determinism is distinguished from provenance. Missing original response bytes have not been reconstructed or invented. |
| DT-06 | medium | partial | Candidate sources are labelled feasibility materials, not a qualified held-out set. External custodian must choose new families. |
| DT-07 | medium | partial | Optional expected SHA-256 checked; failed downloads retained as failures. Source rights and current live acquisition remain unresolved. |
| DT-08 | low | published_correction | Correction published on main at 0aafacc. Independent re-audit remains pending; original archives and release tags are preserved. |
| DT-09 | low | implemented_internal_tests | Unpublished reference-item count removed from the current protocol; historical archives preserved. |
| DT-10 | low | open | No closure is claimed. See the supplied audit criterion. |
| GV-01 | critical | external_or_method_gate | No independent custodian, gold, reviewers, validated study, separate organisation/domain or DOI is claimed. These gates require actual decisions, people or evidence. |
| GV-02 | high | external_or_method_gate | No independent custodian, gold, reviewers, validated study, separate organisation/domain or DOI is claimed. These gates require actual decisions, people or evidence. |
| GV-03 | high | external_or_method_gate | No independent custodian, gold, reviewers, validated study, separate organisation/domain or DOI is claimed. These gates require actual decisions, people or evidence. |
| GV-04 | high | partial | Repairs merged through pull requests and released as internal tests. No independent human approval is claimed. Actual tag signature and CI receipts must be checked separately; required external review remains open. |
| GV-05 | medium | external_or_method_gate | No independent custodian, gold, reviewers, validated study, separate organisation/domain or DOI is claimed. These gates require actual decisions, people or evidence. |
| GV-06 | medium | partial | Private maintainer email documented; no independent arbiter, response SLA or installable package implemented. |
| GV-07 | medium | external_or_method_gate | No independent custodian, gold, reviewers, validated study, separate organisation/domain or DOI is claimed. These gates require actual decisions, people or evidence. |
| GV-08 | low | external_or_method_gate | No independent custodian, gold, reviewers, validated study, separate organisation/domain or DOI is claimed. These gates require actual decisions, people or evidence. |
| GV-09 | low | external_or_method_gate | No independent custodian, gold, reviewers, validated study, separate organisation/domain or DOI is claimed. These gates require actual decisions, people or evidence. |
| WB-01 | high | published_correction | Correction published on main at 0aafacc. Independent re-audit remains pending; original archives and release tags are preserved. |
| WB-02 | high | partial | Eleven deployed files verified by cache-busted HTTPS with response headers from publishing environment. Independent external-network check remains open. |
| WB-03 | medium | corrective_release | Pre-announcement audit reopened this finding after ranks were added. Revision .3 suspends all numerical ranks and retains descriptive sorting; independent re-audit remains pending. |
| WB-04 | medium | published_correction | Correction published on main at 0aafacc. Independent re-audit remains pending; original archives and release tags are preserved. |
| WB-05 | medium | open | No closure is claimed. See the supplied audit criterion. |
| WB-06 | low | previous_correction | Dependency wording and CI badge were added after audited commit in 8cd2b8f. This does not establish independent review or a scoring release. |
| WB-07 | low | partial | Proposal is now a pointer to the protocol. Related-work sources retain their separate historical and comparison roles. |
| WB-08 | low | open | No closure is claimed. See the supplied audit criterion. |
| RP-01 | medium | previous_correction | Dependency wording and CI badge were added after audited commit in 8cd2b8f. This does not establish independent review or a scoring release. |
| RP-02 | medium | open | No closure is claimed. See the supplied audit criterion. |
| RP-03 | medium | implemented_internal_tests | CI matrix extended to Linux, macOS and Windows; run outcomes must be inspected before support is claimed. |
| RP-04 | low | partial | Private maintainer email documented; no independent arbiter, response SLA or installable package implemented. |
| RP-05 | low | open | No closure is claimed. See the supplied audit criterion. |
| RP-06 | low | documented_limit | Manifest scope now explicitly lists exclusions; it is not represented as a whole-repository attestation. |
| RP-07 | low | implemented_internal_tests | Verification claim narrowed to the three provenance codes; complete schema-enumeration mapping remains open. |
| RP-08 | low | implemented_internal_tests | Internal branch reference and repeated end-of-loop write removed; acquisition receipt is written once after processing. |
| LB-01 | critical | corrective_release | Numerical ranks suspended; saturation disclosed. More discriminating independent families and adjudicated labels remain required. |
| LB-02 | high | corrective_release | Missing statements and causes remain visible. Conditional agreement and coverage are distinct; missing opportunities remain in assigned denominators. |
| LB-03 | high | corrective_release | Shared release.json revision 2026-11-11.3 identifies current method, announcement and manifest. No numerical ranks claimed. |
| LB-04 | high | partial | Model ID and revision were not recorded in the original manifest and are explicitly unavailable. Do not infer identity. Human re-annotation remains required. |
| LB-05 | high | partial | Earlier PRs 1-3 merged to main with successful CI. Internal corrective release identifies version and tag; independent human review remains pending. |
| LB-06 | high | corrective_release | Automatic reviewer diagnostics are separate from model results. Channel differences, invalid captures and prompt differences preserved. No reviewer ranking or independent validation. |
| LB-07 | medium | documented_limit | Translation remains model draft, with source-copy counts and limited baseline assistant review disclosed. No semantic quality score or extension acceptance is assigned. |
| LB-08 | medium | open | Next cycle prioritises independent source families and discriminating cases; repetitions are not independent businesses. |
| LB-09 | medium | corrective_release | Numerical charge/time ranks suspended. Observed costs, unknowns, timing and settings remain descriptive; no controlled efficiency comparison. |
| LB-10 | medium | documented_limit | Later selection is disclosed; specialist extractors retain their observed outcomes and task-fit caveat, without numerical quality ranks. No post-hoc score deletion. |
| LB-11 | medium | corrective_release | Current distribution excludes testing badge; project logos remain identity only. Historical artwork retained as provenance. |
| LB-12 | low | corrective_release | Original 63 findings retained and updated alongside 14 LB findings; no independent closure claimed. |
| LB-13 | low | documented_limit | Country remains descriptive provenance, never a quality score, processing location or jurisdiction guarantee. |
| LB-14 | low | open | Raw evidence remains reproducible and inspectable; manifest/archive separation and smaller per-view payload remain future performance work. |
