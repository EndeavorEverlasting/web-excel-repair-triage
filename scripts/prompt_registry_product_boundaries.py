#!/usr/bin/env python3
"""Canonical prompt-registry product ownership and composition.

The contract answers two separate questions without mixing them:
- which prompt registries belong to each product; and
- which product inputs the legacy combined Prompt Kit still composes.

The legacy builder consumes this module, so registry paths have one canonical
change site while the current combined output remains a compatibility surface.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "registry" / "prompts" / "product-boundaries.v1.json"
SCHEMA_VERSION = "prompt-registry-product-boundaries/v1"
AFK_PRODUCT = "afk-agent-flow"
TRIAGE_PRODUCT = "triage-local-operations"
MANAGEMENT_REGISTRY = "registry/prompts/management-operations-prompts.v1.json"


class ProductBoundaryError(ValueError):
    """Raised when prompt-registry ownership becomes ambiguous or incomplete."""


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProductBoundaryError(f"required product-boundary file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProductBoundaryError(f"invalid JSON in {path}: {exc}") from exc


def _require_string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ProductBoundaryError(f"{label} must be a non-empty list")
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ProductBoundaryError(f"{label} entries must be non-empty strings")
        normalized.append(item.strip().replace("\\", "/"))
    if len(normalized) != len(set(normalized)):
        raise ProductBoundaryError(f"{label} contains duplicate entries")
    return normalized


def _paths(values: Iterable[str]) -> tuple[Path, ...]:
    return tuple((ROOT / value).resolve() for value in values)


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError as exc:
        raise ProductBoundaryError(f"path escapes repository root: {path}") from exc


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


def _shared(payload: dict[str, Any]) -> dict[str, Any]:
    shared = payload.get("shared_inputs")
    if not isinstance(shared, dict):
        raise ProductBoundaryError("shared_inputs must be an object")
    return shared


def base_registry(payload: dict[str, Any] | None = None) -> Path:
    """Return the one shared base prompt registry."""
    payload = payload or load_contract()
    value = _shared(payload).get("base_registry")
    if not isinstance(value, str) or not value.strip():
        raise ProductBoundaryError("shared_inputs.base_registry must be a non-empty path")
    return (ROOT / value.strip()).resolve()


def content_registries(payload: dict[str, Any] | None = None) -> tuple[Path, ...]:
    """Return shared content-only registries in declared order."""
    payload = payload or load_contract()
    values = _require_string_list(
        _shared(payload).get("content_registries"), "shared_inputs.content_registries"
    )
    return _paths(values)


def extension_registries_for_product(
    product_id: str, payload: dict[str, Any] | None = None
) -> tuple[Path, ...]:
    """Return extension registries owned by one declared product."""
    payload = payload or load_contract()
    values = _require_string_list(
        _product(payload, product_id).get("extension_registries"),
        f"products.{product_id}.extension_registries",
    )
    return _paths(values)


def legacy_extension_registries(
    payload: dict[str, Any] | None = None,
) -> tuple[Path, ...]:
    """Compose legacy extension registries from declared product owners."""
    payload = payload or load_contract()
    legacy = payload.get("legacy_combined_surface")
    if not isinstance(legacy, dict):
        raise ProductBoundaryError("legacy_combined_surface must be an object")
    composition = _require_string_list(
        legacy.get("composition"), "legacy_combined_surface.composition"
    )
    registries: list[Path] = []
    for product_id in composition:
        registries.extend(extension_registries_for_product(product_id, payload))
    return tuple(registries)


def _validate_paths_exist(paths: Iterable[Path], label: str) -> None:
    missing = [_repo_relative(path) for path in paths if not path.is_file()]
    if missing:
        raise ProductBoundaryError(f"{label} references missing files: {missing}")


def validate_product_boundaries(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fail closed when ownership, compatibility composition, or NTH locality drifts."""
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

    afk_paths = extension_registries_for_product(AFK_PRODUCT, payload)
    triage_paths = extension_registries_for_product(TRIAGE_PRODUCT, payload)
    all_owned = (*afk_paths, *triage_paths)
    relative_owned = tuple(_repo_relative(path) for path in all_owned)
    if len(relative_owned) != len(set(relative_owned)):
        raise ProductBoundaryError("an extension registry has more than one product owner")

    afk = _product(payload, AFK_PRODUCT)
    afk_forbidden = _require_string_list(
        afk.get("must_not_include"), f"products.{AFK_PRODUCT}.must_not_include"
    )
    afk_relative = {_repo_relative(path) for path in afk_paths}
    if MANAGEMENT_REGISTRY not in afk_forbidden:
        raise ProductBoundaryError("AFK boundary must explicitly reject the Triage management registry")
    if MANAGEMENT_REGISTRY in afk_relative:
        raise ProductBoundaryError("AFK Agent Flow may not own the Triage management registry")

    triage = _product(payload, TRIAGE_PRODUCT)
    if triage.get("target_repository") != "EndeavorEverlasting/web-excel-repair-triage":
        raise ProductBoundaryError("Triage-local owner must remain this repository")
    triage_relative = tuple(_repo_relative(path) for path in triage_paths)
    if triage_relative != (MANAGEMENT_REGISTRY,):
        raise ProductBoundaryError(
            "first product-boundary slice keeps management operations as one Triage-local owner"
        )

    legacy_paths = legacy_extension_registries(payload)
    if MANAGEMENT_REGISTRY not in {_repo_relative(path) for path in legacy_paths}:
        raise ProductBoundaryError(
            "legacy compatibility composition dropped Triage-local management prompts"
        )

    shared_paths = (base_registry(payload), *content_registries(payload))
    _validate_paths_exist((*shared_paths, *all_owned), "product-boundary contract")

    management_payload = _load_json(ROOT / MANAGEMENT_REGISTRY)
    if not isinstance(management_payload, dict):
        raise ProductBoundaryError("management operations registry must remain a JSON object")
    if management_payload.get("registry_id") != "management-operations-prompts":
        raise ProductBoundaryError("management operations registry identity changed")
    prompts = management_payload.get("prompts")
    if not isinstance(prompts, list):
        raise ProductBoundaryError("management operations registry must define prompts")
    p74 = next(
        (
            prompt
            for prompt in prompts
            if isinstance(prompt, dict) and str(prompt.get("id")) == "P74"
        ),
        None,
    )
    if not isinstance(p74, dict):
        raise ProductBoundaryError("Triage-local management registry lost P74")
    if "Neuron Track Hours" not in str(p74.get("name", "")):
        raise ProductBoundaryError("P74 no longer characterizes the NTH-local boundary")
    if p74.get("profile") != "billing-management":
        raise ProductBoundaryError("P74 billing-management profile changed unexpectedly")

    return {
        "schema_version": SCHEMA_VERSION,
        "legacy_builder": legacy["builder"],
        "legacy_site": legacy["site"],
        "legacy_extension_count": len(legacy_paths),
        "afk_extension_count": len(afk_paths),
        "triage_local_extension_count": len(triage_paths),
        "afk_extension_registries": [_repo_relative(path) for path in afk_paths],
        "triage_local_extension_registries": [_repo_relative(path) for path in triage_paths],
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
