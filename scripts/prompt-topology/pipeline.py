#!/usr/bin/env python3
"""Deterministic renderer-neutral Prompt Kit topology engine (Phase A)."""
from __future__ import annotations

import copy
from typing import Any, Iterable, Mapping, Sequence

from topology_core import *  # re-export tested Phase A surface
from topology_cluster import (
    build_opportunities, classify_opportunity, cluster_input, cluster_vectors,
    enrich_clusters, reconcile_clusters,
)
from topology_graph import build_edges


def build_topology(
    prompts: Sequence[Mapping[str, Any]],
    sections: Sequence[Mapping[str, Any]],
    *,
    tutorial_routes: Mapping[str, Mapping[str, Any]] | None = None,
    previous_topology: Mapping[str, Any] | None = None,
    config: RuntimeConfig | None = None,
    source_provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or RuntimeConfig()
    config.validate()
    snapshot = copy.deepcopy(list(prompts))
    canonical_snapshot = sorted(snapshot, key=lambda prompt: (int(str(prompt["seq"])), str(prompt["id"])))
    rows = canonicalize_prompts(snapshot, sections)
    semantic, role, metadata = build_embeddings(rows, config)
    scores = build_pair_scores(rows, semantic, role, metadata, config)
    edges = build_edges(rows, scores, config, tutorial_routes)
    prompt_ids = [str(row["prompt_id"]) for row in rows]
    raw_clusters, outliers, probabilities = cluster_vectors(
        prompt_ids,
        cluster_input(semantic, role, config),
        min_cluster_size=config.min_cluster_size,
        min_samples=config.min_samples,
        cluster_selection_method=config.cluster_selection_method,
    )
    previous_clusters = None
    if previous_topology and isinstance(previous_topology.get("clusters"), list):
        previous_clusters = previous_topology["clusters"]
    reconciled = reconcile_clusters(
        raw_clusters,
        previous_clusters,
        min_jaccard=config.cluster_reconcile_min_jaccard,
    )
    clusters = enrich_clusters(
        reconciled, rows, scores, probabilities, config.family_majority_threshold
    )
    nodes = [
        {key: row[key] for key in (
            "prompt_id", "seq", "title", "prompt_type", "prompt_class",
            "sprint_path_role", "family_declared_id", "family_declared",
            "category", "keywords", "record_sha256",
        )}
        for row in rows
    ]
    previous_hash = None
    if previous_topology:
        previous_hash = str(
            previous_topology.get("content_hash_sha256") or sha256_payload(previous_topology)
        )
    artifact: dict[str, Any] = {
        "schema_version": "prompt-topology-artifact/v1",
        "nodes": nodes,
        "edges": edges,
        "clusters": clusters,
        "outlier_prompt_ids": outliers,
        "opportunities": build_opportunities(clusters, outliers, edges, scores, config),
        "provenance": {
            "registry_snapshot_sha256": sha256_payload(canonical_snapshot),
            "prompt_count": len(rows),
            "embedding_provider": "local-hashing-vectorizer/v1",
            "embedding_dimensions": config.embedding_dimensions,
            "similarity_weights_micros": {
                "semantic": round(config.semantic_weight * 1_000_000),
                "role": round(config.role_weight * 1_000_000),
                "metadata": round(config.metadata_weight * 1_000_000),
            },
            "clustering_algorithm": "sklearn.cluster.HDBSCAN",
            "cluster_reconcile_min_jaccard_micros": round(config.cluster_reconcile_min_jaccard * 1_000_000),
            "previous_topology_content_hash_sha256": previous_hash,
            "renderer_neutral": True,
            "live_behavior_channels_populated": False,
            **dict(source_provenance or {}),
        },
    }
    artifact["content_hash_sha256"] = sha256_payload(artifact)
    validate_topology(artifact, prompt_ids)
    if snapshot != list(prompts):
        raise AssertionError("topology pipeline mutated canonical registry input")
    return artifact


def validate_topology(artifact: Mapping[str, Any], canonical_prompt_ids: Iterable[str]) -> None:
    canonical_ids = sorted({str(pid).upper() for pid in canonical_prompt_ids}, key=prompt_key)
    nodes = artifact.get("nodes")
    if not isinstance(nodes, list):
        raise ValueError("topology nodes must be an array")
    node_ids = [str(node.get("prompt_id", "")) for node in nodes if isinstance(node, Mapping)]
    if len(node_ids) != len(set(node_ids)) or sorted(node_ids, key=prompt_key) != canonical_ids:
        raise ValueError("topology node parity failure")
    known = set(node_ids)
    last_edge_key = None
    for edge in artifact.get("edges") or []:
        source, target = str(edge.get("source", "")), str(edge.get("target", ""))
        if source not in known or target not in known:
            raise ValueError(f"unknown edge endpoint: {source}->{target}")
        if source == target:
            raise ValueError(f"self edge is forbidden: {source}")
        edge_key = (prompt_key(source), prompt_key(target))
        if prompt_key(source) >= prompt_key(target) or (last_edge_key is not None and edge_key <= last_edge_key):
            raise ValueError("edges are not canonical/strictly ordered")
        last_edge_key = edge_key
        channels = edge.get("channels") or []
        names = [str(channel.get("type", "")) for channel in channels]
        if not names or any(name in LIVE_CHANNELS for name in names):
            raise ValueError(f"invalid Phase A edge channels: {source}->{target}")
        if names != sorted(names, key=CHANNEL_ORDER.index) or len(names) != len(set(names)):
            raise ValueError(f"invalid edge channel ordering: {source}->{target}")
    clustered: set[str] = set()
    cluster_ids: set[str] = set()
    for cluster in artifact.get("clusters") or []:
        cluster_id = str(cluster.get("cluster_id", ""))
        members = [str(pid) for pid in cluster.get("member_prompt_ids") or []]
        if not CLUSTER_ID_RE.fullmatch(cluster_id) or cluster_id in cluster_ids:
            raise ValueError(f"invalid/duplicate cluster id: {cluster_id}")
        cluster_ids.add(cluster_id)
        if len(members) < 2 or members != sorted(members, key=prompt_key):
            raise ValueError(f"invalid cluster membership ordering: {cluster_id}")
        if any(pid not in known for pid in members) or clustered.intersection(members):
            raise ValueError(f"invalid cluster membership: {cluster_id}")
        clustered.update(members)
        if cluster.get("membership_fingerprint_sha256") != membership_fingerprint(members):
            raise ValueError(f"membership fingerprint mismatch: {cluster_id}")
        if cluster.get("representative_prompt_id") not in members or cluster.get("lineage") not in LINEAGE_STATES:
            raise ValueError(f"invalid cluster metadata: {cluster_id}")
    outliers = [str(pid) for pid in artifact.get("outlier_prompt_ids") or []]
    if outliers != sorted(outliers, key=prompt_key) or len(outliers) != len(set(outliers)):
        raise ValueError("outlier ids are not unique/canonically sorted")
    if clustered.intersection(outliers) or clustered.union(outliers) != known:
        raise ValueError("clusters + outliers must partition canonical ids")
    for item in artifact.get("opportunities") or []:
        if item.get("state") not in OPPORTUNITY_STATES or item.get("recommended_action") not in OPPORTUNITY_ACTIONS:
            raise ValueError("invalid opportunity state/action")
        if any(str(pid) not in known for pid in item.get("prompt_ids") or []):
            raise ValueError("opportunity references unknown prompt")
    stored_hash = str(artifact.get("content_hash_sha256", ""))
    unhashed = dict(artifact)
    unhashed.pop("content_hash_sha256", None)
    if stored_hash != sha256_payload(unhashed):
        raise ValueError("topology content hash mismatch")


def topology_bytes(artifact: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes(artifact, pretty=True)
