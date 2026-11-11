"""Validate development-packet structure and provenance, never semantic gold truth."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = Path(__file__).resolve().parent
DISPOSITIONS = {"supported", "contradicted", "not_established", "unresolved_conflict"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_bank(bank, coverage, checks):
    require(bank["qualification"] is False, "development bank cannot claim qualification")
    require(bank["independent_source_families"] == 0, "authored scenarios are not independent families")
    require(bank["authoring_provenance_groups"] == 1, "one authoring provenance group must be disclosed")
    require(bank["status"] == "development_material_not_gold", "draft status required")
    require(bank["author"]["human_domain_review"] == "not_performed", "no invented domain review")
    cases = bank["cases"]
    case_ids = [c["id"] for c in cases]
    require(len(case_ids) == len(set(case_ids)), "duplicate case ID")
    probes = {}
    source_hashes = set()
    pairs = {}
    actual_coverage = {}
    for case in cases:
        require(case["split"] == "development_exposed", "new material is development exposed")
        require(case["scenario_group"] == case["id"], "scenario boundary mismatch")
        units = {}
        document_ids = []
        for document in case["documents"]:
            document_ids.append(document["id"])
            expected_text = "".join(u["id"] + ": " + u["text"] + "\n" for u in document["units"])
            require(document["text"] == expected_text, "source text and units differ")
            require(document["sha256"] == digest(expected_text.encode("utf-8")), "source hash mismatch")
            require(document["sha256"] not in source_hashes, "duplicate source document")
            source_hashes.add(document["sha256"])
            for unit in document["units"]:
                require(unit["id"] not in units, "duplicate source unit")
                units[unit["id"]] = document["id"]
        require(len(document_ids) == len(set(document_ids)), "duplicate document ID")
        cross_document = False
        for probe in case["probes"]:
            pid = probe["id"]
            require(pid not in probes, "duplicate probe ID")
            require(probe["draft_disposition"] in DISPOSITIONS, "invalid draft disposition")
            require(probe["label_status"] == "assistant_draft", "no human gold may be fabricated")
            require(probe["human_adjudication"] == "pending", "human adjudication remains pending")
            require(probe["source_units"] and set(probe["source_units"]) <= set(units), "cross-case or missing source citation")
            if len({units[x] for x in probe["source_units"]}) > 1:
                cross_document = True
            probes[pid] = (case["id"], probe)
            actual_coverage.setdefault(probe["dimension"], []).append(pid)
            if probe["minimal_pair_group"]:
                pairs.setdefault(probe["minimal_pair_group"], []).append((case["id"], probe))
        require(cross_document, "each scenario needs cross-document reasoning")
    require(len(cases) == coverage["scenario_count"], "scenario count mismatch")
    require(len(probes) == coverage["probe_count"], "probe count mismatch")
    require(set(coverage["required_dimensions"]) <= set(actual_coverage), "missing design dimension")
    require(actual_coverage == coverage["dimensions"], "coverage matrix drift")
    require(coverage["coverage_is_statistical_sufficiency"] is False, "coverage is not statistical sufficiency")
    require(len(pairs) >= coverage["minimum_pair_groups"], "minimal pairs missing")
    for pair in pairs.values():
        require(len(pair) == 2 and len({c for c, _ in pair}) == 1, "minimal pair must have two probes in one case")
        require({p["draft_disposition"] for _, p in pair} == {"supported", "contradicted"}, "minimal pair draft dispositions must contrast")
        require(len({p["statement"] for _, p in pair}) == 2, "minimal pair statements must differ")
    require(checks["execution_count"] == 0, "no metamorphic execution may be invented")
    check_ids = set()
    for check in checks["checks"]:
        require(check["id"] not in check_ids, "duplicate check ID")
        check_ids.add(check["id"])
        require(check["case_id"] in case_ids, "check case missing")
        require(check["status"] == "assistant_draft_unexecuted", "check status must remain unexecuted")
        used = check["invariant_probe_ids"] + check.get("probe_scope", [])
        require(all(p in probes and probes[p][0] == check["case_id"] for p in used), "metamorphic check crosses case boundaries")
        require(not set(check["invariant_probe_ids"]) & set(check.get("probe_scope", [])), "changed and invariant probes overlap")
        if check["operation"] == "reverse_document_order":
            require(set(used) == {p for p, (cid, _) in probes.items() if cid == check["case_id"]}, "order check must cover the entire case")
        elif check["operation"] == "replace_source_text":
            require(set(check["expected_dispositions"]) == set(check["probe_scope"]), "counterfactual scope mismatch")
            case = next(c for c in cases if c["id"] == check["case_id"])
            unit_text = {u["id"]: u["text"] for d in case["documents"] for u in d["units"]}
            for replacement in check["replacements"]:
                require(replacement["unit_id"] in unit_text and replacement["old"] in unit_text[replacement["unit_id"]], "counterfactual source text missing")
                require(replacement["old"] != replacement["new"], "counterfactual must change source")
            for pid, disposition in check["expected_dispositions"].items():
                require(disposition in DISPOSITIONS and disposition != probes[pid][1]["draft_disposition"], "counterfactual must change target draft disposition")
        else:
            raise ValueError("unsupported metamorphic operation")
    return {"cases": len(cases), "probes": len(probes), "minimal_pairs": len(pairs), "metamorphic_checks": len(check_ids), "dimensions": len(actual_coverage)}


def validate_legacy(root=ROOT, packet=PACKET):
    provenance = read(packet / "adjudication/custodian-provenance.json")
    relative = Path(provenance["source_path"])
    require(not relative.is_absolute() and ".." not in relative.parts, "legacy path outside repository")
    raw = (root / relative).read_bytes()
    require(digest(raw) == provenance["source_sha256"], "legacy source changed")
    legacy = {c["id"]: c for c in json.loads(raw)}
    reviewer = read(packet / "adjudication/reviewer-packet.json")
    items = {x["review_item"]: x for x in reviewer["items"]}
    require(len(items) == 3, "three legacy challenges required")
    for mapping in provenance["items"]:
        case = legacy[mapping["original_case_id"]]
        original = next(p for p in case["probes"] if p["id"] == mapping["original_probe_id"])
        require(original["expected"] == mapping["original_expected_label"], "frozen original label changed")
        item = items[mapping["review_item"]]
        require(item["statement"] == original["text"] and item["source_units"] == case["source"], "legacy reviewer packet must quote exact source and statement")
        require(not {"expected", "original_expected_label", "model", "model_output", "competing_interpretations"} & set(item), "first-pass packet leaks labels or model outputs")
    adjudication = read(packet / "adjudication/adjudication.template.json")
    require(adjudication["qualification"] is False and adjudication["independence_verified_externally"] is False, "blank template cannot establish independent qualification")
    for decision in adjudication["decisions"]:
        require(decision["status"] == "pending" and decision["final_disposition"] is None and decision["adjudicator_registry_id"] is None, "no adjudication may be fabricated")


def validate_workflow(bank, workflow):
    cases = {case["id"]: case for case in bank["cases"]}
    require(workflow["status"] == "human_review_required_before_execution", "workflow tasks are unexecuted drafts")
    require({task["case_id"] for task in workflow["tasks"]} == set(cases), "workflow task coverage mismatch")
    require(len(workflow["tasks"]) == len(cases), "one workflow task per case required")
    for task in workflow["tasks"]:
        require(task["input"] and task["do_not_send_draft_expected_decisions_to_model"] is True, "workflow task must preserve its answer-key boundary")
        units = {unit["id"] for doc in cases[task["case_id"]]["documents"] for unit in doc["units"]}
        decisions = task["draft_expected_decisions"]
        require(len({d["decision"] for d in decisions}) == len(decisions), "duplicate workflow decision")
        for decision in decisions:
            require(decision["review_status"] == "assistant_draft_pending_human", "workflow labels are not human gold")
            require(decision["disposition"] in {"required", "not_required", "permitted", "prohibited", "not_established", "unresolved_conflict"}, "invalid workflow disposition")
            require(decision["source_units"] and set(decision["source_units"]) <= units, "workflow citation outside case")


def main():
    counts = validate_bank(read(PACKET / "case-bank.json"), read(PACKET / "coverage-matrix.json"), read(PACKET / "metamorphic-checks.json"))
    validate_legacy()
    validate_workflow(read(PACKET / "case-bank.json"), read(PACKET / "workflow-tasks.json"))
    gates = read(PACKET / "sufficiency-gates.json")
    require(gates["new_model_calls"] == 0 and gates["new_model_spend_usd"] == 0, "preparation made no inference calls")
    print(json.dumps({"status": "structural_and_provenance_checks_passed", **counts, "semantic_labels_validated": False, "independent_qualification": False}))


if __name__ == "__main__":
    main()
