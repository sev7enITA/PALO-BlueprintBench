#!/usr/bin/env python3
"""Audit retained local counter-test outputs without rerunning inference.

Canonical parsed files retain the original JSON value. Bare-array projection is
explicit, post-hoc and diagnostic; it never changes strict transport acceptance.
"""
from __future__ import annotations

import json
from pathlib import Path

from run_qwen import CASES, ROOT, digest, parse_prompt, save_json, validate


def main() -> None:
    output = ROOT / "responses" / "qwen"
    summaries = []
    for case in CASES:
        attempts = sorted((output / case).glob("*/receipt.json"))
        if len(attempts) != 1:
            raise ValueError(f"{case}: expected one frozen reviewer attempt; found {len(attempts)}")
        receipt_path = attempts[0]
        attempt = receipt_path.parent
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        for filename, field in (
            ("raw-response.json", "raw_response_sha256"),
            ("raw-text.txt", "raw_text_sha256"),
            ("request-body.json", "request_sha256"),
            ("exact-frozen-prompt.txt", "prompt_sha256"),
        ):
            if digest((attempt / filename).read_bytes()) != receipt[field]:
                raise ValueError(f"{case}: hash mismatch for {filename}")
        raw = json.loads((attempt / "raw-response.json").read_bytes())
        text = (attempt / "raw-text.txt").read_bytes().decode("utf-8")
        if raw["choices"][0]["text"] != text:
            raise ValueError(f"{case}: raw completion does not bind to text")
        value = json.loads(text)
        prompt = (ROOT / f"{case}-prompt.txt").read_bytes()
        if digest(prompt) != receipt["prompt_sha256"]:
            raise ValueError(f"{case}: frozen prompt drift")
        rules, items = parse_prompt(prompt.decode("utf-8"))
        strict = validate(value, rules, items)
        projection_name = "array_to_items_object" if isinstance(value, list) else "none"
        projected = {"items": value} if isinstance(value, list) else value
        records = validate(projected, rules, items)
        save_json(output / f"{case}-parsed.json", value)
        save_json(attempt / "wrapper-projection.json", projected)
        save_json(attempt / "record-level-validation.json", {
            **records,
            "raw_envelope_valid": strict["valid"],
            "strict_contract_valid": strict["valid"],
            "projection": projection_name,
            "post_hoc_projection": projection_name != "none",
            "answer_fields_modified": False,
            "scope": "Record contract checks after disclosed structural projection; no semantic adjudication",
        })
        binding = {
            "case": case,
            "reviewer": receipt["reviewer"],
            "requested_model": receipt["requested_model"],
            "returned_model": receipt["returned_model"],
            "frozen_commit": receipt["frozen_commit"],
            "raw_envelope_valid": strict["valid"],
            "strict_contract_valid": strict["valid"],
            "projection": projection_name,
            "post_hoc_projection": projection_name != "none",
            "canonical_parsed_preserves_original_array": isinstance(value, list),
            "semantic_records_valid": records["valid_records"],
            "semantic_records_valid_definition": "Usable record fields only; not agreement with gold or independent validation",
            "assigned_records": len(items),
            "answer_fields_modified": False,
            "primary_scoring_unchanged": True,
            "qualified": False,
            "family_overlap": "Same Qwen family as Qwen Max Prime; different local model and weights. Not independent human review.",
            "receipt_path": receipt_path.relative_to(ROOT).as_posix(),
            "receipt_sha256": digest(receipt_path.read_bytes()),
            "raw_response_path": (attempt / "raw-response.json").relative_to(ROOT).as_posix(),
            "raw_response_sha256": receipt["raw_response_sha256"],
            "raw_text_path": (attempt / "raw-text.txt").relative_to(ROOT).as_posix(),
            "raw_text_sha256": receipt["raw_text_sha256"],
            "request_sha256": receipt["request_sha256"],
            "prompt_sha256": receipt["prompt_sha256"],
            "parsed_sha256": digest((output / f"{case}-parsed.json").read_bytes()),
            "finish_reason": receipt["finish_reason"],
            "elapsed_seconds": receipt["elapsed_seconds"],
            "usage": receipt["usage"],
            "warnings": records.get("warnings", []),
            "record_errors": records["errors"],
            "cloud_calls": 0,
            "cloud_cost_usd": 0,
            "local_energy_and_hardware_cost_usd": None,
        }
        save_json(output / f"{case}-receipt.json", binding)
        summaries.append(binding)
    save_json(output / "summary.json", {
        "reviewer": "qwen3.8-27b-uncensored-local",
        "qualification": "internal_countertest_only",
        "qualified": False,
        "primary_scoring_unchanged": True,
        "assigned_records": sum(row["assigned_records"] for row in summaries),
        "usable_semantic_records": sum(row["semantic_records_valid"] for row in summaries),
        "strict_valid_batches": sum(row["strict_contract_valid"] for row in summaries),
        "assigned_batches": len(summaries),
        "elapsed_seconds": round(sum(row["elapsed_seconds"] for row in summaries), 3),
        "cloud_calls": 0,
        "cloud_cost_usd": 0,
        "local_energy_and_hardware_cost_usd": None,
        "attempts": summaries,
        "policy": "Original arrays retained. Post-hoc structural projection only; no answer repair, semantic adjudication or primary-score change.",
    })
    files = {}
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "integrity-manifest.json":
            files[path.relative_to(ROOT).as_posix()] = digest(path.read_bytes())
    save_json(output / "integrity-manifest.json", {
        "algorithm": "sha256",
        "scope": "Retained Qwen response artifacts; integrity checks, not external time or identity attestations",
        "files": files,
    })
    print(json.dumps({"assigned": 36, "usable_records": sum(row["semantic_records_valid"] for row in summaries), "strict_valid_batches": sum(row["strict_contract_valid"] for row in summaries), "cloud_calls": 0}))


if __name__ == "__main__":
    main()
