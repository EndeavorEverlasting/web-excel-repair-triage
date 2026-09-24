# AFKAF Prompt Topology Classifier — Deterministic Pipeline Contract

**Lane:** classifier architecture + generated ordering
**Branch:** `design-only` (unresolved until implementation begins)
**Authority:** `harness/prompt-topology/schema.v1.json` + `harness/prompt-topology/config.v1.json`
**Status:** design contract — no NodeWeaver, no ontology rewrite, no ID renumbering, no UI/3D viewer implementation.

---

## 1. Core Principle

> **Semantic topology is derived evidence. The existing registry remains authoritative for prompt identity and explicit metadata. The classifier may recommend changes; it must not silently rewrite ontology truth.**

Invariants (enforced by validator):

- Every registered prompt produces exactly one canonical classifier record or explicit failure.
- Classifier never embeds arbitrary repository text — only canonical records from validated parser.
- 3D projection never determines classification; deleting `projection-3d.json` and recomputing must not change `clusters.json` or `classifications.json`.
- Prompt IDs (`P00`…​) and `seq` are immutable; ordering artifacts are derived presentation manifests.
- All generated state under `artifacts/prompt-topology/` is disposable: `rm -rf artifacts/prompt-topology/* && python scripts/prompt-topology/run.py` must reconstruct identical artifacts given identical inputs.

---

## 2. End-to-End Pipeline

```
Prompt Registry + Prompt Files
          │
          ▼
┌───────────────────────────────┐
│ 1. Canonical Prompt Record    │  ← scripts/prompt-topology/build-records.py
│    harness/prompt-topology/schema.v1.json:$defs/canonical_prompt_record
│    single input contract      │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│ 2. Feature Views              │  ← embed input preparation
│    semantic / role / structural
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│ 3. Embedding                  │  ← scripts/prompt-topology/embed.py
│    provider adapter           │     embed(text)->vector
│    semantic + role + struct  │     L2-normalized, provenance required
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│ 4. Similarity Index           │  ← scripts/prompt-topology/neighbors.py
│    k-nearest, cosine, brute   │     O(n²) JSON artifact, no vector DB
│    0.70*sem +0.20*role+0.10*meta
└──────────────┬────────────────┘
               │
        ┌──────┴─────────┐
        ▼                ▼
┌───────────────┐ ┌─────────────────┐
│ 5. Clustering │ │ 6. 3D Projection│  ← parallel leaves
│    HDBSCAN    │ │    UMAP(3)      │     clustering never reads 3D
│    PCA 30-50D │ │    viz only     │
└──────┬────────┘ └────────┬────────┘
       │                   │
       └─────────┬─────────┘
                 ▼
┌───────────────────────────────┐
│ 7. Classification Policy      │  ← scripts/prompt-topology/cluster.py
│    family/cluster/confidence  │     + classifications.json
│    drift/outlier/duplicate    │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│ 8. Generated Kit Ordering     │  ← scripts/prompt-topology/order.py
│    kit-order.json             │     stable IDs, derived placement
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│ 9. Validators + Reports       │  ← scripts/prompt-topology/validate.py
│    structural fail / semantic │     + validation-report.json + run-manifest.json
│    warnings + AFKAF gate      │
└───────────────────────────────┘
```

Single orchestrator (future): `python scripts/prompt-topology/run.py` runs all stages in order; no hand-running seven scripts.

---

## 3. Canonical Prompt Record — The Single Input Contract

Path: `artifacts/prompt-topology/canonical-prompts.json` — sorted array of `canonical_prompt_record`.

Every prompt first becomes one deterministic record validated against `schema.v1.json:$defs/canonical_prompt_record`:

