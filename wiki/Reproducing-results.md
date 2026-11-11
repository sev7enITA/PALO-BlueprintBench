# Reproducing results

## Choose the claim you want to check

| Claim | Check |
|---|---|
| Evaluator behaviour | Run the regression suite and synthetic demonstration |
| Archived structural counts | Replay the frozen checker over retained responses |
| Generated artifact consistency | Run the public-artifact drift check |
| Semantic correctness | Requires independent source-based annotation, not just code execution |

Follow [[Quick start|Quick-start]] to prepare an isolated environment and pin a release. The released regression record has 42 tests.

## Offline historical replay

From the repository root, with the environment active:

```sh
python -m pip install -r evidence/development-2026-11-10/requirements.txt
python evidence/development-2026-11-10/replay.py
```

The retained release result has `recorded_attempts: 26`, `replayed_attempts: 26`, `differences: []` and `counts_match: true`. This makes no model calls. Do not run the archived runner to repeat live inference; it is guarded and retained for inspection.

The archive contains parsed responses, requests, configurations and a retained checker snapshot. These are not original HTTP wire bytes or proof of a bit-identical original runtime. Read the [archive disclosure](https://github.com/sev7enITA/PALO-BlueprintBench/blob/main/evidence/development-2026-11-10/README.md).

## Public and wiki artifacts

On the current `main` documentation revision:

```sh
python tools/build_public.py --check
python tools/check_wiki.py
```

The first checks generated copies and packages. The second checks wiki navigation and Markdown source links. A local check does not prove deployment: HTTPS readback and GitHub publication are separate evidence.

For an audit, state the commit, environment, command, expected result, actual result and smallest public or synthetic reproducer. [[Contributing|Contributing]] | [Release evidence](https://github.com/sev7enITA/PALO-BlueprintBench/blob/main/results/release-v0.3.0-pilot.1/)
