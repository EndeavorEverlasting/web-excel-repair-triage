# Prompt Topology Phase C — Execution Handoff

**Status:** READY FOR EXECUTION — successor to completed Phase B  
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`  
**Required floor:** refreshed `main` containing Phase A PR #440 and Phase B PR #451  
**Phase B integration commit:** `3bab155714fbd13aa7bdbf0692fc6c7e518756b6`  
**Phase B closeout:** [`PHASE_B_CLOSEOUT.md`](./PHASE_B_CLOSEOUT.md)

This handoff is durable repository state. A future agent should refresh provider/repository truth first, then reconcile this handoff against current `main`. Do not make an old chat or stale worktree a prerequisite for execution.

## Phase C mission

Build the first practical immersive Prompt Topology viewer that **consumes** the accepted Phase A topology and Phase B projection artifacts without becoming a new semantic source of truth.

The viewer should make the prompt system easier for a human to inspect spatially: prompts as stable nodes, discovered semantic relationships as inspectable edges/groups, and the Phase B projection as presentation coordinates. The UI may expose useful topology evidence; it may not rewrite the topology because a visual arrangement looks better.

## Required inputs

Phase C must consume repository-owned outputs rather than reimplement their logic:

- `artifacts/prompt-topology/topology.v1.json` — Phase A renderer-neutral semantic topology;
- `artifacts/prompt-topology/projection-3d.json` — Phase B coordinates;
- `artifacts/prompt-topology/projection-state.v1.json` — Phase B epoch/provenance/integrity state;
- `harness/prompt-topology/schema.v1.json`;
- `harness/prompt-topology/config.v1.json`;
- `harness/prompt-topology/phase-b-projection.v1.json`;
- `harness/contracts/prompt-topology-classifier.v1.json`.

If those generated artifacts are absent, regenerate them through the canonical Phase A/B builders. Do not hand-author coordinates or topology fixtures for production behavior.

## Owned scope

Phase C owns the viewer boundary only. The smallest complete first slice should establish:

1. a repository-owned viewer route/surface resolved from the current web architecture rather than invented in isolation;
2. loading and validating the Phase A + Phase B artifact pair;
3. one rendered node for every projection point, keyed by stable `prompt_id`;
4. meaningful visual grouping/relationship cues derived from existing topology evidence;
5. camera/orbit/pan/zoom interaction appropriate to the chosen viewer stack;
6. prompt selection with inspectable identity and topology evidence;
7. deterministic loading of the accepted projection frame — no aesthetic coordinate jitter or random relayout;
8. fail-closed handling for topology/projection/state mismatch, missing prompt points, duplicate IDs, or stale incompatible artifacts;
9. accessibility and non-3D fallback sufficient to avoid making the topology unreadable when full 3D interaction is unavailable;
10. focused browser/unit proof plus repository build/validator parity.

The exact implementation stack is not preselected here. Inspect the current repository web/runtime architecture and reuse its established patterns. Do not introduce React Three Fiber, Three.js, raw WebGL, or another rendering stack merely because it is popular; choose from current evidence and bounded fit.

## Forbidden scope

Phase C must not:

- mutate prompt IDs, sequence numbers, canonical registry records, families, clusters, opportunities, or Phase A/B artifacts;
- recompute semantic similarity or clustering inside the browser;
- use 3D proximity as classification evidence;
- add live telemetry, session tracking, user analytics, or behavioral relation channels;
- introduce a vector database;
- expand NodeWeaver;
- silently replace canonical Prompt Kit sequence ordering with topology ordering;
- hand-edit a generated web artifact when a repository-owned builder owns that surface;
- treat cluster envelopes, convex hulls, alpha shapes, or decorative geometry as semantic truth.

## Fresh-floor procedure

Before mutation:

1. refresh `main` and overlapping open/recent PRs;
2. verify `3bab155714fbd13aa7bdbf0692fc6c7e518756b6` remains contained in current `main`;
3. inspect current web/product seams and generated-output ownership;
4. run the Phase A+B validators/builders on the current floor;
5. record the current topology/projection/state identities as versioned inputs for Phase C proof;
6. use an isolated branch/worktree when current local work is dirty or separately owned.

A registry change that produces a new valid topology/projection epoch is normal. Rebuild before viewer certification rather than pinning Phase C to historical Phase B hashes.

## Acceptance gates

Phase C is not complete merely because a 3D scene renders.

Minimum proof:

- viewer input validation rejects mismatched/stale/tampered Phase A/B artifacts;
- every current projection prompt appears exactly once in the viewer model;
- prompt identity remains stable across reloads;
- selection/inspection resolves to the correct canonical prompt/topology evidence;
- camera/view manipulation cannot mutate underlying semantic state;
- current accepted Phase B coordinates load without random relayout;
- viewer changes do not alter Phase A or Phase B rebuild bytes;
- focused interaction/browser tests pass;
- repository build/static/registered validators pass;
- generated outputs, if any, are produced through canonical builders and parity checks;
- the exact validated head is integrated into refreshed `main` before Phase C is closed.

## First executable action

On a refreshed current `main`, inspect the existing web/runtime owners and choose the narrowest viewer surface that can consume the canonical Phase A/B artifacts. Persist that ownership decision in the Phase C contract/spec before writing renderer code if the repository does not already have an obvious owner.

The first implementation slice should then render and inspect real current artifacts end-to-end before adding visual polish or advanced geometry.

## Collision risks

- `web/prompt-kit/index.html` is generated and must not become an ad-hoc viewer implementation surface.
- Prompt Kit navigation/order contracts remain independent of topology discovery metadata.
- Future Prompt Kit registry additions can legitimately move the projection; viewer tests must bind to regenerated current artifacts rather than historical coordinates.
- Multiple UI sprints can collide on shared CSS/JS/build entrypoints; establish one writer per generated/shared surface.

## Successor sequence after Phase C

Only **Phase C** is an explicit approved successor at this handoff. Earlier discussion also proposed the following conceptual sequence:

- **Phase D candidate — Passive Learning**: behavioral/co-usage/transition evidence could enrich topology recommendations.
- **Phase E candidate — Historical Intelligence**: compare accepted topology/projection epochs over time to expose durable evolution, drift, splits, merges, and recurring opportunity patterns.

These are **CANDIDATES, NOT AUTHORIZED EXECUTION PHASES**. Their names preserve prior design intent so the idea is not lost; they do not grant scope.

### Admission gate for a Phase D candidate

Before any passive-learning implementation, create and approve a separate contract covering:

- whether behavioral evidence is needed at all;
- privacy and data-minimization boundaries;
- local vs remote collection;
- opt-in/consent and retention policy where applicable;
- provenance and aggregation rules;
- separation between advisory behavioral evidence and canonical registry/topology truth;
- deterministic fixtures/evals that prove value before live collection;
- explicit ownership for reserved channels such as `CO_USAGE`, `TRANSITION`, `SUBSTITUTION`, and `COMPLEMENT`.

Phase C must not preempt this admission gate by adding telemetry “for later.”

### Admission gate for a Phase E candidate

Before historical-intelligence implementation, prove that multiple accepted topology/projection epochs exist and define:

- which snapshots are authoritative and durable;
- epoch/version identity and retention;
- split/merge/drift comparison semantics;
- reproducible historical reconstruction;
- distinction between historical evidence and current canonical state;
- storage/scale needs from measured data before adding infrastructure.

Do not add a vector database merely to prepare for this candidate.

## Handoff rule for every future phase

At the end of Phase C and any later approved phase:

1. commit a phase closeout beside this document;
2. record exact integrated `main` identity plus the strongest observed proof;
3. distinguish historical artifact hashes from permanent invariants;
4. state proof ceiling and forbidden scope;
5. name the next **approved** owner and dependencies;
6. preserve attractive but unapproved successors as candidates with admission gates rather than silently expanding scope;
7. ensure the actionable continuation exists in the repository, not only in chat.

That closeout/handoff pair becomes the recovery floor for the next agent.
