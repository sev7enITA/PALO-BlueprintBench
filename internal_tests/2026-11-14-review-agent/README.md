# Local review agent end-to-end diagnostics

Date: 2026-11-14. Status: internal development; not independent validation.

The unmodified model requests were sent to LM Studio on a private LAN server using the review agent CLI. The private endpoint is redacted only in each published report.json; request and response files are unchanged. Captured source, input, progress, output and replay artifacts are included. The server catalog identified the loaded Qwen3.8 27B Ultimate Heretic Turbo Brilliance model locally. The model file name indicates NVFP4 and MTP; quantization and GPU offload were not independently verified. Context: 8192 tokens; temperature: 0; output cap: 2048 tokens; timeout: 180 seconds. The first request included model loading. Hardware inventory was recorded on 2026-11-12 as Intel Core i7-12850HX and NVIDIA RTX A5500 Laptop GPU; it was not re-inventoried for this run.

| Case | Status | Time (seconds) | Label |
|---|---|---:|---|
| C01 | advisory_contract_valid | 131.516 | supported |
| C09 | advisory_contract_valid | 44.391 | contradicted |
| C13 | advisory_contract_valid | 22.026 | contradicted |
| ITEM-B | advisory_contract_valid | 31.732 | not_established |
| ITEM-C | advisory_contract_valid | 89.981 | mixed_or_compound |
| DAVIS_BACON | transport_failed | 180.019 | N/A |

C01, C09 and C13 are synthetic seeded development cases with assistant-draft expectations. C01 was a faithful control and C09 and C13 were seeded alterations. The three determinate labels matched those expectations; these are not independently adjudicated labels. ITEM-B and ITEM-C are public synthetic process scenarios. DAVIS_BACON uses a FEMA excerpt and a synthetic scenario input; source provenance has not been independently verified. A timeout is unassessed, not a semantic error or success. One repetition per case, a small exposed sample, and no independent gold prevent a quality ranking. Citation and format checks do not establish semantic correctness. Local replay checks file consistency, not independent replication. The development calibration and process samples are not directly comparable with earlier charts.

The first three requests were completed through calibrate; the others through review. A timeout stops subsequent requests in the same batch and is not automatically retried. The local report records include `qualified: false`; the endpoint redaction is the only intentional modification to their report JSON after the run.
