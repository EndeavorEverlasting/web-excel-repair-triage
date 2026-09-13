#!/usr/bin/env python3
"""Fail-closed validation of the executable Phase A Prompt Kit topology."""
from __future__ import annotations

import argparse
import importlib.util
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

DEFAULT_ARTIFACT = REPO_ROOT / "artifacts" / "prompt-topology" / "topology.v1.json"


def _load_builder():
    path = SCRIPT_DIR / "run.py"
    spec = importlib.util.spec_from_file_location("prompt_topology_run", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load topology builder: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    parser.add_argument("--rebuild", action="store_true", help="Also require byte-identical live-registry regeneration.")
    parser.add_argument("--previous-topology", type=Path)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    artifact = json.loads(args.artifact.read_text(encoding="utf-8"))
    prompts = registry.load_prompt_kit_registry()
    canonical_ids = [str(prompt["id"]).upper() for prompt in prompts]
    pipeline.validate_topology(artifact, canonical_ids)

    rebuilt_hash = None
    if args.rebuild:
        builder = _load_builder()
        previous = None
        if args.previous_topology:
            previous = json.loads(args.previous_topology.read_text(encoding="utf-8"))
        rebuilt = builder.build(previous_topology=previous)
        if pipeline.topology_bytes(rebuilt) != args.artifact.read_bytes():
            raise SystemExit("Live-registry rebuild differs from supplied topology artifact")
        rebuilt_hash = rebuilt["content_hash_sha256"]

    result = {
        "status": "PASS",
        "artifact": str(args.artifact),
        "content_hash_sha256": artifact["content_hash_sha256"],
        "live_prompt_count": len(canonical_ids),
        "node_count": len(artifact["nodes"]),
        "edge_count": len(artifact["edges"]),
        "cluster_count": len(artifact["clusters"]),
        "outlier_count": len(artifact["outlier_prompt_ids"]),
        "opportunity_count": len(artifact["opportunities"]),
        "live_registry_rebuild_hash": rebuilt_hash,
        "proof_ceiling": "Repository/runtime Phase A semantics and deterministic regeneration; no browser 3D or live behavior telemetry proof.",
    }
    if args.summary:
        print(json.dumps(result, sort_keys=True))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
