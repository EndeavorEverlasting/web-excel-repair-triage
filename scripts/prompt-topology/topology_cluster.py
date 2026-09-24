"""HDBSCAN clusters, persistent identity reconciliation, and opportunities."""
from __future__ import annotations

import hashlib
import math
from collections import Counter, defaultdict
from typing import Any, Mapping, Sequence

import numpy as np
from sklearn.cluster import HDBSCAN
from sklearn.decomposition import PCA

from topology_core import CLUSTER_ID_RE, RuntimeConfig, membership_fingerprint, pair_key, prompt_key


def cluster_input(semantic: np.ndarray, role: np.ndarray, config: RuntimeConfig) -> np.ndarray:
    combined = np.hstack((semantic * math.sqrt(config.semantic_weight), role * math.sqrt(config.role_weight)))
    components = min(config.pca_dimensions, combined.shape[1], max(1, len(combined) - 1))
    if len(combined) > 2 and components >= 2:
        return PCA(n_components=components, svd_solver="full").fit_transform(combined)
    return combined


def cluster_vectors(prompt_ids: Sequence[str], vectors: np.ndarray, *, min_cluster_size: int = 3, min_samples: int = 2, cluster_selection_method: str = "eom") -> tuple[list[list[str]], list[str], dict[str, int]]:
    if len(prompt_ids) != len(vectors):
        raise ValueError("prompt/vector length mismatch")
    if len(prompt_ids) < min_cluster_size:
        return [], sorted(prompt_ids, key=prompt_key), {pid: 0 for pid in prompt_ids}
    model = HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="euclidean",
        cluster_selection_method=cluster_selection_method,
        allow_single_cluster=False,
        copy=True,
    )
    labels = model.fit_predict(vectors)
    probabilities = getattr(model, "probabilities_", np.ones(len(prompt_ids)))
    groups: dict[int, list[str]] = defaultdict(list)
    outliers: list[str] = []
    probability_micros: dict[str, int] = {}
    for pid, label, probability in zip(prompt_ids, labels, probabilities):
        probability_micros[pid] = round(float(probability) * 1_000_000)
        if int(label) < 0:
            outliers.append(pid)
        else:
            groups[int(label)].append(pid)
    clusters = [
        sorted(ids, key=prompt_key)
        for _, ids in sorted(groups.items(), key=lambda item: min(prompt_key(pid) for pid in item[1]))
    ]
    clusters.sort(key=lambda ids: tuple(prompt_key(pid) for pid in ids))
    return clusters, sorted(outliers, key=prompt_key), probability_micros


def _lineage(previous: set[str] | None, current: set[str]) -> str:
    if previous is None: return "NEW"
    if previous == current: return "UNCHANGED"
    if previous < current: return "EXPANDED"
    if current < previous: return "CONTRACTED"
    return "REVISED"


def _new_cluster_id(fingerprint: str, used: set[str]) -> str:
    salt = 0
    while True:
        seed = fingerprint if salt == 0 else f"{fingerprint}:{salt}"
        candidate = "C-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:6].upper()
        if candidate not in used:
            return candidate
        salt += 1


def reconcile_clusters(current: Sequence[Sequence[str]], previous: Sequence[Mapping[str, Any]] | None, *, min_jaccard: float = 0.50) -> list[dict[str, Any]]:
    prior = [
        (str(cluster.get("cluster_id", "")), {str(pid) for pid in cluster.get("member_prompt_ids", [])})
        for cluster in previous or []
    ]
    prior = [(cluster_id, members) for cluster_id, members in prior if CLUSTER_ID_RE.fullmatch(cluster_id) and members]
    used_prior: set[str] = set()
    used_ids = {cluster_id for cluster_id, _ in prior}
    result: list[dict[str, Any]] = []
    memberships = sorted((sorted(set(ids), key=prompt_key) for ids in current), key=lambda ids: tuple(prompt_key(pid) for pid in ids))
    for members in memberships:
        current_set = set(members)
        fingerprint = membership_fingerprint(members)
        candidates = sorted(
            (
                (len(current_set & old) / len(current_set | old), len(current_set & old), cluster_id, old)
                for cluster_id, old in prior if cluster_id not in used_prior
            ),
            key=lambda item: (-item[0], -item[1], item[2]),
        )
        if candidates and candidates[0][0] >= min_jaccard and candidates[0][1] > 0:
            jaccard, _, cluster_id, old = candidates[0]
            used_prior.add(cluster_id)
            lineage = _lineage(old, current_set)
            overlap_micros = round(jaccard * 1_000_000)
        else:
            cluster_id = _new_cluster_id(fingerprint, used_ids)
            used_ids.add(cluster_id)
            lineage, overlap_micros = "NEW", 0
        result.append({
            "cluster_id": cluster_id,
            "member_prompt_ids": members,
            "member_count": len(members),
            "membership_fingerprint_sha256": fingerprint,
            "lineage": lineage,
            "previous_overlap_micros": overlap_micros,
        })
    return result


