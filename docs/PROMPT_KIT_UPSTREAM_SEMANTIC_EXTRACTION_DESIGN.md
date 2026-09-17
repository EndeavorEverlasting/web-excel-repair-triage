# Upstream semantic extraction program design

**Status:** design + executable prototype, critique passes complete

**Repository floor:** `main@c0090aa285fe0580ff19c26c1e1de0d7e95506bc`

**Program:** body-level semantic extraction for registered external resources.

## User outcome

Prompt Kit should be able to take a resource already discovered and pinned by the external-resource intake plane, inspect its body without copying that body into the public metadata index, and emit a deterministic, provenance-rich set of candidate mechanics that P97/P79 or another canonical comparison owner can evaluate against local prompts/contracts.

The terminal value is **a normalized comparison input**, not automatic prompt authoring and not a second source of Operant authority.

## Invariants

1. `harness/contracts/operant-external-resource-intake.v1.json` remains the canonical owner of donor discovery and source-floor pinning.
2. `web/prompt-kit/resources.v1.json` remains metadata-only; semantic extraction must not add upstream bodies to it.
3. Every extraction is bound to `source_id + resource_id + repository + source_sha + path + body_sha256`.
4. Raw upstream bodies are transient inputs. Durable receipts contain extracted candidates and provenance, not a mirrored full body.
5. Deterministic parsing may identify structure and lexical signals. It must not claim semantic equivalence, adoption fitness, license compatibility, or Operant authority.
6. Body acquisition is an adapter seam. The extraction core accepts text and is testable without network access.
7. Stale or mismatched body identity fails closed.
8. Production sync and semantic extraction remain separate stages until a later build proves a safe orchestration contract.

## Domain vocabulary

- **ResourceIdentity** — source, repository, commit SHA, path, and resource ID already established by the intake plane.
- **PinnedBody** — transient UTF-8 body paired with ResourceIdentity and its SHA-256 digest.
- **DirectiveCandidate** — one source-located policy/procedure statement extracted from prose or a list item.
- **LexicalSignal** — deterministic hint such as `isolation`, `freshness`, `evidence`, or `retry`; never a semantic verdict.
- **ExtractionReceipt** — durable normalized output containing identity, body digest, document metadata, candidate records, counts, and proof ceiling.
- **BodyPort** — adapter interface that obtains a body matching an exact ResourceIdentity.
- **ComparisonOwner** — downstream P97/P79/domain owner that decides commonality, residual, adoption, strengthening, reference-only, rejection, or unknown.

## Candidate architectures compared

| Candidate | Shape | Advantages | Failure / cost | Decision |
| --- | --- | --- | --- | --- |
| A. Extend `sync_operant_external_resources.py` | discovery + body fetch + extraction + coverage in one producer | one command | couples metadata refresh to body parsing; increases network/copyright/latency blast radius; muddies public projection ownership | **Reject** |
| B. Separate semantic stage after intake | registered ResourceIdentity -> BodyPort -> extraction core -> receipt -> comparison owner | narrow ownership, independently testable, transient bodies, reusable across donors | requires a second orchestration stage | **Select** |
| C. Mirror upstream skill bodies locally | sync full bodies into repo/cache then parse offline | easy replay | duplicates external content, creates stale cache ownership, expands repository/provenance surface | **Reject** |
| D. Runtime model reads raw repo and returns conclusions directly | agent fetch -> free-form semantic answer | flexible | nondeterministic shape, weak provenance, no stable regression seam, easy evidence promotion | **Reject as canonical stage**; model reasoning may consume normalized receipts later |

## Module / interface map

### Existing intake owner

`sync_operant_external_resources.py`

Owns source registration, default-branch verification, source-SHA resolution, enumeration, metadata projection, and deterministic title/keyword coverage. It does **not** become the semantic extractor.

### Prototype extraction core

`scripts/prototype_external_skill_semantics.py`

Public seam:

```text
build_receipt(
  source_id,
  resource_id,
  repository,
  source_sha,
  path,
  body,
  expected_body_sha256=None,
) -> ExtractionReceipt
```

