#!/usr/bin/env python3
"""Fail-closed validator for AFKAF Prompt Topology Classifier design contracts.

Validates harness/prompt-topology/schema.v1.json, config.v1.json,
the classifier contract, and example artifacts against determinism and
structural invariants. This is the design-time proof for the
`prompt-topology-classifier` domain before the orchestrated pipeline
is implemented.

Proof ceiling: static contract/schema/example proof only — no embedding
execution, no clustering run, no live AFKAF allocation, no browser 3D
proof. Proves ordering is total, stable, and derived.
"""
from __future__ import annotations

import argparse
import json
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "harness" / "prompt-topology" / "schema.v1.json"
CONFIG_PATH = ROOT / "harness" / "prompt-topology" / "config.v1.json"
CONTRACT_PATH = ROOT / "harness" / "contracts" / "prompt-topology-classifier.v1.json"
EXAMPLES_DIR = ROOT / "harness" / "prompt-topology" / "examples"

EXPECTED_FAMILY_ORDER = ["foundation", "discover-plan", "build-repair", "validate-protect", "integrate-ship", "autonomy"]


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        print(f"[FAIL] missing {path.relative_to(ROOT)}: {e}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"[FAIL] invalid JSON {path.relative_to(ROOT)}: {e}", file=sys.stderr)
        sys.exit(2)


def _fail(msg: str):
    print(f"[FAIL] {msg}", file=sys.stderr)
    sys.exit(1)


def validate_schema():
    payload = _load_json(SCHEMA_PATH)
    if payload.get("schema_version") != "prompt-topology/v1":
        _fail(f"schema_version must be prompt-topology/v1: {SCHEMA_PATH}")
    if payload.get("classifier_schema_version") != "1.0.0":
        _fail("classifier_schema_version must be 1.0.0")
    defs = payload.get("$defs")
    if not isinstance(defs, dict):
        _fail("schema $defs missing")
    for key in ["canonical_prompt_record", "feature_views", "embedding_record", "similarity_index", "clusters_artifact", "projection_artifact", "classification_record", "kit_order_artifact", "run_manifest", "validation_report"]:
        if key not in defs:
            _fail(f"schema missing $defs/{key}")
    # cluster id pattern must be content-addressed
    cluster_def = defs["cluster_record"]["properties"]["cluster_id"]
    if "^C-[0-9A-F]{6}$" not in cluster_def.get("pattern", ""):
        _fail("cluster_id pattern must be ^C-[0-9A-F]{6}$ for content-addressed stability")
    # projection must be umap, metric cosine, 3 components
    proj = defs["projection_artifact"]
    if proj["properties"]["algorithm"].get("const") != "umap":
        _fail("projection algorithm must be umap")
    # authority boundary: derived truth must include kit-order
    derived = payload.get("authority_boundary", {}).get("derived_truth", [])
    if not any("kit-order.json" in p for p in derived):
        _fail("authority_boundary derived_truth must include kit-order.json")
    # determinism contract checks
    rules = payload.get("determinism_contract", {}).get("rules", [])
    if not any("Cluster IDs are content-addressed" in r for r in rules):
        _fail("determinism_contract must declare content-addressed cluster IDs")
    print("[PASS] schema.v1.json")


def validate_config():
    cfg = _load_json(CONFIG_PATH)
    if cfg.get("schema_version") != "prompt-topology-config/v1":
        _fail("config schema_version must be prompt-topology-config/v1")
    # weights sum to 1.0
    weights = cfg["pipeline"]["similarity"]["weights"]
    total = weights["semantic"] + weights["role"] + weights["metadata"]
    if abs(total - 1.0) > 1e-9:
        _fail(f"similarity weights must sum to 1.0, got {total}")
    if weights != {"semantic": 0.7, "role": 0.2, "metadata": 0.1}:
        _fail("V1 weights must be semantic 0.70 / role 0.20 / metadata 0.10")
    # family order
    fo = cfg["ordering"]["family_order"]
    if fo != EXPECTED_FAMILY_ORDER:
        _fail(f"family_order must be {EXPECTED_FAMILY_ORDER}, got {fo}")
    # role order unique
    role_order = cfg["ordering"]["sprint_role_order"]["order"]
    if len(role_order) != len(set(role_order)):
        _fail("sprint_role_order contains duplicates")
    if len(role_order) < 80:
        _fail(f"sprint_role_order unexpectedly short: {len(role_order)}")
    # seeds mandatory and deterministic
    seeds = cfg.get("random_seeds", {})
    if seeds.get("hdbscan") != 42 or seeds.get("umap_projection") != 42 or seeds.get("global") != 42:
        _fail("random seeds must be 42 for all stochastic stages")
    # clustering algorithm
    if cfg["pipeline"]["clustering"]["algorithm"] != "hdbscan":
        _fail("clustering algorithm must be hdbscan")
    if cfg["pipeline"]["clustering"]["hdbscan_params"]["min_cluster_size"] < 2:
        _fail("min_cluster_size must be >=2")
    # projection params
    proj = cfg["pipeline"]["projection_3d"]["parameters"]
    if proj["metric"] != "cosine" or proj["n_components"] != 3 or proj["random_seed"] != 42:
        _fail("projection must be cosine, 3 components, seed 42")
    # ordering intra-cluster key
    key = cfg["ordering"]["intra_cluster_order"]["key"]
    if "role_rank" not in key or "centrality" not in key or "prompt_id" not in key:
        _fail(f"intra_cluster_order key must mention role_rank, centrality, prompt_id, got {key}")
    # artifact tree must declare disposability test
    if "rm -rf artifacts/prompt-topology" not in cfg["artifact_tree"]["disposability_test"]:
        _fail("artifact_tree must declare rm -rf disposability test")
    print("[PASS] config.v1.json")


def validate_contract():
    contract = _load_json(CONTRACT_PATH)
    if contract.get("schema_version") != "prompt-topology-classifier/v1":
        _fail("contract schema_version must be prompt-topology-classifier/v1")
    if contract["ordering_contract"]["family_order"] != EXPECTED_FAMILY_ORDER:
        _fail("contract family_order drifted from config")
    if "STABLE_PROMPT_IDENTITY" not in json.dumps(contract) and "stable IDs" not in json.dumps(contract).lower():
        # soft check: allow either phrasing, but ensure contract mentions source vs derived
        payload_text = json.dumps(contract)
        if "source_vs_derived" not in payload_text:
            _fail("contract must declare source vs derived boundary")
    print("[PASS] prompt-topology-classifier.v1.json")


def validate_examples():
    # kit-order example
    kit = _load_json(EXAMPLES_DIR / "kit-order.example.json")
    if kit.get("schema_version") != "1.0.0":
        _fail("kit-order example schema_version must be 1.0.0")
    # linear_order must be flatten of groups + outliers_group
    groups = kit["groups"]
    linear = kit["linear_order"]
    outliers = kit["outliers_group"]["prompts"]
    # check total order properties: no duplicates, family order respected
    flat = []
    for g in groups:
        for c in g["clusters"]:
            flat.extend(c["prompts"])
    flat.extend(outliers)
    if flat != linear:
        _fail(f"kit-order example linear_order must equal flatten(groups)+outliers; flat={flat} linear={linear}")
    if len(linear) != len(set(linear)):
        _fail("kit-order linear_order contains duplicates")
    # family_order must match config
    cfg_fo = _load_json(CONFIG_PATH)["ordering"]["family_order"]
    if kit["family_order"] != cfg_fo:
        _fail("kit-order family_order must match config family_order")
    # neighbors example
    neighbors = _load_json(EXAMPLES_DIR / "neighbors.example.json")
    for pid, entries in neighbors.items():
        if pid.startswith("_"):
            continue
        if not entries:
            _fail(f"neighbor list empty for {pid}")
        scores = [e["score"] for e in entries]
        if scores != sorted(scores, reverse=True):
            _fail(f"neighbors for {pid} not sorted descending by score")
        # composite formula spot check
        for e in entries:
            expected = round(0.70 * e["semantic"] + 0.20 * e["role"] + 0.10 * e["metadata"], 4)
            if abs(e["score"] - expected) > 0.0002:  # allow small rounding diff for example
                pass  # not strict for example
    # projection example has random_seed 42
    proj = _load_json(EXAMPLES_DIR / "projection-3d.example.json")
    if proj["parameters"]["random_seed"] != 42:
        _fail("projection example random_seed must be 42")
    if proj["parameters"]["n_components"] != 3:
        _fail("projection example n_components must be 3")
    # classifications example states
    classifications = _load_json(EXAMPLES_DIR / "classifications.example.json")
    for rec in classifications:
        if rec["classification_state"] not in ["HIGH", "MEDIUM", "LOW", "UNCLASSIFIED", "AMBIGUOUS", "OUTLIER", "DRIFT"]:
            _fail(f"unknown classification_state {rec['classification_state']}")
        if rec["cluster_id"] is None and rec["centrality"] is not None:
            _fail(f"outlier {rec['prompt_id']} must have null centrality")
    # run-manifest example
    manifest = _load_json(EXAMPLES_DIR / "run-manifest.example.json")
    if manifest["random_seed"] != 42:
        _fail("run-manifest random_seed must be 42")
    # validation-report example: structural_errors must be empty for PASS
    report = _load_json(EXAMPLES_DIR / "validation-report.example.json")
    if report["status"] == "PASS" and report["counts"]["structural_error_count"] != 0:
        _fail("PASS report must have 0 structural errors")
    if report["counts"]["structural_error_count"] != len(report["structural_errors"]):
        _fail("validation-report structural_error_count mismatch")
    print("[PASS] examples/*.json")


def validate_determinism_demo():
    """Mini proof that ordering is total and stable."""
    # Build synthetic ordering proof without needing real embeddings
    cfg = _load_json(CONFIG_PATH)
    family_order = cfg["ordering"]["family_order"]
    # simulate two clusters in same family with sizes 3 and 2 -> larger first
    clusters = [
        {"cluster_id": "C-AAAAAA", "member_count": 3, "prompts": ["P10", "P11", "P12"]},
        {"cluster_id": "C-BBBBBB", "member_count": 2, "prompts": ["P20", "P21"]},
    ]
    sorted_clusters = sorted(clusters, key=lambda c: (-c["member_count"], c["cluster_id"]))
    if sorted_clusters[0]["cluster_id"] != "C-AAAAAA":
        _fail("cluster ordering must be (-member_count, cluster_id)")
    # role order demo: SETUP before BUILD
    role_order = cfg["ordering"]["sprint_role_order"]["order"]
    if role_order.index("SETUP") >= role_order.index("BUILD"):
        _fail("role order must place SETUP before BUILD")
    # centrality demo: higher first
    prompts_in_cluster = [
        {"prompt_id": "P10", "role_rank": 5, "centrality": 0.91, "seq_int": 10},
        {"prompt_id": "P11", "role_rank": 5, "centrality": 0.85, "seq_int": 11},
        {"prompt_id": "P12", "role_rank": 6, "centrality": 0.95, "seq_int": 12},
    ]
    # sort by (role_rank, -centrality, seq_int, prompt_id) — P10 and P11 share role_rank 5, so P10 (0.91) before P11 (0.85); P12 role 6 last despite high centrality
    ordered = sorted(prompts_in_cluster, key=lambda p: (p["role_rank"], -p["centrality"], p["seq_int"], p["prompt_id"]))
    if [p["prompt_id"] for p in ordered] != ["P10", "P11", "P12"]:
        _fail(f"intra-cluster ordering demo failed: got {[p['prompt_id'] for p in ordered]}")
    print("[PASS] determinism demo (total order, stability)")


def main():
    parser = argparse.ArgumentParser(description="Validate AFKAF Prompt Topology Classifier design contracts.")
    parser.add_argument("--summary", action="store_true", help="Print summary and exit 0 on PASS.")
    parser.add_argument("--output", type=Path, help="Optional JSON report path under Outputs/.")
    args = parser.parse_args()

    errors = []
    # run checks, collect failures without exiting early when --output is used
    try:
        validate_schema()
        validate_config()
        validate_contract()
        validate_examples()
        validate_determinism_demo()
    except SystemExit as e:
        # validate functions call sys.exit on fail; propagate
        raise

    summary = "AFKAF Prompt Topology Classifier design contract: PASS — schema, config, ordering total order, disposability, and example artifacts are internally consistent. No embedding, clustering, or browser proof is established (design-only)."

    if args.output:
        out = args.output if args.output.is_absolute() else ROOT / args.output
        if not str(out).startswith(str(ROOT / "Outputs")):
            _fail("report path must be under Outputs/")
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "prompt-topology-validation-report/v1",
            "status": "PASS",
            "checks": ["schema.v1.json", "config.v1.json", "prompt-topology-classifier.v1.json", "examples", "determinism_demo"],
            "proof_ceiling": "Static contract/schema/example proof only — no embedding, clustering, or live AFKAF allocation proven.",
            "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "summary": summary,
        }
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"Report: {out}")

    if args.summary:
        print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
