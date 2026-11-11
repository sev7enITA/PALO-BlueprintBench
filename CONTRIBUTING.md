# Contributing

We welcome independent process annotators, business-user participants, technical reproducers and corpus contributors. Start with the [reviewer kit](docs/reviewer-kit.md) and [live participation page](https://paloframework.org/PALO_BlueprintBench.html#participate).

Do not upload company documents, personal datasets, credentials or active held-out references to GitHub. For a corpus proposal, provide a public URL, workflow description, provenance and known reuse terms. Reuse permission must be established before copying originals.

For code changes, open a topic branch, explain the problem and run `python3 -m unittest -v test_blueprintbench` in `evaluator/`. Keep scoring changes separate from bug fixes and include examples demonstrating the intended numerator/denominator behaviour. Do not update a score silently when repairing an evaluator.

For research proposals, state the intended population, task, reference scope, failure policy and falsifiable acceptance condition. Declare conflicts and whether model outputs were visible during annotation. Existing PALO development cases are not eligible held-out submissions.

Reviewers are still being recruited. An expression of interest does not imply enrolment, authorship, endorsement or permission to disclose data. Attribution is agreed separately.