def enrich_clusters(clusters: Sequence[Mapping[str, Any]], rows: Sequence[Mapping[str, Any]], scores: Mapping[tuple[str, str], Mapping[str, int]], probabilities: Mapping[str, int], threshold: float) -> list[dict[str, Any]]:
    by_id = {str(row["prompt_id"]): row for row in rows}
    result: list[dict[str, Any]] = []
    for cluster in clusters:
        item = dict(cluster)
        members = list(cluster["member_prompt_ids"])
        counts = Counter(str(by_id[pid]["family_declared_id"]) for pid in members)
        family, count = sorted(counts.items(), key=lambda entry: (-entry[1], entry[0]))[0]
        confidence = round(count / len(members) * 1_000_000)
        centrality = {
            pid: round(sum(int(scores[pair_key(pid, other)]["score_micros"]) for other in members if other != pid) / max(1, len(members) - 1))
            for pid in members
        }
        representative = sorted(members, key=lambda pid: (-centrality[pid], prompt_key(pid)))[0]
        item.update({
            "representative_prompt_id": representative,
            "family_candidate_id": family if confidence >= round(threshold * 1_000_000) else None,
            "family_confidence_micros": confidence,
            "family_alignment_distribution": {key: counts[key] for key in sorted(counts)},
            "centrality_micros": {key: centrality[key] for key in sorted(centrality, key=prompt_key)},
            "membership_probability_micros": {pid: int(probabilities.get(pid, 0)) for pid in members},
        })
        result.append(item)
    return sorted(result, key=lambda item: item["cluster_id"])


def classify_opportunity(components: Mapping[str, int], *, lineage: str, member_count: int) -> tuple[str, str, int]:
    values = {key: max(0, min(100, int(value))) for key, value in components.items()}
    score = round(
        0.25 * values.get("semantic_gap", 0)
        + 0.25 * values.get("ambiguity", 0)
        + 0.20 * values.get("underdevelopment", 0)
        + 0.15 * values.get("redundancy_penalty", 0)
        + 0.15 * values.get("workflow_gap", 0)
    )
    if values.get("redundancy_penalty", 0) >= 70: return "REDUNDANT", "CONSOLIDATE", score
    if values.get("ambiguity", 0) >= 45: return "AMBIGUOUS", "REVIEW_CLASSIFICATION", score
    if values.get("workflow_gap", 0) >= 70 and member_count >= 3: return "FRAGMENTED", "CONNECT_WORKFLOW", score
    if values.get("underdevelopment", 0) >= 60: return "UNDERDEVELOPED", "STRENGTHEN_EXISTING", score
    if lineage == "NEW" and score >= 40: return "EMERGING", "INVESTIGATE_CONTRIBUTION", score
    return "HEALTHY", "NONE", score


def build_opportunities(clusters: Sequence[Mapping[str, Any]], outliers: Sequence[str], edges: Sequence[Mapping[str, Any]], scores: Mapping[tuple[str, str], Mapping[str, int]], config: RuntimeConfig) -> list[dict[str, Any]]:
    edge_map = {(str(edge["source"]), str(edge["target"])): edge for edge in edges}
    result: list[dict[str, Any]] = []
    for cluster in clusters:
        members = list(cluster["member_prompt_ids"])
        pairs = [pair_key(a, b) for index, a in enumerate(members) for b in members[index + 1:]]
        semantic = [int(scores[pair]["semantic_micros"]) for pair in pairs]
        relevant = [edge_map[pair] for pair in pairs if pair in edge_map]
        workflow = sum(any(channel["type"] == "WORKFLOW_NEXT" for channel in edge["channels"]) for edge in relevant)
        tutorial = sum(any(channel["type"] == "TUTORIAL_ROUTE" for channel in edge["channels"]) for edge in relevant)
        avg_semantic = round(sum(semantic) / len(semantic)) if semantic else 0
        high_semantic = max(semantic, default=0)
        duplicate_floor = round(config.duplicate_threshold * 1_000_000)
        components = {
            "semantic_gap": max(0, min(100, round((1_000_000 - avg_semantic) / 10_000))),
            "ambiguity": round((1_000_000 - int(cluster["family_confidence_micros"])) / 10_000),
            "underdevelopment": max(0, min(100, round((6 - len(members)) / 5 * 100))),
            "redundancy_penalty": min(100, round((high_semantic - duplicate_floor) / max(1, 1_000_000 - duplicate_floor) * 100)) if high_semantic > duplicate_floor else 0,
            "workflow_gap": 100 if workflow + tutorial == 0 else (50 if workflow == 0 else 0),
        }
        state, action, score = classify_opportunity(components, lineage=str(cluster["lineage"]), member_count=len(members))
        result.append({
            "sector_id": str(cluster["cluster_id"]), "cluster_id": str(cluster["cluster_id"]),
            "prompt_ids": members, "state": state, "recommended_action": action, "score": score,
            "components": components,
            "evidence_refs": sorted(f"edge:{edge['source']}->{edge['target']}" for edge in relevant),
        })
    for pid in sorted(outliers, key=prompt_key):
        candidates = [
            (int(value["semantic_micros"]), other)
            for pair, value in scores.items() if pid in pair
            for other in pair if other != pid
        ]
        ranked = sorted(candidates, key=lambda item: (-item[0], prompt_key(item[1])))
        top = ranked[0][0] if ranked else 0
        related = [edge for edge in edges if pid in {str(edge["source"]), str(edge["target"])}]
        has_flow = any(any(channel["type"] in {"WORKFLOW_NEXT", "TUTORIAL_ROUTE"} for channel in edge["channels"]) for edge in related)
        components = {
            "semantic_gap": max(0, min(100, round((1_000_000 - top) / 10_000))),
            "ambiguity": 0, "underdevelopment": 100, "redundancy_penalty": 0,
            "workflow_gap": 0 if has_flow else 100,
        }
        state, action, score = classify_opportunity(components, lineage="NEW", member_count=1)
        result.append({
            "sector_id": f"OUTLIER:{pid}", "cluster_id": None, "prompt_ids": [pid],
            "state": state, "recommended_action": action, "score": score,
            "components": components, "evidence_refs": [f"node:{pid}"],
        })
    return sorted(result, key=lambda item: (item["cluster_id"] is None, item["sector_id"]))
