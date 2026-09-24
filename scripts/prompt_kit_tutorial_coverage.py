#!/usr/bin/env python3
"""Derive deterministic Prompt Kit tutorial coverage from the canonical classifier."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import build_prompt_kit_registry as registry  # noqa: E402
from scripts import prompt_classification  # noqa: E402

POLICY_PATH = REPO_ROOT / "registry" / "prompts" / "tutorial-coverage.v1.json"


def _heading_anchor(title: str) -> str:
    """Return the deterministic GitHub-style anchor used by the tutorial policy."""
    normalized = re.sub(r"[^\w\- ]", "", title.strip().casefold())
    return re.sub(r"\s+", "-", normalized).strip("-")


def _tutorial_anchors(text: str) -> set[str]:
    """Collect deterministic Markdown heading anchors, including duplicate suffixes."""
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for line in text.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        base = _heading_anchor(match.group(1))
        if not base:
            continue
        occurrence = counts.get(base, 0)
        counts[base] = occurrence + 1
        anchors.add(base if occurrence == 0 else f"{base}-{occurrence}")
    return anchors


def _validate_tutorial_anchors(policy: dict[str, Any], tutorial_text: str) -> None:
    anchors = _tutorial_anchors(tutorial_text)
    required = {str(policy["fallback_anchor"]).strip()}
    required.update(
        str(record["tutorial_anchor"]).strip()
        for record in policy["wired_prompts"]
        if isinstance(record, dict)
    )
    missing = sorted(anchor for anchor in required if anchor not in anchors)
    if missing:
        raise SystemExit(
            "Tutorial coverage policy references missing tutorial anchors: "
            + ", ".join(missing)
        )


def _load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "prompt-tutorial-coverage/v1":
        raise SystemExit(f"Unsupported tutorial coverage schema: {path}")

    required_strings = (
        "policy_id",
        "tutorial_entry",
        "tutorial_document",
        "fallback_anchor",
        "wired_status",
        "fallback_status",
        "wiring_rule",
    )
    for field in required_strings:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"Tutorial coverage policy field must be non-empty: {field}")

    wired = payload.get("wired_prompts")
    if not isinstance(wired, list):
        raise SystemExit("Tutorial coverage policy must define wired_prompts")

    seen: set[str] = set()
    for index, record in enumerate(wired):
        if not isinstance(record, dict):
            raise SystemExit(f"Tutorial coverage record {index} is not an object")
        for field in ("prompt_id", "tutorial_anchor", "reason"):
            value = record.get(field)
            if not isinstance(value, str) or not value.strip():
                raise SystemExit(
                    f"Tutorial coverage record {index} field must be non-empty: {field}"
                )
        prompt_id = str(record["prompt_id"]).strip().upper()
        if prompt_id in seen:
            raise SystemExit(f"Duplicate tutorial coverage prompt id: {prompt_id}")
        seen.add(prompt_id)

    tutorial_path = REPO_ROOT / str(payload["tutorial_document"])
    if not tutorial_path.is_file():
        raise SystemExit(f"Tutorial coverage document is missing: {tutorial_path}")
    _validate_tutorial_anchors(payload, tutorial_path.read_text(encoding="utf-8"))
    return payload


def _wired_map(policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(record["prompt_id"]).strip().upper(): dict(record)
        for record in policy["wired_prompts"]
    }


def coverage_for_prompt(
    prompt: dict[str, Any], policy: dict[str, Any] | None = None
) -> dict[str, Any]:
    policy = policy or _load_policy()
    prompt_id = str(prompt.get("id", "")).strip().upper()
    name = str(prompt.get("name", "")).strip()
    prompt_type = str(prompt.get("type", "")).strip()
    if not prompt_id or not name or not prompt_type:
        raise SystemExit(f"Tutorial coverage requires id/name/type: {prompt}")

    section = prompt_classification.require_known_prompt_type(prompt_type)
    curated = _wired_map(policy).get(prompt_id)
    status = str(policy["wired_status"] if curated else policy["fallback_status"])
    anchor = str(curated["tutorial_anchor"] if curated else policy["fallback_anchor"])

    return {
        "prompt_id": prompt_id,
        "prompt_name": name,
        "prompt_type": prompt_type,
        "classifier_section": section,
        "tutorial_route": [
            str(policy["tutorial_entry"]),
            section,
            f"{prompt_id} — {name}",
        ],
        "tutorial_document": str(policy["tutorial_document"]),
        "tutorial_anchor": anchor,
        "wiring_status": status,
        "needs_wiring": False,
        "wiring_source": "curated" if curated else "classifier",
        "curated": curated is not None,
        "reason": str(curated["reason"]) if curated else (
            "The classifier-derived route is the canonical prompt-specific tutorial path; "
            "no manual wiring step is required."
        ),
    }


def audit(
    prompts: list[dict[str, Any]] | None = None,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy = policy or _load_policy()
    prompts = prompts if prompts is not None else registry.load_prompt_kit_registry()

    prompt_ids: list[str] = []
    duplicate_ids: list[str] = []
    seen: set[str] = set()
    routes: list[dict[str, Any]] = []
    route_errors: list[str] = []

    for prompt in prompts:
        prompt_id = str(prompt.get("id", "")).strip().upper()
        if prompt_id in seen:
            duplicate_ids.append(prompt_id)
            continue
        seen.add(prompt_id)
        prompt_ids.append(prompt_id)
        try:
            route = coverage_for_prompt(prompt, policy)
        except SystemExit as exc:
            route_errors.append(f"{prompt_id or '?'}: {exc}")
            continue
        if len(route["tutorial_route"]) != 3 or not all(route["tutorial_route"]):
            route_errors.append(f"{prompt_id}: incomplete tutorial route")
            continue
        routes.append(route)

    curated = _wired_map(policy)
    unknown_wired_ids = sorted(set(curated) - set(prompt_ids))
    needs_wiring = sorted(
        (route for route in routes if route["needs_wiring"]),
        key=lambda route: (
            str(route["classifier_section"]),
            str(route["prompt_id"]),
        ),
    )
    curated_routes = [route for route in routes if route["curated"]]
    classifier_routes = [route for route in routes if not route["curated"]]

    ready = (
        not duplicate_ids
        and not route_errors
        and not unknown_wired_ids
        and not needs_wiring
        and len(routes) == len(prompt_ids)
    )
    return {
        "schema_version": "prompt-tutorial-coverage-report/v1",
        "policy_id": str(policy["policy_id"]),
        "tutorial_document": str(policy["tutorial_document"]),
        "prompt_count": len(prompt_ids),
        "route_covered_count": len(routes),
        "wired_count": len(routes),
        "curated_wired_count": len(curated_routes),
        "classifier_wired_count": len(classifier_routes),
        "needs_wiring_count": len(needs_wiring),
        "needs_wiring_prompt_ids": [route["prompt_id"] for route in needs_wiring],
        "unknown_wired_prompt_ids": unknown_wired_ids,
        "duplicate_prompt_ids": sorted(set(duplicate_ids)),
        "route_errors": route_errors,
        "ready": ready,
        "routes": routes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit complete classifier-backed tutorial wiring and optional curated teaching paths."
        )
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print compact JSON without the full per-prompt route list.",
    )
    parser.add_argument(
        "--prompt-id",
        help="Print the coverage record for one prompt id instead of the full audit.",
    )
    args = parser.parse_args(argv)

    report = audit()
    if args.prompt_id:
        wanted = args.prompt_id.strip().upper()
        match = next(
            (route for route in report["routes"] if route["prompt_id"] == wanted),
            None,
        )
        if match is None:
            raise SystemExit(f"Prompt is not present in tutorial coverage: {wanted}")
        print(json.dumps(match, indent=2, sort_keys=True))
    elif args.summary:
        compact = {key: value for key, value in report.items() if key != "routes"}
        print(json.dumps(compact, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
