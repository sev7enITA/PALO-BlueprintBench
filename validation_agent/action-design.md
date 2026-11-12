# Agent Action Design

Status: draft design, not an executable Action Claim, authority grant, signed Effect Contract or certification.

## Mandate

A human operator chooses a local source packet and explicitly starts a review. The agent reads only that packet, sends filtered excerpts to the fixed loopback LM Studio endpoint and writes a new local results directory. It may calculate a local calibration diagnostic using the existing development key after inference. The named human principal, formal delegation, individual expiry and authorisation over non-public documents are not established by access to the tool. They must be resolved for any operational deployment.

## Boundaries

Permitted operations are reading an explicitly selected packet, local inference, local file creation, deterministic format and citation checks, and offline replay. Forbidden effects are modification of the source packet or frozen benchmark evidence, transmission to remote services by the agent, claims of human approval or independent custody, changes to answer keys, publication, recruitment, automatic retries after uncertain completion, and assignment of a qualified score or rank.

The agent is constrained to `http://127.0.0.1:1234`; this does not attest how LM Studio itself is configured, what it logs or whether the underlying model is served elsewhere. The operator is responsible for data rights and LM Studio configuration. No code executes instructions supplied in source text or in model output. The model may nevertheless follow malicious instructions inside a document.

## Action Claim Requirements

A future executable Action Claim would need a verified principal and delegation, agent and case identifiers, exact input and output scopes, tool operation and arguments with digests, network intent, request time, expiry, nonce, idempotency key and sequence number. These fields are requirements for a future authorisation system. This prototype does not issue an Action Claim or provide identity authentication, revocation checks, signatures or policy enforcement.

## Intended Effects and Verification

The expected effect is a new local directory with a filtered packet, source hash, per-item request and response records, status, advisory results and an HTML report. Verification consists of checking retained request and response hashes and reapplying the format and exact-quotation checks. These checks do not establish a correct interpretation, complete source, external timestamp or independence. A valid result remains advisory.

For a future Effect Contract, the target would be the operator-selected new output directory and the source packet version. Preconditions would include permission for local processing, the expected source digest, the intended model identity and an unused output path. Forbidden effects include changes to prior evidence or reference answers. The observation source would be the retained local files; a mismatch or unobservable outcome must remain inconclusive and be held for review. A compensation or repeat action would require its own authority.

## Uncertain Results

An in-flight request can outlive a client timeout or interruption. Preserve the partial directory and its `progress.json`, do not automatically retry, and inspect the local server before starting a distinct run. An invalid, incomplete, missing or unsupported response remains unassessed. A different returned model identity is rejected. Existing results are not overwritten.

## Evidence States

| State | Evidence |
| --- | --- |
| Authorisation | Explicit operator invocation; separate rights and delegation for any non-public source remain unresolved |
| Execution | Local request and response files and progress record, when present |
| Effect verification | Local offline replay and its stated limits |
| Business outcome | Human review and independent qualification remain unobserved |
