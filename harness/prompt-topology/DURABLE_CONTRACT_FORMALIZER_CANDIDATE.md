# Settled Decision → Durable Contract Formalizer — Candidate Contract

**Status:** PROVISIONAL / P79 ADMISSION PENDING / NOT A REGISTERED PROMPT
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Evidence floor:** refreshed `main@e7abdb67c9ce56c5a87cfc18781caf006e01f6e9`
**Candidate owner until Prompt Kit disposition:** P79 `Prompt Registry Prompt Adder`
**Registry authority:** none yet; this file MUST NOT be treated as a prompt identity, ID allocation, or copy-safe prompt body

## Why this artifact exists

A design or operating decision can be good enough to implement yet still be trapped in chat. That leaves later agents unable to assess, complete, or extend the work without reconstructing the originating conversation. The missing lifecycle transition is:

`DESIGNED / DECIDED -> CONTRACTED`

This candidate formalizes only that transition. It does not choose strategy, resolve material architecture uncertainty, or implement the contracted behavior.

The practical closure invariant is strict:

> If the next competent agent still needs the originating chat to determine what must remain true, what it may change, how compliance is proved, or what owner acts next, the contract is incomplete.

## Smallest residual against neighboring Prompt Kit owners

| Neighbor | Existing ownership | Residual left for this candidate |
| --- | --- | --- |
| P02 Previous Chat → Active Sprint Executor | Recover previous-chat state, reconcile current repo/provider truth, execute unresolved work | This candidate does not recover/continue a whole prior sprint; it formalizes an already-settled result into durable authority. |
| P07 Repo Sprint Executor | Execute bounded repository mutation through validation and mainline convergence | P07 may implement a contract, but this candidate deliberately stops once the contract is canonical and implementation-ready. |
| P76 Progressive-Disclosure Spec & Harness Factorer | Factor existing specs/harness into demand-loaded information architecture | P76 changes how existing authority is exposed; this candidate creates/formalizes the missing normative contract itself. |
| P79 Prompt Registry Prompt Adder | Harvest chat insights into Prompt Kit; strengthen first; add only after prior-art/overlap proof | P79 owns whether this candidate becomes a prompt at all. It is not the runtime owner for arbitrary future repository contract formalization. |
| P95 Program Design & Call-Stack Prototype Architect | Resolve program architecture, interfaces, ownership, seams, call stacks, bounded prototypes | P95 answers what the design should be; this candidate begins only after the material design decision is settled. |
| P141 Repository Strategic Opportunity Scout | Compare/falsify strategic theses and select one bounded investigation | P141 decides what deserves investigation; it does not formalize a settled result into downstream authority. |

**Distinct terminal state:** `CONTRACTED / IMPLEMENTATION-READY`, with no implementation of the contracted product behavior performed by this prompt.

## Admission criteria

Admit only when every required condition below is true. Fail closed otherwise.

### 1. Concrete subject exists

There is a specific decision, design, workflow, interface, state/data ownership rule, integration boundary, artifact/schema contract, behavioral invariant, producer/consumer relationship, failure/recovery rule, or operating rule to formalize. An interesting idea alone is insufficient.

### 2. Material decision is already settled

Evidence supports a sufficiently stable answer to `what has been decided?`

Acceptable settlement sources include explicit operator decision; accepted repository/provider state; completed P95 design work; an experiment whose decision rule selected an outcome; a merged architecture/spec decision; evidenced current behavior whose semantics are settled but under-contracted; or another authoritative design/decision owner.

If materially different viable alternatives remain unresolved, reject admission and route to the relevant investigation/design owner.

### 3. Missing work is principally formalization

The core defect is that accepted understanding is not yet represented as one canonical durable contract another agent can reliably discover and consume. Documentation polish alone is not admission.

### 4. Downstream consumer exists

Identify at least one credible consumer: implementation sprint, validator/test author, integration agent, deployment/release owner, adjacent subsystem, future maintainer, automation, another repository, or future architecture extension.

### 5. Evidence separates truth from proposal

The evidence can distinguish accepted decisions/facts, observations, assumptions, unresolved questions, rejected alternatives, and implementation suggestions. Unknowns remain typed as unknown; they never silently become invariants.

### 6. Canonical durable destination exists or can be derived

Reuse an existing authoritative contract/spec/schema/registry/workflow/manifest/decision owner before creating another one. Creating a new document hierarchy merely to house the contract is forbidden.

### 7. Substantial product implementation is not required

Minimal contract-local registration, references, schema validation, or discoverability wiring is allowed. If truthful contract completion requires substantial runtime/product implementation first, reject admission and route that work to its implementation owner.

