<p align="center">

> **Internal-test release notice, revision 2026-11-11.3:** Evaluator 0.3.0 repairs the non-claim exclusion defect and is distributed as `v0.3.0-internal.1`. Automated regression checks do not establish independent human review or scientific qualification. The historical `v0.3.0-pilot.1` package contains evaluator 0.2.0 with known EV-01 and must not be used for qualification. See [release identity](release.json), [migration and limits](docs/evaluator-0.3-draft.md) and [the warning](evaluator/EVALUATOR-0.2-WARNING.md).

  <img src="web/assets/logo.webp" alt="Original PALO Framework logo" width="80">
  <img src="web/assets/blueprintbench/brand/blueprintbench-logo.png" alt="PALO BlueprintBench logo" width="100%">
</p>

<p align="center">
  <a href="https://github.com/sev7enITA/PALO-BlueprintBench/actions/workflows/verify.yml"><img src="https://github.com/sev7enITA/PALO-BlueprintBench/actions/workflows/verify.yml/badge.svg" alt="Evaluator and artifact verification"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-83e2dc" alt="Code licence: MIT"></a>
  <a href="https://github.com/sev7enITA/PALO-BlueprintBench/releases/tag/v0.3.0-internal.1"><img src="https://img.shields.io/badge/release-0.3.0--internal.1-1f6feb" alt="Internal-test release 0.3.0-internal.1"></a>
  <a href="docs/specification-fidelity-study.md"><img src="https://img.shields.io/badge/independent_validation-open-e9bc73" alt="Independent validation is open"></a>
</p>

<h3 align="center">Benchmark for specification fidelity</h3>

<p align="center">
  <a href="https://paloframework.org/PALO_BlueprintBench_Leaderboard.html"><b>Open internal test results</b></a> |
  <a href="https://paloframework.org/PALO_BlueprintBench.html"><b>Research overview</b></a> |
  <a href="https://github.com/sev7enITA/PALO-BlueprintBench/wiki"><b>Read the wiki</b></a> |
  <a href="#quick-start"><b>Run the evaluator</b></a> |
  <a href="CONTRIBUTING.md"><b>Contribute</b></a>
</p>

**PALO BlueprintBench evaluates specification fidelity:** the preservation of business obligations, permissions, exceptions and responsibilities in AI-generated specifications. Human correction effort is a proposed measure and has not yet been validated.

The [local validation agent](validation_agent/README.md) prepares model-assisted reviews and calibration diagnostics with LM Studio. Its outputs are advisory and do not establish independent expert approval or benchmark qualification.

The project is an **open research pilot**. The executable evaluator, historical diagnostic evidence and contribution process are available now. The first proposed independent study focuses on procurement. **Qualified held-out results: 0. No PALO Blueprint Index score is assigned.**