| Field | Source | Notes |
|---|---|---|
| `prompt_id` | `registry.id` | `^P[0-9]+$`, stable |
| `seq` / `seq_int` | `registry.seq` | String seq + integer view for sorting; never reordered |
| `title` | `registry.name` | |
| `prompt_class` | `registry.class` | Raw class string |
| `prompt_type` | `registry.type` | Taxonomy key (e.g. `BUILD`) |
| `sprint_path_role` | `registry.sprintRole` normalized | First 120 chars, lower-kebab fallback |
| `family_declared` / `family_declared_id` | `registry/type → section name/id` via `registry/prompts/prompt-classification.v1.json` | Human-stable declared family; e.g. `type=BUILD` → `family_declared=Build & Repair`, `family_declared_id=build-repair` |
| `use_this_when` | `registry.useWhen` | Verbatim |
| `inspect_first` | `registry.inspectFirst` | |
| `expected_output` | `registry.expectedOutput` | |
| `acceptance_gate` | `registry.proofGate` | |
| `body` | `registry.copyContent` | Full canonical prompt text; no README/generated contamination |
| `keywords` | `registry.keywords` | |
| `source.registry_path` | provenance | e.g. `docs/prompts.json` or `registry/prompts/*.json` |
| `source.sha256` / `canonical_sha256` | SHA-256 of canonical JSON (sorted keys) | Detects preprocessing/config drift |

The classifier embeds **only** these records. Formatting changes, comments, README duplication, or generated files must not alter topology except through the canonical record hash.

---

## 4. Feature Views

Three views prevent one giant concatenation from conflating semantics:

**Semantic view** (`semantic_view`) — main embedding input:
```
TITLE:
{title}

USE THIS WHEN:
{use_this_when}

INSPECT FIRST:
{inspect_first}

EXPECTED OUTPUT:
{expected_output}

ACCEPTANCE GATE:
{acceptance_gate}

PROMPT BODY:
{body}
```

**Role/intent view** (`role_view`) — high-value metadata weighted explicitly:
```
PROMPT_CLASS={prompt_class}
PROMPT_TYPE={prompt_type}
SPRINT_PATH_ROLE={sprint_path_role}
DECLARED_FAMILY={family_declared}
DECLARED_FAMILY_ID={family_declared_id}
USE_THIS_WHEN={use_this_when}
EXPECTED_OUTPUT={expected_output}
```

**Structural vector** (`structural_vector`) — categorical/numeric, not prose:
```json
{
  "has_acceptance_gate": 1,
  "has_repo_scope": 1,
  "has_remote_truth_requirement": 1,
  "has_parallel_lane": 0,
  "prompt_class": "SPRINT / BUILD + MUTATE",
  "prompt_type": "BUILD",
  "sprint_path_role": "execute-any-bounded-repo-change",
  "declared_family_id": "build-repair",
  "declared_family": "Build & Repair",
  "category": "standard",
  "color": "Green"
}
```

V1 deliberately limits structural flags to metadata already owned; derived flags (`requires_mutation`, `is_meta_prompt`, …​) are deferred until validated signal proves value.

---

## 5. Embedding Construction

Per prompt at least two embeddings:

```json
{ "semantic_embedding": [...], "role_embedding": [...] }
```

+ provider provenance:
```json
{
  "embedding_model": "openai/text-embedding-3-large",
  "embedding_dimensions": 3072,
  "classifier_schema_version": "1.0.0",
  "generated_at": "2026-09-11T00:00:00Z",
  "input_sha256": "…"
}
```

Composite similarity is **computed**, not physically mangled vectors:

```
score(A,B) = 0.70 * cosine(semantic_A, semantic_B)
           + 0.20 * cosine(role_A, role_B)
           + 0.10 * metadata_similarity(A,B)
```

`metadata_similarity` = cosine over L2-normalized one-hot of `structural_vector`. Changing embedding model or preprocessing rules changes provenance and is detectable via `input_sha256` / `registry_sha256` / `config_sha256`.

Provider behind adapter `embed(text) -> vector` so AFKAF is not married to OpenAI / local / enterprise.

---

## 6. Similarity Search

- No vector DB in V1. Corpus ≈ 200 prompts → 40k comparisons, trivial.
- Brute-force cosine, local computation.
- Output `artifacts/prompt-topology/neighbors.json`: map `P-ID → [ {prompt_id, score, semantic, role, metadata} ]` sorted descending by `score`, then `prompt_id` ascending; top `neighbors.top_k = 15`.
- Also compute reverse neighbors for asymmetry detection (`P105` ranks `P117` top-1 but `P117` has 10 closer → bridge prompt).

---

## 7. Clustering