## Rejection / routing rules

- competing strategies/opportunities remain -> P141 or other strategic owner;
- internal architecture/boundary/state ownership remains unresolved -> P95;
- one bounded empirical hypothesis must be tested -> P82/experiment owner;
- contract already exists and implementation is missing -> P07;
- contract exists but default loading/routing is bloated -> P76;
- task is adding/strengthening a Prompt Kit identity -> P79;
- task is primarily recovering a previous chat and continuing it -> P02;
- task is explanatory documentation/tutorial content -> documentation owner;
- existing contract conflicts with implementation and authority cannot be resolved -> resolve authority/design conflict before admission.

## Required outputs

Use the repository's existing contract format where one exists. Semantics below are required; headings are not mandatory when a machine schema already expresses them.

### Contract identity and authority

Record contract name/ID, canonical path/provider location, owner, and repository-native status. Do not invent a second status vocabulary.

### Intent / outcome

State the externally meaningful outcome the contract protects and why downstream consumers need it.

### Owned scope

State exactly what behavior, boundary, data, workflow, interface, artifact, or responsibility the contract governs.

### Forbidden / non-owned scope

State what the contract does not govern and identify adjacent owners where ambiguity is likely.

### Inputs / outputs / observable transitions

Record externally meaningful inputs, outputs, events, artifacts, state transitions, or interface obligations where applicable. Do not force an I/O model where it is meaningless.

### Ownership and dependency direction

Record authoritative owner, consumers, dependencies, dependency direction, and foreign contracts that remain authoritative. Important state/responsibility must not gain duplicate owners.

### Invariants

Record only properties future work MUST preserve. Every invariant must be intentional, evidence-backed, relevant to downstream correctness/interoperability/safety/accepted outcome, and testable or inspectable where practical.

### Degrees of Freedom — REQUIRED

Explicitly identify implementation choices future agents MAY change without reopening or violating the contract.

Candidate freedoms may include internal class/module decomposition, algorithm, library/framework, storage representation, concurrency mechanism, caching, UI implementation, private naming, optimization strategy, file/service boundaries, or implementation language where not constrained by the accepted boundary.

Use this test for every proposed invariant:

> If a future implementation changed this mechanism while preserving every externally required behavior, ownership boundary, safety property, and acceptance gate, would the actual accepted decision be violated?

If **no**, it belongs under Degrees of Freedom rather than Invariants.

A downstream agent must be able to answer: `What can I redesign creatively without reopening this contract?`

### Extension points

Record only meaningful compatible extension seams already implied by the settled design. Do not invent speculative future architecture.

### Failure and recovery semantics

When applicable, state invalid-input behavior, dependency-unavailable behavior, degraded mode, retry/recovery ownership, fail-open/fail-closed posture, and persistence/replay implications. Unsettled semantics remain unresolved rather than invented.

### Evidence floor

Record the evidence that supports the contract and its strongest proven state. Distinguish DESIGNED, TRACKED, IMPLEMENTED, WIRED/REACHABLE, VALIDATED, INTEGRATED, DEPLOYED, and OBSERVED where material. Weaker evidence never silently proves a stronger state.

### Acceptance / proof gates

State how downstream work proves compliance. Prefer observable tests, schema validation, interface checks, artifact comparisons, integration behavior, traces, user-visible outcome, or explicitly justified manual acceptance over prose interpretation.

### Open questions

Preserve unresolved items that do not invalidate the settled core. Mark whether each blocks implementation, is safely deferrable, requires future investigation, or belongs outside the contract.

### Rejected / superseded alternatives

Preserve only alternatives whose omission creates meaningful rediscovery risk. Do not turn the contract into an architecture diary.

### Successor route

Identify the next canonical owner and first unproven gate.

## Required repository integration

Creating a Markdown file alone is not automatically completion. Integrate the authoritative contract into the smallest existing discovery path needed for a fresh agent to find it without knowing the filename. Reuse existing registries/manifests/maps/indexes; do not create a duplicate routing hierarchy.

## Allowed mutations

This candidate may create/update the canonical contract; register it in an existing index/registry; repair references; mark superseded contracts; add narrow contract/schema/discoverability validation; update routing metadata needed for consumption; and commit/push/integrate those contract-local changes when authorized.

These mutations serve formalization, not product implementation.

## Forbidden behavior

The formalizer MUST NOT:

