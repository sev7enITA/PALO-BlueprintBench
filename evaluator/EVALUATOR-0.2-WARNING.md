# Evaluator 0.2: acceptance outputs are not qualified evidence

Notice revision: 2026-11-11.3. The immutable GitHub release `v0.3.0-pilot.1` distributes evaluator `0.2.0`.

EV-01 permits a submitter to hide an incorrect substantive assertion in an excluded non-claim span. This can produce inflated precision and acceptance. Do not use 0.2 acceptance outputs to qualify submissions or models. Version 0.3.0 rejects excluded spans unless their actual bytes decode to whitespace permitted by the contract.

The original 0.2 ZIP and tag remain unchanged for audit reproduction. This notice accompanies the current toolkit and is distributed separately beside the historical release. A release tag or successful regression test does not establish human review or independent validation.

Upgrade in a separate directory. Preserve original input/output bytes and locks. Build new 0.3 records from source evidence, document conversion and re-adjudicate missing fields. Freeze and evaluate under the new version; never edit an old lock's version or silently substitute new scores.
