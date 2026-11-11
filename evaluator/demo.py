"""Create labelled synthetic fixtures. These are evaluator tests, not model results."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import blueprintbench as bb


def put(root, name, value):
    path = Path(root) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def put_text(root, name, text):
    path = Path(root) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def bind_output(root, name, emitted):
    """Synthetic decomposition with exact code-point spans, including separators."""
    text = ""
    non_claim = []
    for claim in emitted:
        if text:
            non_claim.append({"span": [len(text), len(text) + 1], "reason": "newline separator"})
            text += "\n"
        claim["span"] = [len(text), len(text) + len(claim["text"])]
        text += claim["text"]
    return (put(root, f"{name}/claims.json", emitted),
            put_text(root, f"{name}/raw.txt", text), non_claim)


def make(root):
    root = Path(root)
    config = put(root, "configuration.json", {
        "model": {"id": "synthetic-fixture-not-a-model", "revision": "fixture-2", "quantisation": "not_applicable"},
        "provider_runtime": {"id": "none", "revision": "not_applicable"},
        "settings": {"reasoning": "not_applicable", "temperature": None, "seed": None, "max_output_tokens": None, "unavailable_reason": "Synthetic fixture; no model call"},
        "pipeline": {"version": "fixture-2", "adapter_revision": "fixture-2", "prompt_sha256": "unavailable", "schema_sha256": "unavailable", "unavailable_reason": "Synthetic fixture; no inference prompt or generation schema"},
        "environment": {"id": "synthetic", "runtime_version": "fixture-2"}})
    tasks = []
    attempts = []
    for name, state, matches in [("faithful", "pass", ["g1", "g2"]),
                                  ("inverted_rule", "fail", ["g1", None]),
                                  ("empty", "abstain", [])]:
        gold = put(root, f"{name}/gold.json", {
            "required_propositions": ["g1", "g2"], "annotation_status": "synthetic",
            "answerable": True, "allowed_match_groups": [], "allowed_alternatives": {},
            "forbidden_inferences": [{"id": "f1", "text": "All purchases require owner approval", "violated_gold": ["g2"]}], "critical_rule_ids": ["g1", "g2"],
            "source_scope": "Synthetic purchase example, two propositions only",
            "source_text": "Purchases above EUR 500 require owner approval. Purchases at or below EUR 500 may proceed without owner approval.",
            "meaning": {"g1": "Above EUR 500 requires owner approval", "g2": "At or below EUR 500 permits proceeding without owner approval"}})
        tasks.append({"id": name, "family": "synthetic-purchasing", "domain": "procurement",
                      "scope": "two explicitly defined rules", "gold": gold})
        meaning = {"g1": "Purchases above EUR 500 require owner approval.",
                   "g2": "Purchases at or below EUR 500 may proceed without owner approval."}
        emitted = [{"id": f"c{i}", "text": (meaning[m] if m else "All purchases must have owner approval")}
                   for i, m in enumerate(matches)]
        claims_ref, raw_ref, non_claim = bind_output(root, name, emitted)
        receipt = put(root, f"{name}/receipt.json", {
            "task_id": name, "repetition": 1, "state": state, "termination_reason": "completed",
            "all_retry_costs_included": True, "artifacts": [claims_ref, raw_ref], "claims_artifact": claims_ref,
            "raw_output": raw_ref, "non_claim_spans": non_claim, "request_identity": {"provider_request_id": None, "request_sha256": None, "unavailable_reason": "Synthetic fixture, no provider call"}})
        annotation = put(root, f"{name}/annotation.json", {
            "task_id": name, "receipt_sha256": receipt["sha256"], "scope_complete": True, "atomicity_reviewed": True,
            "review_type": "synthetic", "claims": [
                {"id": f"c{i}", "equivalence_id": f"p{i}", "verdict": "supported" if m else "unsupported",
                 "matches_gold": [m] if m else [], "critical": m is None,
                 "violated_gold": [] if m else ["g2"], "matches_forbidden": [] if m else ["f1"], "matches_alternatives": [], "error_category": "none" if m else "source_rule_inversion",
                 "critical_rationale": "Synthetic rule inversion" if m is None else "No critical error",
                 "text_sha256": hashlib.sha256(emitted[i]["text"].encode("utf-8")).hexdigest()}
                for i, m in enumerate(matches)]})
        attempts.append({"task_id": name, "repetition": 1, "state": state, "elapsed_seconds": 0,
                         "cost": {"status": "not_incurred", "usd": 0, "reason": "Synthetic fixture, no inference"},
                         "receipt": receipt, "annotation": annotation})
    campaign = {"id": "synthetic-evaluator-conformance", "benchmark_version": bb.VERSION,
                "split": "synthetic", "track": "interpretation", "repetitions": 1,
                "success_policy": {"minimum_precision": 1, "minimum_recall": 1, "maximum_critical_errors": 0},
                "subjects": [{"id": "fixture", "configuration": config}], "tasks": tasks}
    lock = bb.freeze(campaign, root)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    run = {"run_id": "synthetic-example", "campaign_sha256": lock["sha256"], "subject_id": "fixture",
           "configuration_sha256": config["sha256"], "started_at": now, "finished_at": now,
           "evidence_status": "self_reported", "attempts": attempts, "submitter_id": "synthetic-author", "execution": {"mode": "serial", "max_concurrency": 1}}
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
