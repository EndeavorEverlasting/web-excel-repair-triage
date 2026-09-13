# Prompt Topology Successor Roadmap — Phase B / Phase C

**Status:** durable successor plan; Phase A is complete and is not reopened by this document.  
**Plan owner:** `harness/prompt-topology/PHASE_B_C_ROADMAP.md`  
**Semantic authority:** the current Prompt Kit registry plus `harness/prompt-topology/schema.v1.json`, `config.v1.json`, `phase-a-refinements.v1.json`, and the executable Phase A pipeline.  
**Historical Phase A integration:** `b627ce43254b603d8b197ca704aaebfc3730572e`.

## Why this file exists

The original topology design already specified visualization-only UMAP projection and downstream shapes, while `EXECUTABLE_PHASE_A.md` deliberately stopped before projection/viewer work. Phase A later became executable without creating one current successor plan. This file closes that durability gap: future agents should recover the successor roadmap from the repository, not from the chat that discussed it.

## Proven floor — Phase A COMPLETE

Phase A owns semantic truth:

`registry -> deterministic feature/embedding seam -> multi-channel graph -> deterministic PCA -> HDBSCAN/outliers -> persistent cluster reconciliation -> advisory opportunities -> artifacts/prompt-topology/topology.v1.json`

Phase A invariants remain binding throughout later phases:

- prompt IDs remain canonical node identity;
- semantic topology is derived evidence and never silently rewrites registry truth;
- projection/viewer output cannot influence clustering, classification, opportunities, or registry mutation;
- generated topology is reproducible from current canonical inputs;
- later visualization work consumes Phase A output rather than replacing it.

## Phase B — Deterministic 3D projection + spatial stability

### Dependency
A freshly rebuilt and validated Phase A topology for the current registry floor.

### Owned scope
- a renderer-neutral 3D projection artifact derived from Phase A node vectors/topology;
- deterministic projection implementation using the existing `config.v1.json` UMAP contract (`n_components=3`, cosine metric, fixed seed 42 unless the canonical config is explicitly revised);
- projection provenance and validator coverage;
- spatial-stability reconciliation against a previous accepted projection when one exists;
- visualization-only cluster envelopes, beginning with the existing bounding-sphere contract;
- focused CI evidence for determinism and semantic non-interference.

### Spatial-stability rule
Fixed randomness is necessary but not sufficient once the corpus changes. Phase B must align a new projection to the previous accepted projection using unchanged prompt IDs as anchors before publishing coordinates. The implementation may use a deterministic rigid/orthogonal Procrustes-style alignment or an equivalently bounded canonical method, but the chosen method must be encoded in config/schema and proven by fixtures. If the anchor set is insufficient, publish an explicit lineage/reset state rather than pretending coordinates are spatially continuous.

### Required artifacts
- `artifacts/prompt-topology/projection-3d.json` (or an explicitly versioned successor chosen by schema migration);
- projection provenance: algorithm, dimensions, parameters, random seed, Phase A content hash/input identity, prior projection identity when aligned, stability method/result;
- cluster envelope metadata downstream of coordinates;
- validation receipt proving node parity, determinism, and semantic non-interference.

### Acceptance gates
- identical Phase A inputs + identical projection config produce byte-identical canonical projection output;
- shuffled input order does not alter canonical output;
- every projected prompt references exactly one Phase A node and no unknown node appears;
- deleting/regenerating projection cannot change Phase A semantic topology/content hash;
- unchanged anchor nodes preserve orientation/continuity within an explicit tested tolerance after alignment;
- insufficient continuity evidence fails closed to a declared reset/lineage state;
- projection remains visualization-only.

### Forbidden in Phase B
Interactive viewer implementation, live usage/session telemetry, `CO_USAGE`, `TRANSITION`, `SUBSTITUTION`, `COMPLEMENT`, vector database introduction, prompt renumbering, or registry mutation driven by coordinates.

## Phase C — Read-only interactive topology viewer

### Dependency
Accepted Phase B projection plus current validated Phase A semantic topology.

### Owned scope
- an interactive 3D explorer that consumes canonical Phase A + Phase B artifacts without recomputing semantic truth;
- node selection/search and readable prompt identity/title/family/cluster/outlier/opportunity context;
- family/cluster visibility controls and relationship-edge inspection;
- navigation that preserves stable prompt IDs and existing canonical Prompt Kit sequence semantics;
- graceful failure when projection or semantic artifacts are stale/mismatched;
- accessibility/performance checks appropriate to the chosen renderer.

### Viewer invariants
- renderer state is presentation state only;
- moving/hiding/filtering nodes cannot mutate registry, cluster identity, or topology artifacts;
- the viewer must bind displayed data to exact artifact/provenance identities and reject mismatched Phase A/Phase B generations;
- topology recommendation order may aid discovery but never silently replaces canonical sequence ordering.

### Acceptance gates
- viewer loads the exact canonical artifacts and exposes their identities/provenance;
- representative nodes, outliers, clusters, multi-channel edges, and opportunities can be inspected;
- stale/mismatched artifacts fail visibly rather than being combined;
- no viewer action changes semantic artifact hashes or canonical registry state;
- observed browser proof covers navigation, selection, filtering, and artifact-mismatch behavior.

### Forbidden in Phase C
Telemetry-driven topology mutation, automatic prompt rewriting, vector DB migration, prompt renumbering, or treating visual proximity as classification truth.

## Later / explicitly deferred lanes

### Behavioral telemetry channels
`CO_USAGE`, `TRANSITION`, `SUBSTITUTION`, and `COMPLEMENT` remain a later evidence layer. They require a separate privacy/provenance/session-identity contract and must join the graph as typed evidence without rewriting semantic channels by default.

### Vector database
Deferred. Current corpus scale does not justify it. Reconsider only when measured corpus/query/runtime evidence shows brute-force/local storage is the limiting factor.

### Prompt identity / ontology rewrites
Prompt renumbering remains forbidden. Family/ontology changes require their own explicit P07/P79-owned registry mutation and proof; neither projection nor viewer behavior authorizes them.

## Execution order

1. Refresh current default branch and rebuild/validate Phase A on the current registry.
2. Declare a new bounded **Prompt Topology Phase B** sprint from this file; implement and integrate projection + spatial-stability proof.
3. Refresh main and verify Phase B containment/provenance.
4. Declare a new bounded **Prompt Topology Phase C** sprint; implement and integrate the read-only viewer.
5. Only after Phase C proof, evaluate whether behavioral telemetry has enough evidence and privacy/provenance design to justify a separate successor sprint.

This roadmap is the durable execution dependency. Chat may summarize it, but future agents should sprint from this file and refreshed repository/provider truth.
