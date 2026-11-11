#!/usr/bin/env python3
"""BlueprintBench 0.3 draft: evidence registration and bounded, adjudicated scoring.

No model calls, automatic human certification, or inferred gold answers.
Python 3.10+, jsonschema dependency pinned in requirements.txt.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
import re
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

CONTRACT = json.loads(Path(__file__).with_name("evidence.schema.json").read_text(encoding="utf-8"))
Draft202012Validator.check_schema(CONTRACT)

VERSION = "0.3.0-dev.1"
STATES = {"pass", "fail", "abstain", "not_run"}


class Invalid(ValueError):
    pass


def validate_record(kind, value):
    schema = {"$ref": "#/$defs/" + kind, "$defs": CONTRACT["$defs"]}
    error = next(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value), None)
    if error is not None:
        raise Invalid(f"{kind} schema: {list(error.absolute_path)}: {error.message}")


def require(condition, message):
    if not condition:
        raise Invalid(message)


def number(value, label):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0,
            f"{label}: expected finite nonnegative number")
    return value


def instant(value):
    try:
        require(isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value), "timestamp requires RFC 3339 date-time with timezone")
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
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs,
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
    validate_record("campaign", campaign)
    require(campaign["benchmark_version"] == VERSION, "unsupported benchmark version")
    for key in ("minimum_precision", "minimum_recall"):
        number(campaign["success_policy"][key], "success_policy." + key)
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
        validate_record("gold", gold)
        required_ids = set(gold["required_propositions"])
        require(set(gold["meaning"]) == required_ids, "gold meaning must define every required proposition")
        require(set(gold["critical_rule_ids"]) <= required_ids, "unknown critical gold rule")
        require(set(gold["allowed_alternatives"]) <= required_ids, "unknown alternative gold rule")
        unique([x["id"] for x in gold["forbidden_inferences"]], "forbidden inference IDs")
        unique([x["id"] for values in gold["allowed_alternatives"].values() for x in values], "alternative IDs")
        for forbidden in gold["forbidden_inferences"]:
            require(set(forbidden["violated_gold"]) <= set(gold["critical_rule_ids"]), "unknown forbidden critical rule")
        require(all(set(group) <= required_ids for group in gold["allowed_match_groups"]), "unknown allowed matching group")
        require(bool(required_ids) == gold["answerable"], "answerability and required scope disagree")
        require(isinstance(gold["required_propositions"], list), "gold propositions must be a list")
        unique(gold["required_propositions"], "gold propositions")
        require(all(isinstance(x, str) and x for x in gold["required_propositions"]), "invalid gold ID")
        require(gold["annotation_status"] in {"synthetic", "assistant_draft", "independent_adjudicated"},
                "invalid gold annotation status")
        if gold["annotation_status"] == "independent_adjudicated":
            require(len(set(gold.get("annotator_ids", []))) >= 2 and gold.get("adjudicator_id")
                    and gold["adjudicator_id"] not in gold["annotator_ids"],
                    "independent gold requires two annotators and adjudicator")
        require(task["scope"] and gold["source_scope"], "explicit bounded gold scope required")
    for subject in campaign["subjects"]:
        configuration = read_json(artifact(subject["configuration"], root))
        validate_record("configuration", configuration)
        for group in ("model", "provider_runtime", "settings", "pipeline", "environment"):
            require(isinstance(configuration.get(group), dict) and configuration[group],
                    f"configuration missing {group}")
            for field, value in configuration[group].items():
                if isinstance(value, str) and field != "unavailable_reason":
                    require(bool(value.strip()), f"{group}.{field}: blank value")
                if value is None or value == "unavailable":
                    require(bool(configuration[group].get("unavailable_reason")), f"{group}.{field}: unavailable value needs reason")
            if group == "pipeline":
                for field in ("prompt_sha256", "schema_sha256"):
                    value = configuration[group][field]
                    require(value == "unavailable" or (len(value) == 64 and all(c in "0123456789abcdef" for c in value)), f"invalid {field}")
    return campaign


def freeze(campaign, root):
    """Create a local integrity lock. This does not establish external preregistration."""
    validate_campaign(campaign, root)
    payload = {"registered_at": dt.datetime.now(dt.timezone.utc).isoformat(), "campaign": campaign}
    return {"payload": payload, "sha256": digest(payload)}


def evaluate(lock, run, root):
    validate_record("lock", lock)
    validate_record("run", run)
    require(digest(lock["payload"]) == lock["sha256"], "campaign lock was modified")
    campaign = validate_campaign(lock["payload"]["campaign"], root)
    require(run["campaign_sha256"] == lock["sha256"], "run uses another campaign")
    require(instant(run["started_at"]) >= instant(lock["payload"]["registered_at"]),
            "run predates registration; import as historical diagnostic instead")
    require(instant(run["finished_at"]) >= instant(run["started_at"]), "negative run duration")
    now = dt.datetime.now(dt.timezone.utc)
    require(instant(run["finished_at"]) <= now + dt.timedelta(seconds=5), "run timestamp is in the future")
    duration = (instant(run["finished_at"]) - instant(run["started_at"])).total_seconds()
    execution = run["execution"]
    require(execution["mode"] != "serial" or execution["max_concurrency"] == 1, "serial execution requires concurrency one")
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
    proposition_bank = {}
    request_ids = set()
    output_hashes = {}
    warnings = []
    elapsed_total = 0
    for attempt in run["attempts"]:
        key = (attempt["task_id"], attempt["repetition"])
        require(type(key[1]) is int and key in expected, "unexpected task or repetition")
        require(key not in observed, "duplicate task/repetition; retries belong inside its receipt")
        observed.add(key)
        require(attempt["state"] in STATES, "invalid state; mandatory tasks cannot be N/A")
        elapsed_total += number(attempt["elapsed_seconds"], "elapsed_seconds")
        require(attempt["elapsed_seconds"] <= duration + 1, "attempt elapsed time exceeds run window")
        cost = attempt["cost"]
        require(cost["status"] in {"reported", "reconciled", "unknown", "not_incurred"}, "invalid cost state")
        if cost["status"] == "unknown":
            require(cost["usd"] is None, "unknown cost cannot be represented by zero")
            all_cost_known = False
        else:
            number(cost["usd"], "cost.usd")
            if cost["usd"] == 0:
                require(bool(cost.get("reason", "").strip()), "zero cost needs an explanation")
            if cost["status"] == "not_incurred":
                require(cost["usd"] == 0 and cost.get("reason"), "zero cost needs an explanation")
        if "reserved_usd" in cost:
            number(cost["reserved_usd"], "cost.reserved_usd")
            require(cost["status"] == "unknown", "reservation must belong to unknown cost")
        receipt = read_json(artifact(attempt["receipt"], root))
        validate_record("receipt", receipt)
        require(receipt["task_id"] == key[0] and receipt["repetition"] == key[1], "receipt belongs to another attempt")
        require(receipt["state"] == attempt["state"], "receipt/result state disagreement")
        require(receipt["all_retry_costs_included"] is True, "retry cost accounting is incomplete")
        for ref in receipt["artifacts"]:
            artifact(ref, root)
        if attempt["state"] == "pass":
            require(bool(receipt["artifacts"]), "passing task requires outcome artifact")
        gold = read_json(artifact(tasks[key[0]]["gold"], root))
        required = set(gold["required_propositions"])
        emitted = read_json(artifact(receipt["claims_artifact"], root))
        validate_record("emitted", emitted)
        unique([c["id"] for c in emitted], "emitted claim IDs")
        raw = artifact(receipt["raw_output"], root).read_bytes().decode("utf-8")
        # Offsets refer to exact decoded code points: no newline or Unicode normalisation.
        require(not raw.startswith("\ufeff"), "UTF-8 BOM is unsupported; preserve original and record an explicit conversion")
        identity = receipt["request_identity"]
        if identity["provider_request_id"] is None or identity["request_sha256"] is None:
            require(bool(identity["unavailable_reason"].strip()), "missing request identity requires reason")
            warnings.append({"code": "request_identity_unavailable", "task_id": key[0], "repetition": key[1]})
        if identity["provider_request_id"] is not None:
            require(bool(identity["provider_request_id"].strip()), "empty provider request ID")
            require(identity["provider_request_id"] not in request_ids, "provider request ID reused across attempts")
            request_ids.add(identity["provider_request_id"])
        output_key = (key[0], receipt["raw_output"]["sha256"])
        if raw and output_key in output_hashes:
            warnings.append({"code": "identical_output_across_repetitions", "task_id": key[0], "repetition": key[1], "first_repetition": output_hashes[output_key]})
        output_hashes.setdefault(output_key, key[1])
        spans = []
        for claim in emitted:
            begin, end = claim["span"]
            require(0 <= begin < end <= len(raw) and raw[begin:end] == claim["text"], "claim span/text differs from raw output")
            spans.append((begin, end))
        for segment in receipt["non_claim_spans"]:
            begin, end = segment["span"]
            require(0 <= begin < end <= len(raw), "invalid non-claim span")
            spans.append((begin, end))
        # Check coverage first, then restrict exclusions to ASCII whitespace only.
        # Preambles, punctuation, JSON keys and substantive text need claim coverage.
        cursor = 0
        for begin, end in sorted(spans):
            require(begin == cursor, "raw output coverage gap or overlapping spans")
            cursor = end
        require(cursor == len(raw), "raw output coverage gap")
        for segment in receipt["non_claim_spans"]:
            begin, end = segment["span"]
            require(all(c in " \t\r\n" for c in raw[begin:end]), "non-claim spans may contain only ASCII whitespace")
        excluded = sum(end - begin for begin, end in [x["span"] for x in receipt["non_claim_spans"]])
        if raw and excluded / len(raw) > .5:
            warnings.append({"code": "high_non_claim_fraction", "task_id": key[0], "repetition": key[1]})
        termination = receipt["termination_reason"]
        require((attempt["state"] == "not_run") == (termination == "precall_blocked"), "not_run requires precall_blocked")
        if attempt["state"] in {"pass", "abstain"}:
            require(termination == "completed", "reported completed task has unfinished termination")
        if attempt["state"] == "not_run":
            require(not emitted and not raw, "not_run cannot contain generated output")
        if not emitted and attempt["annotation"] is None:
            require(attempt["state"] != "pass", "reported pass requires assessed output")
            claims = []
            human = True  # No semantic output to annotate; not_run still blocks comparability.
        else:
            require(attempt["annotation"] is not None, "emitted claims require annotation")
            annotation = read_json(artifact(attempt["annotation"], root))
            validate_record("annotation", annotation)
            require(annotation["task_id"] == key[0], "annotation belongs to another task")
            require(annotation["receipt_sha256"] == attempt["receipt"]["sha256"], "annotation is not bound to receipt")
            require(annotation["scope_complete"] is True, "partial annotations must not be presented as complete scoped precision")
            require(annotation["atomicity_reviewed"] is True, "atomicity review required")
            human = gold["annotation_status"] == "independent_adjudicated" and annotation["review_type"] == "independent_human"
            if annotation["review_type"] == "independent_human":
                require(len(set(annotation.get("reviewer_ids", []))) >= 2 and annotation.get("adjudicator_id")
                        and annotation["adjudicator_id"] not in annotation["reviewer_ids"],
                        "human assessment needs two reviewers and adjudicator")
                gold_panel = set(gold.get("annotator_ids", [])) | {gold.get("adjudicator_id")}
                output_panel = set(annotation["reviewer_ids"]) | {annotation["adjudicator_id"]}
                require(not (gold_panel & output_panel), "gold and output review panels overlap")
                require(run["submitter_id"] not in gold_panel | output_panel, "submitter cannot be an independent reviewer")
            claims = annotation["claims"]
        all_human = all_human and human and gold["annotation_status"] == "independent_adjudicated"
        unique([c["id"] for c in claims], "claim IDs")
        require({c["id"] for c in emitted} == {c["id"] for c in claims}, "unannotated or invented claim IDs")
        text_hashes = {c["id"]: hashlib.sha256(c["text"].encode("utf-8")).hexdigest() for c in emitted}
        matched = set()
        supported = 0
        critical_occurrences = 0
        inverted_rules = set()
        propositions = {}
        forbidden_by_id = {item["id"]: item for item in gold["forbidden_inferences"]}
        alternatives_by_id = {item["id"]: gold_id for gold_id, values in gold["allowed_alternatives"].items() for item in values}
        for original_claim in claims:
            claim = dict(original_claim)
            forbidden_matches = set(claim["matches_forbidden"])
            require(forbidden_matches <= forbidden_by_id.keys(), "unknown forbidden inference ID")
            alternative_matches = set(claim["matches_alternatives"])
            require(alternative_matches <= alternatives_by_id.keys(), "unknown alternative ID")
            require({alternatives_by_id[x] for x in alternative_matches} <= set(claim["matches_gold"]), "alternative must map to its registered gold rule")
            if forbidden_matches:
                require(claim["verdict"] == "unsupported", "forbidden inference cannot be supported")
                claim["critical"] = True
                claim["violated_gold"] = sorted(set(claim["violated_gold"]) | {g for x in forbidden_matches for g in forbidden_by_id[x]["violated_gold"]})
                claim["critical_rationale"] = "Matched preregistered forbidden inference: " + ", ".join(sorted(forbidden_matches))
                claim["error_category"] = "source_rule_inversion" if claim["violated_gold"] else "unsupported_addition"
            require(claim["verdict"] in {"supported", "unsupported"}, "unassessed claim in complete scope")
            require(type(claim["critical"]) is bool, "critical must be boolean")
            require(claim["text_sha256"] == text_hashes[claim["id"]], "annotation text hash differs from emitted claim")
            require(not (claim["verdict"] == "supported" and claim["critical"]), "supported claim cannot be a critical error")
            violations = set(claim["violated_gold"])
            require(violations <= set(gold["critical_rule_ids"]), "critical inversion must reference a predeclared critical rule")
            require(not violations or claim["critical"], "violated critical rule requires critical error flag")
            if claim["critical"]:
                require(bool(claim.get("critical_rationale")), "critical error needs rationale")
            if claim["critical"]:
                require((bool(violations) and claim["error_category"] == "source_rule_inversion") or
                        (not violations and claim["error_category"] == "unsupported_addition"),
                        "critical error requires violated_gold or unsupported_addition category")
            else:
                require(claim["error_category"] == ("none" if claim["verdict"] == "supported" else "other_noncritical"), "inconsistent error category")
            critical_occurrences += int(claim["critical"])
            inverted_rules |= violations
            hits = set(claim["matches_gold"])
            require(hits <= required, "claim matches unknown gold item")
            if len(hits) > 1:
                require(any(hits == set(group) for group in gold["allowed_match_groups"]) and claim.get("mapping_rationale"),
                        "multi-gold match needs a preregistered group and mapping rationale")
            equivalence = claim["equivalence_id"]
            require(isinstance(equivalence, str) and equivalence, "human proposition equivalence ID required")
            signature = (claim["verdict"], tuple(sorted(hits)), claim["critical"], tuple(sorted(violations)))
            require(equivalence not in propositions or propositions[equivalence] == signature,
                    "inconsistent equivalent proposition annotations")
            bank_key = (key[0], equivalence)
            require(bank_key not in proposition_bank or proposition_bank[bank_key] == signature,
                    "inconsistent equivalent proposition across repetitions")
            proposition_bank[bank_key] = signature
            propositions[equivalence] = signature
            if claim["verdict"] == "supported":
                supported += 1
                matched |= hits
            else:
                require(not hits, "unsupported claims cannot earn recall credit")
        critical = sum(int(v[2]) for v in propositions.values())
        precision = sum(v[0] == "supported" for v in propositions.values()) / len(propositions) if propositions else None
        recall = len(matched) / len(required) if required else None
        policy = campaign["success_policy"]
        if gold["answerable"]:
            accepted = (attempt["state"] == "pass" and termination == "completed" and precision is not None
                        and recall is not None and precision >= policy["minimum_precision"]
                        and recall >= policy["minimum_recall"] and critical == 0)
        else:
            accepted = attempt["state"] == "abstain" and termination == "completed" and not emitted
        rows.append({"task_id": key[0], "repetition": key[1], "family": tasks[key[0]]["family"],
                     "domain": tasks[key[0]]["domain"], "state": attempt["state"],
                     "emitted": len(claims), "supported": supported, "gold": len(required),
                     "recovered": len(matched), "critical_errors": critical,
                     "critical_error_occurrences": critical_occurrences,
                     "critical_unsupported_additions": sum(v[2] and not v[3] for v in propositions.values()),
                     "critical_source_rule_inversions": len(inverted_rules),
                     "critical_source_rules": len(gold["critical_rule_ids"]),
                     "critical_inversions_per_100_rules": 100 * len(inverted_rules) / len(gold["critical_rule_ids"]) if gold["critical_rule_ids"] and propositions else None,
                     "accepted_task": accepted, "termination_reason": termination,
                     "unique_propositions": len(propositions),
                     "precision": precision, "recall": recall,
                     "elapsed_seconds": attempt["elapsed_seconds"], "cost": cost})
    require(elapsed_total <= duration * execution["max_concurrency"] + 1, "aggregate elapsed time exceeds declared concurrency window")
    missing = sorted(expected - observed)
    success = sum(r["state"] == "pass" for r in rows)
    accepted = sum(r["accepted_task"] for r in rows)
    critical = sum(r["critical_errors"] for r in rows)
    known_cost = sum(r["cost"]["usd"] or 0 for r in rows)
    reasons = ["external_preregistration_not_verified", "independent_human_gold_or_assessment_missing", "identity_and_independence_not_verified"]
    policy_is_trivial = not campaign["success_policy"]["minimum_precision"] or not campaign["success_policy"]["minimum_recall"]
    if policy_is_trivial:
        reasons.append("trivial_success_policy")
    if any(w["code"] == "request_identity_unavailable" for w in warnings):
        reasons.append("request_identity_incomplete")
    if campaign["split"] != "heldout_candidate": reasons.append("development_or_synthetic_data")
    if missing: reasons.append("missing_assigned_attempts")
    if any(r["state"] == "not_run" for r in rows): reasons.append("assigned_tasks_not_run")
    if campaign["repetitions"] < 3: reasons.append("fewer_than_three_repetitions")

    # No automatic qualification: identities, independence and real evidence need
    # maintainer review. A hash establishes byte integrity, not semantic truth.
    return {"tool_version": VERSION, "run_id": run["run_id"], "campaign_sha256": lock["sha256"],
            "subject_id": run["subject_id"], "split": campaign["split"], "track": campaign["track"],
            "evidence_status_declared": run["evidence_status"], "identity_and_independence_verified": False,
            "assigned_attempts": len(expected), "recorded_attempts": len(observed),
            "missing_attempts": missing, "reported_passed": success, "reported_completion_rate": success / len(expected),
            "accepted_tasks": accepted, "accepted_task_rate": accepted / len(expected),
            "critical_errors": critical, "known_reported_cost_usd": known_cost,
            "cost_known_attempts": sum(r["cost"]["status"] != "unknown" for r in rows),
            "unresolved_reserved_usd": sum(r["cost"].get("reserved_usd", 0) for r in rows if r["cost"]["status"] == "unknown"),
            "registration_provenance": "self_declared", "external_registration_verified": False,
            "human_effort_status": "not_measured", "qualification_decision": None,
            "cost_complete": all_cost_known and not missing,
            "cost_per_accepted_task_usd": known_cost / accepted if accepted and all_cost_known and not missing else None,
            "cost_per_reported_completion_usd": known_cost / success if success and all_cost_known and not missing else None,
            "record_comparable_candidate": False, "comparability_blocks": reasons,
            "comparability_status": "external_verification_not_implemented",
            "human_review_declared_complete": all_human, "policy_is_trivial": bool(policy_is_trivial),
            "warnings": warnings, "aggregates": aggregate_rows(rows, tasks, campaign["repetitions"]),
            "qualified": False, "qualification_reason": "Independent evidence review is not automated by this tool.",
            "rows": rows, "note": "Scoped annotation scores; not full-corpus precision/recall, human usability, or a model ranking."}


def aggregate_rows(rows, tasks, repetitions):
    """Descriptive totals only. Missing assessments never become zero inversions."""
    def summary(selected_tasks, selected_rows, repeat_count):
        assigned = len(selected_tasks) * repeat_count
        numerator = sum(r["critical_source_rule_inversions"] for r in selected_rows)
        denominator = sum(r["critical_source_rules"] for r in selected_rows if r["unique_propositions"] > 0)
        assessed = sum(r["unique_propositions"] > 0 for r in selected_rows)
        return {"assigned_attempts": assigned, "recorded_attempts": len(selected_rows),
                "assessed_nonempty_attempts": assessed,
                "accepted_tasks": sum(r["accepted_task"] for r in selected_rows),
                "critical_unique_errors_summed_over_attempts": sum(r["critical_errors"] for r in selected_rows),
                "critical_occurrences": sum(r["critical_error_occurrences"] for r in selected_rows),
                "observed_inverted_source_rules": numerator,
                "assessed_critical_rule_opportunities": denominator,
                "inversions_per_100_rules": 100 * numerator / denominator if denominator and assessed == assigned else None,
                "uncertainty": "not_estimated; descriptive audit totals only"}
    result = {"run": summary(tasks, rows, repetitions)}
    for dimension in ("family", "domain"):
        result[dimension] = {}
        for value in sorted({t[dimension] for t in tasks.values()}):
            selected = {k: t for k, t in tasks.items() if t[dimension] == value}
            result[dimension][value] = summary(selected, [r for r in rows if r[dimension] == value], repetitions)
    result["repetitions"] = {str(r): summary(tasks, [row for row in rows if row["repetition"] == r], 1)
                             for r in range(1, repetitions + 1)}
    return result


def write_new(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
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
    except (Invalid, KeyError, TypeError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Invalid evidence: {exc}\n")


if __name__ == "__main__":
    main()
