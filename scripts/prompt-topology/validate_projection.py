#!/usr/bin/env python3
"""Validate executable Prompt Topology Phase B projection artifacts fail-closed."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
for value in (str(SCRIPT_DIR), str(REPO_ROOT)):
    if value not in sys.path:
        sys.path.insert(0, value)

import projection  # noqa: E402
import project  # noqa: E402
import run as phase_a_run  # noqa: E402

DEFAULT_TOPOLOGY = REPO_ROOT / "artifacts" / "prompt-topology" / "topology.v1.json"
DEFAULT_PROJECTION = REPO_ROOT / "artifacts" / "prompt-topology" / "projection-3d.json"
DEFAULT_STATE = REPO_ROOT / "artifacts" / "prompt-topology" / "projection-state.v1.json"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected JSON object: {path}")
    return payload


def _phase_b_contract() -> dict[str, Any]:
    contract = _load_json(project.PHASE_B_CONTRACT)
    if contract.get("schema_version") != "prompt-topology-phase-b-projection/v1":
        raise ValueError("Phase B contract schema drift")
    if contract["projection"]["algorithm"] != "umap":
        raise ValueError("Phase B projection algorithm drift")
    if contract["projection"]["visualization_only"] is not True:
        raise ValueError("Phase B projection must remain visualization-only")
    if contract["alignment"]["method"] != projection.ALIGNMENT_METHOD:
        raise ValueError("Phase B alignment method drift")
    if contract["phase_boundary"]["next_phase"].split()[0:2] != ["Phase", "C"]:
        raise ValueError("Phase B -> Phase C boundary drift")
    return contract


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topology", type=Path, default=DEFAULT_TOPOLOGY)
    parser.add_argument("--projection", type=Path, default=DEFAULT_PROJECTION)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    _phase_b_contract()
    topology = _load_json(args.topology)
    projection_artifact = _load_json(args.projection)
    state = _load_json(args.state)
    config = project._projection_config()

    projection.validate_projection_bundle(
        topology,
        projection_artifact,
        state,
        config=config,
    )

    if args.rebuild:
        rebuilt_topology, rebuilt_projection, rebuilt_state = project.build(topology=topology)
        if phase_a_run.pipeline.topology_bytes(rebuilt_topology) != phase_a_run.pipeline.topology_bytes(topology):
            raise SystemExit("Phase A topology changed during Phase B rebuild")
        if projection.projection_bytes(rebuilt_projection) != projection.projection_bytes(projection_artifact):
            raise SystemExit("Phase B projection rebuild differs from artifact")
        if projection.state_bytes(rebuilt_state) != projection.state_bytes(state):
            raise SystemExit("Phase B projection-state rebuild differs from artifact")

    if args.summary:
        print(json.dumps({
            "status": "PASS",
            "topology_content_hash_sha256": state["topology_content_hash_sha256"],
            "projection_sha256": state["projection_sha256"],
            "epoch_id": state["epoch_id"],
            "prompt_count": state["prompt_count"],
            "alignment_mode": state["alignment"]["mode"],
            "anchor_count": state["alignment"]["anchor_count"],
            "spatial_stability": state["alignment"]["within_limits"],
            "rebuild_verified": bool(args.rebuild),
        }, sort_keys=True))
    else:
        print("Prompt topology Phase B projection validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
