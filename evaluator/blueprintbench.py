#!/usr/bin/env python3
"""BlueprintBench 0.1: evidence registration and bounded, adjudicated scoring.

No model calls, automatic human certification, or inferred gold answers.
Python 3.10+, standard library only.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

VERSION = "0.1.0"
STATES = {"pass", "fail", "abstain", "not_run"}


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def number(value, label):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0,
            f"{label}: expected finite nonnegative number")
    return value


def instant(value):
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(parsed.tzinfo is not None, "timestamps require timezone")
        return parsed
    except (AttributeError, ValueError) as exc:
        raise Invalid("invalid timestamp") from exc


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(Invalid(f"invalid number {x}")))


def artifact(ref, root):
    require(isinstance(ref, dict), "artifact reference must be an object")
    relative = Path(ref["path"])
    require(not relative.is_absolute(), "absolute artifact paths are forbidden")
    root = Path(root).resolve()
    target = (root / relative).resolve()
    require(target.is_relative_to(root), "artifact escapes evidence root")
    require(target.is_file(), f"missing artifact: {relative}")
    actual = hashlib.sha256(target.read_bytes()).hexdigest()
    require(actual == ref["sha256"], f"artifact hash mismatch: {relative}")
    return target


def unique(items, label):
    require(len(items) == len(set(items)), f"duplicate {label}")


def validate_campaign(campaign, root):
    require(campaign["benchmark_version"] == VERSION, "unsupported benchmark version")
    require(campaign["split"] in {"development", "synthetic", "heldout_candidate"}, "invalid split")
    require(campaign["track"] in {"interpretation", "end_to_end", "controls"}, "invalid track")
    require(type(campaign["repetitions"]) is int and campaign["repetitions"] > 0,
            "repetitions must be a positive integer")
    require(campaign["tasks"] and campaign["subjects"], "empty campaign")
    unique([t["id"] for t in campaign["tasks"]], "task IDs")
    unique([s["id"] for s in campaign["subjects"]], "subject IDs")
    for task in campaign["tasks"]:
        require(task["family"] and task["domain"], "task family and domain required")
        gold = read_json(artifact(task["gold"], root))
        require(isinstance(gold["required_propositions"], list), "gold propositions must be a list")
        unique(gold["required_propositions"], "gold propositions")
        require(all(isinstance(x, str) and x for x in gold["required_propositions"]), "invalid gold ID")
        require(gold["annotation_status"] in {"synthetic", "assistant_draft", "independent_adjudicated"},
                "invalid gold annotation status")
        if gold["annotation_status"] == "independent_adjudicated":
            require(len(set(gold["annotator_ids"])) >= 2 and gold["adjudicator_id"],
                    "independent gold requires two annotators and adjudicator")
        require(task["scope"] and gold["source_scope"], "explicit bounded gold scope required")
    for subject in campaign["subjects"]:
        configuration = read_json(artifact(subject["configuration"], root))
        for group in ("model", "provider_runtime", "settings", "pipeline", "environment"):
            require(isinstance(configuration.get(group), dict) and configuration[group],
                    f"configuration missing {group}")
    return campaign


def freeze(campaign, root):
    validate_campaign(campaign, root)
    payload = {"registered_at": dt.datetime.now(dt.timezone.utc).isoformat(), "campaign": campaign}
    return {"payload": payload, "sha256": digest(payload)}


def evaluate(lock, run, root):
    require(digest(lock["payload"]) == lock["sha256"], "campaign lock was modified")
    campaign = validate_campaign(lock["payload"]["campaign"], root)
    require(run["campaign_sha256"] == lock["sha256"], "run uses another campaign")
    require(instant(run["started_at"]) >= instant(lock["payload"]["registered_at"]),
            "run predates registration; import as historical diagnostic instead")
    require(instant(run["finished_at"]) >= instant(run["started_at"]), "negative run duration")
    subjects = {s["id"]: s for s in campaign["subjects"]}
    require(run["subject_id"] in subjects, "subject not registered")
    subject = subjects[run["subject_id"]]
    require(run["configuration_sha256"] == subject["configuration"]["sha256"], "configuration changed")
    require(run["evidence_status"] in {"self_reported", "maintainer_reproduced", "independently_reproduced"},
            "invalid evidence status")
    tasks = {t["id"]: t for t in campaign["tasks"]}
    expected = {(t, r) for t in tasks for r in range(1, campaign["repetitions"] + 1)}
    observed = set()
    rows = []
    all_human = True
    all_cost_known = True
    for attempt in run["attempts"]:
        key = (attempt["task_id"], attempt["repetition"])
        require(type(key[1]) is int and key in expected, "unexpected task or repetition")
        require(key not in observed, "duplicate task/repetition; retries belong inside its receipt")
        observed.add(key)
        require(attempt["state"] in STATES, "invalid state; mandatory tasks cannot be N/A")
        number(attempt["elapsed_seconds"], "elapsed_seconds")
        cost = attempt["cost"]
        require(cost["status"] in {"reported", "reconciled", "unknown", "not_incurred"}, "invalid cost state")
        if cost["status"] == "unknown":
            require(cost["usd"] is None, "unknown cost cannot be represented by zero")
            all_cost_known = False
        else:
            number(cost["usd"], "cost.usd")
            if cost["status"] == "not_incurred":
                require(cost["usd"] == 0 and cost.get("reason"), "zero cost needs an explanation")
        receipt = read_json(artifact(attempt["receipt"], root))
        require(receipt["task_id"] == key[0] and receipt["repetition"] == key[1], "receipt belongs to another attempt")
        require(receipt["state"] == attempt["state"], "receipt/result state disagreement")
        require(receipt["all_retry_costs_included"] is True, "retry cost accounting is incomplete")
        for ref in receipt["artifacts"]:
            artifact(ref, root)
        if attempt["state"] == "pass":
            require(bool(receipt["artifacts"]), "passing task requires outcome artifact")
        gold = read_json(artifact(tasks[key[0]]["gold"], root))
        required = set(gold["required_propositions"])
        annotation = read_json(artifact(attempt["annotation"], root))
        require(annotation["task_id"] == key[0], "annotation belongs to another task")
        require(annotation["receipt_sha256"] == attempt["receipt"]["sha256"], "annotation is not bound to receipt")
        require(annotation["scope_complete"] is True, "partial annotations must not be presented as complete scoped precision")
        human = gold["annotation_status"] == "independent_adjudicated" and annotation["review_type"] == "independent_human"
        if human:
            require(len(set(annotation["reviewer_ids"])) >= 2 and annotation["adjudicator_id"],
                    "human assessment needs two reviewers and adjudicator")
        all_human = all_human and human
        claims = annotation["claims"]
        unique([c["id"] for c in claims], "claim IDs")
        # Raw output must enumerate exactly the same claims. This prevents quietly
        # removing rejected claims before computing precision.
        emitted = read_json(artifact(receipt["claims_artifact"], root))
        unique([c["id"] for c in emitted], "emitted claim IDs")
        require({c["id"] for c in emitted} == {c["id"] for c in claims}, "unannotated or invented claim IDs")
        matched = set()
        supported = 0
        critical = 0
        propositions = {}
        for claim in claims:
            require(claim["verdict"] in {"supported", "unsupported"}, "unassessed claim in complete scope")
            require(type(claim["critical"]) is bool, "critical must be boolean")
            critical += int(claim["critical"])
            hits = set(claim["matches_gold"])
            require(hits <= required, "claim matches unknown gold item")
            equivalence = claim["equivalence_id"]
            require(isinstance(equivalence, str) and equivalence, "human proposition equivalence ID required")
            signature = (claim["verdict"], tuple(sorted(hits)))
            require(equivalence not in propositions or propositions[equivalence] == signature,
                    "inconsistent equivalent proposition annotations")
            propositions[equivalence] = signature
            if claim["verdict"] == "supported":
                supported += 1
                matched |= hits
            else:
                require(not hits, "unsupported claims cannot earn recall credit")
        rows.append({"task_id": key[0], "repetition": key[1], "family": tasks[key[0]]["family"],
                     "domain": tasks[key[0]]["domain"], "state": attempt["state"],
                     "emitted": len(claims), "supported": supported, "gold": len(required),
                     "recovered": len(matched), "critical_errors": critical,
                     "unique_propositions": len(propositions),
                     "precision": sum(v[0] == "supported" for v in propositions.values()) / len(propositions) if propositions else None,
                     "recall": len(matched) / len(required) if required else None,
                     "elapsed_seconds": attempt["elapsed_seconds"], "cost": cost})
    missing = sorted(expected - observed)
    success = sum(r["state"] == "pass" for r in rows)
    critical = sum(r["critical_errors"] for r in rows)
    known_cost = sum(r["cost"]["usd"] or 0 for r in rows)
    reasons = []
    if campaign["split"] != "heldout_candidate": reasons.append("development_or_synthetic_data")
    if missing: reasons.append("missing_assigned_attempts")
    if any(r["state"] == "not_run" for r in rows): reasons.append("assigned_tasks_not_run")
    if campaign["repetitions"] < 3: reasons.append("fewer_than_three_repetitions")
    if not all_human: reasons.append("independent_human_gold_or_assessment_missing")
    # No automatic qualification: identities, independence and real evidence need
    # maintainer review. A hash establishes byte integrity, not semantic truth.
    return {"tool_version": VERSION, "run_id": run["run_id"], "campaign_sha256": lock["sha256"],
            "subject_id": run["subject_id"], "split": campaign["split"], "track": campaign["track"],
            "evidence_status_declared": run["evidence_status"], "identity_and_independence_verified": False,
            "assigned_attempts": len(expected), "recorded_attempts": len(observed),
            "missing_attempts": missing, "reported_passed": success, "reported_completion_rate": success / len(expected),
            "critical_errors": critical, "known_reported_cost_usd": known_cost,
            "cost_complete": all_cost_known and not missing,
            "cost_per_success_usd": known_cost / success if success and all_cost_known and not missing else None,
            "record_comparable_candidate": not reasons, "comparability_blocks": reasons,
            "qualified": False, "qualification_reason": "Independent evidence review is not automated by this tool.",
            "rows": rows, "note": "Scoped annotation scores; not full-corpus precision/recall, human usability, or a model ranking."}


def write_new(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    freeze_parser = sub.add_parser("freeze")
    freeze_parser.add_argument("campaign")
    evaluate_parser = sub.add_parser("evaluate")
    evaluate_parser.add_argument("lock")
    evaluate_parser.add_argument("run")
    for command in (freeze_parser, evaluate_parser):
        command.add_argument("--evidence-root", required=True)
        command.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        result = (freeze(read_json(args.campaign), args.evidence_root) if args.command == "freeze"
                  else evaluate(read_json(args.lock), read_json(args.run), args.evidence_root))
        write_new(args.output, result)
        print(json.dumps({"status": "written", "output": args.output, "tool_version": VERSION}))
    except (Invalid, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Invalid evidence: {exc}\n")


if __name__ == "__main__":
    main()
