# FirstMate + AgentSwitchboard + Prompt Kit Durable Vision & Owner Map

Status: TRACKED PLAN
Canonical repository: `EndeavorEverlasting/web-excel-repair-triage`
Planning floor: `main@b87ad29ea0e78fddb1f26b1f0a10b6efd2c94adb`
Factoring date: 2026-09-19

## Mission

**Target end state:** FirstMate can run in parallel with AgentSwitchboard **while** AgentSwitchboard consumes Prompt Kit prompts, portability panels, and parallel-dispatch manifests as **machine inputs** (not human paste as the primary path).

**Current state:** NOT complete. This vision is explicitly **not claiming live dual-path complete**. The contract floor exists; live lane dispatch and runtime execution remain unproven.

**Completion definition:** FirstMate operates as the canonical crew/session runtime for parallel open analogues; AgentSwitchboard operates as the durable machine consumer of Prompt Kit panels/manifests + bootstrap/policy/evidence surfaces; both can run concurrently without competition or scheduler duplication; observed dual-path execution evidence exists and is independently verifiable.

## Current proof ceiling

### Proven (repository evidence exists)

- **Triage floors through ADP-00:** Prompt Kit prompt registry, parallel-dispatch manifest contract, repository-actions contract, local-proof continuity, billing-artifact safety, operator-delivery semantics, merge-gate doctrine, Evidence Spine architecture (P95), Prompt Compilation program (Sprints 1–6), Prompt Runtime Compliance program foundation.
- **AgentSwitchboard #320 consumer floor @ `a483853d` (merged):** Contract + static tests only. Proof ceiling: contract floor integrated to main. Does **not** prove live lane dispatch, runtime execution, or Cursor Cloud Agent launch.
- **ADP-01 OpenCode capability/readiness (ASB #318 @ `138253d`):** INTEGRATED. Provider launch/readiness probe validated.
- **ADP-02 canonical adapter + config generator (ASB #321 @ `352640136e320a91f85999bf81af2f734fa23016`):** INTEGRATED. P67 placeholder invocation writes neutral result.
- **ADP-03 synthetic interoperability (ASB #322 @ `e1ecaf955e331f45554d444ea3812fdf3198997f`):** INTEGRATED. Action/validation/subagent/parallel/error paths covered; cross-repo consumer contract green.
- **Triage ADP-00 neutral capture authority (PR #598 @ `0733897c`):** INTEGRATED. Versioned neutral capture + evaluator annotation derivation.
- **Protocol v1 contract-only on ASB:** Structural adapter contract exists; runtime execution unproven.

### Unproven (no runtime evidence yet)

- **Live panel→ASB dispatch:** No observed evidence that AgentSwitchboard consumes a Prompt Kit panel/manifest and launches a bounded lane execution in production or evaluation.
- **ADP-04 live smoke (operator workstation):** Blocked on operator provider authentication/workstation configuration. TC01 control/treatment pair with real provider/agent/model unexecuted.
- **ASQ-017 Admin Box physical floor:** Reference identity; not currently proven in Triage evidence.
- **Prompt Kit→FirstMate prompt-dispatch scout:** No observed evidence of FirstMate consuming Prompt Kit lanes as machine input.
- **Observed dual-path (FirstMate + ASB parallel):** No runtime proof that both can operate concurrently on the same or separate lanes without scheduler conflict.

## AUTONOMY_GAP statement

**Gap:** Prompt Kit panels and parallel-dispatch manifests exist as versioned machine-readable transport, but no autonomous execution currently consumes them. Human paste is the operational path; machine ingestion is the target but unproven.

**Closing the gap:** AgentSwitchboard must machine-ingest panels/manifests and execute the bounded lanes they describe, returning typed execution receipts. Panels are the agent-consumable lane-prompt TRANSPORT; they must not be deleted or treated as incidental compatibility.

**Policy truths from #320:** `human_scheduler_allowed: false`, `panel_ingest_required: true`.

## Authority boundaries

| Domain | Owner | Scope | Forbidden |
|---|---|---|---|
| **Prompt Kit (Triage)** | Triage P79 + registry + builders | Doctrine/source of lane prompts, panels, parallel-dispatch manifests, portability surfaces, semantic capabilities, quality history, strength floor | Becoming a scheduler; duplicating FirstMate crew runtime; absorbing AgentSwitchboard consumer authority |
| **AgentSwitchboard** | `EndeavorEverlasting/AgentSwitchboard` | Durable machine consumer of panels/manifests + bootstrap/policy/evidence; human paste is backup only; launches bounded lane execution; returns typed receipts | Becoming a second crew scheduler; replacing FirstMate session runtime; mutating Prompt Kit registry/contracts without explicit Triage reconciliation |
| **FirstMate** | `kunchenguid/firstmate` | Canonical live crew/session runtime; open analogue; parallel execution capability owner | Being replaced by AgentSwitchboard as scheduler; being treated as the Prompt Kit consumer owner (ASB is the durable consumer) |
| **Triage doctrine/proof/contracts** | Triage harness spine | prompt-parallel-dispatch, merge gate, local-proof continuity, Prompt Kit portability, checkpoints, Evidence Spine, billing-artifact safety, operator delivery | Owning live lane dispatch implementation (ASB owns); owning crew scheduling (FirstMate owns) |
| **GitHub provider** | GitHub CI + PR + merge plane | Independent hosted proof; PR/branch/merge operations; remote truth when available | Being the only execution path (local proof + Actions-off continuity exist); being treated as required when provider degradation is expected |

**Standing ADR reference:** `ASB-ADR-2026-09-FIRSTMATE-CREW-RUNTIME` — AgentSwitchboard must NOT become a second crew scheduler. FirstMate is the canonical crew/session runtime. ASB consumes prompts/manifests and launches isolated workers; it does not replace FirstMate's parallel-session authority.

## Owner / phase map

| Phase / Component | Owner | Current status | Next gate | Dependencies |
|---|---|---|---|---|
| **Triage continue-map / local required checks / merge-gate doctrine** | Triage P04/P07 + `.githooks/pre-push` + `scripts/validate_pr_merge_gate.py` | INTEGRATED on main | Continue: local proof execution independent of provider | Prompt Kit contracts, repository-actions, local-proof continuity |
| **ASB triage-consumer floor (#320)** | AgentSwitchboard | INTEGRATED @ `a483853d` | Next: live lane dispatch adapter (g3 ASB-link mutation lane) | Prompt Kit panels/manifests as machine-readable input |
| **ASB-link (g3) durable linkage lane** | g3 (separate owner) | PLANNED / UNPROVEN | Implement live dispatch/execution | #320 contract floor integrated |
| **FirstMate parallel analogue lane** | FirstMate (comparison/crew; not consumer owner) | OPERATIONAL in parallel execution domain | Maintain separation from ASB consumer authority | ASB must not duplicate FirstMate scheduler |
| **Protocol-wire remote-safe observation-adapter** | Runtime-compliance / compute-authority eval | CONTRACT ONLY (adapter-contract.v2.json) | Not Admin Box; not ADP OpenCode; not triage-consumer live-dispatch | Evaluation capture boundary; not operational mutation authority |
| **Vision-map (this document)** | Triage governance + planning | TRACKED PLAN | Advance to CONTRACT FLOOR when live dispatch surfaces stabilize | Durable one-page authority for Agent Flow family + peers |
| **SSH + local execution bridge sprint map** | Triage P04/P07 + AgentSwitchboard local host adapter | Separate program (see `SSH_LOCAL_EXECUTION_BRIDGE_SPRINT_MAP.md`) | Actions-off canary observed | Independent parallel program; not merged into this vision |
| **P67 OpenCode / ADP ladder** | Triage P67 eval + AgentSwitchboard adapter | ADP-01/02/03 INTEGRATED; ADP-04 blocked on operator auth | Execute ADP-04 observed smoke when provider auth available | Compute-authority evaluation program; pointer only from this vision |

## Collision ledger — surfaces this plan MUST NOT mutate

- **AgentSwitchboard `tooling/harness/triage-consumer/**` live-dispatch follow-ons:** Owned by g3 ASB-link lane; this plan indexes only; does not implement.
- **FirstMate scheduler/session semantics:** FirstMate product authority; Triage and ASB must not create competing scheduler.
- **P67/ADP OpenCode ladder (ADP-04+):** Separate evaluation program owner; this vision references only.
- **Generated `web/prompt-kit/index.html`:** Single-writer surface; only canonical Prompt Kit builder may update.
- **`.ai/WORK_QUEUE.md` if owned by open PR:** Check before mutation; PR #524 merged so currently free.
- **Private SSH material / operator credentials:** Never tracked; local boundary only.
- **Prompt Kit frozen Gen1 treatment identities (TRQ-007):** Locked for compute-authority evaluation; no mutation during study.

## Phase ladder with honest gates

```
Phase 0: TRACKED PLAN (this document)
         ↓
         Current state: HERE
         ↓
Phase 1: CONTRACT FLOOR (ASB consumer contract + Triage panels/manifests versioned)
         ↓
         Gate: #320 integrated ✓; live dispatch surfaces stabilize (g3 lane)
         Status: #320 contract integrated; live dispatch UNPROVEN
         ↓
Phase 2: LIVE DISPATCH OBSERVED (ASB consumes one panel, launches lane, returns receipt)
         ↓
         Gate: ADP-04 live smoke completes; observed ASB lane execution with typed receipt
         Status: BLOCKED on operator provider auth + workstation config
         ↓
Phase 3: PARALLEL FIRSTMATE+ASB OBSERVED (both operate concurrently without conflict)
         ↓
         Gate: FirstMate crew session + ASB consumer lane run in parallel; no scheduler duplication
         Status: UNPROVEN
         ↓
Phase 4: COMPLETE (observed live dual-path evidence; independently verifiable)
         ↓
         Gate: Dual-path execution observed + typed receipts + no scheduler conflict + operator verification
         Status: NOT COMPLETE
```

**Mark where we are today:** Phase 0 → Phase 1 transition in progress. #320 contract floor is integrated. Live dispatch surfaces (g3 ASB-link lane) are planned but not operational. No runtime proof yet.

## Definition of done for the whole program

The program is complete only when:

1. **Contract floor stable:** Prompt Kit panels/manifests + AgentSwitchboard consumer contract are versioned, integrated, and stable on both repositories.
2. **Live dispatch observed:** AgentSwitchboard has consumed at least one Prompt Kit panel/manifest, launched a bounded lane execution, and returned a typed execution receipt with exact proof (not synthetic).
3. **Parallel execution proven:** FirstMate crew/session runtime and AgentSwitchboard consumer can operate in parallel (same or separate lanes) without scheduler conflict, duplication, or authority collision.
4. **Typed receipts independent:** Both FirstMate and ASB produce typed execution receipts that can be independently read back by a coordinator (Triage P04/P07 or equivalent).
5. **No false green:** Observed evidence is from real provider/agent/model execution, not synthetic fixtures or static tests alone.
6. **Dual-path independently verifiable:** Operator can observe both paths operating, verify no conflict, and confirm receipts match expectations.

**Must require observed live dual-path evidence, not docs alone.** Plans, contracts, and static tests are necessary floors, but not sufficient proof of the completion state.

## Skills / capabilities / triggers

| Surface | Owner | Trigger | Output / proof |
|---|---|---|---|
| Prompt Kit panels/manifests | Triage registry + builders | Agent requests bounded lane execution | Machine-readable panel JSON + parallel-dispatch manifest |
| AgentSwitchboard consumer | ASB triage-consumer floor | Panel/manifest ingestion required | Typed lane-execution receipt (when live dispatch operational) |
| FirstMate crew runtime | FirstMate | Parallel crew/session execution | Session receipts + parallel lane evidence |
| Local proof continuity | Triage `.githooks/pre-push` + `scripts/validate_pr_merge_gate.py` | Provider degradation (Actions exhaustion, rate-limit, runner unavailable) | Local proof execution + merge continuity without provider block |
| Prompt parallel dispatch | Triage `scripts/prompt_parallel_dispatch.py` | Dependency graph + lane execution | Manifest + dispatch receipt |
| Evidence Spine (P95) | Triage prompt-topology | Outcome receipt + recurrence finding + lifecycle routing | Typed outcome classification + optional next-action recommendation |

## Coordination with related programs

### SSH + Local Execution Bridge Sprint Map

- **Authority:** `docs/plans/SSH_LOCAL_EXECUTION_BRIDGE_SPRINT_MAP.md`
- **Relation:** Parallel independent program. Restores SSH transport + local worker adapter for Actions-off execution. Does not replace or duplicate this vision's dual-path (FirstMate + ASB) scope.
- **Shared contract:** `repository-local-proof-continuity.v1.json` — both programs respect provider degradation continuity.
- **Collision avoidance:** SSH sprint map owns local worker adapter; this vision owns ASB consumer floor + dual-path vision. No overlap.

### P67 Compute-Authority Evaluation (ADP ladder)

- **Authority:** `harness/evals/COMPUTE_AUTHORITY_EVALUATION_SPRINT_PLAN.md`
- **Relation:** ADP-04+ are evaluation phases that test ASB adapter + OpenCode backend. Proof from ADP-04 observed smoke will inform Phase 2 live dispatch readiness for this vision.
- **Current state:** ADP-01/02/03 INTEGRATED; ADP-04 blocked on operator provider auth.
- **Next action from P67:** Execute ADP-04 when operator provider authentication and workstation access are available.
- **Collision avoidance:** P67 owns evaluation + effectiveness verdict; this vision owns production dual-path coordination. Adapter contract is shared seam.

### Prompt Compilation Program

- **Authority:** `harness/prompt-compilation/PROMPT_COMPILATION_SPRINT_MAP.md`
- **Relation:** Provides compiled effective prompts (exhaustive/efficient) as execution-profile metadata. ASB consumer may use compiled prompts when consuming panels; FirstMate may use them in crew sessions.
- **Current state:** Sprints 1–6 INTEGRATED; Compute Mode runtime operational with browser proof.
- **Collision avoidance:** Prompt Compilation owns effective-prompt generation; this vision owns consumer/crew coordination. No scheduler duplication.

## Integration authority

- **Triage main:** This vision map integrated to Triage `main` after local proof + PR gates pass.
- **AgentSwitchboard main:** g3 ASB-link lane integrates live dispatch to ASB `main` under ASB governance.
- **FirstMate:** No integration dependency; FirstMate remains independent parallel runtime.
- **Merge authority:** Triage P04/P07 + `.githooks/pre-push` + `scripts/validate_pr_merge_gate.py` for Triage surfaces; ASB governance for ASB surfaces.

## Forbidden mutations (restated for emphasis)

- Claiming live dual-path complete, live lane dispatch PASS, or green remote checks you did not observe.
- Rewriting SSH sprint map or #320 deliverables.
- Mutating AgentSwitchboard repository, FirstMate product, g3 live-dispatch surfaces, or Voyager ADP-04 without explicit reconciliation authority.
- Treating panels as disposable or incidental; they are the canonical agent-consumable lane-prompt transport.
- Creating a second crew scheduler in Triage or ASB; FirstMate is the canonical crew runtime.
- Promoting synthetic test PASS to observed runtime proof.

## Exact next command

When ADP-04 is unblocked (operator provider auth + workstation config available):

```
Execute ADP-04 (observed adapter smoke) from harness/evals/COMPUTE_AUTHORITY_EVALUATION_SPRINT_PLAN.md §16 adapter phase map
```

When g3 ASB-link lane is ready for live dispatch implementation:

```
Implement ASB triage-consumer live lane dispatch adapter in AgentSwitchboard tooling/harness/triage-consumer/
```

Until then:

```
none; no safe actionable work remains for this vision map document
```
