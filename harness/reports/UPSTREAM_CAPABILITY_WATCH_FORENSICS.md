# Upstream Capability Watch Forensics — Missed Matt Signal

**Repository floor:** `main@b9089975e5dd87bc710102b4d35af54e4c499709`  
**Canonical plan:** `docs/plans/UPSTREAM_CAPABILITY_WATCH_SPRINT_MAP.md`  
**Forensic lane:** U0A — Missed teach forensic classification  
**Evidence class:** repository/provider/runtime-history evidence  
**Result:** PROVEN forensic classification; implementation remains successor work.

## Question

Classify the missed upstream signal without forcing one root cause:

- `SOURCE_UNWATCHED`
- `POLL_NOT_SCHEDULED`
- `IDENTITY_DETECTION_GAP`
- `IMPACT_EDGE_MISSING`
- `VISIBILITY_GAP`

The incident anchor was that Matt Pocock's work changed and the local teaching workflow appeared to be left behind. The forensic pass must distinguish an upstream repository change from a proven change to Matt's `productivity/teach` skill.

## Evidence floor

1. `mattpocock-skills` is registered in `harness/contracts/operant-external-resource-intake.v1.json` for `mattpocock/skills`, default branch `main`, root `skills`, nested `SKILL.md` enumeration.
2. Refresh configuration is daily with provider schedule `37 5 * * *`; canonical command is `python scripts/sync_operant_external_resources.py`.
3. Provider run history proves the scheduled workflow executed repeatedly. Relevant run `35332457839` started 2026-09-18T10:00:22Z and failed at **Compare live donor candidate with tracked projection** after candidate generation and canonical validation both passed.
4. Run `35332457839` uploaded artifact `10541966248`, preserving `resources.v1.json` and `gaps.v1.json`.
5. At that run's repository head `33a2296426c018c6652b6d925a434274f39b1b33`, tracked Matt floor was `959a8e9f1edc3adbe2f7e3054bb6fbefa6696260` with 37 resources.
6. The live candidate artifact resolved Matt to `74ca5fe077456a0b3b2f5310cf9430999fd0b5fd` with 38 resources and added `mattpocock-skills:in-progress/pr`.
7. Upstream compare `959a8e9...74ca5fe` changes only the new PR-skill surfaces; it does not modify `skills/productivity/teach/SKILL.md`.
8. Upstream compare `74ca5fe...c55ee46` modifies only `skills/in-progress/pr/SKILL.md`.
9. The `productivity/teach` blob SHA is `c679eeccd48ca720c8196e5d9a9e58223abf213b` at the September 10, September 16, and September 18/20 donor floors inspected in this sprint.
10. Current external-resource projection pins Matt at `c55ee46073ed923f86ce59a5eb3b6d895095d1b7`; `mattpocock-skills:productivity/teach` remains `POINT_TO_EXTERNAL`, `target_id: null`, `REVIEW_ADD_PROMPT`.
11. `scripts/sync_operant_external_resources.py` reads each Git-tree item's blob SHA to enumerate files but emits resource rows with the **repository `source_sha`**, not the individual resource blob SHA.
12. `.github/workflows/operant-external-resource-refresh.yml` has `contents: read`; scheduled behavior builds a candidate, validates tracked canonical projection, compares files, and uploads evidence. It has no P115 dispatch or user-notification step.
13. `scripts/prompt_kit_afk_signal_router.py` supports prompt feedback/vote/usage and Operant friction classes; it has no upstream-capability change event class.
14. Open PR #615 currently owns `.ai/WORK_QUEUE.md`; this lane intentionally does not mutate that shared file.

## Disposition matrix

