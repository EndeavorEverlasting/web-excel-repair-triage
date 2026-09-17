# Upstream semantic extraction program design

**Status:** design + executable prototype, critique/review passes complete

**Repository floor:** `main@c0090aa285fe0580ff19c26c1e1de0d7e95506bc`

**Program:** body-level semantic extraction for registered external resources.

## User outcome

Prompt Kit should be able to take a resource already discovered and pinned by the external-resource intake plane, inspect its body without copying that body into the public metadata index, and emit a deterministic, provenance-rich set of candidate mechanics that P97/P79 or another canonical comparison owner can evaluate against local prompts/contracts.

The terminal value is **a normalized comparison input**, not automatic prompt authoring and not a second source of Operant authority.

## Invariants

1. `harness/contracts/operant-external-resource-intake.v1.json` remains the canonical owner of donor discovery and source-floor pinning.
2. `web/prompt-kit/resources.v1.json` remains metadata-only; semantic extraction must not add upstream bodies to it.
3. Every extraction is bound to a validated `ResourceIdentity` plus a digest-checked `PinnedBody`.
4. Raw upstream bodies are transient inputs. Durable receipts contain extracted candidates and provenance, not a mirrored full body.
5. Deterministic parsing may identify structure and lexical signals. It must not claim semantic equivalence, adoption fitness, license compatibility, or Operant authority.
6. Body acquisition is an adapter seam. The extraction core consumes `PinnedBody` and is testable without network access.
7. Stale, movable, escaping, or internally inconsistent identity/body state fails closed.
8. Production sync and semantic extraction remain separate stages until a later build proves a safe orchestration contract.

## Domain vocabulary

- **ResourceIdentity** — validated source, repository, 40-character commit SHA, relative path, and resource ID established by the intake plane.
- **PinnedBody** — transient UTF-8 body paired with ResourceIdentity, its verified SHA-256 digest, and acquisition proof.
- **DirectiveCandidate** — one source-located policy/procedure statement extracted from directive-bearing prose or a list item.
- **LexicalSignal** — deterministic hint such as `isolation`, `freshness`, `evidence`, or `retry`; never a semantic verdict.
- **ExtractionReceipt** — durable normalized output containing identity, body digest, acquisition mode, document metadata, candidate records, counts, and proof ceiling.
- **BodyPort** — adapter interface that obtains a PinnedBody matching an exact ResourceIdentity.
- **ComparisonOwner** — downstream P97/P79/domain owner that decides commonality, residual, adoption, strengthening, reference-only, rejection, or unknown.

## Candidate architectures compared

| Candidate | Shape | Advantages | Failure / cost | Decision |
| --- | --- | --- | --- | --- |
| A. Extend `sync_operant_external_resources.py` | discovery + body fetch + extraction + coverage in one producer | one command | couples metadata refresh to body parsing; increases network/copyright/latency blast radius; muddies public projection ownership | **Reject** |
| B. Separate semantic stage after intake | ResourceIdentity -> BodyPort -> PinnedBody -> extraction core -> receipt -> comparison owner | narrow ownership, independently testable, transient bodies, reusable across donors | requires a second orchestration stage | **Select** |
| C. Mirror upstream skill bodies locally | sync full bodies into repo/cache then parse offline | easy replay | duplicates external content, creates stale cache ownership, expands repository/provenance surface | **Reject** |
| D. Runtime model reads raw repo and returns conclusions directly | agent fetch -> free-form semantic answer | flexible | nondeterministic shape, weak provenance, no stable regression seam, easy evidence promotion | **Reject as canonical stage**; model reasoning may consume normalized receipts later |

## Module / interface map

### Existing intake owner

`sync_operant_external_resources.py`

Owns source registration, default-branch verification, source-SHA resolution, enumeration, metadata projection, and deterministic title/keyword coverage. It does **not** become the semantic extractor.

### Prototype extraction core

`scripts/prototype_external_skill_semantics.py`

Public semantic seam:

```text
build_receipt(pinned: PinnedBody) -> ExtractionReceipt
```

The trust-boundary helpers are deliberately separate:

```text
ResourceIdentity(...)
fetch_pinned_body(url, identity) -> PinnedBody
verify_body(identity, body, expected_body_sha256, acquisition) -> PinnedBody
load_verified_body(path, identity, expected_body_sha256) -> PinnedBody
```

