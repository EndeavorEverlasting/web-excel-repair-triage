"""Deterministic multi-channel edge construction for Prompt Topology Phase A."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence

from topology_core import (
    CHANNEL_ORDER, EVIDENCE_RE, PHASE_A_CHANNELS, PROMPT_REF_RE, RuntimeConfig,
    canonical_json_bytes, pair_key, prompt_key,
)


def build_edges(rows: Sequence[Mapping[str, Any]], scores: Mapping[tuple[str, str], Mapping[str, int]], config: RuntimeConfig, tutorial_routes: Mapping[str, Mapping[str, Any]] | None = None) -> list[dict[str, Any]]:
    by_id = {str(row["prompt_id"]): row for row in rows}
    edges: dict[tuple[str, str], dict[str, Any]] = {}

    def add(a: str, b: str, channel: str, evidence: Mapping[str, Any]) -> None:
        if channel not in PHASE_A_CHANNELS or a not in by_id or b not in by_id:
            raise ValueError(f"invalid Phase A edge: {a}/{b}/{channel}")
        key = pair_key(a, b)
        entry = edges.setdefault(key, {"source": key[0], "target": key[1], "channels": {}})
        old, new = entry["channels"].get(channel), dict(evidence)
        if old is None or canonical_json_bytes(new) < canonical_json_bytes(old):
            entry["channels"][channel] = new

    neighbors: dict[str, list[tuple[int, str, Mapping[str, int]]]] = defaultdict(list)
    for (a, b), value in scores.items():
        neighbors[a].append((int(value["score_micros"]), b, value))
        neighbors[b].append((int(value["score_micros"]), a, value))
    for pid in sorted(by_id, key=prompt_key):
        ranked = sorted(neighbors[pid], key=lambda item: (-item[0], prompt_key(item[1])))[:config.neighbor_top_k]
        for rank, (_, other, value) in enumerate(ranked, 1):
            add(pid, other, "SEMANTIC_NEIGHBOR", {"rank": rank, **{k: int(v) for k, v in value.items()}})

    ordered = sorted(rows, key=lambda row: (int(row["seq_int"]), str(row["prompt_id"])))
    tokens: dict[str, set[str]] = {}
    for row in ordered:
        pid = str(row["prompt_id"])
        tokens[pid] = {
            next((group for group in match.groups() if group), "").strip().casefold()
            for match in EVIDENCE_RE.finditer(f"{row['inspect_first']}\n{row['acceptance_gate']}")
        } - {""}
    for index, left in enumerate(ordered):
        a = str(left["prompt_id"])
        for right in ordered[index + 1:]:
            b = str(right["prompt_id"])
            if left["family_declared_id"] == right["family_declared_id"]:
                add(a, b, "CLASS_FAMILY", {"family_id": left["family_declared_id"]})
            if left["sprint_path_role"] != "unspecified" and left["sprint_path_role"] == right["sprint_path_role"]:
                add(a, b, "SHARED_SCOPE", {"sprint_path_role": left["sprint_path_role"]})
            shared = sorted(tokens[a] & tokens[b])
            if shared:
                add(a, b, "SHARED_EVIDENCE", {"tokens": shared[:12], "shared_count": len(shared)})

    for row in ordered:
        source = str(row["prompt_id"])
        refs = {
            match.upper()
            for match in PROMPT_REF_RE.findall(f"{row['next_step']}\n{row['body']}")
            if match.upper() in by_id and match.upper() != source
        }
        for target in sorted(refs, key=prompt_key):
            add(source, target, "WORKFLOW_NEXT", {"explicit_reference_from": source})

    grouped: dict[str, list[str]] = defaultdict(list)
    for pid, route in (tutorial_routes or {}).items():
        normalized = pid.upper()
        section = str(route.get("classifier_section", "")).strip()
        if normalized in by_id and section:
            grouped[section].append(normalized)
    for section, ids in sorted(grouped.items()):
        sequence = sorted(set(ids), key=lambda pid: (int(by_id[pid]["seq_int"]), pid))
        for a, b in zip(sequence, sequence[1:]):
            add(a, b, "TUTORIAL_ROUTE", {"classifier_section": section})

    rank = {channel: index for index, channel in enumerate(CHANNEL_ORDER)}
    result: list[dict[str, Any]] = []
    for key in sorted(edges, key=lambda pair: (prompt_key(pair[0]), prompt_key(pair[1]))):
        entry = edges[key]
        channels = [
            {"type": name, "evidence": entry["channels"][name]}
            for name in sorted(entry["channels"], key=rank.__getitem__)
        ]
        semantic = next((channel for channel in channels if channel["type"] == "SEMANTIC_NEIGHBOR"), None)
        base = int(semantic["evidence"].get("score_micros", 0)) if semantic else 0
        bonus = 60_000 * sum(channel["type"] != "SEMANTIC_NEIGHBOR" for channel in channels)
        result.append({
            "source": entry["source"],
            "target": entry["target"],
            "channels": channels,
            "strength_micros": max(0, min(1_000_000, base + bonus)),
        })
    return result