| Disposition | Result | Evidence | Consequence |
|---|---|---|---|
| `SOURCE_UNWATCHED` | **FALSE** | Matt source and `productivity/teach` are registered and projected. | Missing donor registration was not the incident cause. |
| `POLL_NOT_SCHEDULED` | **FALSE** | Daily schedule is configured and scheduled runs are observed, including run `35332457839`. | Scheduler absence was not the incident cause. |
| `IDENTITY_DETECTION_GAP` | **CONFIRMED DEFECT** | Per-resource rows persist donor repo `source_sha`, not the Git blob/content identity. Stable `teach` is revision-churned whenever unrelated Matt commits move the repo floor. | Polling can detect donor drift but cannot precisely attribute which capability changed. |
| `IMPACT_EDGE_MISSING` | **CONFIRMED DEFECT** | Current `teach` coverage has `target_id: null`; no deterministic P96/P98/P65 impact edge exists. | A detected source change cannot deterministically identify the local teaching owners to evaluate. |
| `VISIBILITY_GAP` | **CONFIRMED DEFECT — earliest proven post-detection break** | Scheduled run `35332457839` detected candidate/tracked drift and uploaded evidence, but the workflow and P115 router contain no upstream-change route or user signal. | The system detected drift yet had no path that would bring the change to the user's attention or open bounded AFK review work. |

## Incident correction

The evidence does **not** support the statement that Matt's `productivity/teach` file itself changed during the observed September drift window. The confirmed upstream change was the addition and subsequent refinement of `skills/in-progress/pr/SKILL.md`.

Therefore the durable incident statement is:

> Matt's registered upstream repository changed; the scheduled watcher detected drift, but the system had no capability-level identity, no deterministic impact edge into local teaching owners, and no P115/user-visible drift route. The local teaching workflow may still warrant semantic comparison against broader upstream practices, but U0A does not claim that it missed a direct `teach` file revision.

## Failure boundary

The first **proven** break after successful detection is `VISIBILITY_GAP`:

`scheduled poll -> candidate built -> tracked projection validated -> drift detected -> artifact uploaded -> STOP`

There is no next edge to:

`upstream_capability.changed -> impact resolution -> P115 work request -> user-visible review state`

Because scheduled run history is now available, this is stronger than the earlier planning assumption that due-time execution was unknown.

## Independent defects that must still be repaired

### 1. Capability identity precision

Persist both:

- repository revision/provenance, and
- per-capability immutable identity (Git blob SHA/content digest for `SKILL.md` resources).

A repository revision change with an unchanged capability identity must not be represented as that capability changing.

### 2. Observed versus processed state

Preserve the plan invariant:

- `last_observed_identity` advances when the poll sees a new capability identity;
- `last_processed_identity` advances only after the durable change event and required routing checkpoint succeed.

A routing crash may not silently consume the event.

### 3. Impact edges

Add a deterministic mapping layer from upstream capability identity to local evaluation owners. Zero-edge events remain durable and diagnosable; they are not dropped.

### 4. Visibility / AFK routing

Add a bounded upstream-capability event class and route actionable impacted changes into P115 without giving the poller prompt-mutation, merge, or promotion authority.

### 5. Promotion boundary

External change is evidence. It does not prove local adoption is correct. P79/current canonical owners still decide strengthen/add/reject, and integration remains gated.

## Proof ceiling

**PROVEN:** donor registration, schedule configuration, actual scheduled execution, September 18 drift detection, uploaded candidate artifact, tracked-vs-live Matt floor difference, added `in-progress/pr` skill, absence of a `teach` file change in the inspected upstream intervals, repo-SHA identity granularity, missing `teach` impact target, and absence of P115/user routing in the scheduled workflow.

**UNPROVEN:** which broader Matt mechanics should change P96/P98/P65, whether any local teaching prompt is semantically stale, live AFK delivery after a future repair, and user-visible Capability Radar behavior.

## Next transition

U1 owns the next implementation gate: inspect and extend existing canonical contracts first to encode per-capability identity, observed-vs-processed state, dedupe, impact-edge semantics, and event/promotion boundaries. A new contract path is permitted only after evidence shows the canonical contracts cannot represent the required state and the dispatch manifest is refreshed accordingly.

Ledger synchronization is deferred because open PR #615 currently owns `.ai/WORK_QUEUE.md`. Reconcile that row only after the shared-file owner releases or incorporates the update.
