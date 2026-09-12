# scripts/prompt-topology — Phase A executors

This directory owns the executable, deterministic semantic-topology pipeline. It intentionally stops before 3D projection and live behavior collection.

| File | Responsibility |
|---|---|
| `topology_core.py` | Canonical prompt records, deterministic local vector seam, pair similarity, shared enums/helpers |
| `topology_graph.py` | Multi-channel edge construction |
| `topology_cluster.py` | PCA/HDBSCAN, persistent-cluster reconciliation, opportunity scoring |
| `pipeline.py` | Phase A orchestration, canonical artifact assembly, structural validation, serialization |
| `run.py` | Loads the live Prompt Kit/classification/tutorial owners and writes `artifacts/prompt-topology/topology.v1.json`; `--check` proves repeated and shuffled-input byte identity |
| `validate.py` | Fails closed on live registry parity, edge/cluster/opportunity invariants, content hash, and optional byte-identical live rebuild |

Install the scoped runtime dependencies with `python -m pip install -r requirements-prompt-topology.txt`. The default embedding seam is `local-hashing-vectorizer/v1`: deterministic, network-free, and replaceable. The semantic graph—not any future projection—is authoritative derived evidence.

Use `--previous-topology <accepted topology.v1.json>` when proving persistent cluster identity across an accepted prior topology. The previous topology is an explicit versioned input; the current output is never silently used as its own predecessor.