Hidden complexity: front-matter parsing; Markdown heading/list/prose traversal; fenced-code and table exclusion; multiline list-item ownership; directive detection; lexical signals; line provenance; digest verification.

Failure contract: malformed front matter, stale body digest, no extractable directives, or invalid pinned URL returns a nonzero CLI result / `ValueError` at the library seam.

Side effects: none in the core. The CLI may read one body file or fetch one exact pinned raw GitHub URL and may write one receipt.

### Body adapter

Prototype adapter: `fetch_pinned_body(...)`.

It accepts only an exact `https://raw.githubusercontent.com/<repository>/<source_sha>/<path>` URL. Network acquisition is outside extraction logic and exact-revision bound. A production GitHub API/blob adapter may be added later, but it must return the same PinnedBody contract instead of leaking provider response shapes into the core.

### Downstream comparison owner

Not implemented by this design/prototype lane. It consumes ExtractionReceipt plus current canonical Prompt Kit owners and produces evidence-backed `ADOPT / STRENGTHEN / REFERENCE / REJECT / UNKNOWN` decisions. Lexical signals are inputs, never decisions.

## Ownership and dependency direction

```text
external-resource intake contract
        |
        v
ResourceIdentity (existing metadata index)
        |
        v
BodyPort / pinned body adapter
        |
        v
semantic extraction core
        |
        v
ExtractionReceipt
        |
        v
P97/P79/domain comparison owner
```

Dependency direction is one-way. The extractor does not mutate the donor registry, prompt registry, gap ledger, public resource index, or upstream repository.

## State model

```text
REGISTERED
  -> BODY_ACQUIRED
  -> IDENTITY_VERIFIED
  -> STRUCTURE_PARSED
  -> CANDIDATES_EXTRACTED
  -> RECEIPT_EMITTED

Failure states:
  BODY_UNAVAILABLE
  IDENTITY_MISMATCH
  MALFORMED_DOCUMENT
  NO_CANDIDATES
```

There is no retry policy in the extraction core. Network retries belong to a future BodyPort adapter/orchestrator and must remain bounded.

## Prototype call stacks

### Journey 1 — pinned upstream skill -> normalized comparison input

Terminal user value: a machine-readable candidate set that can be compared without re-reading raw Markdown.

```text
CLI/event
  -> validate exact repository/SHA/path URL
  -> BodyPort fetches pinned UTF-8 body
  -> build_receipt
  -> verify body SHA-256 (when expected digest exists)
  -> parse front matter + Markdown structure
  -> exclude fenced code and reference tables
  -> preserve multiline directive/list boundaries
  -> extract directive candidates + line ranges
  -> attach deterministic lexical signals
  -> emit ExtractionReceipt
```

Live prototype coverage uses three structurally different resources from `michaelshimeles/skills@513f8a24aae6383b00356fa285144b1bc3730dc1`:

- `new-feature/SKILL.md` — prose invariants, numbered steps, multiline bullets, fenced code;
- `evidence-driven-testing/SKILL.md` — long-form procedure, platform tables, evidence rules;
- `greploop/SKILL.md` — bounded loops, provider-specific review mechanics, polling and exit conditions.

### Journey 2 — stale body -> fail closed

```text
body/file/network adapter
  -> build_receipt(expected_body_sha256=<wrong digest>)
  -> digest comparison
  -> IDENTITY_MISMATCH
  -> no receipt
  -> exit 2 / ValueError
```

This prevents a body fetched from a moved branch or mutated cache from inheriting proof attached to a different source identity.

### Journey 3 — malformed or semantically empty document -> fail closed

Unterminated front matter is `MALFORMED_DOCUMENT`; a document with no deterministic directive candidates is `NO_CANDIDATES`. Neither silently becomes an empty successful receipt.

## Observability / proof

ExtractionReceipt is the proof artifact. It contains:

