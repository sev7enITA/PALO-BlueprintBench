import copy
import json
import tempfile
import unittest
from pathlib import Path
import blueprintbench as bb
from demo import make, put


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
        self.assertIsNone(r["cost_per_success_usd"])

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
        with self.assertRaisesRegex(bb.Invalid, "N/A"):
            self.evaluate()

    def test_path_escape(self):
        with self.assertRaisesRegex(bb.Invalid, "escapes"):
            bb.artifact({"path": "../secret", "sha256": "0" * 64}, self.root)

    def test_symlink_escape(self):
        (self.root / "outside").symlink_to(self.root.parent)
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
        ref = put(self.root, "inverted_rule/claims.json", claims)
        receipt["claims_artifact"] = ref
        receipt["artifacts"] = [ref]
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


if __name__ == "__main__":
    unittest.main()
