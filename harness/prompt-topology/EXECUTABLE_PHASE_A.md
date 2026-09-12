# Executable Phase A refinement

This file is an execution addendum to the existing Prompt Topology design contract; it does not replace that architecture. The exact superseded fields live in `phase-a-refinements.v1.json`.

Phase A now executes the live Prompt Kit registry into the renderer-neutral ignored artifact `artifacts/prompt-topology/topology.v1.json`. Prompt IDs remain node identity. One prompt pair produces at most one edge carrying multiple ordered relationship channels. HDBSCAN executes after deterministic PCA and may emit legitimate outliers.

The key refinement from the earlier design is cluster continuity: `cluster_id` is persistent identity reconciled against a previous accepted topology, while `membership_fingerprint_sha256` records exact current membership. A small expansion/contraction therefore changes the fingerprint without automatically inventing a new cluster identity.

Opportunity intelligence is deterministic and advisory only. It may recommend investigation, strengthening, workflow connection, tutorial improvement, classification review, or consolidation, but it never mutates canonical prompt registry truth.

Phase A deliberately excludes projection coordinates and viewer/telemetry work. The historical projection design remains future-facing context; it is not an executable Phase A dependency and cannot influence semantic graph truth.

## Proof commands

```bash
python -m pip install -r requirements-prompt-topology.txt
python scripts/validate_prompt_topology.py --summary
python -m unittest tests.test_prompt_topology_phase_a -v
python scripts/prompt-topology/run.py --summary
python scripts/prompt-topology/run.py --check
python scripts/prompt-topology/validate.py --rebuild --summary
```
