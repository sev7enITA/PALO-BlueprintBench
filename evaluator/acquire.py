"""Download explicitly registered public seed documents; never claims corpus admission."""
import argparse
import datetime as dt
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path


def acquire(registry, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for family in registry["families"]:
        item = {"family": family["id"], "url": family["seed_download_url"],
                "status": "not_selected", "rights_status": "pending", "heldout": False}
        if not item["url"]:
            results.append(item)
            continue
        part = None
        try:
            if not re.fullmatch(r"[a-z0-9-]+", family["id"]):
                raise ValueError("invalid family identifier")
            parsed = urllib.parse.urlsplit(item["url"])
            if parsed.scheme != "https" or parsed.username or parsed.password:
                raise ValueError("only public HTTPS URLs without credentials are supported")
            part = output / (family["id"] + ".part")
            started = time.monotonic()
            req = urllib.request.Request(item["url"], headers={"User-Agent": "PALO-BlueprintBench/0.1 research acquisition"})
            with urllib.request.urlopen(req, timeout=45) as response, part.open("xb") as target:
                if urllib.parse.urlsplit(response.url).scheme != "https":
                    raise ValueError("HTTPS downgrade rejected")
                sha = hashlib.sha256()
                size = 0
                prefix = b""
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk: break
                    size += len(chunk)
                    if size > 1024 ** 3 or time.monotonic() - started > 300:
                        raise ValueError("acquisition transfer guard reached")
                    if not prefix: prefix = chunk[:16]
                    sha.update(chunk)
                    target.write(chunk)
                kind = "pdf" if prefix.startswith(b"%PDF-") else "zip-container" if prefix.startswith(b"PK") else "other"
                if kind == "other": raise ValueError("response is not a PDF or Office ZIP container")
                item.update(status="seed_downloaded", final_url=response.url,
                            content_type=response.headers.get("Content-Type"), bytes=size,
                            sha256=sha.hexdigest(), format=kind,
                            downloaded_at=dt.datetime.now(dt.timezone.utc).isoformat())
            final = output / (family["id"] + (".pdf" if kind == "pdf" else ".zip-container"))
            part.rename(final)
            item["local_filename"] = final.name
        except Exception as exc:
            item["status"] = "download_failed"
            item["error_type"] = type(exc).__name__
            item["error"] = str(exc)[:200]
            if part is not None and part.exists(): part.unlink()
        results.append(item)
        (output / "acquisition.json").write_text(json.dumps({"version": "0.1.0", "status": "seeds_only_not_corpora", "results": results}, indent=2) + "\n")
    (output / "acquisition.json").write_text(json.dumps({"version": "0.1.0", "status": "seeds_only_not_corpora", "results": results}, indent=2) + "\n")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry")
    parser.add_argument("output")
    args = parser.parse_args()
    result = acquire(json.loads(Path(args.registry).read_text()), args.output)
    print(json.dumps([{k: x[k] for k in ("family", "status")} for x in result]))
