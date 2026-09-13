#!/usr/bin/env python3
"""Build the executable Phase A Prompt Kit semantic topology artifact."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
for value in (str(SCRIPT_DIR), str(REPO_ROOT)):
    if value not in sys.path:
        sys.path.insert(0, value)

import pipeline  # noqa: E402
from scripts import build_prompt_kit_registry as registry  # noqa: E402
from scripts import prompt_classification  # noqa: E402
from scripts import prompt_kit_tutorial_coverage as tutorial_coverage  # noqa: E402

CONFIG_PATH = REPO_ROOT / "harness" / "prompt-topology" / "config.v1.json"
REFINEMENTS_PATH = REPO_ROOT / "harness" / "prompt-topology" / "phase-a-refinements.v1.json"
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "prompt-topology" / "topology.v1.json"


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected JSON object: {path}")
    return payload


def _runtime_config() -> pipeline.RuntimeConfig:
    cfg = _load_json(CONFIG_PATH)
    pipe = cfg["pipeline"]
    weights = pipe["similarity"]["weights"]
    hdbscan = pipe["clustering"]["hdbscan_params"]
    family = pipe["classification"]["family_assignment"]
    duplicate = pipe["classification"]["duplicate_detection"]["thresholds"]
    refinements = _load_json(REFINEMENTS_PATH)
    identity = refinements["supersedes"]["config.pipeline.clustering.cluster_id_policy"]
    return pipeline.RuntimeConfig(
        semantic_weight=float(weights["semantic"]),
        role_weight=float(weights["role"]),
        metadata_weight=float(weights["metadata"]),
        neighbor_top_k=int(pipe["neighbors"]["top_k"]),
        embedding_dimensions=384,
        pca_dimensions=min(32, int(pipe["clustering"]["reduction"]["intermediate_pca_dimensions"])),
        min_cluster_size=int(hdbscan["min_cluster_size"]),
        min_samples=int(hdbscan["min_samples"]),
        cluster_selection_method=str(hdbscan["cluster_selection_method"]),
        family_majority_threshold=float(family["threshold"]),
        cluster_reconcile_min_jaccard=float(identity["reconcile_min_jaccard"]),
        duplicate_threshold=float(duplicate["STRENGTHEN_EXISTING_CANDIDATE"]),
    )


def _tutorial_routes(prompts: list[dict]) -> dict[str, dict]:
    report = tutorial_coverage.audit(prompts=prompts)
    if not report.get("ready"):
        raise SystemExit(
            "Tutorial coverage is not ready for topology derivation: "
            + json.dumps({
                "route_errors": report.get("route_errors"),
                "unknown_wired_prompt_ids": report.get("unknown_wired_prompt_ids"),
                "needs_wiring_prompt_ids": report.get("needs_wiring_prompt_ids"),
            }, sort_keys=True)
        )
    return {str(route["prompt_id"]): dict(route) for route in report["routes"]}


def build(*, shuffle_source: bool = False, previous_topology: dict | None = None) -> dict:
    prompts = registry.load_prompt_kit_registry()
    if shuffle_source:
        prompts = list(reversed(copy.deepcopy(prompts)))
    sections = prompt_classification.load_policy()["sections"]
    routes = _tutorial_routes(prompts)
    return pipeline.build_topology(
        prompts,
        sections,
        tutorial_routes=routes,
        previous_topology=previous_topology,
        config=_runtime_config(),
        source_provenance={
            "registry_loader": "scripts/build_prompt_kit_registry.py:load_prompt_kit_registry",
            "classification_policy": "registry/prompts/prompt-classification.v1.json",
            "tutorial_coverage": "scripts/prompt_kit_tutorial_coverage.py:audit",
            "runtime_config": "harness/prompt-topology/config.v1.json",
            "phase_a_refinements": "harness/prompt-topology/phase-a-refinements.v1.json",
        },
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--previous-topology", type=Path)
    parser.add_argument("--shuffle-source", action="store_true")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Prove repeat-build and shuffled-input byte identity; compare existing output when present.",
    )
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    previous = _load_json(args.previous_topology) if args.previous_topology else None
    artifact = build(shuffle_source=args.shuffle_source, previous_topology=previous)
    artifact_bytes = pipeline.topology_bytes(artifact)

    if args.check:
        repeat = pipeline.topology_bytes(build(previous_topology=previous))
        shuffled = pipeline.topology_bytes(build(shuffle_source=True, previous_topology=previous))
        if artifact_bytes != repeat or repeat != shuffled:
            raise SystemExit("Determinism failure: repeated/shuffled builds are not byte-identical")
        if args.output.is_file() and args.output.read_bytes() != artifact_bytes:
            raise SystemExit(f"Artifact parity failure: {args.output} differs from regenerated topology")
        print(
            "Prompt topology determinism: PASS — repeated build hash == shuffled-input hash == "
            + artifact["content_hash_sha256"]
        )
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(artifact_bytes)
    if args.summary:
        print(json.dumps({
            "status": "PASS",
            "output": str(args.output),
            "content_hash_sha256": artifact["content_hash_sha256"],
            "prompt_count": len(artifact["nodes"]),
            "edge_count": len(artifact["edges"]),
            "cluster_count": len(artifact["clusters"]),
            "outlier_count": len(artifact["outlier_prompt_ids"]),
            "opportunity_count": len(artifact["opportunities"]),
        }, sort_keys=True))
    else:
        print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
