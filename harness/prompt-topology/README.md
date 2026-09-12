# Prompt Topology — Executable Phase A

**Authority:** `schema.v1.json` + `config.v1.json` + `harness/contracts/prompt-topology-classifier.v1.json`  
**Canonical source:** `scripts/build_prompt_kit_registry.py:load_prompt_kit_registry`  
**Canonical derived artifact:** `artifacts/prompt-topology/topology.v1.json`

Phase A turns the live Prompt Kit registry into renderer-neutral semantic topology. The registry remains authoritative for identity; generated topology is disposable evidence.

## Executable flow

`Prompt Registry → canonical nodes → deterministic local feature vectors → pair similarity → multi-channel graph → PCA → HDBSCAN → persistent-cluster reconciliation → opportunity scoring → topology.v1.json → fail-closed validation`

Every prompt is exactly one node and its existing `P…` ID is the node ID. Every unordered prompt pair has at most one edge; that edge may carry multiple relationship channels. Phase A populates `SEMANTIC_NEIGHBOR`, `WORKFLOW_NEXT`, `CLASS_FAMILY`, `SHARED_SCOPE`, `SHARED_EVIDENCE`, and `TUTORIAL_ROUTE`. Behavior channels (`CO_USAGE`, `TRANSITION`, `SUBSTITUTION`, `COMPLEMENT`) are reserved and must remain absent until a privacy-bounded telemetry phase is separately authorized.

## Stable cluster identity

`cluster_id` is persistent identity, not an exact-membership hash. The first accepted cluster receives a deterministic ID. Future runs may inherit that ID from the highest-overlap unused prior cluster when Jaccard overlap is at least the configured threshold. `membership_fingerprint_sha256` independently records exact current membership. Lineage records `NEW`, `UNCHANGED`, `EXPANDED`, `CONTRACTED`, or `REVISED`.

## Opportunity intelligence

Opportunity output is advisory. Components are semantic gap, ambiguity, underdevelopment, redundancy penalty, and workflow gap. The scorer emits one of `HEALTHY`, `UNDERDEVELOPED`, `AMBIGUOUS`, `FRAGMENTED`, `REDUNDANT`, or `EMERGING` plus a recommended action. It may not create, rewrite, delete, or renumber prompts.

## Determinism and disposability

```bash
python -m pip install -r requirements-prompt-topology.txt
python scripts/validate_prompt_topology.py --summary
python -m unittest tests.test_prompt_topology_phase_a -v
python scripts/prompt-topology/run.py --summary
python scripts/prompt-topology/run.py --check
python scripts/prompt-topology/validate.py --rebuild --summary
```

The same canonical registry/config/previous-topology input must produce byte-identical output. Reversing source enumeration must produce the same bytes. Generated state under `artifacts/prompt-topology/` is ignored by Git and may be deleted and regenerated.

## Phase boundary

Phase A contains no 3D coordinates, projection epochs, cluster envelopes, WebGL/Three.js/R3F viewer, telemetry, session tracking, analytics, vector database, NodeWeaver expansion, prompt renumbering, or broad ontology rewrite. Phase B may consume the canonical topology artifact to derive stable 3D projection state, but projection must never redefine semantic truth.
