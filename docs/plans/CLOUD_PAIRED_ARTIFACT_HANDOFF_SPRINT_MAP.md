# Cloud-Paired Artifact Handoff Sprint Map

**Status:** TRACKED PLAN / P79 DISPOSITION = STRENGTHEN EXISTING OWNER / IMPLEMENTATION PARTIALLY PRESENT IN PR #641
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Canonical implementation lane:** PR #641 / `feat/p114-cloud-artifact-pairing-20260924`
**Planning floor:** refreshed `main@d0ff35ea4ff4be9bd23cda016e0044849d84e2cd`; PR #641 pre-plan head `b187305905e4a06e5248a52e223c6be268974bbc`
**Primary strategic owner:** P79 Prompt Registry Prompt Adder — strengthen-before-add disposition
**Runtime/delivery owners:** P114 Conversation Context Canary & Handoff Guard; P111 Repository + Google Drive Artifact Synchronizer; `harness/artifact-handoff`
**Recurrence/prevention owners:** P13 recurring-process hardening; P94 regression design
**Validation owner:** P11 End-to-End Harness Validator
**Proof ceiling:** this document is a durable execution plan. It does not itself prove downstream model compliance, local/provider runtime link delivery, Google Drive publication, or mainline integration.

---

## 1. Mission

Make this failure structurally difficult:

> An agent gives the operator a local, sandbox, repo-output, CI, generated-download, or other user-facing artifact reference while a relevant project cloud workspace or mapped cloud counterpart exists, but omits the usable cloud link and forces the operator to ask for it.

The target behavior is not “remember Google Drive more often.” It is a deterministic artifact-delivery contract:

1. detect when a user-facing local/download artifact is being created, offered, or referenced;
2. resolve whether the current project/workstream has a cloud workspace binding or per-artifact mapping;
3. when a healthy cloud counterpart exists, surface the canonical cloud link **in tandem with** the local/download artifact;
4. when the project cloud workspace exists but the artifact mapping is not yet resolved, route through the canonical synchronizer instead of treating “no obvious link” as local-only;
5. permit local-only handoff only when current scoped evidence proves local-only/private/do-not-sync status, or after an exact cloud identity/access/write/readback blocker is named;
6. prove that the cloud link refers to the intended artifact/version before claiming synchronization;
7. retain local/download artifacts as useful supplemental surfaces without forcing the operator to choose between cloud and local delivery.

The default Google Drive policy for a healthy mapped collaboration artifact remains:

**Google Drive link first/primary + local/download copy immediately adjacent/supplemental.**

The underlying kernel should remain provider-extensible so OneDrive, SharePoint, or another registered provider can satisfy the same pairing contract through its own owner.

---

## 2. Operator problem / recurrence evidence

This is a recurring system defect, not an isolated missed link.

Conversation-history recovery on 2026-09-24 found repeated operator corrections across August and September in which:

- a sandbox/local artifact was delivered without the mapped Google Drive link;
- an agent claimed or described Drive synchronization but did not surface the usable Drive URL;
- a stable Drive identity already existed but the final handoff exposed only the local copy;
- the Drive link appeared only after the operator explicitly asked where it was;
- the same correction recurred across different artifact domains (trackers, resumes/job artifacts, H&H artifacts, project/client artifacts), demonstrating that domain-specific prompt edits alone do not close the defect;
- on 2026-09-16 the repository already strengthened Drive-primary handoff semantics in P11/P140 and artifact-handoff;
- on 2026-09-24 PR #641 strengthened P114 for paired local/cloud artifact handoff;
- the operator still had to ask for the Google Drive link for the R9 tracker later on 2026-09-24.

This is enough recurrence to trigger P13/P94 systemic prevention. Raw conversation transcripts and private artifact contents are not required in Git; the retained regression should encode the failure shape, not private user data.

---

## 3. P79 disposition

### Decision

**STRENGTHEN EXISTING OWNER. DO NOT ADD A NEW PROMPT ID.**

### Why

The requested capability already has canonical owners:

| Concern | Existing owner | Disposition |
|---|---|---|
| Detect artifact-bearing context and prevent bad handoff | P114 Conversation Context Canary & Handoff Guard | STRENGTHEN / retain |
| Resolve/synchronize Google Drive identity and readback | P111 Repository + Google Drive Artifact Synchronizer | REUSE |
| Validate artifact delivery/handoff mechanics | `harness/artifact-handoff` + P11 | STRENGTHEN |
| Health-specialized Drive handoff | P140 | REUSE specialist |
| Recurrence/system hardening | P13 | ROUTE |
| Negative/positive retained regression | P94 | ROUTE |
| Prompt identity/admission | P79 | NO NEW ID |
| Professional artifact production | issue #644 / PR #645 candidate | CONSUMER, not owner |