| Inspect | Reproduce | Participate |
|---|---|---|
| [Model explorer](https://paloframework.org/PALO_BlueprintBench.html#explorer) | [Quick start](#quick-start) | [Contributor routes](CONTRIBUTING.md) |
| [35 benchmark references](docs/benchmark-references.md) | [Historical evidence and replay](evidence/development-2026-11-10/README.md) | [Procurement study](docs/specification-fidelity-study.md) |
| [Metrics and trust boundaries](docs/evaluator-contract.md) | [Release and packages](https://github.com/sev7enITA/PALO-BlueprintBench/releases/tag/v0.3.0-internal.1) | [Reviewer kit](docs/reviewer-kit.md) |

## Evaluation tracks

| Track | Task | Source material |
| --- | --- | --- |
| [Policy Interpretation](https://paloframework.org/PALO_BlueprintBench_Leaderboard.html) | Translate rules and classify statements | Three authored procurement texts |
| [Process Interpretation](https://paloframework.org/PALO_BlueprintBench_NextCycle.html) | Interpret propositions and generate workflows | Six authored process descriptions |
| [Specification Generation](https://paloframework.org/PALO_BlueprintBench_Generation.html) | Generate source-linked requirements and decision rules | Three public procurement documents, 200 supplied pages |

[Specification Generation evidence release](https://github.com/sev7enITA/PALO-BlueprintBench/releases/tag/study-2026-11-12-real-document.1): 27 assigned calls, 14 complete responses, five incomplete or unavailable and eight not dispatched. Labels are assistant drafts; independent qualification is pending.

The [Specification Generation study](docs/study-closure-2026-11-12.md) is closed incomplete. Its [workflow connectivity diagnostic](docs/workflow-connectivity-diagnostic.json) is advisory; the [annotation guidelines](docs/annotation-guidelines-draft.md) awaits external approval.

## Current internal tests and dashboard

The published catalogue contains **18 distinct model IDs and 28 cohort/configuration records**. Internal procurement tests have **324 assigned slots, 306 dispatched requests, 299 complete responses, 7 failed or incomplete responses and 18 pre-call-blocked assignments**. These are short synthetic tests with assistant-draft labels. Historical adapter diagnostics remain separate. No independent qualification or PALO Blueprint Index is assigned.

[Interactive internal results](https://paloframework.org/PALO_BlueprintBench_Leaderboard.html) | [Project identity](docs/brand-usage.md)

Six configurations match all 324 assigned verification labels, and eleven are within three matches of the ceiling. Sixteen of twenty generalist disagreements concern three statements needing adjudication. These counts describe a saturated pilot; they do not establish equivalence or superiority. Source and label author model identity was not retained and is explicitly unavailable.

The dashboard retains descriptive comparisons, filters, plots and CSV/JSON exports. Numerical quality, completion, cost and time ranks are suspended. Missing responses remain visible, conditional agreement and coverage are separate, and reviewer diagnostics are outside model-results panels. The prior testing badge is withdrawn from current distribution.

The earlier evaluator and dashboard PRs have merged. The current release is an internal-test corrective package, with no independent scientific qualification or human approval implied.

## Contents

[Specification Fidelity](#specification-fidelity) · [Explore the project](#explore-the-project) · [Evaluation tracks](#evaluation-tracks) · [Quick start](#quick-start) · [Evidence and results](#evidence-and-results) · [Research roadmap](#research-roadmap) · [Contribute](#contribute) · [Documentation](#documentation) · [Citation](#citation) · [Governance](#governance-and-licensing)

## Specification Fidelity

| Source | Candidate specification | What needs review |
|---|---|---|
| The manager **may** approve after review. | The manager **must** approve after review. | A permission became an obligation. |
| Approval is required **unless** the purchase is exempt. | Approval is required for every purchase. | The exception disappeared. |

*Illustrative examples, not measured model results.* A valid citation or valid JSON does not establish that the business meaning is correct.

PALO's proposed study examines **modality, negation, ownership, conditions and exceptions**, together with coverage and human correction effort. It builds on established work in grounded generation, document reasoning, process modelling and evaluation infrastructure. See the [sourced comparison](docs/benchmark-references.md) for overlaps and differences.

## Explore the project

The shared catalogue contains **18 distinct model IDs and 28 configuration/cohort records**. Internal procurement tests retain **324 assigned slots, 306 dispatched requests, 299 complete responses, 7 incomplete or failed responses and 18 pre-call-blocked assignments**. Historical adapter diagnostics remain separate. Filters, sortable internal-test columns, source inspection and a call ledger expose the evidence without assigning a qualified rank.

[Internal adversarial review](internal_tests/2026-11-11-adversarial/README.md): 96 of 108 assigned reviewer judgments retained; three items with observed disagreement, including two partially reviewed panels. GLM capacity failure and Qwen format projection remain visible. Primary scores are unchanged.

[Model results over time](https://paloframework.org/PALO_BlueprintBench_Leaderboard.html#temporal-model-results) plots recorded verification-request timestamps with case, metric and model filters, plus CSV/SVG export. Collection times from 11 November are not model release dates or a longitudinal progress study.

The results table supports descriptive sorting, developer-country filters, source inspection and CSV/JSON export of visible ordered rows. Numerical ranks are suspended. Exports retain scope, denominators, missing observations and metadata sources. Country describes a documented developer-organization business base, not serving location or data residency. See the [country source register](docs/model-origins.json).

[Interactive internal results](https://paloframework.org/PALO_BlueprintBench_Leaderboard.html) · [Project identity and withdrawn-badge notice](docs/brand-usage.md)


<details>
<summary><b>See the document-to-blueprint review context</b></summary>

<img src="presentation/screenshots/07-graph-and-evidence.jpg" alt="Actual Workbench pilot capture with a synthetic procurement entity graph, source reference and pending review states" width="100%">

Actual Workbench pilot capture using synthetic procurement content. The entity graph, source evidence and pending decisions illustrate the workflow being studied. This image is not evidence of a qualified application release or completed benchmark campaign.

[Workbench pilot](https://paloframework.org/PALO_DocumentWorkbench.html)

</details>

## Track definitions

```mermaid
flowchart LR
    S[Source documents] --> A[Source units and task scope]
    A --> G[Independent gold preparation]
    A --> C[Frozen system configuration]
    C --> O[Raw output and claims]
    G --> H[Human annotation and adjudication]
    O --> H
    H --> E[Evidence checks and scoped scoring]
    E --> R[Reviewable results]
```

*Protocol overview. Independent gold preparation and qualification are required study stages, not completed milestones.*

| Track | Evaluation boundary | Present state |
|---|---|---|
| **A. Interpretation** | Human-checked source units to annotated propositions | Evidence contract and synthetic scorer available; independent study proposed |
| **B. Document to blueprint** | Original PDF/XLSX through reviewed export | Development workflow; no new qualified end-to-end app release |
| **C. Control conformance** | Faults, boundaries and actual permitted effects | Protocol scope; does not imply production enforcement |

Eight research dimensions cover document fidelity, semantic faithfulness, coverage and uncertainty, ER/dictionary/ontology, process fidelity, governance controls, reliability, and human effort/FinOps. The first study narrows that programme to procurement. [Method and study design](docs/specification-fidelity-study.md).

## Quick start

**Python 3.10+**, Git and the pinned `jsonschema` dependency. No API key, model download or paid inference is needed for the evaluator demonstration. Dependency installation needs network access unless packages are already cached.

```sh
git clone --branch v0.3.0-internal.1 https://github.com/sev7enITA/PALO-BlueprintBench.git
cd PALO-BlueprintBench
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r evaluator/requirements.txt
python -m unittest discover -s evaluator -p 'test_*.py' -v
python evaluator/demo.py ./demo-evidence
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` instead of `source`. Choose a fresh output directory: evidence is not overwritten.

The synthetic example produces `demo-evidence/result.json`. Its three tasks yield:

| Output field | Example value | Meaning |
|---|---|---|
| `assigned_attempts` | `3` | All assigned tasks remain in the denominator |
| `accepted_tasks` | `1` | Acceptance is computed from the frozen policy |
| `critical_errors` | `1` | Distinct critical proposition classes |
| `qualified` | `false` | Synthetic conformance is not independent qualification |

To evaluate the generated evidence again with a new result path:

```sh
python evaluator/blueprintbench.py evaluate demo-evidence/campaign.lock.json demo-evidence/run.json --evidence-root demo-evidence --output demo-recomputed.json
```

[Detailed evaluator guide](evaluator/README.md) · [Wiki quick start](https://github.com/sev7enITA/PALO-BlueprintBench/wiki/Quick-start) · [Executable JSON Schema](evaluator/evidence.schema.json)

## Evidence and results

| Evidence | Available result | What it establishes |
|---|---|---|
| Evaluator regression suite | **76 evaluator tests pass** in the internal-release verification | Tested integrity, annotation-consistency and accounting behaviour |
| Historical offline replay | **26 of 26** retained attempts reproduce structural counts | Deterministic checker reproduction, without new inference |
| Model diagnostic set | **10 configurations** across development passages | Inspectable observations with differing settings; no qualified ranking |
| Independent held-out study | **0 qualified entries** | Independent annotation, custody and calibration remain open |

[Current verification record](results/release-v0.3.0-internal.1/toolkit-verification.json) · [Offline replay receipt](results/release-v0.3.0-pilot.1/offline-replay.json) · [Raw development evidence](evidence/development-2026-11-10/) · [Audit response and remaining limits](docs/launch-readiness.md)

The three original repositories above 100 MB are development cases used to repair PALO. They do not establish unseen-case performance. Structural acceptance is not semantic accuracy; recorded charges are not invoice-reconciled enterprise costs. The latest recorded Beam full-repository campaign stopped at the workspace budget without a reviewed export. This benchmark release does not qualify a new Workbench app.

<details>
<summary><b>Replay historical structural counts without model calls</b></summary>

With the virtual environment active:

```sh
python -m pip install -r evidence/development-2026-11-10/requirements.txt
python evidence/development-2026-11-10/replay.py
```

Expected: 26 replayed attempts, an empty differences list and `counts_match: true`. This reuses retained responses. It does not repeat generation, validate semantic annotations or prove the original environment was identical. See the [archive boundaries](evidence/development-2026-11-10/README.md).

</details>

## Research roadmap

- [x] Publish the evidence contract, synthetic fixtures and adversarial regression checks.
- [x] Publish retained development requests, responses and offline checker replay.
- [x] Provide a model explorer and a sourced methodological comparison.
- [ ] Establish external preregistration and independent custody.
- [ ] Prepare unseen procurement cases with blinded annotation and adjudication.
- [ ] Calibrate the metric with seeded semantic defects and valid controls.
- [ ] Measure human correction effort and family-aware uncertainty.
- [ ] Consider qualified results and a preregistered PALO Blueprint Index formula.

These are evidence gates, not promised delivery dates. [Study RFC](docs/specification-fidelity-study.md) · [Qualification and roadmap wiki](https://github.com/sev7enITA/PALO-BlueprintBench/wiki/Qualification-and-roadmap).

## Contribute

| Your expertise | A useful first contribution |
|---|---|
| Procurement or process analysis | Review a source-backed rule and document ambiguity before seeing model answers |
| Evaluation engineering | Reproduce a failure, challenge the metric, or inspect output-to-claim mapping |
| Business operations | Join a supervised review session to study correction effort |
| Corpus curation | Propose a public, rights-cleared source family and its provenance |
| Independent research governance | Discuss custody, conflicts, adjudication and qualification responsibilities |

Read [CONTRIBUTING.md](CONTRIBUTING.md), browse [issues](https://github.com/sev7enITA/PALO-BlueprintBench/issues), or [express interest](https://paloframework.org/PALO_BlueprintBench.html#participate). Use public or synthetic examples. Keep company documents, credentials and active held-out answer keys out of issues and pull requests. Participation and attribution are agreed separately.

## Documentation

| Start here | Reference material |
|---|---|
| [Wiki home](https://github.com/sev7enITA/PALO-BlueprintBench/wiki) | [Protocol](docs/protocol.md) |
| [Quick start](https://github.com/sev7enITA/PALO-BlueprintBench/wiki/Quick-start) | [Metrics and evidence contract](docs/evaluator-contract.md) |
| [Reading the explorer](https://github.com/sev7enITA/PALO-BlueprintBench/wiki/Explorer-and-results) | [Reference catalogue](docs/benchmark-references.md) |
| [FAQ](https://github.com/sev7enITA/PALO-BlueprintBench/wiki/FAQ) | [Semantic vocabulary, SKOS and OWL](semantic/README.md) |
| [Contributing](https://github.com/sev7enITA/PALO-BlueprintBench/wiki/Contributing) | [Versioning](docs/versioning.md) and [corrections](docs/corrections.md) |

Repository map: `evaluator/` executable checks; `evidence/` retained diagnostics; `results/` labelled receipts; `docs/` research and contracts; `wiki/` versioned wiki source; `web/` explorer; `semantic/` vocabulary; internal presentation assets are excluded from the public website.

## Citation

Cite the exact release or commit and its evidence scope. There is no project DOI or peer-reviewed validation paper claimed by this release.

```bibtex
@software{degni2026paloblueprintbench,
  author = {Fabrizio Degni},
  title = {PALO BlueprintBench: an open research pilot for AI-generated business blueprints},
  year = {2026},
  version = {0.3.0-internal.1},
  url = {https://github.com/sev7enITA/PALO-BlueprintBench/releases/tag/v0.3.0-internal.1}
}
```

Machine-readable citation: [CITATION.cff](CITATION.cff). Methodological acknowledgements include [BIG-bench](https://github.com/google/BIG-bench), [HELM](https://github.com/stanford-crfm/helm), [LM Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness) and the [full reference comparison](docs/benchmark-references.md). Listing a reference does not imply affiliation or endorsement.

## Governance and licensing

Fabrizio Degni maintains both PALO and this benchmark, a declared conflict of interest. Independent annotators, custodians and reproducers are being recruited; no external board or accreditation is claimed. [Governance](GOVERNANCE.md) · [Cross-review](docs/cross-review-2026-11-11.md).

PALO and this toolkit are free. Code is [MIT licensed](LICENSE); third-party documents and model licences retain their own terms. External inference providers may charge separately.

**Naming:** PALO BlueprintBench concerns business development specifications. It is unrelated to Andon Labs' [Blueprint-Bench 2](https://andonlabs.com/evals/blueprint-bench-2), which evaluates spatial floor-plan reconstruction.

<p align="center"><b>Join the Human Agency.</b><br>Build with AI. Keep humans in command.</p>

## Internal baseline tests

A separate internal cohort adds OpenAI GPT-6.1 Sol, Anthropic Claude Opus 5.5 and Google Gemini 4 Argon. It records 54 requests on three short synthetic procurement cases, three repetitions and two tasks. There are 53 complete responses, one provider failure, and a contested expected label. These are internal tests, with zero independently qualified results.

[Read the report](internal_tests/2026-11-11-frontier/REPORT.md) · [Inspect the frozen design](internal_tests/2026-11-11-frontier/README.md) · [Explore results](https://paloframework.org/PALO_BlueprintBench.html#internal-tests). The 27 exported blueprints are assistant-reviewed drafts requiring business approval. No PBI score, superiority claim or 100 MB processing claim follows from this cohort.


## Shared model catalogue and extensions

The [launch page](https://paloframework.org/PALO_BlueprintBench.html#models) and [internal results](https://paloframework.org/PALO_BlueprintBench_Leaderboard.html) now read one generated catalogue. It retains all ten historical model IDs and separates their adapter checks from the procurement measurements. Eighteen distinct model IDs produce 28 configuration rows across the two evidence groups. Schematron Small/Turbo and Bonsai 9B/27B remain distinct models.

The [twelve-model extension](internal_tests/2026-11-11-expansion/README.md) and [legacy-identity supplement](internal_tests/2026-11-11-legacy-extension/README.md) use the same source, prompt and draft-label bytes as the original baseline, with three repetitions and 324 total assigned task slots across all campaigns. Sakana's 18 supplement assignments are pre-call blocked; no provider response or semantic result is fabricated. Counts are always read alongside completion, missing data and configuration details. Sortable columns and filters support inspection, not independently qualified ranking.

New source-indexed translations are unreviewed drafts linked to raw outputs. They do not inherit the original baseline's 27 assistant-reviewed blueprint exports. Limitations, campaign selection timing, configuration differences, budget reservations and further development are documented in the [internal-results method](docs/leaderboard-method.md). Overall authorised inference and advisory budget: USD40 including prior work.

## Reviewer diagnostics and model roster

[Inspect the model roster](https://paloframework.org/PALO_BlueprintBench_Leaderboard.html#model-roster) for configuration scope, serving settings and observed input-token ranges. These are distinct from catalogue context ceilings. The ten historical configurations remain unranked, and the 35 external benchmark references were not executed.

[Separate internal reviewer diagnostics](https://paloframework.org/PALO_BlueprintBench_Diagnostics.html) separates response structure from draft-label comparisons on 18 elementary pairs. [Review decisions](docs/calibration-review-decisions.md) explain adopted controls and unresolved limits. This does not qualify a PALO Blueprint Index or modify the 18-model cohort.

### Six-scenario engineering feasibility

The separate [next-cycle view](https://paloframework.org/PALO_BlueprintBench_NextCycle.html) reports internal execution on six fictional procurement scenarios, 48 propositions, workflow drafts and metamorphic checks. It preserves the original cohort unchanged. See [execution method](docs/next-cycle-execution.md) and [source records](internal_tests/2026-11-11-next-cycle). Human adjudication remains pending; no numerical model ranks or independent validation are assigned.

### Qualification study

The [planned qualification protocol](docs/qualification-roadmap.md) defines generation tasks, the contradiction rubric, external roles and acceptance evidence. Its six gates remain open. [Archived six-scenario observations](https://github.com/sev7enITA/PALO-BlueprintBench/releases/tag/study-2026-11-11-six-scenario.1) are internal engineering evidence; presentation revision 2026-11-11.5 does not change those records.
