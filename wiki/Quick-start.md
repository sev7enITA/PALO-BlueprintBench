# Run the evaluator

This route checks synthetic evidence without calling an LLM. You need Git, Python 3.10 or later, and the pinned `jsonschema` dependency. Installation downloads Python packages unless already cached. No model weights, API credentials or inference charges are required.

```sh
git clone --branch v0.3.0-pilot.1 https://github.com/sev7enITA/PALO-BlueprintBench.git
cd PALO-BlueprintBench
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r evaluator/requirements.txt
python -m unittest discover -s evaluator -p 'test_*.py' -v
python evaluator/demo.py ./demo-evidence
```

On Windows PowerShell use `.venv\Scripts\Activate.ps1` for activation. Select a new output directory each time: refusing to overwrite evidence is intentional.

## Read the result

Open `demo-evidence/result.json`. The fixture assigns three tasks, accepts one and reports one distinct critical error. `qualified` remains `false`. These are known synthetic cases, not measurements of any language model.

To re-evaluate the generated records:

```sh
python evaluator/blueprintbench.py evaluate demo-evidence/campaign.lock.json demo-evidence/run.json --evidence-root demo-evidence --output demo-recomputed.json
```

For the current documentation and wiki, use `main`; for a reproducible software audit, identify the exact release or commit. Do not silently migrate old records to the new evidence contract.

## Common problems

- `No module named jsonschema`: install the requirements using the same Python environment that runs the command.
- An output already exists: choose another path; do not overwrite the original evidence.
- An artifact hash differs: preserve the files and investigate the modification. Recomputing a hash does not establish trusted preregistration.

[Evaluator reference](https://github.com/sev7enITA/PALO-BlueprintBench/blob/main/evaluator/README.md) | [[Metrics|Metrics]] | [[Reproducing results|Reproducing-results]]
