"""Structural regressions for the development bank; these do not validate labels."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "study/next-cycle"
spec = importlib.util.spec_from_file_location("next_cycle_validator", PACKET / "validate.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def load(name):
    return json.loads((PACKET / name).read_text(encoding="utf-8"))


class NextCycleTests(unittest.TestCase):
    def setUp(self):
        self.bank = load("case-bank.json")
        self.coverage = load("coverage-matrix.json")
        self.checks = load("metamorphic-checks.json")

    def validate(self):
        return validator.validate_bank(self.bank, self.coverage, self.checks)

    def test_packet_has_declared_coverage_without_qualification(self):
        counts = self.validate()
        self.assertEqual(counts, {"cases": 6, "probes": 48, "minimal_pairs": 6, "metamorphic_checks": 7, "dimensions": 13})

    def test_source_edit_without_hash_rejected(self):
        self.bank["cases"][0]["documents"][0]["units"][0]["text"] += " altered"
        with self.assertRaisesRegex(ValueError, "source text and units differ"):
            self.validate()

    def test_cross_case_citation_rejected(self):
        self.bank["cases"][0]["probes"][0]["source_units"] = ["F01"]
        with self.assertRaisesRegex(ValueError, "cross-case"):
            self.validate()

    def test_duplicate_case_rejected(self):
        self.bank["cases"].append(copy.deepcopy(self.bank["cases"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate case"):
            self.validate()

    def test_invented_independent_family_rejected(self):
        self.bank["independent_source_families"] = 6
        with self.assertRaisesRegex(ValueError, "independent families"):
            self.validate()

    def test_fabricated_human_label_rejected(self):
        self.bank["cases"][0]["probes"][0]["label_status"] = "independent_adjudicated"
        with self.assertRaisesRegex(ValueError, "human gold"):
            self.validate()

    def test_coverage_is_not_sample_sufficiency(self):
        self.coverage["coverage_is_statistical_sufficiency"] = True
        with self.assertRaisesRegex(ValueError, "statistical sufficiency"):
            self.validate()

    def test_counterfactual_cannot_change_invariant_probe(self):
        self.checks["checks"][-1]["invariant_probe_ids"].append("emergency-spares-P01")
        with self.assertRaisesRegex(ValueError, "overlap"):
            self.validate()

    def test_counterfactual_requires_real_source_match(self):
        self.checks["checks"][-1]["replacements"][0]["old"] = "missing substring"
        with self.assertRaisesRegex(ValueError, "source text missing"):
            self.validate()

    def test_workflow_tasks_reference_sources_without_claiming_execution(self):
        validator.validate_workflow(self.bank, load("workflow-tasks.json"))

    def test_workflow_cannot_use_answer_key_as_model_input(self):
        workflow = load("workflow-tasks.json")
        workflow["tasks"][0]["do_not_send_draft_expected_decisions_to_model"] = False
        with self.assertRaisesRegex(ValueError, "answer-key boundary"):
            validator.validate_workflow(self.bank, workflow)

    def test_exact_legacy_text_and_frozen_labels_preserved(self):
        validator.validate_legacy()

    def test_first_pass_excludes_expected_labels_and_competing_prompts(self):
        packet = load("adjudication/reviewer-packet.json")
        for item in packet["items"]:
            self.assertFalse({"expected", "original_expected_label", "model", "model_output", "competing_interpretations"} & set(item))
        self.assertTrue(all(x["final_disposition"] is None for x in load("adjudication/adjudication.template.json")["decisions"]))

    def test_threshold_variant_declares_changed_and_unchanged_probes(self):
        check = self.checks["checks"][-1]
        case = self.bank["cases"][0]
        texts = {u["id"]: u["text"] for d in case["documents"] for u in d["units"]}
        for change in check["replacements"]:
            texts[change["unit_id"]] = texts[change["unit_id"]].replace(change["old"], change["new"])
        self.assertIn("EUR 15,000", texts["E01"])
        self.assertNotIn("EUR 12,000", texts["E01"])
        self.assertEqual(len(check["probe_scope"]), 2)
        self.assertEqual(len(check["invariant_probe_ids"]), 4)


if __name__ == "__main__":
    unittest.main()
