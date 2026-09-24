# Ticket Tracker Ingestion Automation Sprint Map

**Status:** TRACKED PLAN / IMPLEMENTATION NOT YET STARTED
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Planning floor:** `main@c7c5a029d92c81a100abc9cde9477ae39a3379e9`
**Planning branch:** `plan/ticket-tracker-ingestion-automation-20260924`
**Primary Prompt Kit owner:** P125 · Health + Hospitals Ticket Discovery & Tracking Harvester
**Artifact mutation owner:** P56 · Context-to-Artifact Generator
**Google Drive sync owner:** P111 · Repository + Google Drive Artifact Synchronizer
**Cloud/local delivery guard:** P114 · Conversation Context Canary & Handoff Guard (integrated on current planning floor via PR #641)
**Prompt identity/admission owner:** P79 · Prompt Registry Prompt Adder
**Recurring-defect / retained-regression owners:** P13 / P94
**Implementation owner:** Triage ticket-ingestion capability under the existing repository harness; exact module path is intentionally deferred until implementation inspection resolves the narrowest existing code owner
**Proof ceiling:** this file is a repository-grounded execution plan. It does not prove screenshot parsing, workbook mutation, website mutation, Drive synchronization, Copilot behavior, ServiceNow truth, or field/runtime acceptance until those stages are separately implemented and observed.

---

## 1. User outcome

The operator should be able to provide **new ticket evidence** in the form available at the moment — screenshot(s), pasted ticket lists, copied incident details, P125/Copilot harvest output, or later a direct provider/API record — and have one deterministic workflow:

```text
incoming evidence
  -> source extraction
  -> normalized observations
  -> ticket identity + duplicate/conflict resolution
  -> tracker-aware merge plan
  -> canonical ticket_update receipt
  -> backend adapter
       -> Excel/workbook
       -> local website/data store
       -> later other supported stores
  -> readback validation
  -> provider synchronization / canonical link
```

The operator should not need to manually remind an agent to:

- add every genuinely new incident;
- ignore repeated incident IDs already present;
- avoid merging two different tickets because they share a site, kiosk, date, person, or similar description;
- populate every tracker column that current evidence or deterministic defaults can support;
- leave unsupported values blank/unknown rather than inventing them;
- preserve stronger existing values when new evidence is weaker;
- record Date Received / intake chronology correctly;
- initialize a newly inserted ticket to the tracker’s contracted initial status when the evidence does not support a later state;
- preserve contradictory evidence rather than silently overwriting it;
- keep ticket intake, coordination, assignment, in-progress work, completion reported, and verified closure separate;
- update the existing tracker identity rather than creating a competing workbook/workspace;
- read the result back and prove row count / unique IDs / duplicates / field dispositions;
- return the mapped cloud artifact link when the tracker is cloud-backed.

This workflow is the **agentic foundation of a later deterministic local engine**. Prompt prose may orchestrate it; prompt prose must not become the implementation of dedupe, merge, parsing, or storage semantics.

---

## 2. Evidence recovered before planning

### 2.1 Current Prompt Kit truth

P125 is already the correct H&H domain owner.

Its current contract already requires:

- Outlook + Teams as one H&H ticket workflow;
- explicit identifier typing;
- explicit ServiceNow/incident/ticket ID as the preferred durable identity;
- cross-source reconciliation for the same incident;
- provisional identities when IDs are absent;
- no merge solely from site/kiosk/person/day similarity;
- preservation of conflicting site/status evidence;
- distinct status states for intake, coordination, assignment, in-progress, waiting/blocked, completion reported, closed/resolved, and unknown;
- no inferred repair, replacement, delivery, attendance, hours, billing, or technician completion;
- a normalized ticket record with identity, site, issue, requester/relay, assignee, timestamps, change state, follow-up, source references, and evidence note.

Historical PRs establish the same ownership:

- PR #343 added P125 as the distinct H&H daily ticket-tracking owner.
- PR #377 strengthened P125 after observed Copilot period/window failures.
- Both rejected creating overlapping ticket-harvest owners where P125 already covered the mission.

### 2.2 Current gap

P125 currently terminates at a **ticket-level digest**. It does not define a deterministic data contract or require mutation of the current tracker.

No current `main` owner was found for:

- `ticket_update.v1`;
- screenshot-to-ticket parsing;
- deterministic tracker-row merge;
- a reusable ticket-ingestion engine;
- shared spreadsheet + local-web backend semantics for ticket data.

Therefore this is not another “search Outlook/Teams better” problem. It is the missing seam between **ticket evidence reconciliation** and **durable tracker mutation**.

### 2.3 Existing owners that must be reused

| Concern | Existing owner | Required disposition |
|---|---|---|
| H&H ticket evidence discovery and semantic reconciliation | P125 | STRENGTHEN |
| Generic context -> create/update/repair artifact | P56 | REUSE / route |
| Repo <-> Google Drive mapping, stable identity, readback | P111 | REUSE |
| Prompt ID / strengthen-before-add | P79 | NO NEW ID at planning floor |
| Repeated workflow failures | P13 | SYSTEMIC prevention owner |
| Negative + positive retained regressions | P94 | RETAIN |
| Workbook structure / artifact safety | existing Triage artifact-engine contracts | REUSE |
| Local application surface | current repository app/runtime patterns | INSPECT THEN EXTEND |
| ServiceNow authoritative record mutation | no proven owner in this repo | EXTERNAL / future adapter; do not invent |

---

## 3. P79 disposition

### Decision

**STRENGTHEN P125. DO NOT ADD A NEW PROMPT ID FOR THIS use case.**

P125 already owns the H&H ticket lifecycle from discovery through normalized ticket-level reconciliation. The missing behavior is:

1. accept additional intake modalities beyond Outlook/Teams when the operator supplies them directly;
2. emit a machine-consumable normalized batch in addition to the human digest;
3. route requested tracker mutation through a deterministic repository capability;
4. require post-mutation readback/proof;
5. preserve P56/P111 ownership rather than absorbing artifact or Drive synchronization mechanics.

The deterministic ticket-ingestion engine is **product/harness behavior, not a prompt identity**.

### Future admission boundary

A later generic prompt may be justified only if multiple non-H&H domains need an operator-facing “ingest ticket evidence into tracker” workflow and P79 proves that generic mission cannot be cleanly composed from P125 + P56 + existing owners.

Until then:

- P125 = H&H domain front door;
- deterministic engine = reusable implementation;
- P56 = generic artifact update coordinator;
- P111 = Drive synchronization owner.

---

## 4. Canonical data model

Implementation should introduce the smallest versioned machine contract needed to separate extraction from mutation.

Recommended initial family:

`ticket-observation/v1` -> `ticket-update-batch/v1` -> `ticket-merge-receipt/v1`

Exact filenames/paths must follow repository conventions discovered by the implementation sprint; the semantic fields below are the required behavior.

### 4.1 Source observation

A source observation records **what one source visibly or textually established**, without tracker mutation.

Minimum fields:

- `observation_id` — deterministic run-local identity;
- `source_kind` — screenshot / pasted_text / p125_digest / outlook / teams / api / other;
- `source_ref` — privacy-safe reference to the source object when durable;
- `observed_at`;
- `ticket_id_raw`;
- `identifier_type` — INCIDENT / REQUEST / CASE / REFERENCE / UNKNOWN;
- `facility_raw`;
- `room_wing_raw`;
- `configuration_item_raw`;
- `assignment_group_raw`;
- `caller_requester_raw`;
- `priority_raw`;
- `summary_raw`;
- `description_raw`;
- `reported_date_raw`;
- `status_raw`;
- `assignee_raw`;
- `other_labeled_fields`;
- `field_evidence` — source coordinate/text span or equivalent proof pointer;
- `extraction_confidence` by field when the adapter can provide it;
- `parse_warnings`;
- `source_hash` or stable source identity when safe/available.

The parser must preserve raw labels and raw text before normalization.

### 4.2 Normalized ticket update

A normalized update is the deterministic merge input, not raw OCR output.

Minimum semantic fields:

- normalized ticket/incident ID;
- identifier type;
- facility/site;
- room/wing/location detail;
- configuration item;
- assignment group;
- requester/relay/caller;
- priority;
- issue/summary;
- description;
- reported timestamp;
- Date Received / first-seen evidence;
- current evidence state;
- current assignee/owner only when supported;
- latest relevant update;
- next follow-up;
- source references;
- evidence note;
- data-quality flags;
- conflict set;
- field-level provenance;
- batch/source chronology.

### 4.3 Per-column disposition

The engine must **not** equate “populate every tracker column” with “invent a value.”

For every current tracker column, the merge plan records exactly one disposition:

- `SET_FROM_SOURCE`
- `SET_FROM_DETERMINISTIC_RULE`
- `PRESERVE_EXISTING_STRONGER_VALUE`
- `PRESERVE_EXISTING_SAME_VALUE`
- `BLANK_UNSUPPORTED`
- `CONFLICT_REVIEW_REQUIRED`
- `NOT_APPLICABLE`

No tracker column may silently disappear from the merge receipt.

This makes “all columns handled” machine-testable while preserving evidence discipline.

---

## 5. Source adapter architecture

All intake modalities must converge on the same source-observation contract.

### 5.1 Screenshot adapter

Mission:

- accept one or many operator-supplied ticket screenshots;
- extract labeled incident fields;
- keep multiple ticket cards/screenshots separate;
- tolerate layout variants without using positional guesses as truth;
- never promote low-confidence/unlabeled text into a definitive tracker value;
- emit source observations only.

Implementation requirements:

1. preserve screenshot bytes outside tracked Git;
2. sanitize fixtures for repository tests;
3. parse text/labels through one bounded vision/OCR adapter interface;
4. separate **recognition** from **semantic normalization**;
5. retain raw recognized text and field confidence in runtime receipts, not public source when private;
6. support multiple incidents per batch;
7. detect repeated screenshot/source input idempotently when source identity permits;
8. route uncertain fields to flags rather than guesses.

The local implementation must not depend on a single cloud vision provider. Use an adapter boundary so a local OCR/vision engine can replace a hosted parser without changing the merge contract.

### 5.2 Pasted-list adapter

Accept batches such as:

```text
INC007601825
INC007601841
INC007601820
...
```

Requirements:

- normalize whitespace/case;
- preserve duplicates in the source receipt while collapsing them in the candidate identity set;
- report duplicate counts explicitly;
- never invent missing ticket metadata;
- reconcile IDs against existing tracker before insert.

### 5.3 P125/Copilot adapter

P125 should emit a machine-consumable normalized batch in addition to its human digest.

Requirements:

- same resolved period/source-coverage semantics already owned by P125;
- same identifier/status non-conflation rules;
- source references survive into the normalized packet;
- unresolved/provisional records remain provisional;
- no direct tracker mutation by prompt prose;
- when the user requested tracker update, route packet to the canonical ticket-ingestion engine.

### 5.4 Future ServiceNow/API adapter

ServiceNow may eventually become the strongest source for selected fields, but this plan does **not** assume credentials, API availability, or mutation authority.

The future adapter must:

- declare read/write authority separately;
- map provider fields into the same observation contract;
- never silently outrank an explicit authority matrix merely because it is “live”;
- preserve API/provider receipt identity;
- keep ticket-ingestion semantics independent of provider transport.

---

## 6. Identity, deduplication, and non-conflation kernel

This is the highest-risk deterministic layer.

### 6.1 Strong identity

When an explicit supported incident ID exists, canonical identity is:

`<identifier_type>:<normalized_id>`

For normal ServiceNow incidents:

`INCIDENT:INC#########`

Normalization may remove harmless whitespace/case variance; it must not repair or guess a materially malformed ID without a flagged rule.

### 6.2 Duplicate classes

Classify duplicates separately:

- `DUPLICATE_WITHIN_SOURCE_BATCH`
- `DUPLICATE_ACROSS_BATCH_SOURCES`
- `ALREADY_PRESENT_IN_TRACKER`
- `POSSIBLE_DUPLICATE_PROVISIONAL`
- `NOT_DUPLICATE`

A repeated ID may contribute newer evidence even when no new row is inserted.

### 6.3 Provisional identity

When no strong ID exists, generate a provisional identity from bounded evidence, but never auto-merge on that identity alone when ambiguity remains.

Site + issue + time/thread/source may produce:

`PROVISIONAL:<fingerprint>`

It remains explicitly provisional until a strong identifier is discovered.

### 6.4 Non-conflation rules

The engine must reject automatic merging based solely on:

- same facility/site;
- same kiosk/device type;
- same requester;
- same date;
- similar issue wording;
- same room if ticket IDs differ;
- same source thread when multiple explicit incidents appear.

Two explicit distinct incident IDs are distinct records even when every other field matches.

### 6.5 Conflict model

Conflicting evidence is retained field-by-field:

```json
{
  "field": "facility",
  "existing": "...",
  "incoming": "...",
  "existing_source": "...",
  "incoming_source": "...",
  "resolution": "PRESERVE_AND_FLAG"
}
```

Recency alone is not a universal winner. Authority + source semantics + chronology determine deterministic precedence where a contract exists; otherwise flag.

---

## 7. Tracker merge semantics

### 7.1 Discover tracker schema at runtime

Do not hard-code one workbook column set as universal.

The adapter must:

1. identify the canonical tracker/table/sheet;
2. read current headers/schema;
3. map canonical ticket fields to existing columns through a versioned column-map contract;
4. fail clearly on unknown required columns or duplicate headers;
5. disposition every existing column.

### 7.2 New-ticket insertion

For a strong ticket ID not already present:

- insert exactly one row;
- use the tracker’s contracted intake position (for current H&H workbook behavior, preserve reserved intake space/top-row semantics rather than appending arbitrarily);
- set Date Received from supported intake chronology;
- set initial status only from the tracker contract — e.g. `Open` when the ticket is genuinely new and no stronger status evidence exists;
- populate every supported column;
- leave unsupported fields blank with receipt disposition;
- preserve formulas, styles, validations, tables, filters, and workbook structure.

### 7.3 Existing-ticket update

When the ticket already exists:

- do not insert another row;
- compare field-by-field;
- apply only contract-authorized changes;
- preserve stronger existing values where incoming evidence is weaker;
- add newer evidence/status only when it represents a supported state transition;
- never “re-open” or “close” by inference;
- record before/after values in the merge receipt.

### 7.4 Idempotency

Applying the same normalized batch twice to the same tracker version must yield:

- zero duplicate rows;
- zero unsupported field churn;
- deterministic no-change dispositions;
- the same logical tracker state.

Idempotency is a release gate.

---

## 8. Backend architecture

The canonical ticket model and merge kernel must be backend-independent.

### 8.1 Excel / workbook adapter — first production target

The first deterministic backend should target the existing H&H tracker workbook because that is the current operational artifact.

Implementation must reuse Triage workbook safety patterns:

- private workbook stays outside Git;
- sanitized/minimal fixtures only;
- source preservation / backup before permitted mutation;
- structure-preserving workbook edit path;
- table/header identity checks;
- formula/style/data-validation preservation;
- before/after row count and unique-ID checks;
- workbook-level validation;
- artifact/readback receipt.

Do not pick openpyxl, Excel COM, Office Script, or another mechanism by preference alone. The implementation sprint must inspect the actual workbook features and existing repository helpers and choose the least-destructive owner compatible with Excel Desktop + Excel for Web requirements.

### 8.2 Local engine CLI/library

The deterministic implementation should expose one stable non-UI seam first, e.g.:

```text
ticket-ingest parse
ticket-ingest reconcile
ticket-ingest apply
ticket-ingest verify
```

Exact CLI names are provisional until repository inspection.

Required characteristics:

- JSON in/out contract;
- deterministic exit codes;
- dry-run / plan mode before mutation;
- same merge kernel for every frontend;
- runtime receipts under approved `Outputs/` path;
- no hidden provider write during parse/reconcile.

### 8.3 Local website

The website is a **projection/controller over the same engine**, not a second database implementation.

The current repo already has a Python application surface; implementation must inspect whether extending that surface is appropriate before creating another web framework.

Desired UX:

1. select/open current tracker profile;
2. drag/drop screenshot(s) or paste ticket IDs/details;
3. show parsed candidate tickets;
4. show NEW / EXISTING / CONFLICT / PROVISIONAL classification;
5. preview exact row/field changes;
6. apply;
7. show readback proof and cloud-link handoff.

The website must call the canonical library/CLI contract. No duplicated dedupe/merge logic in UI code.

### 8.4 Local data store

If a web UI needs working state, use a small structured local store only as a runtime cache/intake queue unless a later design explicitly promotes it to authority.

The workbook/current project tracker remains authoritative according to the active profile until an explicit migration changes authority.

---

## 9. Drive / provider synchronization

When the tracker has an established Google Drive identity:

1. resolve the current mapped artifact before mutation;
2. operate on the correct authority/export according to P111;
3. update in place rather than create `copy`, `(1)`, or another CURRENT tracker;
4. read back the Drive identity/version;
5. return the Drive link as the primary operator-facing tracker artifact when the Drive mapping is healthy;
6. return local/download representation as supplemental.

The ticket-ingestion engine must not reimplement P111.

The merge receipt should carry a safe sync handoff key such as:

- logical artifact ID;
- local post-merge hash/version;
- required provider action;
- expected stable provider identity.

P111 consumes that handoff and owns provider proof.

---

## 10. P125 strengthening target

P125 should remain operationally readable. Do not paste the entire engine specification into the prompt.

Protected edit must go through P79 / `scripts/prompt_registry_ops.py`.

### Required semantic additions

P125 should:

1. accept operator-supplied screenshots, pasted incident lists, copied ticket detail, and prior normalized batches as valid intake evidence in addition to Outlook/Teams;
2. preserve its existing Outlook/Teams source-coverage rules when those sources are in scope;
3. emit a machine-consumable normalized ticket batch when a tracker update is requested;
4. state that all fields are evidence-bound and missing values stay unknown/blank rather than inferred;
5. require explicit duplicate classification against both the incoming batch and existing tracker;
6. require field-level non-conflation/conflict preservation;
7. route tracker mutation through the canonical deterministic ticket-ingestion capability / P56 artifact owner;
8. route cloud publication/readback through P111;
9. require post-apply receipt: input count, unique candidate IDs, existing IDs, inserted IDs, updated IDs, duplicates ignored, provisional/conflicts, tracker row count, unique tracker ID count, and per-column disposition summary;
10. not append repository closeout noise to an ordinary operational run unless repo work was explicitly requested.

### Suggested lightweight embedded contract

> When the operator supplies ticket screenshots, pasted incident IDs/details, or asks to update the current tracker, treat those as additional H&H intake evidence. Normalize them into the canonical ticket-update batch, reconcile explicit incident identity against both the batch and current tracker, preserve conflicts and provisional identities, and route mutation through the repository-owned ticket-ingestion/artifact owner. Every tracker column must receive an explicit evidence/derived/preserve/blank/conflict disposition; do not invent missing values. Read back the resulting tracker, prove unique IDs/no duplicate insertion, and route mapped Drive synchronization through P111. Keep discovery/evidence semantics in P125; do not implement spreadsheet/storage mechanics in prompt prose.

---

## 11. Retained regression matrix

The implementation program must retain sanitized negative and positive cases.

Minimum cases:

1. **single screenshot / new ID** -> one new row, supported fields populated, unsupported columns explicitly blank;
2. **same screenshot twice** -> second application inserts zero rows;
3. **pasted list contains repeated IDs** -> one candidate per unique ID, duplicate count preserved;
4. **batch ID already in tracker** -> no duplicate row;
5. **existing ticket receives newer status evidence** -> update state only when transition is supported;
6. **same site + different incident IDs** -> two records;
7. **same issue text + different incident IDs** -> two records;
8. **one screenshot contains two incident cards** -> two observations, no cross-field bleed;
9. **two screenshots of same incident with complementary fields** -> one ticket update with provenance from both;
10. **two screenshots of same incident with conflicting facility/status** -> conflict retained, no silent winner without precedence contract;
11. **case/reference identifier** -> not relabeled to ServiceNow incident;
12. **coordination-only chat** -> not inserted as ticket;
13. **reported “done” without closure proof** -> COMPLETION_REPORTED, not CLOSED;
14. **missing Date Received** -> derived only when intake chronology contract supports it, otherwise blank/flagged;
15. **new ticket with no later status evidence** -> contracted initial Open state;
16. **existing closed ticket + weak new intake mention** -> preserve stronger state; do not reopen;
17. **all tracker columns** -> each column has a disposition in receipt;
18. **unknown required tracker header** -> fail closed before mutation;
19. **workbook formulas/styles/validation** -> unchanged outside intended cells/rows;
20. **top intake reservation** -> committed records never consume reserved blank intake rows incorrectly;
21. **batch with 10–15 new tickets plus repeats** -> correct unique insert/update counts;
22. **cross-reference two independently generated ticket lists** -> exact missing/extra/common identity sets;
23. **local apply followed by Drive sync** -> same logical tracker identity, no duplicate Drive workbook;
24. **Drive unavailable** -> local result may exist but sync remains BLOCKED, never “synced”;
25. **website and CLI apply same batch from same baseline** -> logically identical resulting ticket state;
26. **parser low-confidence field** -> flagged/blank, never guessed into tracker;
27. **private screenshot fixture boundary** -> no raw private image/text enters tracked Git;
28. **re-run after no-op** -> deterministic no-change receipt.

The historical operator-visible failure family should be represented by synthetic fixtures that mimic the shape of real batches without persisting private ticket content.

---

## 12. Sprint sequence

### TTI-0 — Forensics + contract floor

**Mission:** turn repeated manual workflow corrections into a repository contract before implementation.

**Owned:**

- this plan;
- a sanitized use-case/evidence matrix;
- canonical owner map;
- proposed contract schemas;
- work-queue indexing.

**Gate:**

- P125/P56/P111/P79/P13/P94 boundaries explicit;
- no duplicate current owner found;
- no raw H&H screenshot bytes committed;
- implementation inputs/outputs and proof ceiling unambiguous.

### TTI-1 — Ticket observation + update schemas

Implement versioned schemas and fixtures for:

- source observation;
- normalized update batch;
- merge receipt.

Add validators.

**Gate:** malformed/ambiguous identities, unsupported field promotion, missing per-column disposition, and duplicate canonical ticket IDs fail.

### TTI-2 — Identity / dedupe / conflict kernel

Implement pure deterministic reconciliation independent of workbook/web UI.

**Gate:** regression matrix identity cases pass; applying a batch twice is idempotent.

### TTI-3A — Screenshot/pasted-text intake adapters

Build source adapters that emit observation contract.

Parallel-safe with TTI-3B after TTI-1/TTI-2 interface stabilizes.

**Gate:** sanitized screenshot/text fixtures parse to expected observations; low-confidence and absent fields remain flagged.

### TTI-3B — Tracker schema + merge planner

Read current tracker headers and produce exact row/column action plan without mutating.

**Gate:** every tracker column dispositioned; duplicate/conflict behavior deterministic.

### TTI-4 — Excel backend

Apply validated merge plan to a workbook fixture and then protected private operational workbook in observed acceptance.

**Gate:** structure preserved; row/unique-ID counts correct; all intended fields/readback match; source untouched or approved backup retained.

### TTI-5 — P125 protected strengthening

Run P79 prior-art/owner check, then `prompt_registry_ops.py edit` against P125.

Update focused `tests/test_hh_ticket_tracking_prompt.py`, semantic/source-history/profile records required by current lifecycle, and generated Prompt Kit parity.

**Gate:** no new prompt ID; existing P125 semantics preserved; new intake/update routing retained in deterministic floor.

### TTI-6 — Local CLI + application UI

Expose the shared engine through a stable CLI/library and a local web/app surface.

**Gate:** UI performs no independent merge logic; CLI/UI produce equivalent logical result; dry-run preview matches applied receipt.

### TTI-7 — P111 / Drive handoff integration

Publish/update the established tracker identity through P111.

**Gate:** stable Drive identity reused; readback proves current version; Drive link returned; no duplicate CURRENT workbook.

### TTI-8 — Observed H&H acceptance

Use a real operator-controlled daily intake batch.

Acceptance packet:

- number of source items/screenshots;
- parsed observations;
- unique strong IDs;
- duplicates in batch;
- already-present tracker IDs;
- inserted IDs;
- updated IDs;
- unresolved/provisional/conflict IDs;
- post-apply row count;
- post-apply unique-ID count;
- duplicate count = 0;
- selected field/readback checks;
- mapped cloud identity/version;
- operator-visible Drive link.

This is the first stage allowed to claim the workflow works on real H&H data.

### TTI-9 — Generalization decision

Only after H&H runtime success:

- assess whether another ticket domain can consume the same engine;
- if yes, keep the engine generic and add a domain profile/adapter;
- ask P79 again whether a generic prompt identity is actually useful;
- do not generalize before there is a second real consumer.

---

## 13. Parallel execution map

After TTI-1 and TTI-2 stabilize the contracts, the work graph can widen.

| Lane | Dependencies | Owned scope | Forbidden scope | Return artifact |
|---|---|---|---|---|
| A — screenshot/text adapters | TTI-1, TTI-2 interfaces | parsers + sanitized fixtures | workbook writes, P125 mutation | observation fixtures + parser tests |
| B — tracker merge planner | TTI-1, TTI-2 | column map + dry-run planner | image parsing, Drive | merge-plan fixtures + tests |
| C — P125 strengthening prep | TTI-0 owner map | candidate wording + focused test delta | protected mutation until engine contract exists | P79 edit packet |
| D — UI spike | stable engine API from TTI-2 | read-only prototype consuming engine API | duplicate merge implementation | UI call-stack proof |

Convergence owner integrates A+B before Excel mutation. C must not land before the implementation owner exists, or P125 would promise behavior the repo cannot execute.

---

## 14. Safety / privacy boundaries

- Real H&H screenshots and private workbook bytes are runtime/private evidence, not public Git fixtures.
- Tracked fixtures must be synthetic or safely sanitized.
- Do not persist phone numbers, caller names, internal URLs, account identifiers, or other private fields merely to reproduce parser logic.
- No ServiceNow credentials/tokens in repo, logs, fixtures, receipts, or prompts.
- Screenshot parsing does not prove ServiceNow authoritative truth.
- Communication evidence does not prove closure unless the source establishes it.
- Local engine must not upload screenshots to an external provider silently; adapter/provider choice is explicit.
- Provider/cloud writes remain behind P111 or another canonical provider owner.
- Never overwrite a private source workbook merely because a generated candidate exists.

---

## 15. Observability and receipts

Every ingestion run should produce a machine-readable private/runtime receipt with at least:

- run ID;
- engine/schema versions;
- source count by kind;
- source hashes/identities when safe;
- parsed observation count;
- unique strong IDs;
- provisional IDs;
- duplicate counts by class;
- tracker baseline identity/version/hash;
- candidate insert/update/no-change/conflict counts;
- per-column disposition summary;
- post-write tracker identity/version/hash;
- post-write row count;
- post-write unique ticket-ID count;
- validator results;
- provider sync disposition;
- proof ceiling.

A human summary is derived from this receipt.

The receipt must never call a skipped provider/readback gate PASS.

---

## 16. Done definition

The whole program is complete only when:

1. P125 is strengthened through protected lifecycle tooling with no duplicate prompt identity.
2. A versioned ticket observation/update/merge contract exists.
3. Screenshot + pasted-text sources can produce normalized observations.
4. Explicit ticket identity and non-conflation rules are implemented in code.
5. Existing tracker schema is introspected rather than assumed.
6. Every tracker column receives an explicit merge disposition.
7. New tickets insert exactly once.
8. Existing tickets update without duplicate rows.
9. Same batch replay is idempotent.
10. Workbook structure-preservation tests pass.
11. CLI/library and local website consume the same merge kernel.
12. Private screenshots/workbooks remain outside Git.
13. P111 reuses and read-backs the established Drive tracker identity.
14. Final operator handoff includes the canonical Drive link when mapped.
15. Sanitized recurrence fixtures are registered in the deterministic floor.
16. A real H&H batch is observed end-to-end with zero duplicate tracker IDs.
17. Mainline integration is verified.
18. Static/CI proof is not mislabeled as ServiceNow/Copilot/live acceptance.

---

## 17. Repository ownership decision

This plan belongs canonically in **web-excel-repair-triage** because that repository already owns:

- Prompt Kit P125;
- artifact generation/repair infrastructure;
- workbook safety contracts;
- local application surfaces;
- deterministic validators/harness;
- P56/P111 routing semantics.

A separate NYC H&H repository does **not** need a competing copy of this plan merely for project context.

If another repository later becomes the actual H&H runtime/data owner, add a thin handoff/reference there that points to this canonical plan and pins the required contract version. Do not fork the specification.

---

## 18. First executable successor sprint

**Owner:** TTI-1 repository implementation agent
**Base:** refresh current `main`; do not assume this planning SHA remains the implementation floor
**Dependency:** this plan integrated or otherwise accepted as canonical planning authority
**First action:** inspect current schema/contract/validator naming conventions and create the smallest versioned `ticket-observation`, `ticket-update-batch`, and `ticket-merge-receipt` contracts plus sanitized positive/negative fixtures and validators.
**Forbidden:** P125 canonical mutation, private H&H bytes, workbook mutation, Drive mutation.
**Expected proof:** schema validators reject duplicate strong IDs, unsupported promoted values, malformed provenance/conflict state, and incomplete per-column dispositions while accepting representative screenshot/list/P125 normalized batches.
**Completion gate:** TTI-1 contracts and fixtures pass focused tests and are registered in repository discovery/harness; then TTI-2 may implement the pure reconciliation kernel.

---

## 19. Operator-facing end state

The desired daily experience is:

1. operator sends screenshots or pastes incoming ticket IDs/details;
2. engine says what it recognized and what remains uncertain;
3. engine cross-checks the current tracker;
4. duplicates are identified automatically;
5. distinct tickets stay distinct;
6. every tracker column is populated, preserved, blanked, or flagged by explicit rule;
7. a dry-run shows exactly what will change;
8. apply updates the one canonical tracker;
9. readback proves no duplicate IDs and confirms inserted/updated rows;
10. cloud synchronization updates the existing Drive tracker;
11. response gives the operator the current tracker link and concise intake receipt.

No repeated explanation of the workflow should be necessary.

---

## 20. Prompt Kit routing now, before the deterministic engine exists

There are two different questions that must not be conflated:

### Which prompt owns the H&H ticket semantics?

**P125 · Health + Hospitals Ticket Discovery & Tracking Harvester.**

Use P125 as the canonical source for:

- incident/ticket identity semantics;
- Outlook/Teams reconciliation;
- source coverage;
- duplicate/non-conflation rules;
- status/evidence boundaries;
- normalized H&H ticket fields;
- open/follow-up/completion/closure distinctions.

### Which prompt can own the actual screenshot -> existing tracker artifact update today?

**P56 · Context-to-Artifact Generator**, with P125 semantics as the domain contract and P111 for Drive synchronization.

P56 already owns:

- recovering the current screenshots/files/conversation corrections;
- resolving UPDATE_EXISTING vs CREATE_NEW;
- binding the canonical tracker artifact;
- reusing the existing generator/schema/provider identity;
- generating/updating the actual artifact;
- running artifact checks;
- routing the durable provider handoff.

### Interim composition

Until TTI-1..TTI-5 land:

```text
operator screenshots / pasted IDs / ticket detail
    |
    v
P125 semantic rules
(identity, status, dedupe, non-conflation, evidence discipline)
    |
    v
P56 UPDATE_EXISTING
(recover current tracker + map evidence into artifact without inventing fields)
    |
    v
readback / duplicate-count / row-count / field verification
    |
    v
P111
(reuse mapped Drive identity, update/read back, return canonical link)
```

Important boundaries:

- Do not claim P125 executed Outlook/Teams searches when those providers were not actually queried. Screenshot-only intake may reuse P125's ticket semantics without fabricating source coverage.
- Do not let P56 invent ticket-specific precedence rules; use the P125 contract/current tracker evidence and preserve unknowns/conflicts.
- Do not create a new tracker because P56 can generate files. The normal intent for the current H&H tracker is UPDATE_EXISTING.
- Do not call a local workbook result Drive-synced until P111/provider readback proves the mapped identity.
- When the deterministic ticket-ingestion engine lands, P56 should discover/route to that canonical owner instead of performing ad-hoc row logic.

### Practical current invocation target

For a screenshot batch whose purpose is **“put these incoming tickets into my existing tracker now”**, start with **P56**, explicitly binding:

- target = current H&H ticket tracker;
- intent = UPDATE_EXISTING;
- domain semantics = P125;
- input evidence = current screenshots/lists plus relevant prior tracker corrections;
- acceptance = no duplicate ticket IDs, no conflation, all tracker columns dispositioned, unsupported fields not guessed, post-write readback;
- provider handoff = P111.

For a task whose purpose is **“search Outlook/Teams and tell me what H&H tickets are new/changed”**, start with **P125**.

After TTI-5, P125 should be able to emit the normalized machine packet directly and trigger the same deterministic update path when the operator asks for tracker mutation.