PR #641 already proves that P114 can absorb the detection/closure behavior without a new capability identity. A second “always give me the Drive link” prompt would create overlapping authority and make routing worse.

### P79 acceptance rule

Any future canonical P114 edit must continue through `scripts/prompt_registry_ops.py` with semantic/source-history migration proof. No direct registry edit and no manually allocated prompt ID.

---

## 4. Exact invariant to install

### 4.1 Trigger

The pairing contract activates when the **operator-facing response** creates, offers, links, opens, downloads, or materially refers to a user-facing artifact through any local-ish surface, including:

- `sandbox:/...`;
- local filesystem path;
- generated conversation attachment;
- repo-output artifact intended for the operator;
- CI/build artifact intended for download/use;
- an artifact filename the response tells the operator to open/use/download;
- a later follow-up that refers back to one of those artifacts as the current deliverable.

It does **not** activate merely because prose mentions implementation source such as `scripts/foo.py`, a test path, a log path, or an internal repo file that is not being presented as the user's deliverable.

### 4.2 Project cloud relevance

A known project/workstream cloud workspace binding makes cloud relevance **presumptive** for user-facing artifacts.

Therefore:

- “No per-artifact mapping was immediately visible” is **not** proof of `LOCAL_ONLY_VERIFIED`.
- If a project cloud directory/workspace is known, the agent must resolve the artifact through the appropriate synchronizer/manifest before final closeout.
- Local-only is valid only when an explicit authority/privacy contract marks the artifact local-only/private/do-not-sync, or when the synchronizer proves no relevant cloud counterpart should exist.
- Broad cloud-account sweeping is forbidden; resolution is scoped to the current project/workspace/artifact.

### 4.3 Delivery states

Every material user-facing artifact reaches exactly one state before final handoff:

- `LOCAL_ONLY_VERIFIED`
- `MAPPED_CLOUD_VERIFIED`
- `PROJECT_CLOUD_RESOLUTION_REQUIRED`
- `CLOUD_BLOCKED`
- `CONFLICT`

No implicit/unknown state may be closed as “done.”

### 4.4 Pairing rule

`MAPPED_CLOUD_VERIFIED + LOCAL_SURFACED => PAIR_REQUIRED`

The response must expose both references as one logical handoff:

1. canonical cloud link;
2. local/download link.

For Google Drive when publication/readback is healthy, Drive is primary and the local artifact is supplemental.

The two links must be adjacent enough that the operator does not have to scan the response to discover that two representations exist.

### 4.5 Resolve-before-local rule

`PROJECT_CLOUD_RESOLUTION_REQUIRED + LOCAL_SURFACED` is not terminal.

Before closeout:

- invoke/route to P111 for Google Drive;
- reuse the existing workspace/file identity;
- update/publish when authority permits;
- read back;
- return the paired link.

If that cannot execute, transition to `CLOUD_BLOCKED` with the exact identity/access/write/readback gate, then local fallback may be surfaced without claiming synchronization.

### 4.6 Correspondence rule

A cloud URL is not sufficient merely because it points into the right folder.

Where evidence permits, prove the cloud reference corresponds to the same logical artifact/version by stable provider identity plus one or more of:

- readback title/version;
- content/hash/size;
- manifest revision;
- producer/input revision;
- registered artifact key;
- explicit same-ID update receipt.

Wrong-version, stale, ambiguous, or merely same-named cloud links fail closed.

### 4.7 No duplicate workspace rule

Pairing may never create a second CURRENT artifact/project workspace merely to obtain a link. Stable provider identity is reused.

---

## 5. Target prompt wording

This is **provisional wording for strengthening the existing owner**, not a new registered prompt:

> **PAIRED CLOUD ARTIFACT HANDOFF —** Before final response, if you create, offer, or refer the operator to a user-facing local/sandbox/download artifact, inspect the current project's scoped cloud workspace/mapping. When a healthy mapped cloud counterpart exists, surface the canonical cloud link together with the local/download reference; for a healthy Google Drive mapping, put the Drive link first and treat local/download as supplemental. A known project cloud workspace with no resolved per-artifact mapping requires P111/provider-owner resolution before closeout; absence of an obvious link is not proof that the artifact is local-only. Local-only handoff is allowed only when current scoped evidence proves local-only/private/do-not-sync status, or after an exact cloud identity/access/write/readback blocker is named. Reuse stable cloud identities, verify correspondence/readback, never claim sync from local bytes alone, and do not trigger on internal source-code paths that are not operator-facing artifacts.

