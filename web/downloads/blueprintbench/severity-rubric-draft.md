# Specification-fidelity severity rubric draft

Status: proposed procurement annotation guidance. Not preregistered, independently agreed or calibrated. It must be reviewed and frozen before scoring an independent campaign. No measured agreement or detection rate is claimed.

A source proposition identifies its actor, action, modality, conditions, thresholds, exceptions and scope. A reviewer records the exact supporting passage and any genuine ambiguity. Inference plausibility is not source support. A permission must not silently become a duty, and a missing statement is not a prohibition.

Before seeing model output, domain annotators identify all scoped source propositions and independently mark those whose inversion could change an approval decision, permitted action, accountable actor, applicable exception or material threshold. Each critical designation and exclusion needs a written rationale. The adjudicator resolves disagreements, preserving the original labels. This is a proposed selection rule, not an established risk model.

For an output proposition:

- Supported: the cited source supports the scoped meaning, including an allowed alternative.
- Unsupported, critical source-rule inversion: the output changes a predeclared critical proposition. Record the violated gold ID and the changed semantic component.
- Unsupported, critical addition: the output introduces an unestablished obligation, permission, authority or material threshold. Record it separately from inversions; do not force it into the source-rule denominator.
- Unsupported, noncritical: an unsupported assertion without the specified critical consequence. Record the reason; do not downgrade a registered forbidden inference.
- Ambiguous or unassessable: leave the task unqualified pending adjudication. The current complete-scope evaluator does not accept this as a scored verdict.

Blind reviewers should retain their pre-adjudication labels, model-blinding procedure, task time and uncertainty reasons separately. The draft evaluator does not yet enforce a complete record of these fields or calculate agreement. Category-specific agreement, false-alarm and seeded-defect detection rates must be reported before this rubric supports a headline score. Do not substitute an LLM's agreement for independent human agreement.
