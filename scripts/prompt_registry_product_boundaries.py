#!/usr/bin/env python3
"""Validate and expose prompt-registry product ownership boundaries.

This module answers one maintenance question: which canonical prompt-registry
inputs belong to AFK Agent Flow, and which remain WebExcel Triage-local?
It deliberately does not change the legacy combined Prompt Kit build.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_prompt_kit_registry  # noqa: E402

CONTRACT = ROOT / "registry" / "prompts" / "product-boundaries.v1.json"
SCHEMA_VERSION = "prompt-registry-product-boundaries/v1"
AFK_PRODUCT = "afk-agent-flow"
TRIAGE_PRODUCT = "triage-local-operations"
MANAGEMENT_REGISTRY = "registry/prompts/management-operations-prompts.v1.json"


class ProductBoundaryError(ValueError):
    """Raised when prompt-registry ownership becomes ambiguous or drifts."""


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProductBoundaryError(f"required product-boundary file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProductBoundaryError(f"invalid JSON in {path}: {exc}") from exc


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError as exc:
        raise ProductBoundaryError(f"path escapes repository root: {path}") from exc


def _require_string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ProductBoundaryError(f"{label} must be a non-empty list")
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ProductBoundaryError(f"{label} entries must be non-empty strings")
        normalized.append(item.strip().replace("\\", "/"))
    if len(normalized) != len(set(normalized)):
        raise ProductBoundaryError(f"{label} contains duplicate paths")
    return normalized


def load_contract(path: Path = CONTRACT) -> dict[str, Any]:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ProductBoundaryError("product-boundary contract must be a JSON object")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ProductBoundaryError(
            f"unsupported product-boundary schema: {payload.get('schema_version')!r}"
        )
    if payload.get("contract_id") != "prompt-registry-product-boundaries":
        raise ProductBoundaryError("unexpected product-boundary contract_id")
    return payload


def _product(payload: dict[str, Any], product_id: str) -> dict[str, Any]:
    products = payload.get("products")
    if not isinstance(products, dict):
        raise ProductBoundaryError("contract must define a products object")
    product = products.get(product_id)
    if not isinstance(product, dict):
        raise ProductBoundaryError(f"contract is missing product owner: {product_id}")
    return product


def extension_registries_for_product(
    product_id: str, payload: dict[str, Any] | None = None
) -> tuple[Path, ...]:
    """Return canonical extension registries owned by one declared product."""
    payload = payload or load_contract()
    raw_paths = _require_string_list(
        _product(payload, product_id).get("extension_registries"),
        f"products.{product_id}.extension_registries",
    )
    return tuple((ROOT / path).resolve() for path in raw_paths)


def _legacy_extension_paths() -> tuple[str, ...]:
    return tuple(
        _repo_relative(Path(path)) for path in build_prompt_kit_registry.EXTENSION_REGISTRIES
    )


def _legacy_content_paths() -> tuple[str, ...]:
    return tuple(
        _repo_relative(Path(path)) for path in build_prompt_kit_registry.CONTENT_REGISTRIES
    )


def _validate_declared_paths_exist(paths: Iterable[str], label: str) -> None:
    missing = [path for path in paths if not (ROOT / path).is_file()]
    if missing:
        raise ProductBoundaryError(f"{label} references missing files: {missing}")


def validate_product_boundaries(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fail closed when registry ownership no longer matches the legacy builder."""
    payload = payload or load_contract()

    legacy = payload.get("legacy_combined_surface")
    if not isinstance(legacy, dict):
        raise ProductBoundaryError("legacy_combined_surface must be an object")
    if legacy.get("status") != "compatibility_surface":
        raise ProductBoundaryError("legacy Prompt Kit surface must remain compatibility_surface")
    if legacy.get("builder") != "scripts/build_prompt_kit_registry.py":
        raise ProductBoundaryError("legacy builder identity changed without contract update")
    if legacy.get("site") != "web/prompt-kit/index.html":
        raise ProductBoundaryError("legacy site identity changed without contract update")
    composition = _require_string_list(
        legacy.get("composition"), "legacy_combined_surface.composition"
    )
    if composition != [AFK_PRODUCT, TRIAGE_PRODUCT]:
        raise ProductBoundaryError(
            "legacy composition must explicitly preserve AFK + Triage-local inputs"
        )

    shared = payload.get("shared_inputs")
    if not isinstance(shared, dict):
        raise ProductBoundaryError("shared_inputs must be an object")
    base_registry = shared.get("base_registry")
    if not isinstance(base_registry, str) or not base_registry.strip():
        raise ProductBoundaryError("shared_inputs.base_registry must be a non-empty path")
    base_registry = base_registry.strip().replace("\\", "/")
    actual_base = _repo_relative(build_prompt_kit_registry.BASE_REGISTRY)
    if base_registry != actual_base:
        raise ProductBoundaryError(
            f"base registry ownership drift: contract={base_registry} builder={actual_base}"
        )
    content_registries = _require_string_list(
        shared.get("content_registries"), "shared_inputs.content_registries"
    )
    if tuple(content_registries) != _legacy_content_paths():
        raise ProductBoundaryError(
            "shared content registry set no longer matches the canonical builder"
        )

    afk_paths = tuple(
        _repo_relative(path) for path in extension_registries_for_product(AFK_PRODUCT, payload)
    )
    triage_paths = tuple(
        _repo_relative(path)
        for path in extension_registries_for_product(TRIAGE_PRODUCT, payload)
    )
    all_owned = afk_paths + triage_paths
    if len(all_owned) != len(set(all_owned)):
        raise ProductBoundaryError("an extension registry has more than one product owner")

    legacy_paths = _legacy_extension_paths()
    if set(all_owned) != set(legacy_paths):
        missing = sorted(set(legacy_paths) - set(all_owned))
        extra = sorted(set(all_owned) - set(legacy_paths))
        raise ProductBoundaryError(
            f"product ownership does not cover the legacy builder exactly; missing={missing}, extra={extra}"
        )

    _validate_declared_paths_exist((base_registry, *content_registries, *all_owned), "contract")

    afk = _product(payload, AFK_PRODUCT)
    afk_forbidden = _require_string_list(
        afk.get("must_not_include"), f"products.{AFK_PRODUCT}.must_not_include"
    )
    if MANAGEMENT_REGISTRY not in afk_forbidden:
        raise ProductBoundaryError("AFK boundary must explicitly reject the Triage management registry")
    if MANAGEMENT_REGISTRY in afk_paths:
        raise ProductBoundaryError("AFK Agent Flow may not own the Triage management registry")

    triage = _product(payload, TRIAGE_PRODUCT)
    if triage.get("target_repository") != "EndeavorEverlasting/web-excel-repair-triage":
        raise ProductBoundaryError("Triage-local owner must remain this repository")
    if triage_paths != (MANAGEMENT_REGISTRY,):
        raise ProductBoundaryError(
            "first product-boundary slice keeps management operations as one explicit Triage-local owner"
        )

    management_payload = _load_json(ROOT / MANAGEMENT_REGISTRY)
    if not isinstance(management_payload, dict):
        raise ProductBoundaryError("management operations registry must remain a JSON object")
    if management_payload.get("registry_id") != "management-operations-prompts":
        raise ProductBoundaryError("management operations registry identity changed")
    prompts = management_payload.get("prompts")
    if not isinstance(prompts, list):
        raise ProductBoundaryError("management operations registry must define prompts")
    by_id = {
        str(prompt.get("id")): prompt
        for prompt in prompts
        if isinstance(prompt, dict) and prompt.get("id")
    }
    p74 = by_id.get("P74")
    if not isinstance(p74, dict):
        raise ProductBoundaryError("Triage-local management registry lost P74")
    if "Neuron Track Hours" not in str(p74.get("name", "")):
        raise ProductBoundaryError("P74 no longer characterizes the NTH-local ownership boundary")
    if p74.get("profile") != "billing-management":
        raise ProductBoundaryError("P74 billing-management profile changed unexpectedly")

    if MANAGEMENT_REGISTRY not in legacy_paths:
        raise ProductBoundaryError(
            "legacy builder stopped composing Triage-local management prompts; that is a behavior change"
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "legacy_builder": legacy["builder"],
        "legacy_site": legacy["site"],
        "legacy_extension_count": len(legacy_paths),
        "afk_extension_count": len(afk_paths),
        "triage_local_extension_count": len(triage_paths),
        "afk_extension_registries": list(afk_paths),
        "triage_local_extension_registries": list(triage_paths),
        "legacy_behavior_preserved": True,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate prompt-registry ownership across AFK Agent Flow and Triage."
    )
    parser.add_argument("--summary", action="store_true", help="print JSON validation summary")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = validate_product_boundaries()
    except ProductBoundaryError as exc:
        print(f"Prompt registry product boundary: FAIL: {exc}", file=sys.stderr)
        return 1
    if args.summary:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("Prompt registry product boundary: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
