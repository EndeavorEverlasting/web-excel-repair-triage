# Executable Phase B — Deterministic 3D Projection and Spatial Stability

Phase B starts only after executable Phase A has produced and validated the renderer-neutral semantic topology. It consumes `artifacts/prompt-topology/topology.v1.json`; it does not redefine prompt identity, edges, clusters, opportunity states, classification, or ordering.

## Owned behavior

- Regenerate canonical semantic vectors from the same Prompt Kit registry/config floor used by Phase A.
- Project those semantic vectors with the existing config authority:
  - UMAP
  - `n_components=3`
  - `n_neighbors=15`
  - `min_dist=0.15`
  - `metric=cosine`
  - `random_seed=42`
- Normalize the initial coordinate frame to zero center and unit RMS radius, then choose deterministic axis signs.
- Persist renderer-neutral coordinates as `artifacts/prompt-topology/projection-3d.json`.
- Persist epoch lineage, provenance, topology binding, anchor alignment, and displacement evidence as `artifacts/prompt-topology/projection-state.v1.json`.
- When a previous accepted projection/state is supplied, align all shared prompt anchors with orientation-preserving rigid orthogonal Procrustes. Scale changes and reflections are forbidden.
- Fail closed when shared-anchor RMS or maximum displacement exceeds the thresholds in `phase-b-projection.v1.json`.
- Require byte-identical repeated and shuffled-source builds for identical inputs.
- Require an unchanged Phase A topology plus accepted predecessor projection/state to reproduce byte-identical projection/state.

## Source-of-truth boundary

Projection is visualization evidence only. Phase A semantic topology remains authoritative derived evidence, and the Prompt Kit registry remains authoritative source truth. `projection-3d.json` never feeds HDBSCAN, opportunity scoring, declared/inferred family classification, prompt IDs, sequence order, or registry mutation.

The historical `$defs.projection_artifact` in `schema.v1.json` remains the coordinate artifact contract. Phase B adds the companion state artifact rather than widening the historical projection object with epoch/alignment fields that its `additionalProperties: false` contract forbids.

## Commands

```bash
python -m pip install -r requirements-prompt-topology.txt
python scripts/validate_prompt_topology.py --summary
python -m unittest tests.test_prompt_topology_phase_a tests.test_prompt_topology_phase_b -v

python scripts/prompt-topology/run.py \
  --output artifacts/prompt-topology/topology.v1.json \
  --summary

python scripts/prompt-topology/project.py \
  --topology artifacts/prompt-topology/topology.v1.json \
  --output artifacts/prompt-topology/projection-3d.json \
  --state-output artifacts/prompt-topology/projection-state.v1.json \
  --summary

python scripts/prompt-topology/project.py \
  --topology artifacts/prompt-topology/topology.v1.json \
  --output artifacts/prompt-topology/projection-3d.json \
  --state-output artifacts/prompt-topology/projection-state.v1.json \
  --check

python scripts/prompt-topology/validate_projection.py \
  --topology artifacts/prompt-topology/topology.v1.json \
  --projection artifacts/prompt-topology/projection-3d.json \
  --state artifacts/prompt-topology/projection-state.v1.json \
  --rebuild --summary
```

For a successor epoch, add both:

```bash
--previous-projection path/to/accepted/projection-3d.json \
--previous-state path/to/accepted/projection-state.v1.json
```

The predecessor pair is explicit versioned input. Current output is never silently treated as its own predecessor.

## Phase boundary

Phase B explicitly does **not** implement:

- WebGL, Three.js, React Three Fiber, camera controls, selection, or immersive viewer UI;
- live telemetry, session tracking, user analytics, or behavioral channels;
- cluster envelopes, convex hulls, alpha shapes, or other rendered shapes;
- vector database infrastructure;
- NodeWeaver expansion;
- prompt ID/sequence renumbering;
- any projection-driven semantic classification.

Those are not required to certify deterministic Phase B. Phase C may consume Phase B coordinates for the immersive viewer, but it must not redefine topology truth for aesthetics.
