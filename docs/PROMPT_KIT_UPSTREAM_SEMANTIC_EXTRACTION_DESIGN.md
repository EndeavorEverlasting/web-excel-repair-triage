# Upstream semantic extraction program design

**Status:** design + executable prototype

**Repository floor:** `main@c0090aa285fe0580ff19c26c1e1de0d7e95506bc`

**Program:** body-level semantic extraction for registered external resources.

## User outcome

Prompt Kit should be able to take a resource already discovered and pinned by the external-resource intake plane, inspect its body without copying that body into the public metadata index, and emit a deterministic, provenance-rich set of candidate mechanics that P97/P79 or another canonical comparison owner can evaluate against local prompts/contracts.

The terminal value of this program is **a normalized comparison input**, not automatic prompt authoring and not a second source of Operant authority.

## Invariants

1. `harness/contracts/operant-external-resource-intake.v1.json` remains the canonical owner of donor discovery and source-floor pinning.
2. `web/prompt-kit/resources.v1.json` remains metadata-only; semantic extraction must not add upstream bodies to it.
3. Every extraction is bound to `source_id + resource_id + repository + source_sha + path + body_sha256`.
4. Raw upstream bodies are transient inputs. Durable receipts contain extracted candidates and provenance, not a mirrored full body.
5. Deterministic parsing is allowed to identify structure and lexical signals. It must not claim semantic equivalence, adoption fitness, license compatibility, or Operant authority.
6. Body acquisition is an adapter seam. The extraction core accepts text and is testable without network access.
7. Stale or mismatched body identity fails closed.
8. Production sync and semantic extraction remain separate stages until a later build proves a safe orchestration contract.

## Domain vocabulary

- **ResourceIdentity** — registered upstream identity: source, repository, commit SHA, path, resource ID.
- **PinnedBody** — transient UTF-8 body paired with ResourceIdentity and its SHA-256 digest.
- **DirectiveCandidate** — one source-located policy/procedure statement extracted from prose or a list item.
- **LexicalSignal** — deterministic hint such as `isolation`, `freshness`, `evidence`, or `retry`; never a semantic verdict.
- **ExtractionReceipt** — durable normalized output: identity, body digest, document metadata, candidate records, counts, proof ceiling.
- **BodyPort** — adapter interface that obtains a body matching an exact ResourceIdentity.
- **ComparisonOwner** — downstream P97/P79/domain owner that decides commonality, residual, adoption, strengthening, reference-only, or rejection.

## Candidate architectures compared

| Candidate | Shape | Advantages | Failure / cost | Decision |
| --- | --- | --- | --- | --- |
| A. Extend `sync_operant_external_resources.py` | discovery + body fetch + extraction + coverage in one producer | one command | couples metadata refresh to body parsing; increases network/copyright/latency blast radius; makes public projection ownership muddy | **Reject** |
| B. Separate semantic stage after intake | registered ResourceIdentity -> BodyPort -> extraction core -> receipt -> comparison owner | narrow ownership, independently testable, keeps bodies transient, reusable across donors | requires a second orchestration step later | **Select** |
| C. Mirror upstream skill bodies locally | sync full bodies into repo/cache then parse offline | easy replay | duplicates copyrighted/external content, stale cache ownership, larger repository and provenance surface | **Reject** |
| D. Runtime model reads raw repo and returns conclusions directly | agent fetch -> free-form semantic answer | flexible | nondeterministic shape, weak provenance, no stable regression seam, easy evidence promotion | **Reject as canonical stage**; model reasoning may consume normalized receipts later |

## Module / interface map

### Existing intake owner

`sync_operant_external_resources.py`

Responsibility: source registration, default-branch verification, source-SHA resolution, enumeration, metadata projection, deterministic title/keyword coverage. It does **not** become the semantic extractor.

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

Hidden complexity: front-matter parsing, Markdown heading/list/prose traversal, fenced-code exclusion, directive detection, lexical signals, line provenance, digest verification.

