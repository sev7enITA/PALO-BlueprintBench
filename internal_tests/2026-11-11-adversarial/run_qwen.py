#!/usr/bin/env python3
"""Run the frozen, identity-masked counter-test through a local LM Studio server.

No selection keys, baseline labels or author identities are read or supplied.
Every invocation creates a new immutable attempt directory. No automatic retries
or substantive answer repair. This is an internal model counter-test only.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.request
import urllib.parse

ROOT = Path(__file__).resolve().parent
CASES = ("purchase-approval", "supplier-onboarding", "invoice-matching")
FREEZE_COMMIT = "80df7dbb33c446239370c000c0649b2aaedee30c"
TEMPLATE_PREFIX = "<|im_start|>user\n"
TEMPLATE_SUFFIX = "\n<|im_end|>\n<|im_start|>assistant\n<think>\n</think>\n"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_prompt(prompt: str) -> tuple[list[dict], list[dict]]:
    _, rest = prompt.split("\nSOURCE RULES:\n", 1)
    rules, items = rest.split("\nITEMS:\n", 1)
    return json.loads(rules), json.loads(items)


def validate(value: object, rules: list[dict], items: list[dict]) -> dict:
    expected = {item["id"]: item for item in items}
    source_ids = {rule["id"] for rule in rules}
    errors: list[str] = []
    valid_ids: list[str] = []
    warnings: list[str] = []
    allowed = {
        "verification": {"supported", "contradicted", "not_established", "uncertain"},
        "translation": {"faithful", "altered", "uncertain"},
    }
    if not isinstance(value, dict) or set(value) != {"items"} or not isinstance(value.get("items"), list):
        return {"valid": False, "errors": ["Expected sole top-level items array"], "assigned": len(items), "valid_records": 0, "missing_ids": list(expected)}
    rows = value["items"]
    ids = [row.get("id") for row in rows if isinstance(row, dict) and isinstance(row.get("id"), str)]
    counts = Counter(ids)
    duplicates = sorted(key for key, count in counts.items() if count != 1)
    if len(rows) != len(items):
        errors.append(f"Expected {len(items)} records, received {len(rows)}")
    if duplicates:
        errors.append("Duplicate IDs: " + ", ".join(duplicates))
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"Record {index} is not an object")
            continue
        key = row.get("id")
        row_errors = []
        if set(row) != {"id", "relation", "source_ids", "reason"}:
            row_errors.append("unexpected or missing fields")
        if not isinstance(key, str) or key not in expected:
            row_errors.append("unknown ID")
        elif counts[key] != 1:
            row_errors.append("duplicate ID")
        else:
            if row.get("relation") not in allowed[expected[key]["task"]]:
                row_errors.append("relation enum invalid for task")
        references = row.get("source_ids")
        if not isinstance(references, list) or any(not isinstance(v, str) or v not in source_ids for v in references):
            row_errors.append("invalid source_ids")
        elif len(set(references)) != len(references):
            row_errors.append("duplicate source_ids")
        if references == []:
            warnings.append(f"{key or index}: citation_missing")
        reason = row.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            row_errors.append("reason missing")
        elif len(reason.split()) > 18:
            row_errors.append("reason exceeds 18 whitespace-delimited words")
        if row_errors:
            errors.extend(f"{key or index}: {e}" for e in row_errors)
        else:
            valid_ids.append(key)
    missing = sorted(set(expected) - set(ids))
    if missing:
        errors.append("Missing IDs: " + ", ".join(missing))
    return {"valid": not errors, "assigned": len(items), "received_records": len(rows), "valid_records": len(valid_ids), "valid_ids": valid_ids, "missing_ids": missing, "duplicate_ids": duplicates, "errors": errors, "warnings": warnings, "scope": "Contract validation only; no semantic score or gold adjudication"}


def run(args: argparse.Namespace, case: str) -> dict:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    prompt_path = ROOT / f"{case}-prompt.txt"
    prompt_bytes = prompt_path.read_bytes()
    assert digest(prompt_bytes) == manifest["files"][prompt_path.name], "Frozen prompt drift"
    protocol_bytes = (ROOT / "protocol.json").read_bytes()
    assert digest(protocol_bytes) == manifest["files"]["protocol.json"], "Frozen protocol drift"
    prompt = prompt_bytes.decode("utf-8")
    rules, items = parse_prompt(prompt)
    assert len(items) == 12 and len({item["id"] for item in items}) == 12
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    destination = ROOT / "responses" / "qwen" / case / stamp
    destination.mkdir(parents=True, exist_ok=False)
    endpoint = args.endpoint.rstrip("/")
    model_snapshot = None
    snapshot_error = None
    try:
        with urllib.request.urlopen(endpoint + "/api/v0/models", timeout=15) as response:
            models = json.load(response)
        model_snapshot = next((model for model in models["data"] if model["id"] == args.model), None)
    except Exception as error:
        snapshot_error = {"type": type(error).__name__, "message": str(error)}
    save_json(destination / "model-runtime.json", {"target_model": model_snapshot, "error": snapshot_error})
    request_body = {
        "model": args.model,
        "prompt": TEMPLATE_PREFIX + prompt + TEMPLATE_SUFFIX,
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
        "stream": False,
    }
    request_bytes = json.dumps(request_body, ensure_ascii=False).encode("utf-8")
    (destination / "request-body.json").write_bytes(request_bytes)
    (destination / "exact-frozen-prompt.txt").write_bytes(prompt_bytes)
    receipt = {
        "case": case,
        "reviewer": "qwen3.8-27b-uncensored-local",
        "endpoint": endpoint + "/v1/completions",
        "requested_model": args.model,
        "frozen_commit": FREEZE_COMMIT,
        "prompt_sha256": digest(prompt_bytes),
        "protocol_sha256": digest(protocol_bytes),
        "request_sha256": digest(request_bytes),
        "assigned_records": 12,
        "request_started_at": datetime.now(timezone.utc).isoformat(),
        "loaded_context_tokens": model_snapshot.get("loaded_context_length") if model_snapshot else None,
        "quantization": model_snapshot.get("quantization") if model_snapshot else None,
        "completion_template": {"prefix": TEMPLATE_PREFIX, "suffix": TEMPLATE_SUFFIX},
        "template_note": "Exact frozen prompt without substantive additions. Explicit closed thinking channel requests a final-only completion; this configuration is disclosed and differs from web reviewer settings.",
        "settings": {"max_tokens": args.max_tokens, "temperature": args.temperature, "stream": False, "seed": "not_set", "provider_defaults_otherwise": True},
        "qualification": "internal_countertest_only",
        "cloud_calls": 0,
        "selection_or_author_identity_supplied": False,
    }
    save_json(destination / "receipt.json", receipt | {"state": "dispatched"})
    began = time.monotonic()
    print(json.dumps({"case": case, "state": "dispatched", "attempt": destination.relative_to(ROOT).as_posix()}), flush=True)
    request = urllib.request.Request(receipt["endpoint"], data=request_bytes, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            response_bytes = response.read()
            receipt["http_status"] = response.status
            receipt["response_headers"] = {k: v for k, v in response.headers.items() if k.lower() in {"content-type", "date", "server"}}
        (destination / "raw-response.json").write_bytes(response_bytes)
        receipt["raw_response_sha256"] = digest(response_bytes)
        parsed = json.loads(response_bytes)
        choice = parsed.get("choices", [{}])[0]
        text = choice.get("text")
        receipt.update({"returned_model": parsed.get("model"), "response_id": parsed.get("id"), "finish_reason": choice.get("finish_reason"), "usage": parsed.get("usage")})
        if not isinstance(text, str):
            raise ValueError("Provider did not return completion text")
        (destination / "raw-text.txt").write_text(text, encoding="utf-8")
        receipt["raw_text_sha256"] = digest(text.encode("utf-8"))
        try:
            value = json.loads(text)
            save_json(destination / "parsed.json", value)
            save_json(ROOT / "responses" / "qwen" / f"{case}-parsed.json", value)
            validation = validate(value, rules, items)
        except json.JSONDecodeError as error:
            validation = {"valid": False, "assigned": 12, "valid_records": 0, "errors": ["Output is not strict JSON: " + str(error)]}
        if choice.get("finish_reason") != "stop":
            validation["valid"] = False
            validation.setdefault("errors", []).append("Provider did not report a complete stop")
        save_json(destination / "validation.json", validation)
        receipt.update({"state": "complete_valid" if validation["valid"] else "complete_invalid", "contract_valid": validation["valid"], "valid_records": validation["valid_records"]})
    except Exception as error:
        receipt.update({"state": "failed", "error_type": type(error).__name__, "error": str(error), "contract_valid": False, "valid_records": 0})
        if isinstance(error, urllib.error.HTTPError):
            (destination / "error-response.bin").write_bytes(error.read())
    receipt["elapsed_seconds"] = round(time.monotonic() - began, 3)
    receipt["request_finished_at"] = datetime.now(timezone.utc).isoformat()
    save_json(destination / "receipt.json", receipt)
    result = {"case": case, "attempt": destination.relative_to(ROOT).as_posix(), "state": receipt["state"], "valid_records": receipt["valid_records"], "assigned_records": 12, "elapsed_seconds": receipt["elapsed_seconds"]}
    print(json.dumps(result), flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:1234")
    parser.add_argument("--model", default="qwen3.8-27b-uncensored")
    parser.add_argument("--case", choices=CASES, action="append", dest="cases")
    parser.add_argument("--max-tokens", type=int, default=3000)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    parsed_endpoint = urllib.parse.urlparse(args.endpoint)
    if (parsed_endpoint.scheme != "http" or parsed_endpoint.hostname not in {"127.0.0.1", "localhost"}
            or parsed_endpoint.username is not None or parsed_endpoint.password is not None
            or parsed_endpoint.path not in {"", "/"} or parsed_endpoint.query or parsed_endpoint.fragment):
        parser.error("This runner permits loopback inference only")
    results = [run(args, case) for case in (args.cases or CASES)]
    print(json.dumps({"state": "completed", "attempts": results, "qualified": False, "semantic_validation": "not_performed"}), flush=True)


if __name__ == "__main__":
    main()
