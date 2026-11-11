# Postrun semantic observations

This is an automated advisory review after observing a model response. It is not blind, independent human adjudication or a correction to the frozen key. No paid calls were made.

## Bank-change P07: description and obligation

Source B06: “The bank-change log records operator ID and approver ID. The documents do not define a department-tenure requirement for either role.”

Proposition: “The log must contain the operator ID and approver ID.”

The frozen draft label is `supported`. Anthropic Claude Opus 5.5 answered `not_established`, explaining that the source describes the log without establishing an obligation.

Two readings are defensible:

- **Supported, specification reading.** The procedure defines the contents of a conforming bank-change log. Present-tense language can specify a system invariant; “must contain” then expresses what conforming implementation requires. This assumes that B06 is prescriptive and that “must” denotes conformance necessity.
- **Not established, descriptive reading.** The source reports what a log records. That factual description does not entail an obligation to record it. This assumes that “must” is deontic and that a prescriptive convention cannot be added without explicit support.

B06 does not settle which convention applies. Other units use explicit “must not”, “only after”, and “may”, which makes the added “must” a legitimate concern. The document's procedure framing supports the first reading but does not uniquely establish it.

**Recommendation:** refer this item for human adjudication. Preserve the original key and disagreement in the current campaign, with a visible postrun ambiguity annotation. Do not retroactively exclude the item, accept an extra label, or classify the model response as a demonstrated semantic failure.

The earlier automated preflight accepted the normative reading. This observation records the competing reading and the limitation of that preflight rather than rewriting it.

For a future version, separate a factual log-content proposition from an explicitly mandatory recordkeeping proposition. Include both descriptive-only and explicit normative source variants, and freeze the modality convention before new inference. Human reviewers should determine whether “must” denotes logical conformance or an actor obligation in this item.

The JSON companion retains source text, response provenance and hashes. The original bank, frozen files, labels and scoring denominators were not changed.
