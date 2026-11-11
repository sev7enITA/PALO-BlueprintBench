# Historical passage evidence

Ten configurations, three frozen public-source passages, 10 November 2026. This archive contains parsed model responses (not original HTTP byte streams), observed errors/times/accounting metadata, the prompts and schemas used for the passages, configuration metadata, recorded deterministic audit results, and a frozen checker/adapter source snapshot.

The source snapshot was retained from the PALO quality workspace on 11 November. Its exact identity at the moment of each original request is not independently attested. Offline replay checks whether this retained checker reproduces the published raw/structural counts. It does not replay provider generation, establish semantic accuracy or qualify a model. Provider revisions and random generation may change. Request templates are consumed by the runner; each result records the actual model/provider/reasoning/output cap.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python replay.py
```

Offline replay needs no API key and makes no inference calls. The historical runner is disabled to prevent accidental reuse of evidence or spending; its credential-file read was removed. No API key, private budget file or original provider ledger is included. The adapter source is retained for inspection. The dependency set supports this offline checker; it is not a frozen original provider environment or the complete Workbench application. macOS/Linux are the supported replay environments.

Source excerpts are the bounded public-document passages already used in the development investigation, not a new held-out corpus. Related editions remain development material. PALO code follows the included project licence; this archive does not grant rights to entire third-party source documents. No synthetic scores are substituted for historical observations.
