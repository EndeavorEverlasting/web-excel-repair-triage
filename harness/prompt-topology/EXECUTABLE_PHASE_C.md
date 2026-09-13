# Executable Phase C — Read-Only Immersive Prompt Topology Viewer

Phase C begins only after executable Phase A semantic topology and executable Phase B deterministic projection are validated. Its job is to make those artifacts inspectable by a human without turning presentation geometry into a second source of semantic truth.

## Current execution slice

This slice delivers one deterministic, dependency-free browser viewer at `Outputs/prompt-topology-viewer/index.html`. It is generated from the exact Phase A topology, Phase B projection, and Phase B projection-state artifacts. The builder fails closed when the state does not bind to the topology hash, when the projection hash does not bind to state, or when prompt IDs and projected point IDs differ.

The baseline interaction model is intentionally small but useful:

- drag the universe to rotate it;
- use the mouse wheel to zoom;
- hover a node to identify it and soften unrelated nodes;
- click a prompt to pin selection and inspect semantic relationships;
- search by prompt ID, title, family, type, or keyword and focus the best match;
- focus a discovered cluster without rewriting cluster membership;
- inspect relationship channels and advisory opportunity states from Phase A evidence.

The renderer uses a 2D canvas with deterministic perspective projection of the Phase B 3D coordinates. This keeps the first executable viewer zero-dependency, portable, testable, and easy to replace later with WebGL without changing its data contract.

## Source and artifact ownership

- Phase C contract: `harness/prompt-topology/phase-c-viewer.v1.json`
- Viewer JavaScript: `docs/prompt-topology-viewer.js`
- Viewer CSS: `docs/prompt-topology-viewer.css`
- Deterministic builder: `scripts/build_prompt_topology_viewer.py`
- Canonical runtime viewer: `Outputs/prompt-topology-viewer/index.html` (gitignored/CI artifact until publication is separately proven)
- Focused tests: `tests/test_prompt_topology_phase_c.py`
- Observed browser proof: `tests/prompt_topology_viewer_browser_proof.py`
- Provider gate: `.github/workflows/prompt-topology-phase-c.yml`

## Source-of-truth boundary

Phase C may read prompt IDs, titles, declared families, prompt types, clusters, edge channels, opportunity records, and Phase B coordinates. It may derive transient screen coordinates, depth, opacity, display labels, selection state, search matches, and cluster focus state.

It may not derive or persist a new semantic cluster, relationship, family, opportunity state, prompt identity, sequence, or projection epoch. Screen distance is not semantic evidence. Rotation and zoom are presentation state only.

## Privacy and runtime boundary

The generated viewer is self-contained. After the HTML document loads it performs no fetch/XHR/WebSocket/EventSource/sendBeacon calls, records no telemetry, creates no analytics identity, and writes no localStorage/sessionStorage state. Browser proof must fail if these boundaries regress.

## Build and validation

```bash
python -m pip install -r requirements-prompt-topology.txt
python scripts/validate_prompt_topology.py --summary
python -m unittest tests.test_prompt_topology_phase_a tests.test_prompt_topology_phase_b tests.test_prompt_topology_phase_c -v

python scripts/prompt-topology/run.py --output artifacts/prompt-topology/topology.v1.json --summary
python scripts/prompt-topology/project.py \
  --topology artifacts/prompt-topology/topology.v1.json \
  --output artifacts/prompt-topology/projection-3d.json \
  --state-output artifacts/prompt-topology/projection-state.v1.json \
  --summary

python scripts/build_prompt_topology_viewer.py \
  --topology artifacts/prompt-topology/topology.v1.json \
  --projection artifacts/prompt-topology/projection-3d.json \
  --state artifacts/prompt-topology/projection-state.v1.json \
  --output Outputs/prompt-topology-viewer/index.html

python scripts/build_prompt_topology_viewer.py \
  --topology artifacts/prompt-topology/topology.v1.json \
  --projection artifacts/prompt-topology/projection-3d.json \
  --state artifacts/prompt-topology/projection-state.v1.json \
  --output Outputs/prompt-topology-viewer/index.html \
  --check

node --check docs/prompt-topology-viewer.js
python tests/prompt_topology_viewer_browser_proof.py
```

When canonical `artifacts/prompt-topology/*.json` are absent, the builder may reconstruct Phase A and Phase B in a temporary directory through their existing canonical producers. It does not make the generated runtime JSON tracked source truth.

## Successor map

The next viewer phases remain deliberately separate from this baseline:

1. **Shape refinement** — cluster envelopes/hulls may be added only as derived rendering aids and must remain non-semantic.
2. **Publication** — add a stable public navigation/delivery surface only after repository and browser proof are green.
3. **Usability refinement** — tune layout, labels, keyboard access, and visual density from observed interaction evidence.
4. **WebGL acceleration** — move rendering to WebGL only if measured node/edge scale or interaction performance justifies it; preserve the same artifact bindings.

Live telemetry, session/user analytics, vector-database infrastructure, NodeWeaver expansion, prompt renumbering, and projection-driven classification are not successor viewer phases under this contract.

## Proof ceiling

A green repository and Chromium run proves that this exact generated artifact is bound to exact Phase A/B evidence and that the tested interactions work in the observed headless Chromium environment. It does not prove GitHub Pages deployment, every browser/GPU/input device, production acceptance, or changes to the semantic classifier.