P114 should carry the detection/closure version of this text. P111 and the artifact-handoff harness remain the execution/validation owners.

---

## 6. Architecture / owner map

### P114 — sensor + closure guard

P114 owns:

- detecting an operator-facing local artifact reference;
- detecting project cloud relevance from scoped evidence;
- forcing resolution before closeout;
- requiring paired cloud/local handoff when verified;
- refusing false `CLOUD=NONE` when only lookup is missing;
- emitting an exact blocker when pairing cannot be completed.

P114 does **not** own Drive sync mechanics.

### P111 — Google Drive execution owner

P111 owns:

- workspace discovery/reuse;
- artifact authority classification;
- stable Drive identity resolution;
- upload/update/import decision;
- two-sided divergence handling;
- Drive write/readback;
- per-artifact sync ledger/receipt.

P111's final response must project the verified Drive URL, not merely say “synced.”

### Artifact-handoff harness — delivery contract owner

The current `share-alias-download/v1` contract mixes alias-copy rules with Drive-primary precedence. Preserve it for compatibility, but factor generalized delivery pairing into a sibling canonical contract rather than duplicating rules across prompts.

Planned owner:

`harness/artifact-handoff/contracts/artifact-delivery.v1.json`

Suggested schema concepts:

- artifact key / logical identity;
- operator-facing local reference present?;
- project cloud workspace bound?;
- provider;
- authority;
- cloud-resolution state;
- stable cloud identity resolved?;
- cloud URL;
- cloud publication/readback state;
- local URL/path;
- primary/supplemental roles;
- correspondence proof;
- exact blocker;
- final disposition.

The artifact-handoff manifest/validator composes alias/download correctness with delivery-pairing correctness.

### P11 — proof gate

P11 should consume the artifact-delivery receipt and fail when:

- a local operator artifact is surfaced while a healthy required cloud counterpart is omitted;
- Drive is marked healthy but not primary in a Drive-primary allocation;
- cloud fallback lacks an exact blocker;
- a cloud URL is present but correspondence/readback is unproven when required.

### P13 / P94 — recurrence retention

P13 owns the systemic repair program. P94 owns the retained failure cases and positive controls.

### Consumer prompts

Artifact-producing prompts (P56 and the professional-artifact candidate, plus domain specialists) should **route to the shared artifact-handoff owner** instead of copying the entire cloud-link doctrine into each prompt.

---

## 7. Sprint map

### Sprint 0 — Converge the existing #641 implementation

**Mission:** preserve the useful P114 strengthening already implemented while reconciling it to current `main`.

**Owned surfaces:**

- PR #641 branch;
- its existing P114 registry/migration/profile/tests/generated-site changes;
- this canonical plan.

**Forbidden:**

- new Prompt Kit ID;
- duplicating P111 mechanics inside P114;
- absorbing unrelated upstream donor-refresh drift;
- touching PR #645 candidate surfaces.

**Current evidence:**

- PR #641 is open and mergeable;
- pre-plan head `b187305905e4a06e5248a52e223c6be268974bbc`;
- branch is 9 ahead / 3 behind current `main`;
- deterministic repository test floor, app harness, prompt quality history, prompt topology, Prompt Kit web/runtime checks, and artifact engine checks were green at that head;
- `operant-external-resource-refresh` failed on independent registered-donor drift (59 live vs 57 tracked), not P114 semantics.

**Gate:**

1. rebase/merge current main non-destructively;
2. rerun affected P114 semantic/history/parity/focused tests;
3. preserve provider-drift failure as independent;
4. merge #641 only when current-head gates permit.

### Sprint 1 — Canonical artifact-delivery contract

**Mission:** convert the operator correction from prompt prose into one reusable artifact-delivery contract.

**Expected artifacts:**

- `harness/artifact-handoff/contracts/artifact-delivery.v1.json`;
- manifest registration;
- provider-agnostic states and decision table;
- explicit project-cloud-binding semantics;
- compatibility relationship to `share-alias-download/v1`.

**Acceptance:**

- one owner for delivery pairing;
- no duplicate Drive sync logic;
- Google Drive rule can be specialized without making Drive universally authoritative;
- local-only/private cases remain valid;
- internal source-code references do not spuriously trigger cloud sync.