- **HDBSCAN**, not k-means (unknown k, variable sizes, legitimate outliers, sparse/dense coexistence, `UNKNOWN` desirable).
- Input: moderate reduced space from embeddings (`PCA 50D → optional UMAP 10-15D → HDBSCAN`; V1 simple `PCA 30-50D → HDBSCAN`; never the 3D coordinates).
- Deterministic stable cluster IDs: `C-` + first 6 hex chars of `SHA256(sorted(member_prompt_ids).join(','))` uppercase. Membership change ⇒ identity change (useful evidence). Raw HDBSCAN integer labels are never persisted.

---

## 8. Family vs Cluster (Critical Distinction)

- **Family** = human-stable ontology concept (`Build & Repair`, `Validate & Protect`, …​ — the 6 lifecycle sections). Lives in `prompt-classification.v1.json`; topology may recommend but never silently rewrites it.
- **Cluster** = machine-discovered local grouping (`C-18C5A7`). One family may contain several clusters (e.g. `Build & Repair → C-REM-TRUTH, C-DEPLOY-VAL, …​`).

Per prompt classification preserves both:

```json
{ "declared_family": "Build & Repair", "inferred_family": "Build & Repair", "family_alignment": "MATCH" }
{ "declared_family": "Validate & Protect", "inferred_family": "Build & Repair", "family_alignment": "DRIFT" }
```

`DRIFT` is governance gold.

---

## 9. Confidence & States

Signals: `neighbor_agreement` (fraction top-5 neighbors sharing inferred family), `cluster_membership_probability`, `family_majority_strength`, `distance_from_centroid`, `declared_agreement`.

Formula (config): `0.30*neighbor_agreement + 0.30*cluster_membership_probability + 0.20*family_majority_strength + 0.10*(1 - normalized_distance) + 0.10*declared_agreement`.

States: `HIGH ≥0.85`, `MEDIUM ≥0.65`, `LOW ≥0.45`, `UNCLASSIFIED <0.45`, plus orthogonal `AMBIGUOUS` (no family majority), `OUTLIER` (HDBSCAN -1), `DRIFT` (declared≠inferred). Those are states, not failures; validator decides acceptability.

---

## 10. Duplicate / Strengthen Detection

Thresholds produce **review candidates**, not auto-duplicate declarations:

- `≥0.94` `POSSIBLE_DUPLICATE`
- `≥0.88` `STRENGTHEN_EXISTING_CANDIDATE`
- `≥0.78` `RELATED`

Requires role similarity check; lexical resemblance alone must not merge different workflow positions. Decision packet example in `schema.v1.json:$defs/afkaf_new_prompt_decision`. New prompt with `POSSIBLE_DUPLICATE` blocks AFKAF creation gate until explicit `STRENGTHEN` vs `CREATE_NEW` disposition is recorded.

---

## 11. 3D Projection (Visualization Only)

- After topology established: `semantic/composite vectors → UMAP(n_components=3, n_neighbors=15, min_dist=0.15, metric=cosine, random_seed=42) → {x,y,z}`.
- Saved as `projection-3d.json` with full provenance; random seed mandatory (otherwise galaxy rearranges every run).
- Never feeds clustering or classification.

Shapes downstream of projection: V1 `bounding-sphere` (centroid + 95th-percentile radius), V2 `convex-hull`, V3 `alpha-shape`; shape correctness never blocks classifier.

---

## 12. Generated Kit Ordering — Deterministic Total Order

**Owned scope commitment:** stable IDs, derived placement. Never renumber.

Output: `artifacts/prompt-topology/kit-order.json`.

### 12.1 Ordering Keys (in priority order)

1. **Explicit family order** — `config.ordering.family_order` (`foundation → discover-plan → build-repair → validate-protect → integrate-ship → autonomy → outliers`). Any family not in list sorts after `autonomy` lexicographically; `outliers` group always last.
2. **Cluster position/order** — within each family, clusters sorted by `(-member_count, cluster_id_lexicographic)`. Larger (more representative) cluster first; `C-XXXXXX` lexicographic guarantees stability for equal sizes. Rejected alternative: sorting by 3D centroid (would couple ordering to stochastic projection).
3. **Sprint-path role** — within each cluster, `role_rank` = index in `config.ordering.sprint_role_order` (explicit ordered list of ~90 types from `SETUP` through `CLOSEOUT + VALIDATE`); unlisted types sort after listed, lexicographically.
4. **Intra-cluster semantic centrality** — `centrality(P) = mean_{Q∈cluster} score(P,Q)` (composite similarity). Higher first; rounds to 4 decimals so most representative prompt leads the cluster.
5. **Prompt ID as deterministic tie-break** — `seq_int` then `prompt_id` lexicographic; guarantees strict total order even when 1-4 tie.

