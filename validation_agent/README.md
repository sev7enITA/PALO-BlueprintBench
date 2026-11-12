# Local Validation Agent

The agent prepares advisory reviews for PALO BlueprintBench using LM Studio at `http://127.0.0.1:1234` and `qwen3.8-27b-uncensored`. It processes each assigned item separately, retains requests and response bytes, checks the output format and verifies that cited excerpts occur in the supplied source. It cannot assess the truth of a citation, authenticate a human reviewer or establish source completeness.

The included packet contains P002, P013, P036 and a Davis-Bacon scenario. The first three are synthetic, publicly exposed development cases. The fourth uses a recorded FEMA excerpt and a synthetic scenario input; `CASE_INPUT` is an assumption for the scenario, not a FEMA quotation. Each is a review question, not a new answer key. The packet does not include the existing expected labels or model identities. Source provenance is recorded but not independently verified.

## Start on macOS

1. Start LM Studio's local server on port 1234 and load `qwen3.8-27b-uncensored`.
2. Double-click **Start Review.command**. A Terminal window shows progress; the report opens when the run finishes. Results are stored in `Documents/PALO-BlueprintBench-Agent/reviews`.
3. Inspect `report.html`, `report.json`, the visible packet and retained request and response files. A format-checked response is still an advisory model interpretation.

A normal run requests reasoning, asks the model to keep deliberation focused and brief, and permits up to 4,096 output tokens per item. In one internal Davis-Bacon test this instruction yielded a complete response after an earlier truncation; it does not establish improved accuracy or eliminate truncation. Duration depends on hardware and model; multiple minutes per item are possible. The agent does not retry a timeout because the server may still be processing the request. `progress.json` identifies the last in-flight request if a process is interrupted. The user can choose a new output directory to start another run; it does not resume an interrupted run automatically.

## Commands

```sh
python3 validation_agent/agent.py doctor
python3 validation_agent/agent.py review --out /path/to/new-directory
python3 validation_agent/agent.py review --packet /path/to/packet.json --out /path/to/new-directory
python3 validation_agent/agent.py replay /path/to/run-directory
python3 validation_agent/agent.py calibrate --out /path/to/new-directory
```

The `--packet` JSON format is illustrated by `demo-packet.json`. Each item has `review_item`, `statement` and a list of source units containing `id` and `text`. Only these fields are sent for inference; expected labels, source provenance and other fields are not passed to the model. The source hash and any `source_provenance` mapping are recorded locally. Supply the complete relevant source scope and version; the agent cannot establish that excerpts are complete. One item is limited to 18,000 characters, but this is not a token count or a guarantee that a particular LM Studio context is sufficient. Incomplete responses remain invalid.

`calibrate` runs the 18 existing seeded examples. To run an explicitly selected internal subset, use `--ids C01,C09,C13`. The draft answer key is read only after inference. The comparison reports detected changes, misses, false alarms, correct controls and unresolved items. Rates use determinate items only and expose unassessed counts. These synthetic examples have one exposed family and assistant-draft labels; neither these rates nor their replay validate the benchmark metric.

`replay` checks captured request and response digests and reapplies the structural checks to conforming results without model calls. Other captured responses remain unassessed. It detects accidental changes in the local files; the same person can alter both files and hashes. It is not independent reproduction or a trusted timestamp. Keep the original packet separately if later proof of its contents is required; the agent records only its hash and a filtered visible copy.

## Governance and limits

- **Mandate:** examine user-supplied local text and create review artifacts in a new local directory. No credentials, model outputs from evaluated systems or private data are needed for the included examples.
- **Scope:** the code contacts only the fixed loopback endpoint and does not invoke tools, send messages, publish, change evidence, assign ranks or amend reference labels. LM Studio's own configuration, logging, data retention and network behaviour are outside this agent's control.
- **Expert approval and adjudication:** outputs are model suggestions. No human identity, expertise, independent review or acceptance is inferred.
- **Custody:** local SHA-256 hashes support consistency checks. They do not establish an independent custodian, secrecy, authenticity or external timestamp.
- **Metric and reproduction:** internal seeded examples and local replay are diagnostic only. Independent experts, separate custody, a preregistered study and a third-party rerun remain required for qualification.
- **Failure:** wrong model identity, truncated or malformed output and unverifiable quotations are not scored as correct. Missing and unrun items remain visible. No external-action permission, executable PALO Action Claim or digital signature is created.

This is an implementation of a bounded draft workflow inspired by the PALO Agentic Action Design skill. It is not enforcement of platform IAM, an executable Effect Contract, a compliance certificate or proof of outcome. Input sources may contain prompt-injection attempts; treating them as data and checking citations reduce exposure but do not guarantee that the model will ignore them. Use only material authorised for local processing.

[Action design and evidence states](action-design.md).