- exact source identity;
- body SHA-256;
- document name/description when structurally available;
- ordered candidate IDs;
- source section + line range;
- deterministic lexical signals;
- signal counts;
- explicit proof ceiling.

Do not log or persist the full upstream body in durable Prompt Kit state merely to make debugging easier.

## Executed prototype evidence

Focused proof command:

```bash
python -m unittest tests.test_external_skill_semantics_prototype -v
```

The temporary PR proof workflow exercised live pinned bodies and an adversarial stale-digest failure path. The final live proof was bound to prototype head `bd58a74bdc62cb81de55a95e68a15ac5586b9524` and uploaded artifact **10500154065**, digest **`sha256:da03104524a5485da221d6ef672409a3c2b1ca72c476aa90b2848ed20bb26a18`**.

Final live receipt observations after repairs:

| Resource | Directive candidates | Relevant signals observed | Structural-noise check |
| --- | ---: | --- | --- |
| `new-feature` | 13 | isolation, freshness, collision, dependency, cleanup, ownership | fenced code excluded; multiline mechanics preserved |
| `evidence-driven-testing` | 60 | evidence, freshness, retry, ownership | Markdown platform table excluded |
| `greploop` | 42 | review, retry, freshness | fenced code/reference structures do not become provider truth |

All three live success stacks passed. The stale-digest stack returned exit 2 and emitted no success receipt.

## Second-pass architecture critique and repairs

### Finding 1 — candidate fragmentation

The first live `new-feature` receipt emitted 18 records because continuation lines under Markdown list items became separate paragraph candidates. That would force the comparison owner to reconstruct one upstream mechanic from multiple records.

**Repair:** list-item ownership now includes indented continuation lines until the next structural boundary. A focused regression asserts that the lockfile-regeneration mechanic remains one `list_item` with a multi-line source range. After repair the live `new-feature` receipt contains 13 coherent candidates.

### Finding 2 — reference-table noise

The breadth pass against `evidence-driven-testing` flattened its Markdown platform table into a policy paragraph because cells contained directive-like words such as `must` and `verify`.

**Repair:** Markdown table rows are explicitly treated as non-directive reference structure. A regression proves a table containing directive language yields no table candidate while a following prose directive still does. The final live receipt contains zero table-shaped candidates.

### Critique outcome

The selected seam stands after both repairs:

- provider/network state did not leak into the extraction core;
- exact body identity remains fail-closed;
- raw upstream bodies remain transient;
- the receipt does not claim semantic equivalence or adoption fitness;
- adding another BodyPort adapter would not change the core interface;
- deterministic structure extraction is useful across three substantially different skill documents without modifying the production metadata sync.

No further core split/refactor is justified by current evidence. The next uncertainty is downstream semantic comparison, not body parsing ownership.

## Required successor implementation

After this design/prototype lane integrates, broad implementation remains required for the whole extraction-engine outcome. The successor build must:

1. graduate the prototype receipt shape into a versioned canonical schema;
2. add a production BodyPort/orchestrator consuming registered ResourceIdentity records;
3. define bounded transient-fetch/retry/cache rules without mirroring full bodies;
4. add the comparison stage against canonical Prompt Kit owners;
5. route `STRENGTHEN / ADOPT / REFERENCE / REJECT / UNKNOWN` results to the existing strategic owner rather than auto-authoring prompts;
6. wire scheduled/PR evidence only after the production seam is proven;
7. keep the public metadata index metadata-only unless an explicit product contract changes that requirement.

This is **REQUIRED SUCCESSOR WORK**, not an optional idea and not `OUT OF SCOPE` for the whole requested outcome.

## Proof ceiling

This design/prototype lane proves deterministic structure parsing, provenance, exact-body binding, live pinned-body acquisition for three upstream skills, candidate receipt shape, structural-noise rejection for fenced code/tables, multiline directive ownership, and failure propagation. It does not prove that lexical signals equal semantic meaning, that a downstream comparison/model will make correct adoption decisions, that every upstream Markdown dialect is supported, or that production scheduling/retry/storage policy is complete.
