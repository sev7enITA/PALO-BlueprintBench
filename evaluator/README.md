# PALO BlueprintBench evaluator 0.3.0

> Internal-test release `v0.3.0-internal.1`, content revision `2026-11-11.3`. This package contains evaluator and evidence contract `0.3.0`. It has automated regression evidence, not independent human approval or scientific qualification. See `RELEASE.json` and `EVALUATOR-0.2-WARNING.md` included in this package.

> **Historical evaluator 0.2 warning:** Version 0.2 accepts substantive content hidden in non-claim spans (EV-01). Do not use its acceptance outputs for qualification. The historical release `v0.3.0-pilot.1` contains evaluator 0.2.0; its version number does not identify the evaluator version. Preserve its bytes for reproduction and use the explicit migration procedure below.


An executable evidence contract and scoped semantic scorer. Python 3.10+ with pinned `jsonschema`; no model calls, paid APIs or weight downloads. It consumes already-adjudicated references and output annotations. It does not generate reference truth or qualify a model independently.

## Reproduce

Run from this directory and choose fresh output paths:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python blueprintbench.py --version
.venv/bin/python -m unittest discover -v -p 'test_*.py'
.venv/bin/python demo.py /tmp/blueprintbench-v03-example
.venv/bin/python blueprintbench.py evaluate /tmp/blueprintbench-v03-example/campaign.lock.json /tmp/blueprintbench-v03-example/run.json --evidence-root /tmp/blueprintbench-v03-example --output /tmp/blueprintbench-v03-result.json
```

The demo is synthetic conformance testing, not a model measurement. Its three tasks include faithful output, an inverted exception and empty output. An empty answer to an answerable task earns zero recall and undefined precision. The CLI refuses to overwrite output files.

```sh
.venv/bin/python blueprintbench.py freeze campaign.json --evidence-root evidence --output campaign.lock.json
```

This creates a local integrity lock, not trusted external preregistration. `external_registration_verified` and `qualified` remain false. A signed independent decision is a separate governance act.

## Contract and checks

`evidence.schema.json` is the executable record schema. The evaluator enforces hashes, bounded paths, duplicate-key rejection, fixed task/repetition membership, configuration identity, non-compensatory acceptance, deduplicated critical errors and full raw-text span coverage. Annotation text hashes bind decisions to the emitted text. Gold records include meanings, critical rules, answerability, alternatives, prohibited inferences and allowed mapping groups.

Reported completion, calculated task acceptance and independent qualification are separate outputs. Failed, unattempted and missing tasks remain visible. Budget censoring and pre-call blocks have explicit termination reasons. Empty non-execution needs no semantic double annotation. Unknown charges remain unknown, and cost per accepted task includes failures but remains null when accounting is incomplete.

See `evaluator-0.3-draft.md` in the toolkit, or `docs/evaluator-0.3-draft.md` in the repository, for the versioned contract and migration limits. Historical v0.1 records require an explicitly labelled conversion; existing locks must not be rewritten. Structural validity, hashes and review declarations cannot verify semantic truth or reviewer independence.

## Scope and participation

This release supports the initial interpretation-study machinery. Eight-dimensional aggregate scoring, measured business-user effort, independent custody and statistical qualification remain open. `source-registry.json` contains candidate public sources, not qualified new corpora. The optional `acquire.py` downloads selected seed documents, not entire benchmark repositories; review redistribution rights before publishing originals.

Independent procurement-domain annotators, business participants, technical reproducers and custodians can join through the public PALO page. No company documents or credentials should be attached to an expression of interest.

## Upgrade from historical packages

Create a fresh directory for 0.3.0. Install this package's requirements and run its tests. Do not overwrite old outputs or replace the version field in old campaign locks. The schema is intentionally incompatible with 0.2 and the 0.3 development candidate. Reconstruct new records from preserved raw evidence, record the conversion and re-adjudicate fields that were absent. Freeze a new campaign and rerun; do not transfer old acceptance flags or compare scores across contracts silently. The migration guide retains its historical filename `evaluator-0.3-draft.md` so old links continue to resolve.