### Sprint 2 — Machine-checkable handoff receipt + validator

**Mission:** make the invariant mechanically testable.

**Expected artifacts:**

- machine-readable artifact-delivery receipt schema/fixtures;
- extension of `scripts/validate_artifact_handoff_harness.py` or a composed validator invoked by it;
- exact failure messages for omitted cloud link, wrong primary, unresolved project-cloud mapping, stale/wrong cloud correspondence, and fallback without blocker;
- positive controls for verified local-only and cloud-blocked fallback.

**Proof boundary:**

Static receipt/fixture validation proves contract semantics. It does not by itself prove a model actually obeyed the final-response requirement.

### Sprint 3 — Prompt composition without doctrine duplication

**Mission:** wire the shared owner into Prompt Kit.

**Actions:**

- retain P114 as detection/closure owner via protected P79 STRENGTHEN;
- inspect P111/P11/P140 for already-sufficient markers before editing;
- route P56/professional-artifact generation to artifact-handoff for delivery;
- prefer a lightweight shared stub/reference over copying the whole contract into many prompts;
- use `prompt_registry_ops.py edit` for any protected canonical prompt mutation;
- record semantic/source-history migrations.

**Admission rule:** no new prompt identity unless a later P79 prior-art pass proves a residual not covered by P114/P111/artifact-handoff.

### Sprint 4 — Retained regression corpus

Create a privacy-safe regression matrix from the repeated failure family.

Minimum cases:

1. healthy mapped Drive artifact + sandbox link only => **FAIL**;
2. healthy mapped Drive artifact + Drive primary + sandbox supplemental => **PASS**;
3. user explicitly asks for download + Drive healthy + only download returned => **FAIL**;
4. known project Drive workspace + new local deliverable + no per-artifact mapping lookup => **FAIL / RESOLUTION REQUIRED**;
5. known project Drive workspace + P111 resolves/reuses same-ID artifact + both links returned => **PASS**;
6. Drive write/readback blocked + exact gate + local fallback => **PASS WITH BLOCKER**;
7. Drive blocked + local fallback + “synced” claim => **FAIL**;
8. cloud URL points to wrong/stale logical artifact/version => **FAIL**;
9. explicit `LOCAL_ONLY_VERIFIED` artifact with no project-cloud publication obligation => **PASS**;
10. internal source-code path mentioned, no user-facing artifact => **NO TRIGGER / PASS**;
11. follow-up response refers to an already-created local deliverable but omits its healthy cloud counterpart => **FAIL**;
12. multiple user-facing local artifacts => each must receive an independent disposition/pairing result;
13. stable cloud identity exists but agent creates `copy`, `(1)`, new CURRENT, or new workspace to get a link => **FAIL**;
14. cloud link is surfaced but readback/correspondence remains unknown while response claims current/synced => **FAIL**;
15. mapped non-Google provider routes to its established owner and returns provider+local pair => **PASS**;
16. no provider owner exists => **UNKNOWN/BLOCKED**, never fabricated sync.

The corpus must include the exact operator-visible failure shape: local artifact link appears in final answer, operator's next message is effectively “Where is the Google Drive link?”

### Sprint 5 — Cross-owner validation

Required focused gates:

- `tests/test_conversation_context_canary_prompt.py`;
- `tests/test_artifact_handoff_harness.py`;
- `tests/test_google_drive_handoff_prompt_strengthening.py`;
- `tests/test_repository_drive_artifact_synchronizer_prompt.py`;
- new artifact-delivery receipt/regression tests;
- prompt semantic coverage/history/strength validators when protected prompt text moves;
- generated Prompt Kit parity after canonical prompt mutation;
- `git diff --check`.

Then run the repository-owned required-check profile appropriate to exact head.

### Sprint 6 — Observed runtime acceptance

Static Prompt Kit and receipt tests are not enough.

Run a bounded observed acceptance matrix in supported chat/runtime surfaces:

- generate a spreadsheet with a mapped Drive workspace;
- generate a document with mapped Drive workspace;
- refer to an existing local artifact in a later response;
- explicitly request a download while Drive is healthy;
- exercise a verified local-only artifact;
- simulate Drive permission/readback failure.

For mapped healthy cases, acceptance requires that the first artifact-bearing final response exposes the usable cloud link **without an operator reminder**.

Record only privacy-safe outcome metadata:

- case ID;
- model/runtime/config identity;
- contract revision;
- whether local artifact was surfaced;
- cloud relevance state;
- cloud link surfaced?;
- local link surfaced?;
- ordering/adjacency result;
- blocker if any;
- PASS/FAIL.