- choose among materially unresolved architectures or strategies;
- invent requirements to make the contract appear complete;
- turn implementation suggestions into invariants without evidence;
- implement the product/runtime behavior described by the contract;
- perform broad refactors merely because the contract exposes opportunities;
- add production code to avoid a P07 handoff;
- disguise broad implementation as `contract validation`;
- freeze incidental implementation details;
- prescribe mechanisms where capability-level requirements suffice;
- eliminate implementation freedom merely for determinism;
- duplicate another contract's authority or create parallel owners;
- copy the originating chat into the repository as a substitute for a contract;
- use the contract as a project diary;
- hide unresolved questions behind vague wording;
- promote design/static evidence into runtime/production proof;
- widen into neighboring systems except as needed to state ownership boundaries;
- create a new registry/schema/harness layer when an existing owner can carry the contract;
- continue into implementation merely because the contract is now implementation-ready.

**Implementation readiness is the success condition, not permission for this prompt to implement.**

## Quality tests

### Conservative consumer test

A fresh downstream agent can determine what must remain true, what it owns, what it must not change, what evidence established the requirements, and how implementation compliance is proved.

### Creative successor test

The same agent can determine what remains deliberately unspecified, which mechanisms may change, where compatible extensions belong, which assumptions may be revisited without violating the contract, and when reopening design authority is actually required.

Passing only the conservative test creates specification rigidity. Passing only the creative test creates an ineffective contract. Both are required.

## Closure test

Declare COMPLETE only when all are true:

1. **Canonical** — exactly one authoritative contract owner is identified.
2. **Durable** — the contract exists in tracked repository/provider state, not chat alone.
3. **Discoverable** — a fresh downstream agent can reach it through normal repository routing without knowing the path beforehand.
4. **Evidence-bound** — every material invariant is supported by accepted evidence; unsupported claims remain UNKNOWN/PROPOSED/OUT OF SCOPE.
5. **Boundary-safe** — owned/forbidden scope prevents accidental adjacent ownership.
6. **Freedom-preserving** — Degrees of Freedom is explicit and no material mechanism is frozen without necessity.
7. **Actionable** — downstream implementation can derive bounded acceptance criteria and the first implementation gate without reconstructing the originating conversation.
8. **Testable** — material requirements have observable proof gates or justified manual acceptance.
9. **Non-duplicative** — existing authority is referenced rather than copied and no competing owner is created.
10. **Successor-ready** — next owner and first unproven gate are explicit.
11. **No premature implementation** — contracted product behavior was not implemented by this sprint except minimal contract-local registration/validation machinery.

### Hard fail: original-chat dependency

Closure FAILS when the next competent agent still needs the originating chat to determine any material invariant, ownership boundary, permitted implementation freedom, acceptance gate, unresolved core question, or next owner/action.

The originating chat may remain useful history. It must not be an execution dependency.

### Other fail-closed conditions

Do not close while material architecture choices remain unresolved; accepted decision cannot be distinguished from inference; invariants and implementation details are mixed; ownership is ambiguous; no durable canonical location exists; discoverability is absent; acceptance cannot be determined; another authority is duplicated; open questions secretly determine core behavior; or a future implementation agent cannot tell what it is free to change.

## Terminal state

`CONTRACTED / IMPLEMENTATION-READY`

This means accepted understanding is durable authority; downstream boundaries and proof expectations are explicit; implementation freedom is preserved; implementation has not begun under this owner; and the successor can proceed without the originating conversation.

The formalizer stops here and does not execute the successor sprint.

## P79 admission work still required

This file is deliberately **not** a Prompt Kit ADD decision. Before any registry mutation:

1. Refresh current `main` and overlapping Prompt Kit PRs.
2. Run the repository-owned prior-art gate, at minimum:
   `python scripts/prompt_registry_ops.py prior-art --query "settled decision durable repository contract formalizer invariants degrees of freedom implementation freedom original chat dependency"`
3. Require the helper's complete registered-source coverage (`all_registered_sources_searched=true`) and build the required upstream synthesis/overlap ledger.
4. Re-run the owner collision against P02/P07/P76/P79/P95/P141 and any newly discovered current owner.
5. STRENGTHEN an existing owner if it absorbs the residual cleanly; ADD only if the distinct terminal state and admission/closure contract still survive.
6. If ADD survives, use `scripts/prompt_registry_ops.py add`; do not manually assign ID/seq/copySheet.
7. Run the focused Prompt Kit semantic tests, language/discovery checks, canonical builder parity, and integration gates owned by the resulting changed surface.
8. Update/remove this candidate artifact once the authoritative Prompt Kit disposition lands so this file does not become a competing behavior specification.

## Current proof ceiling

This file proves only that the candidate design is durably captured for P79 evaluation. It does **not** prove prior-art clearance, Prompt Kit ADD admission, registered prompt identity, generated-site presence, runtime prompt effectiveness, or user acceptance.