Hidden complexity: identity validation; body digest verification; front-matter parsing; Markdown heading/list/prose traversal; backtick/tilde fence exclusion; reference-table exclusion; multiline list-item ownership; directive-language filtering; lexical signals; line provenance.

Failure contract: malformed identity/front matter, stale or self-inconsistent body digest, no extractable directives, or invalid pinned URL returns a nonzero CLI result / `ValueError` at the library seam.

Side effects: none in the semantic core. The CLI may read one digest-verified body file or fetch one exact pinned raw GitHub URL and may write one receipt.

### Body adapter

Prototype network adapter: `fetch_pinned_body(...)`.

It accepts only an exact `https://raw.githubusercontent.com/<repository>/<source_sha>/<path>` URL and creates a PinnedBody with `acquisition=pinned_raw_url`. Local body files require an explicit expected SHA-256 before a PinnedBody can be constructed.

A production GitHub API/blob adapter may be added later, but it must return the same PinnedBody contract instead of leaking provider response shapes into the core.

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
BodyPort / acquisition adapter
        |
        v
PinnedBody
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
  -> BODY_VERIFIED
  -> STRUCTURE_PARSED
  -> CANDIDATES_EXTRACTED
  -> RECEIPT_EMITTED

Failure states:
  BODY_UNAVAILABLE
  IDENTITY_INVALID
  IDENTITY_MISMATCH
  BODY_DIGEST_MISMATCH
  MALFORMED_DOCUMENT
  NO_CANDIDATES
```

There is no retry policy in the extraction core. Network retries belong to a future BodyPort adapter/orchestrator and must remain bounded.

## Prototype call stacks

### Journey 1 — pinned upstream skill -> normalized comparison input

Terminal user value: a machine-readable candidate set that can be compared without re-reading raw Markdown.

```text
CLI/event
  -> construct validated ResourceIdentity
  -> validate exact repository/SHA/path URL
  -> BodyPort fetches pinned UTF-8 body
  -> construct digest-consistent PinnedBody
  -> build_receipt(PinnedBody)
  -> parse front matter + Markdown structure
  -> exclude backtick/tilde fenced code and reference tables
  -> preserve multiline directive/list boundaries
  -> reject descriptive list/prose structures without directive language
  -> extract directive candidates + line ranges
  -> attach deterministic lexical signals
  -> emit ExtractionReceipt with acquisition proof
```

Live prototype coverage uses three structurally different resources from `michaelshimeles/skills@513f8a24aae6383b00356fa285144b1bc3730dc1`:

- `new-feature/SKILL.md` — prose invariants, numbered steps, multiline bullets, fenced code;
- `evidence-driven-testing/SKILL.md` — long-form procedure, platform tables, evidence rules;
- `greploop/SKILL.md` — bounded loops, provider-specific review mechanics, polling and exit conditions.

### Journey 2 — stale body -> fail closed

```text
body/file/network adapter
  -> verify_body(expected_body_sha256=<wrong digest>)
  -> digest comparison
  -> BODY_DIGEST_MISMATCH
  -> no PinnedBody
  -> no receipt
  -> exit 2 / ValueError