Do not persist private prompts, artifact contents, or account identifiers merely for evaluation.

### Sprint 7 — Convergence and duplicate-rule retirement

After the shared contract is integrated and runtime evidence is sufficient:

- remove/compact duplicated wording that only restates the shared artifact-delivery kernel;
- retain specialist semantics that truly differ;
- ensure P114 remains lightweight enough to function as a canary rather than becoming the sync engine;
- ensure P111 remains the Google Drive synchronization authority;
- close or supersede #641 only through current-head integration proof;
- record final owner map and runtime proof ceiling.

---

## 8. Acceptance criteria / definition of done

The whole outcome is closed only when all applicable items are proven:

1. **Identity:** P79 records STRENGTHEN-existing-owner; no duplicate prompt ID.
2. **Prompt guard:** P114 requires resolution/pairing for operator-facing local artifacts.
3. **Execution owner:** P111 remains the Google Drive sync/readback owner.
4. **Shared delivery contract:** artifact-handoff contains one canonical pairing state machine.
5. **Machine validation:** a receipt/fixture can deterministically fail sandbox/local-only handoff when a healthy cloud pair is required.
6. **Project-workspace rule:** known project cloud workspace cannot be bypassed merely because a per-artifact mapping was not looked up yet.
7. **False-positive control:** internal code paths and genuinely local-only artifacts do not force cloud publication.
8. **Stable identity:** no duplicate CURRENT/workspace created for handoff convenience.
9. **Correspondence:** stale/wrong cloud links cannot satisfy the contract.
10. **Regression:** prior operator-visible omission shapes are retained as negative cases.
11. **Prompt parity:** protected prompt edits use `prompt_registry_ops.py`, semantic/history proof, and generated-site parity.
12. **Runtime:** at least one mapped Google Drive spreadsheet and one mapped document hand off cloud+local without reminder.
13. **Integration:** exact validated implementation is contained in refreshed default branch.
14. **Proof honesty:** static tests are not promoted to live model/runtime compliance.

---

## 9. Collision / dependency map

### Active collision owner — PR #641

Owns:

- P114 canonical registry mutation;
- P114 capability/source-history migrations;
- P114 semantic profile;
- P114 focused tests;
- generated Prompt Kit parity related to that mutation.

Do not open a second branch that edits those same surfaces until #641 is integrated or explicitly superseded.

### PR #645 / issue #644

Owns the professional-artifact builder candidate and its candidate plan/fixtures. It is a future consumer of the artifact-delivery contract, not the cloud-delivery owner. Do not mutate its staged prompt candidate from this lane.

### External-resource refresh

The observed 59-vs-57 donor-resource drift is an independent capability-watch issue. Do not broaden this plan into donor maintenance merely to get a green check.

---

## 10. Proof-relevance fingerprint for this program

Runtime or integration proof is stale when any of these materially change:

- P114 canonical body/profile;
- P111 final handoff/sync semantics;
- artifact-delivery contract/schema;
- artifact-handoff validator;
- project-cloud binding semantics;
- final-response projection/receipt semantics;
- relevant provider owner/adapter;
- test/eval scenario contract.

Documentation-only edits, timestamps, or proof-SHA citation updates do not by themselves invalidate runtime behavior proof.

---

## 11. First executable successor action

**Owner:** PR #641 convergence agent
**Dependency:** authenticated checkout or provider workflow capable of reconciling current `main` with `feat/p114-cloud-artifact-pairing-20260924` without destroying the nine owned commits
**Action:** reconcile the branch to current main, then run the focused P114 + artifact-handoff + repository-drive tests and current required-check profile; only after that integrate #641 or record the exact remaining gate.
**Expected proof:** current-main-contained #641 head with P114 strengthening retained and no collision with #645.
**Completion gate:** exact reconciled head passes all proof-relevant focused checks, independent donor-refresh drift remains separately classified, and the PR is integrated or blocked by a named non-semantic gate.

After #641 integration, launch Sprint 1 from refreshed main and implement the canonical artifact-delivery contract before adding more prompt prose.

---

## 12. Fixed-point target

The desired operator experience is simple:

> Any time the response says “here is the local/download artifact” for a project that has a cloud collaboration workspace, the matching usable cloud link is already beside it—without the operator having to ask.

The repository architecture should achieve that with one delivery contract, one sync owner per provider, one lightweight P114 guard, retained regressions, and observed runtime proof—not with another pile of overlapping prompts.