### 12.2 Construction

```
linear_order = flatten(
  groups in family_order:
    clusters sorted by cluster_order_key:
      prompts sorted by (role_rank, -centrality, seq_int, prompt_id)
)
outliers_group (family_id=outliers, cluster_id=OUTLIER) appended last
```

`kit-order.json` stores both `groups` (hierarchical, with family/cluster/prompt nesting for renderers) and `linear_order` (flat total order for validators and AFKAF). Every registered prompt appears exactly once; duplicates or missing entries are structural hard fails.

### 12.3 Source vs Derived Boundary

- `web/prompt-kit/index.html` canonical library order remains `sequence_ascending` per `harness/contracts/prompt-kit-order-navigation.v1.json`.
- Topology `linear_order` is **recommendation/discovery metadata** (`discoveryRank`-style), usable for guided views or future 3D explorer, but must not silently replace sequence order. This preserves `stable_prompt_identity` and keeps legacy topology order from becoming a second source of truth.

### 12.4 Example

```json
{
  "family_order": ["foundation","discover-plan","build-repair","validate-protect","integrate-ship","autonomy"],
  "groups": [
    { "family": "Build & Repair", "family_id": "build-repair", "clusters": [
      { "cluster_id": "C-18C5A7", "prompts": ["P091","P105","P117"] },
      { "cluster_id": "C-2B91F3", "prompts": ["P074","P088"] }
    ]}
  ],
  "linear_order": ["P00","P01","P03","P091","P105", "..."],
  "outliers_group": { "family": "Outliers", "family_id": "outliers", "cluster_id": "OUTLIER", "prompts": ["P99"] }
}
```

### 12.5 Formal Properties

- **Total order:** `linear_order` defines a strict weak ordering that is total (antisymmetric, transitive, total) over the registered prompt set.
- **Determinism:** sort keys use only deterministic inputs (family/role explicit orders, content-addressed cluster IDs, centrality computed from deterministic similarities, integer seq, lexical ID). No timestamps, no hash randomization, no projection coordinates.
- **Stability:** adding a new prompt that falls into an existing cluster perturbs only that cluster's internal tail; family and cluster ranks of unrelated groups remain stable.
- **Reconstructability:** deleting `artifacts/prompt-topology/*` and rerunning with same registry + config + embeddings yields byte-identical `kit-order.json` (canonical JSON, sorted keys, rounded floats).

---

## 13. Artifact Tree

```
harness/prompt-topology/
  schema.v1.json     ← this contract: all artifact shapes + determinism rules
  config.v1.json     ← weights, thresholds, seeds, explicit family/role orders
  README.md          ← you are here

scripts/prompt-topology/           (future implementation, not in design-only scope)
  build-records.py   canonical records + validation
  embed.py           provider adapter (+ fixture mode for deterministic CI)
  neighbors.py       brute-force cosine + reverse neighbors
  cluster.py         reduction + HDBSCAN + classifications
  project.py         UMAP(3) visualization only
  order.py           deterministic kit ordering (this spec)
  validate.py        structural vs semantic gates + validation-report.json
  run.py             orchestrator + run-manifest.json

artifacts/prompt-topology/         (generated, disposable, gitignored until schema freeze)
  canonical-prompts.json
  feature-views.json
  embeddings.json
  neighbors.json
  clusters.json
  classifications.json
  projection-3d.json               ← future visualization-ready coordinates
  kit-order.json                   ← ordering manifest
  validation-report.json
  run-manifest.json
```

---

## 14. Run Manifest

Every run embeds provenance so topology changes are detectable:

