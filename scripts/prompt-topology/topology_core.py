"""Canonical Prompt Kit records, deterministic vectors, and pair scores."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

PROMPT_ID_RE = re.compile(r"^P([0-9]+)$")
PROMPT_REF_RE = re.compile(r"\bP[0-9]+\b", re.I)
EVIDENCE_RE = re.compile(r"(?:`([^`]+)`)|(?:\b([A-Za-z0-9_.-]+/[A-Za-z0-9_./*?{}\[\]-]+)\b)")
CLUSTER_ID_RE = re.compile(r"^C-[0-9A-F]{6}$")
CHANNEL_ORDER = (
    "SEMANTIC_NEIGHBOR", "WORKFLOW_NEXT", "CLASS_FAMILY", "SHARED_SCOPE",
    "SHARED_EVIDENCE", "TUTORIAL_ROUTE", "CO_USAGE", "TRANSITION",
    "SUBSTITUTION", "COMPLEMENT",
)
LIVE_CHANNELS = {"CO_USAGE", "TRANSITION", "SUBSTITUTION", "COMPLEMENT"}
PHASE_A_CHANNELS = set(CHANNEL_ORDER) - LIVE_CHANNELS
OPPORTUNITY_STATES = {"HEALTHY", "UNDERDEVELOPED", "AMBIGUOUS", "FRAGMENTED", "REDUNDANT", "EMERGING"}
OPPORTUNITY_ACTIONS = {"NONE", "INVESTIGATE_CONTRIBUTION", "STRENGTHEN_EXISTING", "CONNECT_WORKFLOW", "IMPROVE_TUTORIAL", "REVIEW_CLASSIFICATION", "CONSOLIDATE"}
LINEAGE_STATES = {"NEW", "UNCHANGED", "EXPANDED", "CONTRACTED", "REVISED"}


@dataclass(frozen=True)
class RuntimeConfig:
    semantic_weight: float = 0.70
    role_weight: float = 0.20
    metadata_weight: float = 0.10
    neighbor_top_k: int = 15
    embedding_dimensions: int = 384
    pca_dimensions: int = 32
    min_cluster_size: int = 3
    min_samples: int = 2
    cluster_selection_method: str = "eom"
    family_majority_threshold: float = 0.60
    cluster_reconcile_min_jaccard: float = 0.50
    duplicate_threshold: float = 0.88

    def validate(self) -> None:
        if abs(self.semantic_weight + self.role_weight + self.metadata_weight - 1.0) > 1e-12:
            raise ValueError("similarity weights must sum to 1.0")
        if self.neighbor_top_k < 1 or self.embedding_dimensions < 32:
            raise ValueError("invalid neighbor/embedding config")
        if self.min_cluster_size < 2 or self.min_samples < 1:
            raise ValueError("invalid HDBSCAN config")
        if not 0 < self.cluster_reconcile_min_jaccard <= 1:
            raise ValueError("cluster reconcile threshold must be in (0,1]")


def prompt_key(prompt_id: str) -> tuple[int, str]:
    match = PROMPT_ID_RE.fullmatch(prompt_id)
    if not match:
        raise ValueError(f"invalid prompt id: {prompt_id!r}")
    return int(match.group(1)), prompt_id


def pair_key(a: str, b: str) -> tuple[str, str]:
    if a == b:
        raise ValueError(f"self edge is forbidden: {a}")
    return (a, b) if prompt_key(a) < prompt_key(b) else (b, a)


def normalize_text(value: Any) -> str:
    raw = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in raw.splitlines()).strip()


def normalize_role(value: Any) -> str:
    head = normalize_text(value).split("\n", 1)[0][:120].casefold()
    return re.sub(r"[^a-z0-9]+", "-", head).strip("-") or "unspecified"


def canonical_json_bytes(value: Any, *, pretty: bool = False) -> bytes:
    if pretty:
        return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sha256_payload(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def membership_fingerprint(ids: Sequence[str]) -> str:
    return hashlib.sha256(",".join(sorted(ids, key=prompt_key)).encode("utf-8")).hexdigest()


def family_mapping(sections: Sequence[Mapping[str, Any]]) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for section in sections:
        sid = str(section.get("id", "")).strip()
        name = str(section.get("name", "")).strip()
        types = section.get("types")
        if not sid or not name or not isinstance(types, list):
            raise ValueError(f"invalid classification section: {section!r}")
        for item in types:
            prompt_type = str(item).strip()
            if not prompt_type or prompt_type in result:
                raise ValueError(f"invalid/duplicate prompt type: {prompt_type!r}")
            result[prompt_type] = (sid, name)
    return result


def canonicalize_prompts(prompts: Sequence[Mapping[str, Any]], sections: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    families = family_mapping(sections)
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for source in prompts:
        prompt = copy.deepcopy(dict(source))
        pid = str(prompt.get("id", "")).strip().upper()
        kind = str(prompt.get("type", "")).strip()
        seq = str(prompt.get("seq", "")).strip()
        if not PROMPT_ID_RE.fullmatch(pid) or pid in seen or kind not in families or not seq.isdigit():
            raise ValueError(f"invalid canonical prompt identity/classification: {pid}/{kind}/{seq}")
        seen.add(pid)
        family_id, family = families[kind]
        row = {
            "prompt_id": pid,
            "seq": seq,
            "seq_int": int(seq),
            "title": normalize_text(prompt.get("name")),
            "prompt_class": normalize_text(prompt.get("class")),
            "prompt_type": kind,
            "sprint_path_role": normalize_role(prompt.get("sprintRole")),
            "family_declared_id": family_id,
            "family_declared": family,
            "use_this_when": normalize_text(prompt.get("useWhen")),
            "inspect_first": normalize_text(prompt.get("inspectFirst")),
            "expected_output": normalize_text(prompt.get("expectedOutput")),
            "acceptance_gate": normalize_text(prompt.get("proofGate")),
            "next_step": normalize_text(prompt.get("nextStep")),
            "body": normalize_text(prompt.get("copyContent")),
            "keywords": sorted({str(x).strip().casefold() for x in prompt.get("keywords", []) if str(x).strip()}),
            "category": normalize_text(prompt.get("category")),
            "color": normalize_text(prompt.get("color")),
            "copy_sheet": normalize_text(prompt.get("copySheet")),
        }
        if not row["title"] or not row["body"]:
            raise ValueError(f"prompt {pid} missing title/body")
        row["record_sha256"] = sha256_payload(row)
        rows.append(row)
    return sorted(rows, key=lambda row: (row["seq_int"], row["prompt_id"]))


def feature_views(row: Mapping[str, Any]) -> tuple[str, str, frozenset[str]]:
    semantic = (
        f"TITLE:\n{row['title']}\n\nUSE THIS WHEN:\n{row['use_this_when']}\n\n"
        f"INSPECT FIRST:\n{row['inspect_first']}\n\nEXPECTED OUTPUT:\n{row['expected_output']}\n\n"
        f"ACCEPTANCE GATE:\n{row['acceptance_gate']}\n\nPROMPT BODY:\n{row['body']}"
    )
    role = (
        f"PROMPT_CLASS={row['prompt_class']}\nPROMPT_TYPE={row['prompt_type']}\n"
        f"SPRINT_PATH_ROLE={row['sprint_path_role']}\nDECLARED_FAMILY={row['family_declared']}\n"
        f"DECLARED_FAMILY_ID={row['family_declared_id']}\nUSE_THIS_WHEN={row['use_this_when']}\n"
        f"EXPECTED_OUTPUT={row['expected_output']}"
    )
    tokens = {
        f"family:{row['family_declared_id']}",
        f"type:{str(row['prompt_type']).casefold()}",
        f"class:{str(row['prompt_class']).casefold()}",
        f"role:{row['sprint_path_role']}",
        f"category:{str(row['category']).casefold()}",
    }
    tokens.update(f"keyword:{item}" for item in row["keywords"])
    return semantic, role, frozenset(tokens)


def vectorize(texts: Sequence[str], dimensions: int) -> np.ndarray:
    vectorizer = HashingVectorizer(
        n_features=dimensions,
        alternate_sign=False,
        norm="l2",
        lowercase=True,
        ngram_range=(1, 2),
        token_pattern=r"(?u)\b[a-zA-Z0-9_./-]{2,}\b",
    )
    return vectorizer.transform(texts).astype(np.float64).toarray()


def build_embeddings(rows: Sequence[Mapping[str, Any]], config: RuntimeConfig) -> tuple[np.ndarray, np.ndarray, list[frozenset[str]]]:
    views = [feature_views(row) for row in rows]
    return (
        vectorize([item[0] for item in views], config.embedding_dimensions),
        vectorize([item[1] for item in views], config.embedding_dimensions),
        [item[2] for item in views],
    )


def build_pair_scores(rows: Sequence[Mapping[str, Any]], semantic: np.ndarray, role: np.ndarray, metadata: Sequence[frozenset[str]], config: RuntimeConfig) -> dict[tuple[str, str], dict[str, int]]:
    result: dict[tuple[str, str], dict[str, int]] = {}
    for i, left in enumerate(rows):
        for j in range(i + 1, len(rows)):
            sem = float(np.dot(semantic[i], semantic[j]))
            rol = float(np.dot(role[i], role[j]))
            meta = len(metadata[i] & metadata[j]) / math.sqrt(len(metadata[i]) * len(metadata[j])) if metadata[i] and metadata[j] else 0.0
            score = config.semantic_weight * sem + config.role_weight * rol + config.metadata_weight * meta
            result[(str(left["prompt_id"]), str(rows[j]["prompt_id"]))] = {
                "score_micros": round(score * 1_000_000),
                "semantic_micros": round(sem * 1_000_000),
                "role_micros": round(rol * 1_000_000),
                "metadata_micros": round(meta * 1_000_000),
            }
    return result
