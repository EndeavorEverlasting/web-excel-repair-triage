"""Deterministic 3D visualization projection for Prompt Topology Phase B."""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import umap

from topology_core import (
    RuntimeConfig,
    build_embeddings,
    canonical_json_bytes,
    canonicalize_prompts,
    prompt_key,
    sha256_payload,
)

PROJECTION_SCHEMA_VERSION = "1.0.0"
STATE_SCHEMA_VERSION = "prompt-topology-projection-state/v1"
ALGORITHM = "umap"
ALIGNMENT_METHOD = "orthogonal-procrustes-rigid-no-scale"
FRAME_NORMALIZATION = "centered-unit-rms"
EPOCH_PREFIX = "E-"


@dataclass(frozen=True)
class ProjectionConfig:
    n_components: int = 3
    n_neighbors: int = 15
    min_dist: float = 0.15
    metric: str = "cosine"
    random_seed: int = 42
    coordinate_decimals: int = 6
    minimum_anchors: int = 3
    rms_displacement_limit: float = 0.45
    max_displacement_limit: float = 1.25

    def validate(self) -> None:
        if self.n_components != 3:
            raise ValueError("Phase B projection requires exactly 3 dimensions")
        if self.n_neighbors < 2:
            raise ValueError("projection n_neighbors must be >= 2")
        if not 0 <= self.min_dist <= 1:
            raise ValueError("projection min_dist must be in [0,1]")
        if self.metric != "cosine":
            raise ValueError("Phase B projection metric must remain cosine")
        if self.coordinate_decimals < 1 or self.coordinate_decimals > 9:
            raise ValueError("coordinate_decimals must be in [1,9]")
        if self.minimum_anchors < 3:
            raise ValueError("minimum_anchors must be >= 3")
        if self.rms_displacement_limit <= 0 or self.max_displacement_limit <= 0:
            raise ValueError("displacement limits must be positive")
        if self.rms_displacement_limit > self.max_displacement_limit:
            raise ValueError("RMS displacement limit cannot exceed max displacement limit")


def _normalize_frame(coordinates: np.ndarray, prompt_ids: Sequence[str]) -> np.ndarray:
    coords = np.asarray(coordinates, dtype=np.float64)
    if coords.ndim != 2 or coords.shape[1] != 3 or coords.shape[0] != len(prompt_ids):
        raise ValueError("projection coordinates must be Nx3 and match prompt ids")
    if not np.isfinite(coords).all():
        raise ValueError("projection contains non-finite coordinates")
    centered = coords - coords.mean(axis=0, keepdims=True)
    rms_radius = math.sqrt(float(np.mean(np.sum(centered * centered, axis=1))))
    if rms_radius <= 1e-12:
        raise ValueError("projection collapsed to a zero-radius frame")
    normalized = centered / rms_radius

    # UMAP's fixed seed stabilizes optimization. Canonical axis signs make the
    # serialized first epoch insensitive to an equivalent whole-axis reflection.
    for axis in range(3):
        index = max(
            range(len(prompt_ids)),
            key=lambda i: (abs(float(normalized[i, axis])), -prompt_key(prompt_ids[i])[0]),
        )
        if normalized[index, axis] < 0:
            normalized[:, axis] *= -1
    return normalized


def _points_array(points: Mapping[str, Mapping[str, Any]], prompt_ids: Sequence[str]) -> np.ndarray:
    rows: list[list[float]] = []
    for prompt_id in prompt_ids:
        point = points.get(prompt_id)
        if not isinstance(point, Mapping):
            raise ValueError(f"projection missing point for {prompt_id}")
        rows.append([float(point["x"]), float(point["y"]), float(point["z"])])
    result = np.asarray(rows, dtype=np.float64)
    if not np.isfinite(result).all():
        raise ValueError("previous projection contains non-finite coordinates")
    return result


