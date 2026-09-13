# scripts/prompt-topology — Phase A+B executors

This directory owns the executable deterministic semantic-topology pipeline and its visualization-only 3D projection leaf. Semantic topology remains authoritative derived evidence; Phase B coordinates cannot influence classification.

| File | Responsibility |
|---|---|
| `topology_core.py` | Canonical prompt records, deterministic local vector seam, pair similarity, shared enums/helpers |
| `topology_graph.py` | Multi-channel edge construction |
| `topology_cluster.py` | PCA/HDBSCAN, persistent-cluster reconciliation, opportunity scoring |
| `pipeline.py` | Phase A orchestration, canonical topology artifact assembly, structural validation, serialization |
| `run.py` | Loads live Prompt Kit/classification/tutorial owners and writes `artifacts/prompt-topology/topology.v1.json`; `--check` proves repeated/shuffled-input byte identity |
| `validate.py` | Fails closed on live registry parity, edge/cluster/opportunity invariants, content hash, and optional byte-identical Phase A rebuild |
| `projection.py` | Phase B UMAP(3), deterministic frame normalization, projection epochs, rigid shared-anchor alignment, displacement enforcement, artifact/state validation |
| `project.py` | Loads Phase A topology + live registry and writes `projection-3d.json` + `projection-state.v1.json`; `--check` proves repeated/shuffled-input byte identity |
| `validate_projection.py` | Fails closed on topology binding, point parity, state/projection hashes, spatial-stability evidence, and optional byte-identical Phase B rebuild |

Install scoped runtime dependencies with `python -m pip install -r requirements-prompt-topology.txt`. The Phase A embedding seam is `local-hashing-vectorizer/v1`: deterministic, network-free, and replaceable. Phase B consumes those canonical semantic vectors through fixed-seed UMAP and remains visualization-only.

Use `--previous-topology <accepted topology.v1.json>` for Phase A persistent cluster reconciliation. Use `--previous-projection <accepted projection-3d.json> --previous-state <accepted projection-state.v1.json>` for Phase B successor-epoch anchor alignment. Previous artifacts are explicit versioned inputs; current output is never silently used as its own predecessor.
