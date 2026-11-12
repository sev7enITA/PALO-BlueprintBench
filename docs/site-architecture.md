# Research site structure

Presentation revision 2026-11-11.6 separates introduction, results, method and source material. Existing result URLs, query filters, raw evidence identifiers and observation revisions remain unchanged.

```text
BlueprintBench overview
├── Policy Interpretation: Model results
│   └── Adapter diagnostics: separate historical tab
├── Process Interpretation
├── Specification Generation
├── Corpus
└── Method
    ├── Related benchmarks
    ├── Independent-validation requirements
    └── Reviewer participation
Reviewer diagnostics: separate resource linked from method and footer
```

| Navigation label | Existing or new URL | Purpose |
|---|---|---|
| Overview | PALO_BlueprintBench.html | Definition, intended use and choice of test |
| Policy Interpretation | PALO_BlueprintBench_Leaderboard.html | Existing 18-configuration model results, filters and exports |
| Process Interpretation | PALO_BlueprintBench_NextCycle.html | Existing six authored process descriptions and 60 requests |
| Specification Generation | PALO_BlueprintBench_Generation.html | Separate generation experiment on public procurement documents |
| Corpus | PALO_BlueprintBench_Corpus.html | Input provenance, document coverage and distinctions between source sets |
| Method | PALO_BlueprintBench_Method.html | Tasks, evidence rules, qualification requirements and related research |

The header uses these six labels in the same order. The footer provides reviewer diagnostics, GitHub, participation and PALO Framework links. Every module links back to the overview. Input, task, model count, repetition count and execution channel are visible before results.

A test is the input set and task. A run is an execution. A configuration identifies the model and serving conditions. Historical filenames retain campaign, case and scenario identifiers for reproducibility; they are not introduced as additional datasets in the navigation.

The three short synthetic procurement texts are distinct from the three historical public-document excerpts used for adapter checks. The six authored process descriptions are distinct from the three real procurement document inputs. No counts or metrics are pooled across these sets.

`tools/build_site_architecture.py` generates the overview, method and corpus and applies common navigation to the existing result pages. `tools/build_public.py` now places related references on Method. `tools/build_roster.py` retains the roster on Model results only. Dataset JSON-LD remains on result pages; the overview uses descriptive WebPage metadata and links to modules without presenting a second dashboard.
