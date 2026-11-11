import copy
import json
import tempfile
import unittest
from pathlib import Path
import blueprintbench as bb
from demo import make, put, bind_output


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.lock, self.run = make(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def evaluate(self):
        return bb.evaluate(self.lock, self.run, self.root)

    def test_correct_inverted_and_empty_outcomes(self):
        r = self.evaluate()
        self.assertEqual(r["reported_completion_rate"], 1 / 3)
        self.assertEqual(r["rows"][0]["recall"], 1)
        self.assertEqual(r["rows"][1]["precision"], .5)
        self.assertEqual(r["rows"][1]["critical_errors"], 1)
        self.assertIsNone(r["rows"][2]["precision"])
        self.assertEqual(r["rows"][2]["recall"], 0)
        self.assertFalse(r["qualified"])
        self.assertFalse(r["record_comparable_candidate"])

    def test_missing_task_remains_in_denominator(self):
        self.run["attempts"].pop()
        r = self.evaluate()
        self.assertEqual(r["assigned_attempts"], 3)
        self.assertEqual(r["reported_completion_rate"], 1 / 3)
        self.assertEqual(len(r["missing_attempts"]), 1)
        self.assertIsNone(r["cost_per_accepted_task_usd"])

    def test_duplicates_rejected(self):
        self.run["attempts"].append(copy.deepcopy(self.run["attempts"][0]))
        with self.assertRaisesRegex(bb.Invalid, "duplicate task"):
            self.evaluate()

    def test_unknown_cost_not_zero(self):
        self.run["attempts"][1]["cost"] = {"status": "unknown", "usd": 0}
        with self.assertRaisesRegex(bb.Invalid, "unknown cost"):
            self.evaluate()
        self.run["attempts"][1]["cost"]["usd"] = None
        self.assertFalse(self.evaluate()["cost_complete"])

    def test_tampered_lock(self):
        self.lock["payload"]["campaign"]["split"] = "heldout_candidate"
        with self.assertRaisesRegex(bb.Invalid, "modified"):
            self.evaluate()

    def test_changed_evidence(self):
        (self.root / "faithful/claims.json").write_text("[]")
        with self.assertRaisesRegex(bb.Invalid, "hash mismatch"):
            self.evaluate()

    def test_no_na_for_assigned_task(self):
        self.run["attempts"][0]["state"] = "not_applicable"
        with self.assertRaisesRegex(bb.Invalid, "schema"):
            self.evaluate()

    def test_path_escape(self):
        with self.assertRaisesRegex(bb.Invalid, "escapes"):
            bb.artifact({"path": "../secret", "sha256": "0" * 64}, self.root)

    def test_symlink_escape(self):
        (self.root / "outside").symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaisesRegex(bb.Invalid, "escapes"):
            bb.artifact({"path": "outside/secret", "sha256": "0" * 64}, self.root)

    def test_nonfinite_and_boolean_cost(self):
        for bad in [float("nan"), float("inf"), -1, True]:
            self.run["attempts"][0]["cost"] = {"status": "reported", "usd": bad}
            with self.assertRaises(bb.Invalid): self.evaluate()

    def test_no_retroactive_registration(self):
        self.run["started_at"] = "2000-01-01T00:00:00Z"
        with self.assertRaisesRegex(bb.Invalid, "predates"):
            self.evaluate()

    def test_configuration_switch(self):
        self.run["configuration_sha256"] = "0" * 64
        with self.assertRaisesRegex(bb.Invalid, "configuration changed"):
            self.evaluate()

    def test_omitted_rejected_claim_cannot_disappear(self):
        attempt = self.run["attempts"][1]
        annotation = bb.read_json(self.root / attempt["annotation"]["path"])
        annotation["claims"].pop()
        attempt["annotation"] = put(self.root, "inverted_rule/annotation.json", annotation)
        with self.assertRaisesRegex(bb.Invalid, "claim IDs"):
            self.evaluate()

    def test_unsupported_cannot_earn_recall(self):
        attempt = self.run["attempts"][1]
        annotation = bb.read_json(self.root / attempt["annotation"]["path"])
        annotation["claims"][1]["matches_gold"] = ["g2"]
        attempt["annotation"] = put(self.root, "inverted_rule/annotation.json", annotation)
        with self.assertRaisesRegex(bb.Invalid, "unsupported claims"):
            self.evaluate()

    def test_duplicate_json_keys_rejected(self):
        p = self.root / "bad.json"
        p.write_text('{"usd": 1, "usd": 0}')
        with self.assertRaisesRegex(bb.Invalid, "duplicate JSON key"):
            bb.read_json(p)

    def test_repeating_correct_claim_does_not_inflate_precision(self):
        attempt = self.run["attempts"][1]
        receipt = bb.read_json(self.root / attempt["receipt"]["path"])
        claims = bb.read_json(self.root / receipt["claims_artifact"]["path"])
        claims.append({**claims[0], "id": "duplicate"})
        ref, raw, non_claim = bind_output(self.root, "inverted_rule", claims)
        receipt["claims_artifact"] = ref
        receipt["raw_output"] = raw
        receipt["non_claim_spans"] = non_claim
        receipt["artifacts"] = [ref, raw]
        attempt["receipt"] = put(self.root, "inverted_rule/receipt.json", receipt)
        annotation = bb.read_json(self.root / attempt["annotation"]["path"])
        annotation["receipt_sha256"] = attempt["receipt"]["sha256"]
        annotation["claims"].append({**annotation["claims"][0], "id": "duplicate"})
        attempt["annotation"] = put(self.root, "inverted_rule/annotation.json", annotation)
        row = self.evaluate()["rows"][1]
        self.assertEqual(row["emitted"], 3)
        self.assertEqual(row["unique_propositions"], 2)
        self.assertEqual(row["precision"], .5)
        self.assertEqual(row["recall"], .5)

    def test_output_cannot_overwrite_evidence(self):
        with self.assertRaises(FileExistsError):
            bb.write_new(self.root / "run.json", {})

    def rewrite_attempt(self, index, change):
        import hashlib
        a = self.run["attempts"][index]
        receipt = bb.read_json(self.root / a["receipt"]["path"])
        annotation = bb.read_json(self.root / a["annotation"]["path"]) if a["annotation"] else None
        emitted = bb.read_json(self.root / receipt["claims_artifact"]["path"])
        change(a, receipt, annotation, emitted)
        ref, raw, non_claim = bind_output(self.root, f"edited-{index}", emitted)
        receipt.update(claims_artifact=ref, raw_output=raw, non_claim_spans=non_claim, artifacts=[ref, raw])
        a["receipt"] = put(self.root, f"edited-{index}/receipt.json", receipt)
        if annotation is not None:
            hashes = {c["id"]: hashlib.sha256(c["text"].encode("utf-8")).hexdigest() for c in emitted}
            for c in annotation["claims"]: c["text_sha256"] = hashes[c["id"]]
            annotation["receipt_sha256"] = a["receipt"]["sha256"]
            a["annotation"] = put(self.root, f"edited-{index}/annotation.json", annotation)
        return a

    def alter_gold(self, index, change):
        task = self.lock["payload"]["campaign"]["tasks"][index]
        gold = bb.read_json(self.root / task["gold"]["path"])
        change(gold)
        task["gold"] = put(self.root, f"gold-edit-{index}.json", gold)
        self.lock = bb.freeze(self.lock["payload"]["campaign"], self.root)
        self.run["campaign_sha256"] = self.lock["sha256"]
        self.run["started_at"] = self.run["finished_at"] = self.lock["payload"]["registered_at"]

    def test_critical_duplicates_are_unique_but_occurrences_retained(self):
        def change(a, receipt, annotation, emitted):
            for i in range(3):
                ident = f"repeated-{i}"
                emitted.append({**emitted[1], "id": ident})
                annotation["claims"].append({**annotation["claims"][1], "id": ident})
        self.rewrite_attempt(1, change)
        row = self.evaluate()["rows"][1]
        self.assertEqual((row["precision"], row["critical_errors"], row["critical_error_occurrences"]), (.5, 1, 4))
        self.assertEqual(row["critical_source_rule_inversions"], 1)
        self.assertEqual(row["critical_inversions_per_100_rules"], 50)

    def test_supported_critical_rejected(self):
        self.rewrite_attempt(0, lambda a,r,n,e: n["claims"][0].update(critical=True))
        with self.assertRaisesRegex(bb.Invalid, "supported claim"): self.evaluate()

    def test_equivalent_critical_labels_must_agree(self):
        def change(a,r,n,e):
            e.append({**e[1], "id":"duplicate"})
            n["claims"].append({**n["claims"][1], "id":"duplicate", "critical":False, "violated_gold":[], "matches_forbidden":[], "error_category":"other_noncritical"})
        self.rewrite_attempt(1, change)
        with self.assertRaisesRegex(bb.Invalid, "inconsistent equivalent"): self.evaluate()

    def test_reported_pass_with_zero_quality_is_not_accepted(self):
        def change(a,r,n,e):
            a["state"] = r["state"] = "pass"
            for c in n["claims"]: c.update(verdict="unsupported", matches_gold=[], error_category="source_rule_inversion" if c["critical"] else "other_noncritical")
        self.rewrite_attempt(1, change)
        result = self.evaluate()
        self.assertEqual(result["reported_completion_rate"], 2/3)
        self.assertEqual(result["accepted_task_rate"], 1/3)
        self.assertFalse(result["rows"][1]["accepted_task"])

    def test_cost_per_accepted_uses_all_attempt_costs(self):
        for a in self.run["attempts"]: a["cost"] = {"status":"reported", "usd":1}
        result = self.evaluate()
        self.assertEqual(result["cost_per_accepted_task_usd"], 3)
        self.assertEqual(result["cost_known_attempts"], 3)

    def test_unknown_reservations_are_not_settled_charges(self):
        self.run["attempts"][1]["cost"] = {"status":"unknown", "usd":None, "reserved_usd":2}
        r = self.evaluate()
        self.assertEqual(r["unresolved_reserved_usd"], 2)
        self.assertEqual(r["known_reported_cost_usd"], 0)
        self.assertEqual(r["cost_known_attempts"], 2)
        self.assertIsNone(r["cost_per_accepted_task_usd"])

    def test_rehashed_lock_never_becomes_external_registration(self):
        self.lock["payload"]["registered_at"] = "2020-01-01T00:00:00Z"
        self.lock["sha256"] = bb.digest(self.lock["payload"])
        self.run["campaign_sha256"] = self.lock["sha256"]
        r = self.evaluate()
        self.assertFalse(r["external_registration_verified"])
        self.assertFalse(r["record_comparable_candidate"])
        self.assertIn("external_preregistration_not_verified", r["comparability_blocks"])
        self.assertFalse(r["qualified"])

    def test_all_gold_in_one_claim_needs_preregistered_group(self):
        self.rewrite_attempt(0, lambda a,r,n,e: n["claims"][0].update(matches_gold=["g1","g2"],mapping_rationale="Asserted alternative"))
        with self.assertRaisesRegex(bb.Invalid, "preregistered group"): self.evaluate()

    def test_registered_alternative_mapping_is_supported(self):
        self.alter_gold(0, lambda g: g.update(allowed_match_groups=[["g1","g2"]]))
        self.rewrite_attempt(0, lambda a,r,n,e: n["claims"][0].update(matches_gold=["g1","g2"],mapping_rationale="Declared reference granularity"))
        self.assertEqual(self.evaluate()["rows"][0]["recall"], 1)

    def test_atomicity_review_is_required(self):
        self.rewrite_attempt(0, lambda a,r,n,e: n.update(atomicity_reviewed=False))
        with self.assertRaisesRegex(bb.Invalid, "atomicity review"): self.evaluate()

    def test_annotation_text_hash_is_bound(self):
        a=self.run["attempts"][0]; n=bb.read_json(self.root/a["annotation"]["path"])
        n["claims"][0]["text_sha256"]="0"*64
        a["annotation"]=put(self.root,"bad-annotation.json",n)
        with self.assertRaisesRegex(bb.Invalid,"text hash"): self.evaluate()

    def change_receipt(self, index, change):
        a=self.run["attempts"][index]; r=bb.read_json(self.root/a["receipt"]["path"])
        change(r);a["receipt"]=put(self.root,"changed-receipt.json",r)
        if a["annotation"]:
            n=bb.read_json(self.root/a["annotation"]["path"]);n["receipt_sha256"]=a["receipt"]["sha256"]
            a["annotation"]=put(self.root,"changed-annotation.json",n)

    def test_raw_output_gap_rejected(self):
        self.change_receipt(0, lambda r:r.update(non_claim_spans=[]))
        with self.assertRaisesRegex(bb.Invalid,"coverage gap"):self.evaluate()

    def test_overlapping_output_spans_rejected(self):
        self.change_receipt(0, lambda r:r["non_claim_spans"].append({"span":[0,1],"reason":"Overlap"}))
        with self.assertRaisesRegex(bb.Invalid,"overlapping"):self.evaluate()

    def test_not_run_without_semantic_annotation(self):
        self.run["attempts"][2].update(state="not_run",annotation=None)
        self.change_receipt(2, lambda r:r.update(state="not_run",termination_reason="precall_blocked"))
        r=self.evaluate();self.assertEqual(r["assigned_attempts"],3)
        self.assertEqual(r["rows"][2]["recall"],0)
        self.assertIn("assigned_tasks_not_run",r["comparability_blocks"])
        self.assertEqual(r["rows"][2]["termination_reason"],"precall_blocked")

    def test_not_run_cannot_hide_output(self):
        self.run["attempts"][0]["state"]="not_run"
        self.change_receipt(0,lambda r:r.update(state="not_run",termination_reason="precall_blocked"))
        with self.assertRaisesRegex(bb.Invalid,"not_run cannot"): self.evaluate()

    def test_budget_censoring_is_separate_from_semantic_failure(self):
        self.change_receipt(1,lambda r:r.update(termination_reason="budget_censored"))
        r=self.evaluate();self.assertEqual(r["rows"][1]["termination_reason"],"budget_censored")
        self.assertFalse(r["rows"][1]["accepted_task"])

    def test_success_policy_frozen_and_required(self):
        campaign=copy.deepcopy(self.lock["payload"]["campaign"]);campaign.pop("success_policy")
        with self.assertRaisesRegex(bb.Invalid,"success_policy"):bb.freeze(campaign,self.root)
        campaign=copy.deepcopy(self.lock["payload"]["campaign"]);campaign["success_policy"]["maximum_critical_errors"]=1
        with self.assertRaises(bb.Invalid):bb.freeze(campaign,self.root)

    def test_answerability_contract(self):
        with self.assertRaisesRegex(bb.Invalid,"answerability"):self.alter_gold(0,lambda g:g.update(answerable=False))

    def test_schema_rejects_qualification_override(self):
        self.run["qualified"]=True
        with self.assertRaisesRegex(bb.Invalid,"schema"): self.evaluate()

    def test_utf8_io_and_span_coordinates(self):
        self.rewrite_attempt(0,lambda a,r,n,e:e[0].update(text="L’obbligo vale per €500. 承認"))
        self.assertTrue(self.evaluate()["rows"][0]["accepted_task"])


    def test_nonfinite_policy_rejected(self):
        campaign=copy.deepcopy(self.lock["payload"]["campaign"])
        campaign["success_policy"]["minimum_precision"]=float("nan")
        with self.assertRaises(bb.Invalid): bb.freeze(campaign,self.root)

    def test_reserved_cost_requires_unknown(self):
        self.run["attempts"][0]["cost"]["reserved_usd"]=1
        with self.assertRaisesRegex(bb.Invalid,"reservation"):self.evaluate()

    def test_answerable_false_accepts_completed_empty_abstention(self):
        self.alter_gold(2, lambda g:g.update(required_propositions=[],meaning={},critical_rule_ids=[],forbidden_inferences=[],answerable=False))
        r=self.evaluate();self.assertTrue(r["rows"][2]["accepted_task"])
        self.assertIsNone(r["rows"][2]["recall"])
        self.assertFalse(r["qualified"])

    def test_adjudicator_must_be_distinct_from_annotators(self):
        with self.assertRaisesRegex(bb.Invalid,"independent gold"):
            self.alter_gold(0,lambda g:g.update(annotation_status="independent_adjudicated",annotator_ids=["a","b"],adjudicator_id="a"))

    def test_independent_review_declaration_needs_distinct_panel(self):
        self.rewrite_attempt(0,lambda a,r,n,e:n.update(review_type="independent_human",reviewer_ids=["a","b"],adjudicator_id="a"))
        with self.assertRaisesRegex(bb.Invalid,"two reviewers"):self.evaluate()

if __name__ == "__main__":
    unittest.main()