```

This prevents a moved branch, mutated cache, or unverified local body from inheriting proof attached to a different source identity.

### Journey 3 — malformed or semantically empty document -> fail closed

Unterminated front matter is `MALFORMED_DOCUMENT`; a document with no deterministic directive candidates is `NO_CANDIDATES`. Neither silently becomes an empty successful receipt.

## Observability / proof

ExtractionReceipt is the proof artifact. It contains:

- exact validated source identity;
- body SHA-256;
- acquisition proof label;
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

The temporary PR proof workflow exercised three live pinned bodies and an adversarial stale-digest failure path. After the final review-driven behavioral repairs, the live proof was bound to prototype head `03b4f17c55b8f7ec7aca2d03c3f8c9407e01cb38` and uploaded artifact **10500179872**, digest **`sha256:dae2d1929e92add854007a59a3769f214487f822e8e4b66d12333e444ae77266`**.

Final live receipt observations:

| Resource | Directive candidates | Relevant signals observed | Structural/trust check |
| --- | ---: | --- | --- |
| `new-feature` | 13 | isolation, freshness, collision, dependency, cleanup, ownership | multiline mechanics preserved; fenced code excluded; pinned URL acquisition recorded |
| `evidence-driven-testing` | 47 | evidence, freshness, retry, ownership | Markdown table excluded; descriptive bullets filtered |
| `greploop` | 37 | review, retry, freshness | reference/descriptive bullets filtered; bounded-loop mechanics retained |

All three live success stacks passed. The stale-digest stack returned exit 2 and emitted no success receipt.

## Architecture critique, review findings, and repairs

### Finding 1 — candidate fragmentation

The first live `new-feature` receipt emitted 18 records because continuation lines under Markdown list items became separate paragraph candidates.

**Repair:** list-item ownership includes indented continuation lines until the next structural boundary. Regression: the lockfile-regeneration mechanic remains one `list_item` with a multi-line source range. Live `new-feature` now contains 13 coherent candidates.

### Finding 2 — reference-table noise

The first breadth pass flattened the `evidence-driven-testing` platform table into a policy paragraph because cells contained words such as `must` and `verify`.

**Repair:** Markdown table rows are non-directive reference structure. Regression proves a directive-bearing table yields no table candidate while following prose still does.

### Finding 3 — incomplete fence recognition

Code review identified that only backtick fences were excluded, so `~~~` fenced code could leak into comparison input.

**Repair:** `FENCE_RE` recognizes both backtick and tilde fences and tracks the opening marker type until a matching close. Regression: `test_tilde_fenced_code_is_not_extracted`.

### Finding 4 — descriptive list overcapture

Code review identified that every list item was previously accepted even without directive language.

**Repair:** list and prose candidates now share the directive-language gate. Regression: `test_descriptive_list_items_are_not_directives`. Live candidate counts tightened from 60 to 47 for `evidence-driven-testing` and 42 to 37 for `greploop` while required evidence/review/retry signals remained present.

### Finding 5 — weak body trust boundary

Code review identified that the original `build_receipt(...)` accepted arbitrary identity fields plus arbitrary local body text, allowing accidental false binding to an upstream SHA.

**Repair:** `ResourceIdentity` validates repository/SHA/path shape; `PinnedBody` validates its body digest and acquisition proof; `build_receipt` accepts only PinnedBody; local files require an expected SHA-256; exact raw URLs are repository/SHA/path pinned. Regressions cover movable SHA, path escape, self-inconsistent digest, stale digest, and URL mismatch.

All three review threads were replied to and resolved after the repaired three-skill live proof.

### Critique outcome

The selected seam stands after five concrete repairs:

- provider/network state does not leak into the extraction core;
- exact body identity is represented explicitly and fails closed;
- raw upstream bodies remain transient;
- the receipt does not claim semantic equivalence or adoption fitness;
- adding another BodyPort adapter would not change the semantic core interface;
- deterministic structure extraction is useful across three substantially different skill documents without modifying production metadata sync.

No further core split/refactor is justified by current evidence. The next material uncertainty is downstream semantic comparison, not body parsing ownership.

## Required successor implementation

After this design/prototype lane integrates, broad implementation remains required for the whole extraction-engine outcome. The successor build must:

1. graduate the prototype receipt/value-object shape into a versioned canonical schema/interface;
2. add a production BodyPort/orchestrator consuming registered ResourceIdentity records;
3. define bounded transient-fetch/retry/cache rules without mirroring full bodies;
4. add the comparison stage against canonical Prompt Kit owners;
5. route `STRENGTHEN / ADOPT / REFERENCE / REJECT / UNKNOWN` results to the existing strategic owner rather than auto-authoring prompts;
6. wire scheduled/PR evidence only after the production seam is proven;
7. keep the public metadata index metadata-only unless an explicit product contract changes that requirement.

This is **REQUIRED SUCCESSOR WORK**, not an optional idea and not `OUT OF SCOPE` for the whole requested outcome.

## Proof ceiling

This design/prototype lane proves deterministic structure parsing, validated ResourceIdentity/PinnedBody seams, exact-body binding, live pinned-body acquisition for three upstream skills, candidate receipt shape, structural-noise rejection for fenced code/tables/descriptive bullets, multiline directive ownership, and failure propagation. It does not prove that lexical signals equal semantic meaning, that a downstream comparison/model will make correct adoption decisions, that every upstream Markdown dialect is supported, or that production scheduling/retry/storage policy is complete.
