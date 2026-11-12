# Internal calibration implementation and review decisions

11 November 2026. Internal engineering work, not independent validation. The 18-model primary cohort is unchanged. This new exercise is not another model-ranking cohort.

## Four priorities and delivered scope

| Priority | Delivered | Still required |
|---|---|---|
| Atomic rubric and reference bank | Six source-bound rules with explicit scope, answerability, criticality basis, alternatives and forbidden inferences; draft labels frozen before review | Independent procurement experts, independently chosen families and adjudication |
| Workflow reliability | Replay from frozen input through response-envelope checks, draft-label comparison and source-bound review export; missing and uncertain records retained | Repeated order-shuffled model runs, document ingestion and export qualification and business-user sessions |
| Structure and semantics | Separate envelope status and semantic status; no silent JSON repair; wrong but well-formed answers can fail the semantic comparison | Hard negatives, unanswerable items and a validated semantic measure |
| Exposure and versioning | Source and rubric reuse keys, response/prompt hashes, explicit engineering-exposed family, fail-closed qualification | External custody, identity verification, signed independent decisions and new unexposed families |

## Review decisions

- **Accepted, Fable and Gemini:** no confidence intervals or population claim from one family. Six related source rules do not become eighteen independent observations through paraphrase and mutation.
- **Accepted, Fable and Gemini:** preserve fixed denominators and publish missing/uncertain counts. All-abstention cannot appear successful; a zero false-alarm count with unresolved controls is flagged as uninterpretable.
- **Accepted, Fable:** strict parsing rejects duplicate keys, duplicate/unknown IDs, extra fields, empty reasons, malformed JSON and Markdown envelopes. Invalid captures are `not_assessed`, never repaired into a pass. The separate unscored raw review remains inspectable.
- **Accepted, Fable and Gemini:** a change to source, scope, alternatives, criticality or rubric invalidates the reuse key. Local hashes prove byte identity, not authentic timing, independence or semantic correctness.
- **Accepted, Fable and Gemini:** the annotation-preparation export excludes expected labels, reviewer reasons and perturbation classes. It is public, exposed preparation material, not a sealed or independently blind study.
- **Accepted, Fable:** keep all 18-model measurement bytes unchanged. A new calibration packet does not retrospectively validate historic scores. The roster derives existing ranks without changing evidence.
- **Qualified disagreement with Gemini:** retain exact UTF-8 bytes rather than silently canonicalising whitespace and newlines. This follows the existing evaluator's offset contract; a benign byte edit requires a new binding. A future normalised representation must coexist with original bytes and a versioned offset mapping.
- **Qualified disagreement with Gemini:** missing, uncertain or invalid output blocks a successful workflow but is not automatically a demonstrated semantic inversion. Evidence of a changed obligation must remain distinct from no assessed judgment.
- **Qualified disagreement with Gemini:** two human names and a kappa value cannot automatically enable PBI qualification. Identity, conflicts, custody and a signed decision remain external gates.
- **Correction to a reviewer assumption:** the current 18-model dataset already uses fixed assigned denominators. Gemini's suggestion that these would be introduced only by the new method is not supported by the frozen cohort. No cross-version improvement claim is made.
- **Open, Fable and Gemini:** easy copies and obvious operator flips can be solved by shallow heuristics. This is a calibration smoke test, not evidence that a judge is generally reliable. Subtle scope changes, omitted conditions, added exceptions, instruction-bearing candidates and unanswerable tasks require a new versioned challenge set.
- **Open, Fable:** C10's passive wording can be read too broadly. The draft faithful label is unchanged; the warning is shown beside that item. Future adjudication must distinguish optional approval by a specified actor from permission to proceed without any approval.

## Reproduction

`python tools/calibration.py --check` verifies the frozen inputs and captured-response receipts and reproduces the export. `python tools/build_calibration.py --check` checks the rendered panel. `python tools/build_roster.py --check` verifies the roster. None makes a paid model request.

The calibration harness is separate from evaluator 0.3 and from Workbench. It does not imply that the application's PDF/Excel ingestion or full-repository export was tested again. Rationale text is retained model output, not a verified citation. Public release retires these examples from any future independent holdout pool.

## GLM desktop cross-check

GLM 5.3 with Max effort was consulted in ZCode desktop after the web security check and desktop process interruption. The common packet included an additional no-tools/read-only instruction. It recommended a lexical baseline, immutable-denominator replay, a harder uncertainty set and source/derivative exposure controls. The exact-string baseline was executed post hoc: 6/6 seeded alterations detected, 6/12 false alarms on faithful controls. Its six unchanged positives are easy by construction.

We do not adopt GLM's suggestion to remove uncertain answers from the denominator: that would reward abstention. Uncertain remains assigned and separately reported. Nor do we claim a minimum detectable effect from a single authored family.

The copied Gemini answer contains unescaped quotes; the copied GLM answer has a malformed claims_to_avoid member. Both full captures fail strict JSON parsing and receive no semantic score. These are interface captures, not original provider response bytes; transport attribution remains limited. Their methodological feedback is a manually read advisory, not a repaired scored response. Fable's API bytes and complete response are retained.

## Implementation review and corrections

Fable 5.2 High and GLM 5.3 Max reviewed the actual replay, roster and test code. Their captured implementation reviews are retained alongside the prompt. Concrete findings resulted in these changes:

- A post-capture integrity lock binds raw captures and receipts. Required pre-review inputs cannot be silently omitted from verification. This is a versioned drift check, not an external timestamp or protection against a maintainer rewriting the complete repository.
- The legacy dataset and context corpus are pinned separately. `primary_scores_unchanged` is now conditional on an actual digest check. The guard was added after capture and is not preregistration.
- An incomplete control set exports a null false-alarm ratio. Zero controls cannot produce an interpretable rate. Missing and invalid responses retain their assigned counts.
- Annotation reuse identity includes the exact candidate and prompt as well as source, scope and rubric. A faithful control and its altered sibling cannot share a cached judgment.
- Family tallies derive from source bindings; a changed family count blocks the frozen protocol. The roster asserts the frozen cohort size and verifies its source corpus.
- Annotation preparation is a separate label-free file. The public material remains exposed; separation does not retrospectively create a blind study.
- Roster insertion fails when its HTML anchor is missing. Null usage, disabled reasoning and zero denominators are handled explicitly. Text uses UTF-8.
- Partial envelope validity, review completeness and determinate coverage are separate fields. Item exports retain vote counts and dissent even when another reviewer is missing.

Malformed or incomplete capture provenance fails the build. A malformed answer with intact provenance is retained as invalid. These are different conditions. Regression tests include altered capture plus rewritten receipt, missing required frozen input, candidate-specific reuse, unresolved controls and deeply nested JSON.

The reviewers read code and did not execute it. The local automated tests and browser parity receipt are separate evidence. They do not constitute a second human review or qualify a PBI result. Fable's suggested binomial bounds are not adopted because siblings within one source family are not independent trials.

Gemini's initial methodological review is retained. Its subsequent long code request produced no captured answer; a shortened retry showed incomplete submitted text and was stopped. No code-review completion or implementation approval is attributed to Gemini. The implementation reviews completed by Fable and GLM remain advisory.

The first GitHub matrix run passed on macOS and Ubuntu but exposed a Windows path-separator mismatch in capture-lock lookup. The lookup now uses POSIX manifest paths on every platform. The page data were unaffected; the replay portability fix is tracked separately.