Failure contract: malformed front matter, stale body digest, no extractable directives, or invalid pinned URL returns a nonzero CLI result / `ValueError` at the library seam.

Side effects: none in the core. CLI may read one body file or fetch one exact pinned raw GitHub URL and may write one receipt.

### Body adapter

Prototype adapter: `fetch_pinned_body(...)`.

It accepts only an exact `https://raw.githubusercontent.com/<repository>/<source_sha>/<path>` URL. Network acquisition is therefore outside extraction logic and exact-revision bound.

A later production build may introduce GitHub API/blob adapters, but they must return the same PinnedBody contract rather than leak provider response shapes into the extraction core.

### Downstream comparison owner

Not implemented by this design sprint. It should consume ExtractionReceipt and current canonical Prompt Kit owners, then produce evidence-backed `ADOPT / STRENGTHEN / REFERENCE / REJECT / UNKNOWN` decisions. Lexical signals are inputs, not decisions.

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
  -> exclude fenced code
  -> extract directive candidates + line ranges
  -> attach deterministic lexical signals
  -> emit ExtractionReceipt
```

The live prototype target is `michaelshimeles/skills@513f8a24.../new-feature/SKILL.md` because it contains prose invariants, numbered steps, bullets, and code fences.

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

Unterminated front matter is classified as `MALFORMED_DOCUMENT`; a document with no deterministic directive candidates is `NO_CANDIDATES`. Neither condition silently becomes an empty successful receipt.

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

## Prototype proof plan

Focused unit proof:

```bash
python -m unittest tests.test_external_skill_semantics_prototype -v
```

Live vertical proof:

```bash
python scripts/prototype_external_skill_semantics.py \
  --source-id michaelshimeles-skills \
  --resource-id michaelshimeles-skills:new-feature \
  --repository michaelshimeles/skills \
  --source-sha 513f8a24aae6383b00356fa285144b1bc3730dc1 \
  --path new-feature/SKILL.md \
  --url https://raw.githubusercontent.com/michaelshimeles/skills/513f8a24aae6383b00356fa285144b1bc3730dc1/new-feature/SKILL.md \
  --output Outputs/external-semantic-prototype/new-feature.json
```

A temporary PR proof workflow may execute that live stack and upload the receipt. The temporary workflow is not part of the program design and should be removed before integration.

## Second-pass critique questions

After the prototypes run, specifically challenge:

1. Does `prototype_external_skill_semantics.py` accidentally own provider retry/state?
2. Are candidate extraction rules too broad or too coupled to Michael Shimeles' formatting?
3. Does any receipt field imply semantic truth beyond deterministic parsing?
4. Can a stale/moved body produce a receipt under an old source identity?
5. Does the design require copying upstream content into tracked files?
6. Would adding another body adapter change the core interface?

Any concrete defect found here should be repaired in the prototype before handing broad implementation to the build executor.

## Required successor implementation

After this design/prototype lane proves the call stacks, broad implementation remains required for the whole extraction-engine outcome. The successor build should:

1. graduate the prototype receipt shape into a versioned canonical schema;
2. add a production BodyPort/orchestrator consuming registered ResourceIdentity records;
3. define bounded transient-fetch/retry/cache rules without mirroring full bodies;
4. add the comparison stage against canonical Prompt Kit owners;
5. route `STRENGTHEN / ADOPT / REFERENCE / REJECT / UNKNOWN` results to the existing strategic owner rather than auto-authoring prompts;
6. wire scheduled/PR evidence only after the production seam is proven;
7. keep the public metadata index metadata-only unless an explicit product contract changes that requirement.

This is **REQUIRED SUCCESSOR WORK**, not an optional idea and not `OUT OF SCOPE` for the whole requested outcome.

## Proof ceiling

This design sprint can prove parsing, provenance, exact-body binding, live pinned-body acquisition, candidate receipt shape, and failure propagation. It cannot prove that lexical signals equal semantic meaning, that a downstream model will make correct adoption decisions, that every upstream Markdown dialect is supported, or that production scheduling/retry/storage policy is complete.
