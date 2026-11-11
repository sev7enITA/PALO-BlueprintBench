# PALO BlueprintBench

**An open research pilot for evaluating AI-generated business blueprints.**

[Live model explorer](https://paloframework.org/PALO_BlueprintBench.html) · [Protocol](docs/protocol.md) · [Proposed PALO Blueprint Index](docs/palo-blueprint-index.md) · [Contribute](CONTRIBUTING.md)

BlueprintBench studies the route from PDF and Excel documents to source-linked entities, relationships, dictionaries, process rules and a blueprint a business user can review. It separates interpretation, document-to-blueprint performance and control conformance.

## Current status

| Component | Status |
|---|---|
| Explorer | Ten historical model passage diagnostics, filters, charts, four-model comparison and CSV export |
| Evaluator v0.1 | Executable evidence-integrity checks and scoped, already-adjudicated semantic accounting |
| Original three repositories above 100 MB | Development cases used to repair PALO, not held-out qualification |
| Independent reference annotation | Contributors being recruited |
| Qualified held-out entries | **0** |
| PALO Blueprint Index | Proposed name and design contract; **no score published** |

Structural-check acceptance is not semantic accuracy. Recorded provider charges are not invoice-reconciled enterprise costs. Historical model settings differ and are not optimised recommendations. The most recent Beam full-repository campaign stopped at the workspace budget and produced no reviewed export; the remaining two case analyses were blocked before a new request. This research release does not qualify a new Workbench app version.

## Reproduce the first evaluator slice

Python 3.10 or later; standard library only. No API credentials or paid inference are needed.

```sh
cd evaluator
python3 -m unittest -v test_blueprintbench
python3 demo.py /tmp/blueprintbench-example
python3 blueprintbench.py evaluate /tmp/blueprintbench-example/campaign.lock.json /tmp/blueprintbench-example/run.json --evidence-root /tmp/blueprintbench-example --output /tmp/blueprintbench-result.json
```

Choose fresh output paths. The demo is synthetic evaluator testing, not a model measurement. Seventeen checks passed in the initial local verification. Qualification always remains false in this evaluator release because human independence and reproduction are not verified by JSON declarations.

## Repository map

- `evaluator/`: runnable tool, tests and synthetic example generator.
- `docs/`: protocol, design research, index proposal, reference-field contract and reviewer kit.
- `results/development/`: explicitly unranked historical observations and correction metadata.
- `web/`: versioned explorer and public downloads; PALO remains the canonical live host.
- `presentation/`: authoring source and actual application/configuration screenshots for the 15-slide explanation.

No company documents, production credentials or active held-out answer keys belong in this repository. Links to third-party public sources do not grant redistribution rights.

## Independence and governance

Fabrizio Degni maintains PALO and this benchmark. That conflict is disclosed, not removed by giving the project a separate repository. Independent annotators and reproducers are being recruited; no external board or accreditation is claimed. See [governance](GOVERNANCE.md), [version policy](docs/versioning.md) and [corrections](docs/corrections.md).

The project and tooling are free. External model providers may charge for inference. Code is MIT licensed; third-party source documents and model licences retain their own terms.

## Semantic vocabulary

The [BlueprintBench vocabulary](semantic/README.md) defines the evaluation concepts, eight dimensions and review states as JSON, SKOS and OWL.

## Naming clarification

PALO BlueprintBench evaluates business-document interpretation and is unrelated to Andon Labs' [Blueprint-Bench / Blueprint-Bench 2](https://arxiv.org/abs/2509.25229), which evaluates spatial floor-plan generation. See the [dedicated-domain proposal](docs/palo-blueprint-index.md#domain-proposal). No dedicated domain is registered by this project at this stage.

## Cross-review and next study

The [11 November cross-review](docs/cross-review-2026-11-11.md) records GLM, Gemini and LM Studio advice, six reproduced evaluator behaviours and disagreements retained during adjudication. The [Specification Fidelity Study](docs/specification-fidelity-study.md) proposes a procurement-focused calibration and human-review study. These documents add no qualified score or application release.
