#!/usr/bin/env python3
"""Build deterministic Prompt Topology Phase B 3D projection artifacts."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
for value in (str(SCRIPT_DIR), str(REPO_ROOT)):
    if value not in sys.path:
        sys.path.insert(0, value)

import pipeline  # noqa: E402
import projection  # noqa: E402
import run as phase_a_run  # noqa: E402
from scripts import build_prompt_kit_registry as registry  # noqa: E402
from scripts import prompt_classification  # noqa: E402

PHASE_B_CONTRACT = REPO_ROOT / "harness" / "prompt-topology" / "phase-b-projection.v1.json"
DEFAULT_TOPOLOGY = REPO_ROOT / "artifacts" / "prompt-topology" / "topology.v1.json"
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "prompt-topology" / "projection-3d.json"
DEFAULT_STATE_OUTPUT = REPO_ROOT / "artifacts" / "prompt-topology" / "projection-state.v1.json"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected JSON object: {path}")
    return payload


def _projection_config() -> projection.ProjectionConfig:
    cfg = _load_json(phase_a_run.CONFIG_PATH)["pipeline"]["projection_3d"]
    params = cfg["parameters"]
    phase_b = _load_json(PHASE_B_CONTRACT)
    stability = phase_b["spatial_stability"]
    return projection.ProjectionConfig(
        n_components=int(params["n_components"]),
        n_neighbors=int(params["n_neighbors"]),
        min_dist=float(params["min_dist"]),
        metric=str(params["metric"]),
        random_seed=int(params["random_seed"]),
        coordinate_decimals=int(phase_b["serialization"]["coordinate_decimals"]),
        minimum_anchors=int(phase_b["alignment"]["minimum_anchors"]),
        rms_displacement_limit=float(stability["rms_displacement_limit"]),
        max_displacement_limit=float(stability["max_displacement_limit"]),
    )


def _inputs(*, shuffle_source: bool = False) -> tuple[list[dict], list[dict]]:
    prompts = registry.load_prompt_kit_registry()
    if shuffle_source:
        prompts = list(reversed(copy.deepcopy(prompts)))
    sections = prompt_classification.load_policy()["sections"]
    return prompts, sections


def build(
    *,
    topology: dict[str, Any] | None = None,
    shuffle_source: bool = False,
    previous_projection: dict[str, Any] | None = None,
    previous_state: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    prompts, sections = _inputs(shuffle_source=shuffle_source)
    topology_artifact = topology or phase_a_run.build(shuffle_source=shuffle_source)
    canonical_ids = [str(item["id"]).upper() for item in sorted(prompts, key=lambda item: (int(str(item["seq"])), str(item["id"])))]
    pipeline.validate_topology(topology_artifact, canonical_ids)
    projection_artifact, state = projection.build_projection(
        topology_artifact,
        prompts,
        sections,
        phase_a_config=phase_a_run._runtime_config(),
        config=_projection_config(),
        previous_projection=previous_projection,
        previous_state=previous_state,
    )
    return topology_artifact, projection_artifact, state


def _write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topology", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--state-output", type=Path, default=DEFAULT_STATE_OUTPUT)
    parser.add_argument("--previous-projection", type=Path)
    parser.add_argument("--previous-state", type=Path)
    parser.add_argument("--shuffle-source", action="store_true")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Prove repeated/shuffled projection identity and compare existing outputs when present.",
    )
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    if bool(args.previous_projection) != bool(args.previous_state):
        raise SystemExit("--previous-projection and --previous-state must be supplied together")

    topology = _load_json(args.topology) if args.topology else None
    previous_projection = _load_json(args.previous_projection) if args.previous_projection else None
    previous_state = _load_json(args.previous_state) if args.previous_state else None

    topology_artifact, projection_artifact, state = build(
        topology=topology,
        shuffle_source=args.shuffle_source,
        previous_projection=previous_projection,
        previous_state=previous_state,
    )
    projection_bytes = projection.projection_bytes(projection_artifact)
    state_bytes = projection.state_bytes(state)

    if args.check:
        _, repeat_projection, repeat_state = build(
            topology=topology_artifact,
            previous_projection=previous_projection,
            previous_state=previous_state,
        )
        _, shuffled_projection, shuffled_state = build(
            topology=topology_artifact,
            shuffle_source=True,
            previous_projection=previous_projection,
            previous_state=previous_state,
        )
        if projection_bytes != projection.projection_bytes(repeat_projection):
            raise SystemExit("Projection determinism failure: repeated build differs")
        if projection_bytes != projection.projection_bytes(shuffled_projection):
            raise SystemExit("Projection determinism failure: shuffled source differs")
        if state_bytes != projection.state_bytes(repeat_state):
            raise SystemExit("Projection-state determinism failure: repeated build differs")
        if state_bytes != projection.state_bytes(shuffled_state):
            raise SystemExit("Projection-state determinism failure: shuffled source differs")
        if args.output.is_file() and args.output.read_bytes() != projection_bytes:
            raise SystemExit(f"Projection parity failure: {args.output}")
        if args.state_output.is_file() and args.state_output.read_bytes() != state_bytes:
            raise SystemExit(f"Projection-state parity failure: {args.state_output}")
        print(
            "Prompt topology Phase B determinism: PASS — "
            f"epoch={state['epoch_id']} topology={state['topology_content_hash_sha256']}"
        )
        return 0

    _write(args.output, projection_bytes)
    _write(args.state_output, state_bytes)
    if args.summary:
        print(json.dumps({
            "status": "PASS",
            "projection_output": str(args.output),
            "state_output": str(args.state_output),
            "epoch_id": state["epoch_id"],
            "topology_content_hash_sha256": state["topology_content_hash_sha256"],
            "projection_sha256": state["projection_sha256"],
            "prompt_count": state["prompt_count"],
            "alignment_mode": state["alignment"]["mode"],
            "anchor_count": state["alignment"]["anchor_count"],
        }, sort_keys=True))
    else:
        print(args.output)
        print(args.state_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
