"""Create labelled synthetic fixtures. These are evaluator tests, not model results."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import blueprintbench as bb


def put(root, name, value):
    path = Path(root) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")
    return {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def make(root):
    root = Path(root)
    config = put(root, "configuration.json", {
        "model": {"id": "synthetic-fixture-not-a-model"},
        "provider_runtime": {"id": "none"},
        "settings": {"reasoning": "not_applicable"},
        "pipeline": {"version": "fixture-1"}, "environment": {"id": "synthetic"}})
    tasks = []
    attempts = []
    for name, state, matches in [("faithful", "pass", ["g1", "g2"]),
                                  ("inverted_rule", "fail", ["g1", None]),
                                  ("empty", "abstain", [])]:
        gold = put(root, f"{name}/gold.json", {
            "required_propositions": ["g1", "g2"], "annotation_status": "synthetic",
            "source_scope": "Synthetic purchase example, two propositions only",
            "source_text": "Purchases above EUR 500 require owner approval. Purchases at or below EUR 500 may proceed without owner approval.",
            "meaning": {"g1": "Above EUR 500 requires owner approval", "g2": "At or below EUR 500 permits proceeding without owner approval"}})
        tasks.append({"id": name, "family": "synthetic-purchasing", "domain": "procurement",
                      "scope": "two explicitly defined rules", "gold": gold})
        meaning = {"g1": "Purchases above EUR 500 require owner approval.",
                   "g2": "Purchases at or below EUR 500 may proceed without owner approval."}
        emitted = [{"id": f"c{i}", "text": (meaning[m] if m else "All purchases must have owner approval")}
                   for i, m in enumerate(matches)]
        claims_ref = put(root, f"{name}/claims.json", emitted)
        receipt = put(root, f"{name}/receipt.json", {
            "task_id": name, "repetition": 1, "state": state,
            "all_retry_costs_included": True, "artifacts": [claims_ref], "claims_artifact": claims_ref})
        annotation = put(root, f"{name}/annotation.json", {
            "task_id": name, "receipt_sha256": receipt["sha256"], "scope_complete": True,
            "review_type": "synthetic", "claims": [
                {"id": f"c{i}", "equivalence_id": f"p{i}", "verdict": "supported" if m else "unsupported",
                 "matches_gold": [m] if m else [], "critical": m is None}
                for i, m in enumerate(matches)]})
        attempts.append({"task_id": name, "repetition": 1, "state": state, "elapsed_seconds": 0,
                         "cost": {"status": "not_incurred", "usd": 0, "reason": "Synthetic fixture, no inference"},
                         "receipt": receipt, "annotation": annotation})
    campaign = {"id": "synthetic-evaluator-conformance", "benchmark_version": bb.VERSION,
                "split": "synthetic", "track": "interpretation", "repetitions": 1,
                "subjects": [{"id": "fixture", "configuration": config}], "tasks": tasks}
    lock = bb.freeze(campaign, root)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    run = {"run_id": "synthetic-example", "campaign_sha256": lock["sha256"], "subject_id": "fixture",
           "configuration_sha256": config["sha256"], "started_at": now, "finished_at": now,
           "evidence_status": "self_reported", "attempts": attempts}
    put(root, "campaign.json", campaign)
    put(root, "campaign.lock.json", lock)
    put(root, "run.json", run)
    return lock, run


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output")
    args = parser.parse_args()
    destination = Path(args.output)
    if destination.exists(): parser.error("Use a new directory to preserve previous evidence")
    lock, run = make(destination)
    bb.write_new(destination / "result.json", bb.evaluate(lock, run, destination))
    print(destination / "result.json")