`run-manifest.json` includes `schema_version`, `classifier_version`, `source_commit`, `registry_sha256`, `embedding_model/dimensions`, `cluster_algorithm`, `projection_algorithm`, `random_seed`, `prompt_count/embedded/classified/unclassified/outlier_count`, `ordering_policy_version`, `input_config_sha256`, `artifact_hashes` map.

---

## 15. Validation Gates

**Structural hard fails** (must be 0 for PASS):
`PROMPT_MISSING_FROM_TOPOLOGY`, `DUPLICATE_PROMPT_ID`, `EMBEDDING_COUNT_MISMATCH`, `INVALID_VECTOR_DIMENSION`, `NONDETERMINISTIC_INPUT_HASH`, `KIT_ORDER_DUPLICATE`, `KIT_ORDER_MISSING_PROMPT`, `UNKNOWN_CLUSTER_REFERENCE`, `EMBEDDING_MODEL_MISMATCH`, `PROJECTION_MISSING_PROMPT`, `NEIGHBOR_COUNT_MISMATCH`.

**Semantic warnings** (reported, not auto-fail; threshold policy decides gate):
`CLASSIFICATION_DRIFT`, `POSSIBLE_DUPLICATE`, `AMBIGUOUS_FAMILY`, `OUTLIER`, `LOW_CONFIDENCE`, `CROSS_FAMILY_NEAREST_NEIGHBOR`, `STRENGTHEN_EXISTING_CANDIDATE`, `UNCLASSIFIED`.

Special gate: **new prompt with `POSSIBLE_DUPLICATE` (composite ≥0.94, role ≥0.88, same sprint_path_role) fails AFKAF contribution gate until explicit disposition.

---

## 16. New-Prompt AFKAF Flow (Creation Gate)

```
proposed prompt → canonicalize → embed proposed → compare vs current topology
  → top neighbors + candidate family/cluster + decision packet
  → DISPOSITION: STRENGTHEN PXXX | CREATE_NEW | POSSIBLE_DUPLICATE (block)
```

Only after surviving this gate may `scripts/prompt_registry_ops.py` allocate a new prompt identity. Topology becomes a **creation gate**, answering "stop scattering prompts."

---

## 17. Incremental Rebuilds

- V1: rebuild everything (cheap at <1000 prompts).
- Later: cache embeddings by `SHA256(canonical_sha256 + embedding_model + classifier_schema_version)`; reuse unchanged, regenerate changed; neighbors + clustering always recompute globally (right compromise).

---

## 18. Definition of Done (for future implementation sprint)

- [ ] Every registered prompt produces exactly one canonical record.
- [ ] Every canonical prompt receives an embedding or explicit failure.
- [ ] Every prompt has top-N semantic neighbors (N=15) with composite scores.
- [ ] Clustering (HDBSCAN) permits legitimate outliers; 3D never drives classification.
- [ ] Declared vs inferred classification preserved separately; drift surfaced.
- [ ] 3D coordinates exist but ordering never reads them.
- [ ] Prompt IDs unchanged; generated order is hierarchical total order with deterministic tie-breaks.
- [ ] Kit order places related clusters together; outliers last; centrality leads each cluster.
- [ ] New highly overlapping prompt triggers `STRENGTHEN/duplicate` review before ID allocation.
- [ ] Same source + config + embedding responses ⇒ byte-identical artifacts (canonical JSON, rounded floats, seeded randomness).
- [ ] `artifacts/prompt-topology/*` deletable and reconstructable; validator proves disposable/reconstructable property.

---

## 19. Scope Guardrails

- **Forbidden this lane:** NodeWeaver implementation, wholesale Prompt Kit ontology rewrite, prompt-ID renumbering, replacing existing registry truth, UI/3D viewer implementation.
- **This design may recommend** family/cluster reassignments or `STRENGTHEN` vs `CREATE_NEW`, but registry mutation remains an explicit, separately validated P07/P79-owned operation.

---

## 20. References

- `harness/contracts/prompt-kit-order-navigation.v1.json` — stable prompt identity contract (topology ordering is complementary, not replacement).
- `harness/specs/prompt-operations.md` — prompt contribution path (registry → generated site parity).
- `registry/prompts/prompt-classification.v1.json` — lifecycle family authority.
- `harness/manifest.v1.json` — harness domain registration (topology domain to be registered at implementation promotion).
