# scripts/prompt-topology — Future Orchestrator Stubs

This directory will own the deterministic pipeline executors. It is **not implemented** in the `design-only` branch — this README records the intended surface so future implementation does not invent a competing location.

## Intended executables

| Script | Stage | Input → Output |
|---|---|---|
| `build-records.py` | 1. Canonical records | `registry` + `prompt-classification` → `canonical-prompts.json` |
| `feature-views.py` | 2. Feature views | `canonical-prompts.json` → `feature-views.json` (semantic/role/structural) |
| `embed.py` | 3. Embeddings | `feature-views.json` → `embeddings.json` (provider adapter `embed(text)->vector`) |
| `neighbors.py` | 4. Similarity index | `embeddings.json` → `neighbors.json` (brute-force cosine, 0.70/0.20/0.10) |
| `cluster.py` | 5+7. Clustering + classification | `embeddings.json` + `neighbors.json` → `clusters.json` + `classifications.json` |
| `project.py` | 6. 3D projection | `embeddings.json` → `projection-3d.json` (UMAP 3D, seed 42, visualization only) |
| `order.py` | 8. Kit ordering | `classifications.json` + `neighbors.json` + `projection-3d.json` → `kit-order.json` |
| `validate.py` | 9. Validation | all artifacts → `validation-report.json` + exit code (0 = no structural errors) |
| `run.py` | orchestrator | runs 1→9 in order, writes `run-manifest.json`, enforces `--check` byte-identical rederivation |

## Determinism requirements (all future scripts must obey)

- Canonical JSON: sorted keys, UTF-8, LF, 2-space indent, no trailing whitespace; hashes computed over that form.
- Rounded persistence: vectors 6 decimals, scores/centrality 4 decimals.
- Explicit seeds: HDBSCAN 42, UMAP 42; no unseeded randomness.
- Content-addressed cluster IDs: `C-` + first 6 hex of `SHA256(sorted member ids joined by ',')`.
- Ordering never reads `projection-3d.json` coordinates.

## Provider adapter

```python
# embed.py
def embed(text: str, model: str, provider: str) -> list[float]:
    # adapter — route to OpenAI / local sentence-transformers / Ollama / enterprise
    # return L2-normalized vector
```

V1 must support `--provider local` fixture mode that replays canned vectors for deterministic CI (no network).

## Disposability test

```bash
rm -rf artifacts/prompt-topology/*
python scripts/prompt-topology/run.py --provider local
python scripts/prompt-topology/validate.py --artifacts artifacts/prompt-topology --summary
python scripts/prompt-topology/run.py --provider local --check  # must pass byte-identical
```

## Forbidden this lane

No implementation in the design-only branch. Do not add NodeWeaver, ontology rewrite, prompt-ID renumbering, or UI/3D viewer code here.