def _align_to_previous(
    coordinates: np.ndarray,
    prompt_ids: Sequence[str],
    previous_points: Mapping[str, Mapping[str, Any]],
    *,
    minimum_anchors: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    by_index = {prompt_id: index for index, prompt_id in enumerate(prompt_ids)}
    anchor_ids = sorted(
        (prompt_id for prompt_id in prompt_ids if prompt_id in previous_points),
        key=prompt_key,
    )
    if len(anchor_ids) < minimum_anchors:
        return coordinates, {
            "mode": "INSUFFICIENT_ANCHORS",
            "method": ALIGNMENT_METHOD,
            "anchor_prompt_ids": anchor_ids,
            "anchor_count": len(anchor_ids),
            "rms_displacement": None,
            "max_displacement": None,
        }

    current_anchor = np.asarray([coordinates[by_index[prompt_id]] for prompt_id in anchor_ids])
    previous_anchor = _points_array(previous_points, anchor_ids)
    current_center = current_anchor.mean(axis=0)
    previous_center = previous_anchor.mean(axis=0)
    left = current_anchor - current_center
    right = previous_anchor - previous_center

    u, _, vt = np.linalg.svd(left.T @ right)
    rotation = u @ vt
    if np.linalg.det(rotation) < 0:
        u[:, -1] *= -1
        rotation = u @ vt

    aligned = (coordinates - current_center) @ rotation + previous_center
    aligned_anchor = np.asarray([aligned[by_index[prompt_id]] for prompt_id in anchor_ids])
    displacement = np.linalg.norm(aligned_anchor - previous_anchor, axis=1)
    return aligned, {
        "mode": "ANCHORED",
        "method": ALIGNMENT_METHOD,
        "anchor_prompt_ids": anchor_ids,
        "anchor_count": len(anchor_ids),
        "rms_displacement": float(math.sqrt(float(np.mean(displacement * displacement)))),
        "max_displacement": float(np.max(displacement)),
    }


def _round_point(value: float, decimals: int) -> float:
    rounded = round(float(value), decimals)
    return 0.0 if rounded == 0 else rounded


def _projection_points(prompt_ids: Sequence[str], coordinates: np.ndarray, decimals: int) -> dict[str, dict[str, float]]:
    return {
        prompt_id: {
            "x": _round_point(coordinates[index, 0], decimals),
            "y": _round_point(coordinates[index, 1], decimals),
            "z": _round_point(coordinates[index, 2], decimals),
        }
        for index, prompt_id in enumerate(prompt_ids)
    }


def projection_bytes(artifact: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes(artifact, pretty=True)


def state_bytes(state: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes(state, pretty=True)


def _projection_sha256(projection: Mapping[str, Any]) -> str:
    return sha256_payload(projection)


def _state_without_hash(state: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(state)
    result.pop("content_hash_sha256", None)
    return result


def _validate_previous_bundle(
    projection: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    config: ProjectionConfig,
) -> None:
    if projection.get("schema_version") != PROJECTION_SCHEMA_VERSION or projection.get("algorithm") != ALGORITHM:
        raise ValueError("previous projection schema/algorithm drift")
    parameters = projection.get("parameters")
    if not isinstance(parameters, Mapping):
        raise ValueError("previous projection parameters missing")
    if int(parameters.get("n_components", -1)) != config.n_components:
        raise ValueError("previous projection dimension drift")
    if str(parameters.get("metric", "")) != config.metric:
        raise ValueError("previous projection metric drift")
    if int(parameters.get("random_seed", -1)) != config.random_seed:
        raise ValueError("previous projection random seed drift")
    if abs(float(parameters.get("min_dist", -1.0)) - config.min_dist) > 1e-12:
        raise ValueError("previous projection min_dist drift")
    points = projection.get("points")
    if not isinstance(points, Mapping) or not points:
        raise ValueError("previous projection points are invalid")
    previous_ids = sorted((str(prompt_id) for prompt_id in points), key=prompt_key)
    _points_array(points, previous_ids)

    if state.get("schema_version") != STATE_SCHEMA_VERSION:
        raise ValueError("previous projection state schema version drift")
    projection_sha = _projection_sha256(projection)
    if str(state.get("projection_sha256", "")) != projection_sha:
        raise ValueError("previous projection state projection hash mismatch")
    if int(state.get("prompt_count", -1)) != len(previous_ids):
        raise ValueError("previous projection state prompt count mismatch")
    if str(state.get("epoch_id", "")) != EPOCH_PREFIX + projection_sha[:12].upper():
        raise ValueError("previous projection epoch id mismatch")
    topology_hash = str(state.get("topology_content_hash_sha256", ""))
    if len(topology_hash) != 64:
        raise ValueError("previous projection topology binding is invalid")
    alignment = state.get("alignment")
    if not isinstance(alignment, Mapping) or alignment.get("method") != ALIGNMENT_METHOD:
        raise ValueError("previous projection alignment evidence invalid")
    if alignment.get("within_limits") is not True:
        raise ValueError("previous projection was not spatially stable")
    if str(state.get("content_hash_sha256", "")) != sha256_payload(_state_without_hash(state)):
        raise ValueError("previous projection state content hash mismatch")


def build_projection(
    topology: Mapping[str, Any],
    prompts: Sequence[Mapping[str, Any]],
    sections: Sequence[Mapping[str, Any]],
    *,
    phase_a_config: RuntimeConfig | None = None,
    config: ProjectionConfig | None = None,
    previous_projection: Mapping[str, Any] | None = None,
    previous_state: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    config = config or ProjectionConfig()
    config.validate()
    phase_a_config = phase_a_config or RuntimeConfig()
    phase_a_config.validate()

    prompt_snapshot = copy.deepcopy(list(prompts))
    rows = canonicalize_prompts(prompt_snapshot, sections)
    prompt_ids = [str(row["prompt_id"]) for row in rows]
    topology_ids = [str(node.get("prompt_id", "")) for node in topology.get("nodes") or []]
    if topology_ids != prompt_ids:
        raise ValueError("Phase B prompt identity must exactly match Phase A topology nodes")
    topology_hash = str(topology.get("content_hash_sha256", ""))
    if len(topology_hash) != 64:
        raise ValueError("Phase B requires a hashed Phase A topology artifact")

    semantic, _, _ = build_embeddings(rows, phase_a_config)
    effective_neighbors = min(config.n_neighbors, max(2, len(prompt_ids) - 1))
    reducer = umap.UMAP(
        n_components=config.n_components,
        n_neighbors=effective_neighbors,
        min_dist=config.min_dist,
        metric=config.metric,
        random_state=config.random_seed,
        transform_seed=config.random_seed,
        n_jobs=1,
    )
    coordinates = reducer.fit_transform(semantic)
    coordinates = _normalize_frame(coordinates, prompt_ids)

    previous_points = None
    if previous_projection is not None:
        if previous_state is None:
            raise ValueError("previous projection requires previous projection state")
        _validate_previous_bundle(previous_projection, previous_state, config=config)
        previous_points = previous_projection.get("points")
        if not isinstance(previous_points, Mapping):
            raise ValueError("previous projection points are invalid")
        previous_hash = str(previous_state.get("topology_content_hash_sha256", ""))
        if previous_hash == topology_hash:
            candidate = {
                "schema_version": PROJECTION_SCHEMA_VERSION,
                "algorithm": ALGORITHM,
                "parameters": {
                    "n_components": config.n_components,
                    "n_neighbors": effective_neighbors,
                    "min_dist": config.min_dist,
                    "metric": config.metric,
                    "random_seed": config.random_seed,
                },
                "points": _projection_points(prompt_ids, coordinates, config.coordinate_decimals),
            }
            if projection_bytes(candidate) != projection_bytes(previous_projection):
                raise ValueError("unchanged topology produced projection drift")
            if str(previous_state.get("projection_sha256", "")) != _projection_sha256(candidate):
                raise ValueError("previous projection state hash mismatch")
            return dict(previous_projection), dict(previous_state)

    alignment = {
        "mode": "INITIAL",
        "method": ALIGNMENT_METHOD,
        "anchor_prompt_ids": [],
        "anchor_count": 0,
        "rms_displacement": None,
        "max_displacement": None,
    }
    if previous_points is not None:
        coordinates, alignment = _align_to_previous(
            coordinates,
            prompt_ids,
            previous_points,
            minimum_anchors=config.minimum_anchors,
        )

    projection = {
        "schema_version": PROJECTION_SCHEMA_VERSION,
        "algorithm": ALGORITHM,
        "parameters": {
            "n_components": config.n_components,
            "n_neighbors": effective_neighbors,
            "min_dist": config.min_dist,
            "metric": config.metric,
            "random_seed": config.random_seed,
        },
        "points": _projection_points(prompt_ids, coordinates, config.coordinate_decimals),
    }
    projection_sha = _projection_sha256(projection)

    if alignment["mode"] == "ANCHORED":
        rms = float(alignment["rms_displacement"])
        maximum = float(alignment["max_displacement"])
        within_limits = (
            rms <= config.rms_displacement_limit
            and maximum <= config.max_displacement_limit
        )
        if not within_limits:
            raise ValueError(
                "projection spatial stability exceeded displacement limits: "
                f"rms={rms:.6f}/{config.rms_displacement_limit:.6f}, "
                f"max={maximum:.6f}/{config.max_displacement_limit:.6f}"
            )
    else:
        within_limits = alignment["mode"] == "INITIAL"

    parent_epoch_id = None
    if previous_state is not None:
        parent_epoch_id = str(previous_state.get("epoch_id", "")) or None
    epoch_id = EPOCH_PREFIX + projection_sha[:12].upper()

    state: dict[str, Any] = {
        "schema_version": STATE_SCHEMA_VERSION,
        "epoch_id": epoch_id,
        "parent_epoch_id": parent_epoch_id,
        "topology_content_hash_sha256": topology_hash,
        "projection_sha256": projection_sha,
        "prompt_count": len(prompt_ids),
        "alignment": {
            "mode": alignment["mode"],
            "method": alignment["method"],
            "anchor_prompt_ids": alignment["anchor_prompt_ids"],
            "anchor_count": alignment["anchor_count"],
            "rms_displacement_micros": (
                None if alignment["rms_displacement"] is None
                else round(float(alignment["rms_displacement"]) * 1_000_000)
            ),
            "max_displacement_micros": (
                None if alignment["max_displacement"] is None
                else round(float(alignment["max_displacement"]) * 1_000_000)
            ),
            "rms_limit_micros": round(config.rms_displacement_limit * 1_000_000),
            "max_limit_micros": round(config.max_displacement_limit * 1_000_000),
            "within_limits": within_limits,
        },
        "provenance": {
            "algorithm": ALGORITHM,
            "dimensions": config.n_components,
            "n_neighbors": effective_neighbors,
            "min_dist_micros": round(config.min_dist * 1_000_000),
            "metric": config.metric,
            "random_seed": config.random_seed,
            "input": "semantic_embedding",
            "frame_normalization": FRAME_NORMALIZATION,
            "alignment_algorithm": ALIGNMENT_METHOD,
            "visualization_only": True,
        },
    }
    state["content_hash_sha256"] = sha256_payload(_state_without_hash(state))
    validate_projection_bundle(topology, projection, state, config=config)

    if prompt_snapshot != list(prompts):
        raise AssertionError("projection pipeline mutated canonical registry input")
    return projection, state


def validate_projection_bundle(
    topology: Mapping[str, Any],
    projection: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    config: ProjectionConfig | None = None,
) -> None:
    config = config or ProjectionConfig()
    config.validate()
    if projection.get("schema_version") != PROJECTION_SCHEMA_VERSION:
        raise ValueError("projection schema version drift")
    if projection.get("algorithm") != ALGORITHM:
        raise ValueError("projection algorithm must remain umap")
    parameters = projection.get("parameters")
    if not isinstance(parameters, Mapping):
        raise ValueError("projection parameters missing")
    if int(parameters.get("n_components", -1)) != 3:
        raise ValueError("projection must have 3 components")
    if str(parameters.get("metric", "")) != "cosine":
        raise ValueError("projection metric must remain cosine")
    if int(parameters.get("random_seed", -1)) != config.random_seed:
        raise ValueError("projection random seed drift")
    points = projection.get("points")
    if not isinstance(points, Mapping):
        raise ValueError("projection points missing")

    topology_ids = [str(node.get("prompt_id", "")) for node in topology.get("nodes") or []]
    point_ids = sorted((str(prompt_id) for prompt_id in points), key=prompt_key)
    if point_ids != topology_ids:
        raise ValueError("projection point parity failure")
    _points_array(points, topology_ids)

    topology_hash = str(topology.get("content_hash_sha256", ""))
    if state.get("schema_version") != STATE_SCHEMA_VERSION:
        raise ValueError("projection state schema version drift")
    if str(state.get("topology_content_hash_sha256", "")) != topology_hash:
        raise ValueError("projection state does not reference exact Phase A topology")
    projection_sha = _projection_sha256(projection)
    if str(state.get("projection_sha256", "")) != projection_sha:
        raise ValueError("projection state projection hash mismatch")
    if int(state.get("prompt_count", -1)) != len(topology_ids):
        raise ValueError("projection state prompt count mismatch")
    epoch_id = str(state.get("epoch_id", ""))
    if epoch_id != EPOCH_PREFIX + projection_sha[:12].upper():
        raise ValueError("projection epoch id does not match projection hash")
    alignment = state.get("alignment")
    if not isinstance(alignment, Mapping):
        raise ValueError("projection alignment evidence missing")
    if alignment.get("method") != ALIGNMENT_METHOD:
        raise ValueError("projection alignment method drift")
    if alignment.get("within_limits") is not True:
        raise ValueError("projection spatial stability is outside configured limits")
    anchors = [str(prompt_id) for prompt_id in alignment.get("anchor_prompt_ids") or []]
    if anchors != sorted(anchors, key=prompt_key) or len(anchors) != len(set(anchors)):
        raise ValueError("projection anchor ids are not unique/canonically ordered")
    if int(alignment.get("anchor_count", -1)) != len(anchors):
        raise ValueError("projection anchor count mismatch")
    if alignment.get("rms_displacement_micros") is not None:
        if int(alignment["rms_displacement_micros"]) > int(alignment["rms_limit_micros"]):
            raise ValueError("projection RMS displacement limit exceeded")
    if alignment.get("max_displacement_micros") is not None:
        if int(alignment["max_displacement_micros"]) > int(alignment["max_limit_micros"]):
            raise ValueError("projection max displacement limit exceeded")
    provenance = state.get("provenance")
    if not isinstance(provenance, Mapping) or provenance.get("visualization_only") is not True:
        raise ValueError("projection must be explicitly visualization-only")
    stored_hash = str(state.get("content_hash_sha256", ""))
    if stored_hash != sha256_payload(_state_without_hash(state)):
        raise ValueError("projection state content hash mismatch")
